import logging
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
from typing import Optional
from app.database import get_db
from app.models import Review, User
from app.schemas import ReviewRequest, PRReviewRequest, ReviewResponse
from app.llm_client import review_code, LLMReviewError
from app.dependencies import get_current_user
from app.github_client import parse_pr_url, fetch_pr_files
from app.pr_utils import build_diff_prompt
from app.review_service import review_units, build_prompt

logger = logging.getLogger(__name__)



router = APIRouter(prefix="/reviews", tags=["reviews"])

@router.post("/", response_model=ReviewResponse)
def create_review(
    payload: ReviewRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    try:
        findings, warnings = review_units([(None, payload.code)])
        if not findings and warnings:
            raise HTTPException(status_code=502, detail="; ".join(warnings))
    except LLMReviewError as e:
        raise HTTPException(status_code=502, detail={
            "error": "LLM returned malformed JSON",
            "raw_response": e.raw_response
        })
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"LLM review failed: {e}")

    review = Review(
        user_id=current_user.id, code_snippet=payload.code, findings=findings,
        warnings=warnings or None
    )
    try:
        db.add(review)
        db.commit()
        db.refresh(review)
    except SQLAlchemyError:
        db.rollback()
        logger.exception("Failed to save review to database")
        raise HTTPException(status_code=500, detail="Failed to save review")
    return ReviewResponse(id=review.id, findings=findings, warnings=warnings or None)


@router.post("/pr", response_model=ReviewResponse)
def create_pr_review(
    payload: PRReviewRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    try:
        owner, repo, pr_number = parse_pr_url(payload.pr_url)
        files = fetch_pr_files(owner, repo, pr_number)
    except ValueError as e:
        status_code = 404 if "not found" in str(e).lower() else 400
        raise HTTPException(status_code=status_code, detail=str(e))

    units = [(f["filename"], f["patch"]) for f in files if f.get("patch")]
    skipped = [f["filename"] for f in files if not f.get("patch")]

    if not units:
        raise HTTPException(status_code=404, detail="No reviewable files found in this PR")

    try:
        findings, warnings = review_units(units)
    except LLMReviewError as e:
        raise HTTPException(status_code=502, detail={
            "error": "LLM returned malformed JSON",
            "raw_response": e.raw_response
        })
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"LLM review failed: {e}")

    if skipped:
        warnings.append(f"{len(skipped)} file(s) skipped (binary or unavailable): {', '.join(skipped)}")

    review = Review(
        user_id=current_user.id, code_snippet=build_prompt(units), findings=findings,
        warnings=warnings or None, source="github_pr",
        repo_full_name=f"{owner}/{repo}", pr_number=pr_number, pr_url=payload.pr_url
    )
    try:
        db.add(review)
        db.commit()
        db.refresh(review)
    except SQLAlchemyError:
        db.rollback()
        logger.exception("Failed to save review to database")
        raise HTTPException(status_code=500, detail="Failed to save review")
    return ReviewResponse(id=review.id, findings=findings, warnings=warnings or None)


@router.get("/")
def list_reviews(
    severity: Optional[str] = Query(None),
    category: Optional[str] = Query(None),
    limit: int = Query(20, le=100),
    offset: int = Query(0),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    reviews = (
        db.query(Review)
        .filter(Review.user_id == current_user.id)
        .order_by(Review.created_at.desc())
        .offset(offset).limit(limit).all()
    )
    results = []
    for r in reviews:
        findings = r.findings or []
        if severity:
            findings = [f for f in findings if f.get("severity") == severity]
        if category:
            findings = [f for f in findings if f.get("category") == category]
        results.append({"id": r.id, "created_at": r.created_at, "findings": findings})
    return results


@router.get("/{review_id}")
def get_review(review_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    review = db.query(Review).filter(Review.id == review_id, Review.user_id == current_user.id).first()
    if not review:
        raise HTTPException(status_code=404, detail="Review not found")
    return {"id": review.id, "findings": review.findings, "created_at": review.created_at}    
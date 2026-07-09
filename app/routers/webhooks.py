import logging
from fastapi import APIRouter, Request, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from app.database import SessionLocal
from app.webhook_utils import verify_github_signature
from app.models import User, Review
from app.review_service import review_units, build_prompt
from app.github_client import fetch_pr_files
from app.config import settings

router = APIRouter(prefix="/webhooks", tags=["webhooks"])
logger = logging.getLogger("codesage")

RELEVANT_ACTIONS = {"opened", "synchronize", "reopened"}

@router.post("/github")
async def github_webhook(request: Request, background_tasks: BackgroundTasks):
    body = await request.body()
    signature = request.headers.get("X-Hub-Signature-256")

    if not verify_github_signature(body, signature):
        raise HTTPException(status_code=401, detail="Invalid webhook signature")

    event_type = request.headers.get("X-GitHub-Event")
    if event_type != "pull_request":
        return {"status": "ignored", "reason": f"event type '{event_type}' not handled"}

    payload = await request.json()
    action = payload.get("action")
    if action not in RELEVANT_ACTIONS:
        return {"status": "ignored", "reason": f"action '{action}' not relevant"}

    pr = payload["pull_request"]
    owner = payload["repository"]["owner"]["login"]
    repo = payload["repository"]["name"]
    pr_number = pr["number"]
    head_sha = pr["head"]["sha"]
    pr_url = pr["html_url"]

    background_tasks.add_task(process_pr_review, owner, repo, pr_number, head_sha, pr_url)

    return {"status": "accepted", "pr": f"{owner}/{repo}#{pr_number}"}


def process_pr_review(owner: str, repo: str, pr_number: int, head_sha: str, pr_url: str):
    db: Session = SessionLocal()
    try:
        existing = (
            db.query(Review)
            .filter(Review.repo_full_name == f"{owner}/{repo}", Review.pr_number == pr_number, Review.head_sha == head_sha)
            .first()
        )
        if existing:
            logger.info(f"Skipping {owner}/{repo}#{pr_number} — already reviewed at {head_sha}")
            return

        user = db.query(User).filter(User.email == settings.webhook_review_user_email).first()
        if not user:
            logger.error(f"Webhook review user '{settings.webhook_review_user_email}' not found — cannot save review")
            return

        files = fetch_pr_files(owner, repo, pr_number)
        units = [(f["filename"], f["patch"]) for f in files if f.get("patch")]
        skipped = [f["filename"] for f in files if not f.get("patch")]

        if not units:
            logger.info(f"No reviewable files in {owner}/{repo}#{pr_number}")
            return

        findings, warnings = review_units(units)
        if skipped:
            warnings.append(f"{len(skipped)} file(s) skipped (binary or unavailable)")

        review = Review(
            user_id=user.id, code_snippet=build_prompt(units), findings=findings,
            warnings=warnings or None, source="github_pr", repo_full_name=f"{owner}/{repo}",
            pr_number=pr_number, pr_url=pr_url, head_sha=head_sha
        )
        db.add(review)
        db.commit()
        logger.info(f"Webhook review completed for {owner}/{repo}#{pr_number} at {head_sha}")
    except Exception:
        logger.exception(f"Webhook review failed for {owner}/{repo}#{pr_number}")
    finally:
        db.close()
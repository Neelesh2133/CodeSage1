from pydantic import BaseModel
from typing import Literal, Optional

class Finding(BaseModel):
    file_path: Optional[str] = None
    line_number: Optional[int] = None
    severity: Literal["critical", "high", "medium", "low", "info"]
    category: Literal["bug", "security", "performance", "style", "maintainability"]
    message: str
    suggestion: Optional[str] = None

class ReviewRequest(BaseModel):
    code: str

class ReviewResponse(BaseModel):
    id: int
    findings: list[Finding]

class PRReviewRequest(BaseModel):
    pr_url: str    


class ReviewResponse(BaseModel):
    id: int
    findings: list[Finding]
    warnings: list[str] | None = None    
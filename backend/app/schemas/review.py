from datetime import datetime
from enum import Enum
from typing import List, Optional
from uuid import UUID

from pydantic import BaseModel, Field

from app.schemas.grading import GradingResultResponse


class SubmissionStatus(str, Enum):
    uploaded = "uploaded"
    parsed = "parsed"
    grading = "grading"
    graded = "graded"
    reviewed = "reviewed"


# ── Submission list ───────────────────────────────────────────────────────────

class SubmissionSummary(BaseModel):
    id: UUID
    student_name: str
    student_code: str
    status: SubmissionStatus
    total_score: Optional[float] = None       # sum of effective scores (approved/revised)
    max_total_score: float                     # sum of question max_scores
    graded_questions: int
    total_questions: int

    model_config = {"from_attributes": True}


class SubmissionListResponse(BaseModel):
    submissions: List[SubmissionSummary]
    total: int


# ── Submission detail (review panel) ─────────────────────────────────────────

class SubmissionDetailResponse(BaseModel):
    id: UUID
    exam_id: UUID
    student_name: str
    student_code: str
    status: SubmissionStatus
    grading_results: List[GradingResultResponse]
    total_score: Optional[float] = None
    max_total_score: float
    created_at: datetime


# ── Review actions ────────────────────────────────────────────────────────────

class ApproveResultRequest(BaseModel):
    """Approve LLM score as-is. No body needed, but schema provided for consistency."""
    pass


class ReviseResultRequest(BaseModel):
    expert_score: float = Field(..., ge=0, description="Override score from expert")
    expert_feedback: str = Field(..., min_length=1, description="Reason for revision")


class BulkApproveRequest(BaseModel):
    exam_id: UUID


class BulkApproveResponse(BaseModel):
    approved_count: int
    message: str

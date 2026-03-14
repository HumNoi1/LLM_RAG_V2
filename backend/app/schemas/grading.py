from datetime import datetime
from enum import Enum
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field


class GradingStatus(str, Enum):
    idle = "idle"
    running = "running"
    completed = "completed"
    failed = "failed"


class GradingResultStatus(str, Enum):
    pending_review = "pending_review"
    approved = "approved"
    revised = "revised"


# ── Requests ──────────────────────────────────────────────────────────────────


class GradingStartRequest(BaseModel):
    exam_id: UUID


# ── Responses ─────────────────────────────────────────────────────────────────


class GradingProgressResponse(BaseModel):
    exam_id: UUID
    status: GradingStatus
    total_submissions: int
    completed: int
    failed: int
    progress_percent: float = Field(..., ge=0, le=100)


class GradingResultResponse(BaseModel):
    id: UUID
    submission_id: UUID
    question_id: UUID
    question_number: int
    llm_score: float
    expert_score: Optional[float] = None
    max_score: float
    reasoning: str
    expert_feedback: Optional[str] = None
    status: GradingResultStatus
    created_at: datetime

    model_config = {"from_attributes": True}

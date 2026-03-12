from datetime import datetime
from typing import List, Optional
from uuid import UUID

from pydantic import BaseModel, Field


# ── Question schemas ──────────────────────────────────────────────────────────

class QuestionCreate(BaseModel):
    question_number: int = Field(..., ge=1)
    question_text: str = Field(..., min_length=1)
    max_score: float = Field(..., gt=0)


class QuestionUpdate(BaseModel):
    question_text: Optional[str] = Field(None, min_length=1)
    max_score: Optional[float] = Field(None, gt=0)


class QuestionResponse(BaseModel):
    id: UUID
    exam_id: UUID
    question_number: int
    question_text: str
    max_score: float
    created_at: datetime

    model_config = {"from_attributes": True}


# ── Exam schemas ──────────────────────────────────────────────────────────────

class ExamCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=255)
    subject: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    total_questions: int = Field(..., ge=1)


class ExamUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=1, max_length=255)
    subject: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None


class ExamResponse(BaseModel):
    id: UUID
    title: str
    subject: str
    description: Optional[str]
    created_by: UUID
    total_questions: int
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class ExamDetailResponse(ExamResponse):
    """Exam with its questions list."""
    questions: List[QuestionResponse] = []


class ExamListResponse(BaseModel):
    exams: List[ExamResponse]
    total: int

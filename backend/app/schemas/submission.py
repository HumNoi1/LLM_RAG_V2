from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime
from app.schemas.enums import SubmissionStatus, GradingStatus


class StudentCreate(BaseModel):
    student_code: str = Field(min_length=1)
    full_name: str = Field(min_length=1)


class StudentResponse(BaseModel):
    id: str
    student_code: str
    full_name: str
    created_by: str
    created_at: datetime

    model_config = {"from_attributes": True}


class SubmissionResponse(BaseModel):
    id: str
    exam_id: str
    student_id: str
    original_filename: str
    file_path: str
    parsed_text: Optional[str]
    status: SubmissionStatus
    created_at: datetime

    model_config = {"from_attributes": True}


class GradingResultResponse(BaseModel):
    id: str
    submission_id: str
    question_id: str
    student_answer_text: Optional[str]
    llm_score: Optional[float]
    llm_max_score: Optional[float]
    llm_reasoning: Optional[str]
    llm_model_used: Optional[str]
    expert_score: Optional[float]
    expert_feedback: Optional[str]
    status: GradingStatus
    graded_at: Optional[datetime]
    reviewed_at: Optional[datetime]
    reviewed_by: Optional[str]

    model_config = {"from_attributes": True}


class GradingReviseRequest(BaseModel):
    expert_score: float = Field(ge=0)
    expert_feedback: str = Field(min_length=1)

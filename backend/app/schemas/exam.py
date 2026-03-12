from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


class ExamCreate(BaseModel):
    title: str = Field(min_length=1)
    subject: str = Field(min_length=1)
    description: Optional[str] = None


class ExamUpdate(BaseModel):
    title: Optional[str] = None
    subject: Optional[str] = None
    description: Optional[str] = None


class ExamResponse(BaseModel):
    id: str
    title: str
    subject: str
    description: Optional[str]
    created_by: str
    total_questions: int
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class QuestionCreate(BaseModel):
    question_number: int = Field(gt=0)
    question_text: str = Field(min_length=1)
    max_score: float = Field(gt=0)


class QuestionUpdate(BaseModel):
    question_text: Optional[str] = None
    max_score: Optional[float] = Field(default=None, gt=0)


class QuestionResponse(BaseModel):
    id: str
    exam_id: str
    question_number: int
    question_text: str
    max_score: float
    created_at: datetime

    model_config = {"from_attributes": True}


class RubricCreate(BaseModel):
    criteria_text: str
    score_range: str
    description: str


class RubricResponse(BaseModel):
    id: str
    question_id: str
    criteria_text: str
    score_range: str
    description: str

    model_config = {"from_attributes": True}

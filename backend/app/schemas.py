from pydantic import BaseModel, EmailStr, Field
from typing import Optional
from datetime import datetime
from enum import Enum


# ========================
# Enums
# ========================

class UserRole(str, Enum):
    teacher = "teacher"
    admin = "admin"


class DocType(str, Enum):
    answer_key = "answer_key"
    rubric = "rubric"
    course_material = "course_material"


class EmbeddingStatus(str, Enum):
    pending = "pending"
    processing = "processing"
    completed = "completed"
    failed = "failed"


class SubmissionStatus(str, Enum):
    uploaded = "uploaded"
    parsed = "parsed"
    grading = "grading"
    graded = "graded"
    reviewed = "reviewed"


class GradingStatus(str, Enum):
    pending_review = "pending_review"
    approved = "approved"
    revised = "revised"


# ========================
# User Schemas
# ========================

class UserCreate(BaseModel):
    email: EmailStr
    password: str = Field(min_length=6)
    full_name: str = Field(min_length=1)
    role: UserRole = UserRole.teacher


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class UserResponse(BaseModel):
    id: str
    email: str
    full_name: str
    role: UserRole
    created_at: datetime

    model_config = {"from_attributes": True}


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class TokenRefreshRequest(BaseModel):
    refresh_token: str


# ========================
# Exam Schemas
# ========================

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


# ========================
# ExamQuestion Schemas
# ========================

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


# ========================
# Rubric Schemas
# ========================

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


# ========================
# Document Schemas
# ========================

class DocumentResponse(BaseModel):
    id: str
    exam_id: str
    doc_type: DocType
    original_filename: str
    file_path: str
    embedding_status: EmbeddingStatus
    chunk_count: int
    created_at: datetime

    model_config = {"from_attributes": True}


# ========================
# Student Schemas
# ========================

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


# ========================
# StudentSubmission Schemas
# ========================

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


# ========================
# GradingResult Schemas
# ========================

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

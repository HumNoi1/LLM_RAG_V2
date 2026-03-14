from pydantic import BaseModel, Field
from typing import Optional

from app.schemas.auth import (
    UserRole,
    UserCreate,
    UserLogin,
    UserResponse,
    TokenResponse,
    TokenRefreshRequest,
)
from app.schemas.exams import (
    ExamCreate,
    ExamUpdate,
    ExamResponse,
    ExamDetailResponse,
    ExamListResponse,
    QuestionCreate,
    QuestionUpdate,
    QuestionResponse,
)
from app.schemas.documents import (
    DocType,
    EmbeddingStatus,
    DocumentResponse,
    DocumentListResponse,
    DocumentUploadResponse,
)
from app.schemas.grading import (
    GradingStatus,
    GradingResultStatus,
    GradingStartRequest,
    GradingProgressResponse,
    GradingResultResponse,
)
from app.schemas.review import (
    SubmissionStatus,
    SubmissionSummary,
    SubmissionListResponse,
    SubmissionDetailResponse,
    ApproveResultRequest,
    ReviseResultRequest,
    BulkApproveRequest,
    BulkApproveResponse,
)

__all__ = [
    # auth
    "UserRole",
    "UserCreate",
    "UserLogin",
    "UserResponse",
    "TokenResponse",
    "TokenRefreshRequest",
    # exams
    "ExamCreate",
    "ExamUpdate",
    "ExamResponse",
    "ExamDetailResponse",
    "ExamListResponse",
    "QuestionCreate",
    "QuestionUpdate",
    "QuestionResponse",
    # documents
    "DocType",
    "EmbeddingStatus",
    "DocumentResponse",
    "DocumentListResponse",
    "DocumentUploadResponse",
    # grading
    "GradingStatus",
    "GradingResultStatus",
    "GradingStartRequest",
    "GradingProgressResponse",
    "GradingResultResponse",
    # review
    "SubmissionStatus",
    "SubmissionSummary",
    "SubmissionListResponse",
    "SubmissionDetailResponse",
    "ApproveResultRequest",
    "ReviseResultRequest",
    "BulkApproveRequest",
    "BulkApproveResponse",
    # common
    "ErrorResponse",
]


# ── Common error response model ──────────────────────────────────────────────
# ใช้สำหรับ document error responses ใน OpenAPI spec


class ErrorResponse(BaseModel):
    """รูปแบบ error response มาตรฐานของระบบ"""

    detail: str = Field(..., description="รายละเอียดข้อผิดพลาด")
    error_type: Optional[str] = Field(
        None, description="ประเภท exception เช่น NotFoundError, ValidationError"
    )

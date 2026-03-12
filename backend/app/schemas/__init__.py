# Re-export everything for backward compatibility (existing imports from app.schemas still work)
from app.schemas.enums import (
    UserRole,
    DocType,
    EmbeddingStatus,
    SubmissionStatus,
    GradingStatus,
)
from app.schemas.auth import (
    UserCreate,
    UserLogin,
    UserResponse,
    TokenResponse,
    TokenRefreshRequest,
)
from app.schemas.exam import (
    ExamCreate,
    ExamUpdate,
    ExamResponse,
    QuestionCreate,
    QuestionUpdate,
    QuestionResponse,
    RubricCreate,
    RubricResponse,
)
from app.schemas.document import DocumentResponse
from app.schemas.submission import (
    StudentCreate,
    StudentResponse,
    SubmissionResponse,
    GradingResultResponse,
    GradingReviseRequest,
)

__all__ = [
    # Enums
    "UserRole",
    "DocType",
    "EmbeddingStatus",
    "SubmissionStatus",
    "GradingStatus",
    # Auth
    "UserCreate",
    "UserLogin",
    "UserResponse",
    "TokenResponse",
    "TokenRefreshRequest",
    # Exam
    "ExamCreate",
    "ExamUpdate",
    "ExamResponse",
    "QuestionCreate",
    "QuestionUpdate",
    "QuestionResponse",
    "RubricCreate",
    "RubricResponse",
    # Document
    "DocumentResponse",
    # Submission & Grading
    "StudentCreate",
    "StudentResponse",
    "SubmissionResponse",
    "GradingResultResponse",
    "GradingReviseRequest",
]

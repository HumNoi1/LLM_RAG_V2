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
from app.schemas.auth import (
    LoginRequest,
    RegisterRequest,
    TokenResponse,
    RefreshRequest,
    UserResponse,
    UserRole,
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
    "LoginRequest", "RegisterRequest", "TokenResponse", "RefreshRequest",
    "UserResponse", "UserRole",
    # exams
    "ExamCreate", "ExamUpdate", "ExamResponse", "ExamDetailResponse",
    "ExamListResponse", "QuestionCreate", "QuestionUpdate", "QuestionResponse",
    # documents
    "DocType", "EmbeddingStatus", "DocumentResponse",
    "DocumentListResponse", "DocumentUploadResponse",
    # grading
    "GradingStatus", "GradingResultStatus", "GradingStartRequest",
    "GradingProgressResponse", "GradingResultResponse",
    # review
    "SubmissionStatus", "SubmissionSummary", "SubmissionListResponse",
    "SubmissionDetailResponse", "ApproveResultRequest", "ReviseResultRequest",
    "BulkApproveRequest", "BulkApproveResponse",
]

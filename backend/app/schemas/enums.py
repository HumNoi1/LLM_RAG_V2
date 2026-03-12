from enum import Enum


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

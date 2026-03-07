from datetime import datetime
from enum import Enum
from typing import List, Optional
from uuid import UUID

from pydantic import BaseModel


class DocType(str, Enum):
    answer_key = "answer_key"
    rubric = "rubric"
    course_material = "course_material"


class EmbeddingStatus(str, Enum):
    pending = "pending"
    processing = "processing"
    completed = "completed"
    failed = "failed"


# ── Responses ─────────────────────────────────────────────────────────────────

class DocumentResponse(BaseModel):
    id: UUID
    exam_id: UUID
    doc_type: DocType
    original_filename: str
    embedding_status: EmbeddingStatus
    chunk_count: Optional[int] = None
    created_at: datetime

    model_config = {"from_attributes": True}


class DocumentUploadResponse(BaseModel):
    message: str
    document: DocumentResponse


class DocumentListResponse(BaseModel):
    documents: List[DocumentResponse]
    total: int

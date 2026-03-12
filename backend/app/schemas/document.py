from pydantic import BaseModel
from datetime import datetime
from app.schemas.enums import DocType, EmbeddingStatus


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

from datetime import datetime
from enum import Enum
from typing import List, Optional
from uuid import UUID

from pydantic import BaseModel, Field


class DocType(str, Enum):
    """ประเภทเอกสารอ้างอิง"""

    answer_key = "answer_key"
    rubric = "rubric"
    course_material = "course_material"


class EmbeddingStatus(str, Enum):
    """สถานะการ embed เอกสารลง vector DB"""

    pending = "pending"
    processing = "processing"
    completed = "completed"
    failed = "failed"


# ── Responses ─────────────────────────────────────────────────────────────────


class DocumentResponse(BaseModel):
    """ข้อมูลเอกสารที่ส่งกลับจาก API"""

    id: UUID = Field(..., description="UUID ของเอกสาร")
    exam_id: UUID = Field(..., description="UUID ของข้อสอบที่เอกสารนี้สังกัด")
    doc_type: DocType = Field(
        ..., description="ประเภทเอกสาร: answer_key, rubric, course_material"
    )
    original_filename: str = Field(..., description="ชื่อไฟล์ต้นฉบับ")
    embedding_status: EmbeddingStatus = Field(
        ..., description="สถานะการ embed (pending/processing/completed/failed)"
    )
    chunk_count: Optional[int] = Field(
        None, description="จำนวน chunk ที่ embed แล้ว (null ถ้ายังไม่เสร็จ)"
    )
    created_at: datetime = Field(..., description="วันที่อัปโหลด")

    model_config = {"from_attributes": True}


class DocumentUploadResponse(BaseModel):
    """ผลลัพธ์การอัปโหลดเอกสาร"""

    message: str = Field(..., description="ข้อความสถานะ")
    document: DocumentResponse = Field(..., description="ข้อมูลเอกสารที่สร้าง")


class DocumentListResponse(BaseModel):
    """รายการเอกสารของข้อสอบ"""

    documents: List[DocumentResponse] = Field(..., description="รายการเอกสาร")
    total: int = Field(..., description="จำนวนเอกสารทั้งหมด")

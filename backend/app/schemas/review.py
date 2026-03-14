from datetime import datetime
from enum import Enum
from typing import List, Optional
from uuid import UUID

from pydantic import BaseModel, Field

from app.schemas.grading import GradingResultResponse


class SubmissionStatus(str, Enum):
    """สถานะ submission ของนักศึกษา"""

    uploaded = "uploaded"
    parsed = "parsed"
    grading = "grading"
    graded = "graded"
    reviewed = "reviewed"


# ── Submission list ───────────────────────────────────────────────────────────


class SubmissionSummary(BaseModel):
    """ข้อมูลสรุปของ submission แต่ละคน — ใช้ในหน้า review list"""

    id: UUID = Field(..., description="UUID ของ submission")
    student_name: str = Field(..., description="ชื่อ-นามสกุลนักศึกษา")
    student_code: str = Field(..., description="รหัสนักศึกษา")
    status: SubmissionStatus = Field(..., description="สถานะ submission")
    total_score: Optional[float] = Field(
        None, description="คะแนนรวม (effective score: expert ถ้ามี, ไม่งั้นใช้ LLM)"
    )
    max_total_score: float = Field(..., description="คะแนนเต็มรวมทุกข้อ")
    graded_questions: int = Field(..., description="จำนวนข้อที่ตรวจแล้ว")
    total_questions: int = Field(..., description="จำนวนข้อทั้งหมด")

    model_config = {"from_attributes": True}


class SubmissionListResponse(BaseModel):
    """รายการ submission ทั้งหมดของข้อสอบ"""

    submissions: List[SubmissionSummary] = Field(..., description="รายการ submission")
    total: int = Field(..., description="จำนวน submission ทั้งหมด")


# ── Submission detail (review panel) ─────────────────────────────────────────


class SubmissionDetailResponse(BaseModel):
    """รายละเอียด submission พร้อมผลการตรวจทุกข้อ — ใช้ในหน้า review detail"""

    id: UUID = Field(..., description="UUID ของ submission")
    exam_id: UUID = Field(..., description="UUID ของข้อสอบ")
    student_name: str = Field(..., description="ชื่อ-นามสกุลนักศึกษา")
    student_code: str = Field(..., description="รหัสนักศึกษา")
    status: SubmissionStatus = Field(..., description="สถานะ submission")
    grading_results: List[GradingResultResponse] = Field(
        ..., description="ผลการตรวจแต่ละข้อ"
    )
    total_score: Optional[float] = Field(None, description="คะแนนรวม")
    max_total_score: float = Field(..., description="คะแนนเต็มรวม")
    created_at: datetime = Field(..., description="วันที่ส่งกระดาษคำตอบ")


# ── Review actions ────────────────────────────────────────────────────────────


class ApproveResultRequest(BaseModel):
    """อนุมัติคะแนน LLM ตามเดิม (ไม่ต้องส่ง body)"""

    pass


class ReviseResultRequest(BaseModel):
    """แก้ไขคะแนนด้วยคะแนนและ feedback ของผู้เชี่ยวชาญ"""

    expert_score: float = Field(..., ge=0, description="คะแนนที่ผู้เชี่ยวชาญให้ (>= 0)")
    expert_feedback: str = Field(
        ..., min_length=1, description="เหตุผล/ความเห็นของผู้เชี่ยวชาญ"
    )


class BulkApproveRequest(BaseModel):
    """ข้อมูลสำหรับ bulk approve"""

    exam_id: UUID = Field(..., description="UUID ของข้อสอบ")


class BulkApproveResponse(BaseModel):
    """ผลลัพธ์การ bulk approve"""

    approved_count: int = Field(..., description="จำนวนผลการตรวจที่ approve สำเร็จ")
    message: str = Field(..., description="ข้อความสถานะ")

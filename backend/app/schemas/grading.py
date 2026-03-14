from datetime import datetime
from enum import Enum
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field


class GradingStatus(str, Enum):
    """สถานะการตรวจข้อสอบโดยรวม"""

    idle = "idle"
    running = "running"
    completed = "completed"
    failed = "failed"


class GradingResultStatus(str, Enum):
    """สถานะผลการตรวจแต่ละข้อ"""

    pending_review = "pending_review"
    approved = "approved"
    revised = "revised"


# ── Requests ──────────────────────────────────────────────────────────────────


class GradingStartRequest(BaseModel):
    """ข้อมูลสำหรับสั่งให้ LLM เริ่มตรวจข้อสอบ"""

    exam_id: UUID = Field(..., description="UUID ของข้อสอบที่ต้องการตรวจ")


# ── Responses ─────────────────────────────────────────────────────────────────


class GradingProgressResponse(BaseModel):
    """สถานะ progress การตรวจข้อสอบ — ใช้สำหรับ polling"""

    exam_id: UUID = Field(..., description="UUID ของข้อสอบ")
    status: GradingStatus = Field(
        ..., description="สถานะรวม: idle, running, completed, failed"
    )
    total_submissions: int = Field(..., description="จำนวน submission ทั้งหมด")
    completed: int = Field(..., description="จำนวนที่ตรวจเสร็จ")
    failed: int = Field(..., description="จำนวนที่ตรวจล้มเหลว")
    progress_percent: float = Field(
        ..., ge=0, le=100, description="เปอร์เซ็นต์ความคืบหน้า (0-100)"
    )


class GradingResultResponse(BaseModel):
    """ผลการตรวจข้อสอบแต่ละข้อ"""

    id: UUID = Field(..., description="UUID ของผลการตรวจ")
    submission_id: UUID = Field(..., description="UUID ของ submission")
    question_id: UUID = Field(..., description="UUID ของคำถาม")
    question_number: int = Field(..., description="ลำดับข้อ")
    llm_score: float = Field(..., description="คะแนนที่ LLM ให้")
    expert_score: Optional[float] = Field(
        None, description="คะแนนที่ผู้เชี่ยวชาญแก้ (null ถ้ายังไม่ review)"
    )
    max_score: float = Field(..., description="คะแนนเต็มของข้อนี้")
    reasoning: str = Field(..., description="เหตุผลที่ LLM ให้คะแนนนี้")
    expert_feedback: Optional[str] = Field(
        None, description="feedback จากผู้เชี่ยวชาญ (null ถ้ายังไม่ review)"
    )
    status: GradingResultStatus = Field(
        ..., description="สถานะ: pending_review, approved, revised"
    )
    created_at: datetime = Field(..., description="วันที่ตรวจ")

    model_config = {"from_attributes": True}

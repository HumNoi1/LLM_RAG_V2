from datetime import datetime
from typing import List, Optional
from uuid import UUID

from pydantic import BaseModel, Field


# ── Question schemas ──────────────────────────────────────────────────────────


class QuestionCreate(BaseModel):
    """ข้อมูลสำหรับสร้างคำถามใหม่ในข้อสอบ"""

    question_number: int = Field(..., ge=1, description="ลำดับข้อ (เริ่มจาก 1)")
    question_text: str = Field(..., min_length=1, description="เนื้อหาคำถาม")
    max_score: float = Field(..., gt=0, description="คะแนนเต็มของข้อนี้")


class QuestionUpdate(BaseModel):
    """ข้อมูลสำหรับแก้ไขคำถาม (partial update — ส่งเฉพาะ field ที่ต้องการแก้)"""

    question_text: Optional[str] = Field(None, min_length=1, description="เนื้อหาคำถาม")
    max_score: Optional[float] = Field(None, gt=0, description="คะแนนเต็มของข้อนี้")


class QuestionResponse(BaseModel):
    """ข้อมูลคำถามที่ส่งกลับจาก API"""

    id: UUID = Field(..., description="UUID ของคำถาม")
    exam_id: UUID = Field(..., description="UUID ของข้อสอบที่คำถามนี้สังกัด")
    question_number: int = Field(..., description="ลำดับข้อ")
    question_text: str = Field(..., description="เนื้อหาคำถาม")
    max_score: float = Field(..., description="คะแนนเต็ม")
    created_at: datetime = Field(..., description="วันที่สร้าง")

    model_config = {"from_attributes": True}


# ── Exam schemas ──────────────────────────────────────────────────────────────


class ExamCreate(BaseModel):
    """ข้อมูลสำหรับสร้างข้อสอบใหม่"""

    title: str = Field(..., min_length=1, max_length=255, description="ชื่อข้อสอบ")
    subject: str = Field(..., min_length=1, max_length=255, description="วิชา")
    description: Optional[str] = Field(None, description="รายละเอียดเพิ่มเติม (ไม่บังคับ)")
    total_questions: int = Field(..., ge=1, description="จำนวนข้อทั้งหมด")


class ExamUpdate(BaseModel):
    """ข้อมูลสำหรับแก้ไขข้อสอบ (partial update — ส่งเฉพาะ field ที่ต้องการแก้)"""

    title: Optional[str] = Field(
        None, min_length=1, max_length=255, description="ชื่อข้อสอบ"
    )
    subject: Optional[str] = Field(
        None, min_length=1, max_length=255, description="วิชา"
    )
    description: Optional[str] = Field(None, description="รายละเอียดเพิ่มเติม")


class ExamResponse(BaseModel):
    """ข้อมูลข้อสอบที่ส่งกลับจาก API"""

    id: UUID = Field(..., description="UUID ของข้อสอบ")
    title: str = Field(..., description="ชื่อข้อสอบ")
    subject: str = Field(..., description="วิชา")
    description: Optional[str] = Field(None, description="รายละเอียดเพิ่มเติม")
    created_by: UUID = Field(..., description="UUID ของผู้สร้าง")
    total_questions: int = Field(..., description="จำนวนข้อทั้งหมด")
    created_at: datetime = Field(..., description="วันที่สร้าง")
    updated_at: datetime = Field(..., description="วันที่แก้ไขล่าสุด")

    model_config = {"from_attributes": True}


class ExamDetailResponse(ExamResponse):
    """ข้อมูลข้อสอบพร้อมรายการคำถามทั้งหมด"""

    questions: List[QuestionResponse] = Field(
        default=[], description="รายการคำถามในข้อสอบ"
    )


class ExamListResponse(BaseModel):
    """รายการข้อสอบพร้อมจำนวนทั้งหมด"""

    exams: List[ExamResponse] = Field(..., description="รายการข้อสอบ")
    total: int = Field(..., description="จำนวนข้อสอบทั้งหมด")

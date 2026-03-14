"""
Grading endpoints — BE-S responsibility (Sprint 3).

POST /api/v1/grading/start              — สั่งให้ LLM เริ่มตรวจข้อสอบ
GET  /api/v1/grading/status/{exam_id}   — ดู progress การตรวจ
"""

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, BackgroundTasks, Depends

from app import schemas
from app.dependencies import get_current_user
from app.services import grading_service

router = APIRouter()

# ── ค่า response สำหรับ error ที่ใช้ร่วมกัน ──────────────────────────────────
_auth_error = {
    401: {"model": schemas.ErrorResponse, "description": "ไม่ได้ login หรือ token หมดอายุ"}
}


@router.post(
    "/start",
    status_code=202,
    summary="เริ่มตรวจข้อสอบด้วย LLM",
    responses={
        **_auth_error,
        404: {"model": schemas.ErrorResponse, "description": "ไม่พบข้อสอบที่ระบุ"},
    },
)
async def start_grading(
    data: schemas.GradingStartRequest,
    background_tasks: BackgroundTasks,
    current_user: Annotated[dict, Depends(get_current_user)],
):
    """สั่งให้ LLM ตรวจ submission ทั้งหมดของข้อสอบ

    **ขั้นตอนการทำงาน (async):**
    1. ดึงคำถามและ submission ทั้งหมดของข้อสอบ
    2. สำหรับแต่ละ submission × คำถาม:
       - ดึง RAG context จาก Qdrant (เฉลย + rubric ที่เกี่ยวข้อง)
       - ส่งให้ LLM ให้คะแนน + เขียนเหตุผล
    3. บันทึกผลลง DB (status = `pending_review`)

    **หมายเหตุ:**
    - การตรวจทำงานใน background — ใช้ `GET /status/{exam_id}` เพื่อ poll progress
    - ถ้าข้อใดล้มเหลว (timeout/error) จะบันทึก score = 0 พร้อม error message แทน
    - response ส่งกลับทันที (202 Accepted)
    """
    background_tasks.add_task(grading_service.start_grading, data.exam_id)
    return {
        "message": f"Grading started for exam {data.exam_id}",
        "exam_id": data.exam_id,
    }


@router.get(
    "/status/{exam_id}",
    response_model=schemas.GradingProgressResponse,
    summary="ดู progress การตรวจข้อสอบ",
    responses={
        **_auth_error,
        404: {"model": schemas.ErrorResponse, "description": "ไม่พบข้อสอบที่ระบุ"},
    },
)
async def grading_status(
    exam_id: UUID,
    current_user: Annotated[dict, Depends(get_current_user)],
):
    """ดึงสถานะปัจจุบันของการตรวจข้อสอบ

    **Status values:**
    - `idle` — ยังไม่ได้เริ่มตรวจ
    - `running` — กำลังตรวจอยู่
    - `completed` — ตรวจเสร็จทั้งหมด
    - `failed` — เกิดข้อผิดพลาดร้ายแรง

    **การใช้งาน:** Frontend ควร poll endpoint นี้ทุก 2-5 วินาทีหลังจากเรียก `POST /start`
    """
    status = await grading_service.get_grading_status(exam_id)
    return schemas.GradingProgressResponse(
        exam_id=status["exam_id"],
        status=schemas.GradingStatus(status["status"]),
        total_submissions=status["total_submissions"],
        completed=status["completed"],
        failed=status["failed"],
        progress_percent=status["progress_percent"],
    )

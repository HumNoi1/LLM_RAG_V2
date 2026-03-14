"""
Exam endpoints — BE-J responsibility (Sprint 2).

CRUD:
  POST   /api/v1/exams
  GET    /api/v1/exams
  GET    /api/v1/exams/{exam_id}
  PUT    /api/v1/exams/{exam_id}
  DELETE /api/v1/exams/{exam_id}

Questions sub-resource:
  POST   /api/v1/exams/{exam_id}/questions
  PUT    /api/v1/exams/{exam_id}/questions/{question_id}
  DELETE /api/v1/exams/{exam_id}/questions/{question_id}
"""

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends

from app import schemas
from app.dependencies import get_current_user

router = APIRouter()

# ── ค่า response สำหรับ error ที่ใช้ร่วมกันทุก endpoint ──────────────────────
_auth_error = {
    401: {"model": schemas.ErrorResponse, "description": "ไม่ได้ login หรือ token หมดอายุ"}
}
_not_found = {404: {"model": schemas.ErrorResponse, "description": "ไม่พบข้อสอบที่ระบุ"}}


# ── Exam CRUD ─────────────────────────────────────────────────────────────────


@router.post(
    "",
    response_model=schemas.ExamResponse,
    status_code=201,
    summary="สร้างข้อสอบใหม่",
    responses={**_auth_error, 422: {"description": "ข้อมูลไม่ถูกต้อง"}},
)
async def create_exam(
    data: schemas.ExamCreate,
    current_user: Annotated[dict, Depends(get_current_user)],
):
    """สร้างข้อสอบใหม่ในระบบ

    - ระบุ title, subject, total_questions
    - ผู้สร้างจะถูกบันทึกเป็น `created_by` อัตโนมัติจาก JWT
    - หลังสร้างแล้ว ต้องเพิ่มคำถามทีละข้อด้วย `POST /exams/{id}/questions`

    **สถานะ:** BE-J implement ใน Sprint 2
    """
    raise NotImplementedError


@router.get(
    "",
    response_model=schemas.ExamListResponse,
    summary="ดูรายการข้อสอบทั้งหมด",
    responses=_auth_error,
)
async def list_exams(
    current_user: Annotated[dict, Depends(get_current_user)],
):
    """ดึงรายการข้อสอบทั้งหมดที่ผู้ใช้มีสิทธิ์เข้าถึง

    **สถานะ:** BE-J implement ใน Sprint 2
    """
    raise NotImplementedError


@router.get(
    "/{exam_id}",
    response_model=schemas.ExamDetailResponse,
    summary="ดูรายละเอียดข้อสอบ",
    responses={**_auth_error, **_not_found},
)
async def get_exam(
    exam_id: UUID,
    current_user: Annotated[dict, Depends(get_current_user)],
):
    """ดึงรายละเอียดข้อสอบพร้อมรายการคำถามทั้งหมด

    **สถานะ:** BE-J implement ใน Sprint 2
    """
    raise NotImplementedError


@router.put(
    "/{exam_id}",
    response_model=schemas.ExamResponse,
    summary="แก้ไขข้อมูลข้อสอบ",
    responses={**_auth_error, **_not_found, 422: {"description": "ข้อมูลไม่ถูกต้อง"}},
)
async def update_exam(
    exam_id: UUID,
    data: schemas.ExamUpdate,
    current_user: Annotated[dict, Depends(get_current_user)],
):
    """แก้ไข title, subject, หรือ description ของข้อสอบ

    - ส่งเฉพาะ field ที่ต้องการแก้ไข (partial update)

    **สถานะ:** BE-J implement ใน Sprint 2
    """
    raise NotImplementedError


@router.delete(
    "/{exam_id}",
    status_code=204,
    summary="ลบข้อสอบ",
    responses={**_auth_error, **_not_found},
)
async def delete_exam(
    exam_id: UUID,
    current_user: Annotated[dict, Depends(get_current_user)],
):
    """ลบข้อสอบและข้อมูลที่เกี่ยวข้องทั้งหมด (คำถาม, เอกสาร, ผลการตรวจ)

    **สถานะ:** BE-J implement ใน Sprint 2
    """
    raise NotImplementedError


# ── Questions ─────────────────────────────────────────────────────────────────


@router.post(
    "/{exam_id}/questions",
    response_model=schemas.QuestionResponse,
    status_code=201,
    summary="เพิ่มคำถามในข้อสอบ",
    responses={**_auth_error, **_not_found, 422: {"description": "ข้อมูลไม่ถูกต้อง"}},
)
async def add_question(
    exam_id: UUID,
    data: schemas.QuestionCreate,
    current_user: Annotated[dict, Depends(get_current_user)],
):
    """เพิ่มคำถามใหม่ในข้อสอบ

    - ระบุ question_number (ลำดับข้อ), question_text, max_score
    - question_number ต้อง >= 1 และไม่ซ้ำกับข้ออื่นในข้อสอบเดียวกัน

    **สถานะ:** BE-J implement ใน Sprint 2
    """
    raise NotImplementedError


@router.put(
    "/{exam_id}/questions/{question_id}",
    response_model=schemas.QuestionResponse,
    summary="แก้ไขคำถาม",
    responses={
        **_auth_error,
        404: {"model": schemas.ErrorResponse, "description": "ไม่พบข้อสอบหรือคำถามที่ระบุ"},
    },
)
async def update_question(
    exam_id: UUID,
    question_id: UUID,
    data: schemas.QuestionUpdate,
    current_user: Annotated[dict, Depends(get_current_user)],
):
    """แก้ไข question_text หรือ max_score ของคำถาม

    - ส่งเฉพาะ field ที่ต้องการแก้ไข (partial update)

    **สถานะ:** BE-J implement ใน Sprint 2
    """
    raise NotImplementedError


@router.delete(
    "/{exam_id}/questions/{question_id}",
    status_code=204,
    summary="ลบคำถาม",
    responses={
        **_auth_error,
        404: {"model": schemas.ErrorResponse, "description": "ไม่พบข้อสอบหรือคำถามที่ระบุ"},
    },
)
async def delete_question(
    exam_id: UUID,
    question_id: UUID,
    current_user: Annotated[dict, Depends(get_current_user)],
):
    """ลบคำถามออกจากข้อสอบ

    - ถ้ามีผลการตรวจที่เกี่ยวข้อง จะไม่สามารถลบได้

    **สถานะ:** BE-J implement ใน Sprint 2
    """
    raise NotImplementedError

"""
Review endpoints — BE-J responsibility (Sprint 3).

ผู้เชี่ยวชาญตรวจสอบและอนุมัติผลคะแนนจาก LLM

GET  /api/v1/review/exams/{exam_id}/submissions      — รายการ submission พร้อมสรุปคะแนน
GET  /api/v1/review/submissions/{submission_id}      — รายละเอียดผลตรวจทุกข้อ
PUT  /api/v1/review/results/{result_id}/approve      — อนุมัติคะแนน LLM
PUT  /api/v1/review/results/{result_id}/revise       — แก้คะแนน + ให้ feedback
POST /api/v1/review/exams/{exam_id}/approve-all      — อนุมัติทั้งหมดในคราวเดียว
GET  /api/v1/review/exams/{exam_id}/export           — ส่งออก CSV
"""

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse

from app import schemas
from app.dependencies import get_current_user

router = APIRouter()

# ── ค่า response สำหรับ error ที่ใช้ร่วมกัน ──────────────────────────────────
_auth_error = {
    401: {"model": schemas.ErrorResponse, "description": "ไม่ได้ login หรือ token หมดอายุ"}
}
_not_found_exam = {
    404: {"model": schemas.ErrorResponse, "description": "ไม่พบข้อสอบที่ระบุ"}
}


@router.get(
    "/exams/{exam_id}/submissions",
    response_model=schemas.SubmissionListResponse,
    summary="ดูรายการ submission พร้อมสรุปคะแนน",
    responses={**_auth_error, **_not_found_exam},
)
async def list_submissions_with_summary(
    exam_id: UUID,
    current_user: Annotated[dict, Depends(get_current_user)],
):
    """ดึงรายการ submission ทั้งหมดของข้อสอบ พร้อมสรุปคะแนน

    - แสดงชื่อนักศึกษา, รหัส, สถานะ, คะแนนรวม
    - ใช้สำหรับหน้า review list ของ frontend

    **สถานะ:** BE-J implement ใน Sprint 3
    """
    raise NotImplementedError


@router.get(
    "/submissions/{submission_id}",
    response_model=schemas.SubmissionDetailResponse,
    summary="ดูรายละเอียดผลตรวจของนักศึกษา",
    responses={
        **_auth_error,
        404: {"model": schemas.ErrorResponse, "description": "ไม่พบ submission ที่ระบุ"},
    },
)
async def get_submission_detail(
    submission_id: UUID,
    current_user: Annotated[dict, Depends(get_current_user)],
):
    """ดึงรายละเอียดผลการตรวจทุกข้อของ submission

    - แสดง llm_score, reasoning, expert_score, expert_feedback สำหรับทุกข้อ
    - ใช้สำหรับหน้า review detail ของ frontend

    **สถานะ:** BE-J implement ใน Sprint 3
    """
    raise NotImplementedError


@router.put(
    "/results/{result_id}/approve",
    response_model=schemas.GradingResultResponse,
    summary="อนุมัติคะแนน LLM ตามเดิม",
    responses={
        **_auth_error,
        404: {"model": schemas.ErrorResponse, "description": "ไม่พบผลการตรวจที่ระบุ"},
    },
)
async def approve_result(
    result_id: UUID,
    current_user: Annotated[dict, Depends(get_current_user)],
):
    """อนุมัติคะแนนที่ LLM ให้ โดยไม่แก้ไข

    - เปลี่ยน status เป็น `approved`
    - expert_score จะถูกตั้งเป็นค่าเดียวกับ llm_score

    **สถานะ:** BE-J implement ใน Sprint 3
    """
    raise NotImplementedError


@router.put(
    "/results/{result_id}/revise",
    response_model=schemas.GradingResultResponse,
    summary="แก้ไขคะแนนด้วยคะแนนผู้เชี่ยวชาญ",
    responses={
        **_auth_error,
        404: {"model": schemas.ErrorResponse, "description": "ไม่พบผลการตรวจที่ระบุ"},
        422: {"description": "ข้อมูลไม่ถูกต้อง (expert_score < 0 หรือ feedback ว่าง)"},
    },
)
async def revise_result(
    result_id: UUID,
    data: schemas.ReviseResultRequest,
    current_user: Annotated[dict, Depends(get_current_user)],
):
    """แก้ไขคะแนน LLM ด้วยคะแนนและ feedback ของผู้เชี่ยวชาญ

    - ต้องระบุ `expert_score` (>= 0) และ `expert_feedback`
    - เปลี่ยน status เป็น `revised`

    **สถานะ:** BE-J implement ใน Sprint 3
    """
    raise NotImplementedError


@router.post(
    "/exams/{exam_id}/approve-all",
    response_model=schemas.BulkApproveResponse,
    summary="อนุมัติผลตรวจทั้งหมดของข้อสอบ",
    responses={**_auth_error, **_not_found_exam},
)
async def bulk_approve(
    exam_id: UUID,
    current_user: Annotated[dict, Depends(get_current_user)],
):
    """อนุมัติผลการตรวจที่ยัง pending ทั้งหมดของข้อสอบในคราวเดียว

    - เฉพาะ result ที่มี status = `pending_review` เท่านั้น
    - result ที่ถูก revise แล้วจะไม่ถูกเปลี่ยนแปลง
    - ส่งกลับจำนวนที่ approve สำเร็จ

    **สถานะ:** BE-J implement ใน Sprint 3
    """
    raise NotImplementedError


@router.get(
    "/exams/{exam_id}/export",
    summary="ส่งออกผลคะแนนเป็น CSV",
    responses={
        **_auth_error,
        **_not_found_exam,
        200: {
            "content": {"text/csv": {}},
            "description": "CSV file: student name, scores per question, total, status",
        },
    },
)
async def export_results_csv(
    exam_id: UUID,
    current_user: Annotated[dict, Depends(get_current_user)],
):
    """ส่งออกผลการตรวจทั้งหมดเป็นไฟล์ CSV

    **คอลัมน์ใน CSV:**
    - ชื่อนักศึกษา, รหัส
    - คะแนนแต่ละข้อ (effective score: expert ถ้ามี, ไม่งั้นใช้ LLM)
    - คะแนนรวม
    - สถานะการ review

    **Response:** `Content-Type: text/csv`

    **สถานะ:** BE-J implement ใน Sprint 3
    """
    raise NotImplementedError

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
from app.dependencies import get_current_user, get_supabase

router = APIRouter()


# ── Exam CRUD ─────────────────────────────────────────────────────────────────

@router.post("", response_model=schemas.ExamResponse, status_code=201)
async def create_exam(
    data: schemas.ExamCreate,
    current_user: Annotated[dict, Depends(get_current_user)],
    supabase=Depends(get_supabase),
):
    """BE-J: implement in Sprint 2."""
    raise NotImplementedError


@router.get("", response_model=schemas.ExamListResponse)
async def list_exams(
    current_user: Annotated[dict, Depends(get_current_user)],
    supabase=Depends(get_supabase),
):
    """BE-J: implement in Sprint 2."""
    raise NotImplementedError


@router.get("/{exam_id}", response_model=schemas.ExamDetailResponse)
async def get_exam(
    exam_id: UUID,
    current_user: Annotated[dict, Depends(get_current_user)],
    supabase=Depends(get_supabase),
):
    """BE-J: implement in Sprint 2."""
    raise NotImplementedError


@router.put("/{exam_id}", response_model=schemas.ExamResponse)
async def update_exam(
    exam_id: UUID,
    data: schemas.ExamUpdate,
    current_user: Annotated[dict, Depends(get_current_user)],
    supabase=Depends(get_supabase),
):
    """BE-J: implement in Sprint 2."""
    raise NotImplementedError


@router.delete("/{exam_id}", status_code=204)
async def delete_exam(
    exam_id: UUID,
    current_user: Annotated[dict, Depends(get_current_user)],
    supabase=Depends(get_supabase),
):
    """BE-J: implement in Sprint 2."""
    raise NotImplementedError


# ── Questions ─────────────────────────────────────────────────────────────────

@router.post("/{exam_id}/questions", response_model=schemas.QuestionResponse, status_code=201)
async def add_question(
    exam_id: UUID,
    data: schemas.QuestionCreate,
    current_user: Annotated[dict, Depends(get_current_user)],
    supabase=Depends(get_supabase),
):
    """BE-J: implement in Sprint 2."""
    raise NotImplementedError


@router.put("/{exam_id}/questions/{question_id}", response_model=schemas.QuestionResponse)
async def update_question(
    exam_id: UUID,
    question_id: UUID,
    data: schemas.QuestionUpdate,
    current_user: Annotated[dict, Depends(get_current_user)],
    supabase=Depends(get_supabase),
):
    """BE-J: implement in Sprint 2."""
    raise NotImplementedError


@router.delete("/{exam_id}/questions/{question_id}", status_code=204)
async def delete_question(
    exam_id: UUID,
    question_id: UUID,
    current_user: Annotated[dict, Depends(get_current_user)],
    supabase=Depends(get_supabase),
):
    """BE-J: implement in Sprint 2."""
    raise NotImplementedError

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

from fastapi import APIRouter, Depends, HTTPException, status

from app import schemas
from app.database import get_supabase
from app.dependencies import get_current_user

router = APIRouter()


# ── Helpers ───────────────────────────────────────────────────────────────────


async def _get_exam_or_404(exam_id: UUID):
    supabase = get_supabase()
    response = (
        supabase.table("exams")
        .select("*, exam_questions(*)")
        .eq("id", str(exam_id))
        .maybe_single()
        .execute()
    )
    exam = response.data

    if not exam:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Exam not found"
        )

    # Sort questions by question_number ascending
    if exam.get("exam_questions"):
        exam["exam_questions"].sort(key=lambda q: q["question_number"])
    else:
        exam["exam_questions"] = []

    return exam


async def _verify_exam_owner(exam_id: UUID, user_id: str):
    exam = await _get_exam_or_404(exam_id)
    if exam["created_by"] != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Not the owner of this exam"
        )
    return exam


# ── Exam CRUD ─────────────────────────────────────────────────────────────────


@router.post("", response_model=schemas.ExamResponse, status_code=201)
async def create_exam(
    data: schemas.ExamCreate,
    current_user: Annotated[dict, Depends(get_current_user)],
):
    supabase = get_supabase()
    response = (
        supabase.table("exams")
        .insert(
            {
                "title": data.title,
                "subject": data.subject,
                "description": data.description,
                "total_questions": data.total_questions,
                "created_by": current_user["id"],
            }
        )
        .execute()
    )
    exam = response.data[0]

    return schemas.ExamResponse(
        id=exam["id"],
        title=exam["title"],
        subject=exam["subject"],
        description=exam["description"],
        created_by=exam["created_by"],
        total_questions=exam["total_questions"],
        created_at=exam["created_at"],
        updated_at=exam["updated_at"],
    )


@router.get("", response_model=schemas.ExamListResponse)
async def list_exams(
    current_user: Annotated[dict, Depends(get_current_user)],
):
    supabase = get_supabase()
    response = (
        supabase.table("exams")
        .select("*")
        .eq("created_by", current_user["id"])
        .order("created_at", desc=True)
        .execute()
    )
    exams = response.data

    return schemas.ExamListResponse(
        exams=[
            schemas.ExamResponse(
                id=e["id"],
                title=e["title"],
                subject=e["subject"],
                description=e["description"],
                created_by=e["created_by"],
                total_questions=e["total_questions"],
                created_at=e["created_at"],
                updated_at=e["updated_at"],
            )
            for e in exams
        ],
        total=len(exams),
    )


@router.get("/{exam_id}", response_model=schemas.ExamDetailResponse)
async def get_exam(
    exam_id: UUID,
    current_user: Annotated[dict, Depends(get_current_user)],
):
    exam = await _get_exam_or_404(exam_id)
    if exam["created_by"] != current_user["id"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Not the owner of this exam"
        )

    questions = [
        schemas.QuestionResponse(
            id=q["id"],
            exam_id=q["exam_id"],
            question_number=q["question_number"],
            question_text=q["question_text"],
            max_score=q["max_score"],
            created_at=q["created_at"],
        )
        for q in exam.get("exam_questions", [])
    ]

    return schemas.ExamDetailResponse(
        id=exam["id"],
        title=exam["title"],
        subject=exam["subject"],
        description=exam["description"],
        created_by=exam["created_by"],
        total_questions=exam["total_questions"],
        created_at=exam["created_at"],
        updated_at=exam["updated_at"],
        questions=questions,
    )


@router.put("/{exam_id}", response_model=schemas.ExamResponse)
async def update_exam(
    exam_id: UUID,
    data: schemas.ExamUpdate,
    current_user: Annotated[dict, Depends(get_current_user)],
):
    await _verify_exam_owner(exam_id, current_user["id"])

    update_data: dict = {}
    if data.title is not None:
        update_data["title"] = data.title
    if data.subject is not None:
        update_data["subject"] = data.subject
    if data.description is not None:
        update_data["description"] = data.description

    if not update_data:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="No fields to update"
        )

    supabase = get_supabase()
    response = (
        supabase.table("exams").update(update_data).eq("id", str(exam_id)).execute()
    )
    exam = response.data[0]

    return schemas.ExamResponse(
        id=exam["id"],
        title=exam["title"],
        subject=exam["subject"],
        description=exam["description"],
        created_by=exam["created_by"],
        total_questions=exam["total_questions"],
        created_at=exam["created_at"],
        updated_at=exam["updated_at"],
    )


@router.delete("/{exam_id}", status_code=204)
async def delete_exam(
    exam_id: UUID,
    current_user: Annotated[dict, Depends(get_current_user)],
):
    await _verify_exam_owner(exam_id, current_user["id"])
    supabase = get_supabase()
    supabase.table("exams").delete().eq("id", str(exam_id)).execute()
    return None


# ── Questions ─────────────────────────────────────────────────────────────────


@router.post(
    "/{exam_id}/questions", response_model=schemas.QuestionResponse, status_code=201
)
async def add_question(
    exam_id: UUID,
    data: schemas.QuestionCreate,
    current_user: Annotated[dict, Depends(get_current_user)],
):
    await _verify_exam_owner(exam_id, current_user["id"])

    supabase = get_supabase()

    # Check for duplicate question_number
    existing = (
        supabase.table("exam_questions")
        .select("id")
        .eq("exam_id", str(exam_id))
        .eq("question_number", data.question_number)
        .maybe_single()
        .execute()
    )

    if existing.data:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Question number {data.question_number} already exists for this exam",
        )

    response = (
        supabase.table("exam_questions")
        .insert(
            {
                "exam_id": str(exam_id),
                "question_number": data.question_number,
                "question_text": data.question_text,
                "max_score": data.max_score,
            }
        )
        .execute()
    )
    question = response.data[0]

    return schemas.QuestionResponse(
        id=question["id"],
        exam_id=question["exam_id"],
        question_number=question["question_number"],
        question_text=question["question_text"],
        max_score=question["max_score"],
        created_at=question["created_at"],
    )


@router.put(
    "/{exam_id}/questions/{question_id}", response_model=schemas.QuestionResponse
)
async def update_question(
    exam_id: UUID,
    question_id: UUID,
    data: schemas.QuestionUpdate,
    current_user: Annotated[dict, Depends(get_current_user)],
):
    await _verify_exam_owner(exam_id, current_user["id"])

    supabase = get_supabase()
    existing = (
        supabase.table("exam_questions")
        .select("*")
        .eq("id", str(question_id))
        .eq("exam_id", str(exam_id))
        .maybe_single()
        .execute()
    )

    if not existing.data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Question not found"
        )

    update_data: dict = {}
    if data.question_text is not None:
        update_data["question_text"] = data.question_text
    if data.max_score is not None:
        update_data["max_score"] = data.max_score

    if not update_data:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="No fields to update"
        )

    response = (
        supabase.table("exam_questions")
        .update(update_data)
        .eq("id", str(question_id))
        .execute()
    )
    updated = response.data[0]

    return schemas.QuestionResponse(
        id=updated["id"],
        exam_id=updated["exam_id"],
        question_number=updated["question_number"],
        question_text=updated["question_text"],
        max_score=updated["max_score"],
        created_at=updated["created_at"],
    )


@router.delete("/{exam_id}/questions/{question_id}", status_code=204)
async def delete_question(
    exam_id: UUID,
    question_id: UUID,
    current_user: Annotated[dict, Depends(get_current_user)],
):
    await _verify_exam_owner(exam_id, current_user["id"])

    supabase = get_supabase()
    existing = (
        supabase.table("exam_questions")
        .select("id")
        .eq("id", str(question_id))
        .eq("exam_id", str(exam_id))
        .maybe_single()
        .execute()
    )

    if not existing.data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Question not found"
        )

    supabase.table("exam_questions").delete().eq("id", str(question_id)).execute()
    return None

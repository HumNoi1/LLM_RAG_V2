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
from app.database import db
from app.dependencies import get_current_user

router = APIRouter()


# ── Helpers ───────────────────────────────────────────────────────────────────

async def _get_exam_or_404(exam_id: UUID):
    exam = await db.exam.find_unique(
        where={"id": str(exam_id)},
        include={"questions": {"order_by": {"questionNumber": "asc"}}},
    )
    if not exam:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Exam not found")
    return exam


async def _verify_exam_owner(exam_id: UUID, user_id: str):
    exam = await _get_exam_or_404(exam_id)
    if exam.createdBy != user_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not the owner of this exam")
    return exam


# ── Exam CRUD ─────────────────────────────────────────────────────────────────

@router.post("", response_model=schemas.ExamResponse, status_code=201)
async def create_exam(
    data: schemas.ExamCreate,
    current_user: Annotated[dict, Depends(get_current_user)],
):
    exam = await db.exam.create(
        data={
            "title": data.title,
            "subject": data.subject,
            "description": data.description,
            "totalQuestions": data.total_questions,
            "createdBy": current_user.id,
        }
    )
    return schemas.ExamResponse(
        id=exam.id,
        title=exam.title,
        subject=exam.subject,
        description=exam.description,
        created_by=exam.createdBy,
        total_questions=exam.totalQuestions,
        created_at=exam.createdAt,
        updated_at=exam.updatedAt,
    )


@router.get("", response_model=schemas.ExamListResponse)
async def list_exams(
    current_user: Annotated[dict, Depends(get_current_user)],
):
    exams = await db.exam.find_many(
        where={"createdBy": current_user.id},
        order={"createdAt": "desc"},
    )
    return schemas.ExamListResponse(
        exams=[
            schemas.ExamResponse(
                id=e.id,
                title=e.title,
                subject=e.subject,
                description=e.description,
                created_by=e.createdBy,
                total_questions=e.totalQuestions,
                created_at=e.createdAt,
                updated_at=e.updatedAt,
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
    if exam.createdBy != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not the owner of this exam")

    questions = [
        schemas.QuestionResponse(
            id=q.id,
            exam_id=q.examId,
            question_number=q.questionNumber,
            question_text=q.questionText,
            max_score=q.maxScore,
            created_at=q.createdAt,
        )
        for q in (exam.questions or [])
    ]

    return schemas.ExamDetailResponse(
        id=exam.id,
        title=exam.title,
        subject=exam.subject,
        description=exam.description,
        created_by=exam.createdBy,
        total_questions=exam.totalQuestions,
        created_at=exam.createdAt,
        updated_at=exam.updatedAt,
        questions=questions,
    )


@router.put("/{exam_id}", response_model=schemas.ExamResponse)
async def update_exam(
    exam_id: UUID,
    data: schemas.ExamUpdate,
    current_user: Annotated[dict, Depends(get_current_user)],
):
    await _verify_exam_owner(exam_id, current_user.id)

    update_data: dict = {}
    if data.title is not None:
        update_data["title"] = data.title
    if data.subject is not None:
        update_data["subject"] = data.subject
    if data.description is not None:
        update_data["description"] = data.description

    if not update_data:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No fields to update")

    exam = await db.exam.update(
        where={"id": str(exam_id)},
        data=update_data,
    )

    return schemas.ExamResponse(
        id=exam.id,
        title=exam.title,
        subject=exam.subject,
        description=exam.description,
        created_by=exam.createdBy,
        total_questions=exam.totalQuestions,
        created_at=exam.createdAt,
        updated_at=exam.updatedAt,
    )


@router.delete("/{exam_id}", status_code=204)
async def delete_exam(
    exam_id: UUID,
    current_user: Annotated[dict, Depends(get_current_user)],
):
    await _verify_exam_owner(exam_id, current_user.id)
    await db.exam.delete(where={"id": str(exam_id)})
    return None


# ── Questions ─────────────────────────────────────────────────────────────────

@router.post("/{exam_id}/questions", response_model=schemas.QuestionResponse, status_code=201)
async def add_question(
    exam_id: UUID,
    data: schemas.QuestionCreate,
    current_user: Annotated[dict, Depends(get_current_user)],
):
    await _verify_exam_owner(exam_id, current_user.id)

    # Check for duplicate question_number
    existing = await db.examquestion.find_first(
        where={"examId": str(exam_id), "questionNumber": data.question_number}
    )
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Question number {data.question_number} already exists for this exam",
        )

    question = await db.examquestion.create(
        data={
            "examId": str(exam_id),
            "questionNumber": data.question_number,
            "questionText": data.question_text,
            "maxScore": data.max_score,
        }
    )

    return schemas.QuestionResponse(
        id=question.id,
        exam_id=question.examId,
        question_number=question.questionNumber,
        question_text=question.questionText,
        max_score=question.maxScore,
        created_at=question.createdAt,
    )


@router.put("/{exam_id}/questions/{question_id}", response_model=schemas.QuestionResponse)
async def update_question(
    exam_id: UUID,
    question_id: UUID,
    data: schemas.QuestionUpdate,
    current_user: Annotated[dict, Depends(get_current_user)],
):
    await _verify_exam_owner(exam_id, current_user.id)

    question = await db.examquestion.find_first(
        where={"id": str(question_id), "examId": str(exam_id)}
    )
    if not question:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Question not found")

    update_data: dict = {}
    if data.question_text is not None:
        update_data["questionText"] = data.question_text
    if data.max_score is not None:
        update_data["maxScore"] = data.max_score

    if not update_data:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No fields to update")

    updated = await db.examquestion.update(
        where={"id": str(question_id)},
        data=update_data,
    )

    return schemas.QuestionResponse(
        id=updated.id,
        exam_id=updated.examId,
        question_number=updated.questionNumber,
        question_text=updated.questionText,
        max_score=updated.maxScore,
        created_at=updated.createdAt,
    )


@router.delete("/{exam_id}/questions/{question_id}", status_code=204)
async def delete_question(
    exam_id: UUID,
    question_id: UUID,
    current_user: Annotated[dict, Depends(get_current_user)],
):
    await _verify_exam_owner(exam_id, current_user.id)

    question = await db.examquestion.find_first(
        where={"id": str(question_id), "examId": str(exam_id)}
    )
    if not question:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Question not found")

    await db.examquestion.delete(where={"id": str(question_id)})
    return None

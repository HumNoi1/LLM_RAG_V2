"""
Grading endpoints — BE-S responsibility (Sprint 3).

POST /api/v1/grading/start
GET  /api/v1/grading/status/{exam_id}
"""

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, BackgroundTasks, Depends

from app import schemas
from app.dependencies import get_current_user
from app.services import grading_service

router = APIRouter()


@router.post("/start", status_code=202)
async def start_grading(
    data: schemas.GradingStartRequest,
    background_tasks: BackgroundTasks,
    current_user: Annotated[dict, Depends(get_current_user)],
):
    """Trigger LLM grading for all submissions in an exam.
    Grading runs in the background — poll /status/{exam_id} for progress.
    """
    background_tasks.add_task(grading_service.start_grading, data.exam_id)
    return {
        "message": f"Grading started for exam {data.exam_id}",
        "exam_id": data.exam_id,
    }


@router.get("/status/{exam_id}", response_model=schemas.GradingProgressResponse)
async def grading_status(
    exam_id: UUID,
    current_user: Annotated[dict, Depends(get_current_user)],
):
    """Poll current grading progress for an exam."""
    status = await grading_service.get_grading_status(exam_id)
    return schemas.GradingProgressResponse(
        exam_id=status["exam_id"],
        status=schemas.GradingStatus(status["status"]),
        total_submissions=status["total_submissions"],
        completed=status["completed"],
        failed=status["failed"],
        progress_percent=status["progress_percent"],
    )

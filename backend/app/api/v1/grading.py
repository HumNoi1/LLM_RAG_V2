"""
Grading endpoints — BE-S responsibility (Sprint 3).

POST /api/v1/grading/start
GET  /api/v1/grading/status/{exam_id}
"""

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, status

from app import schemas
from app.database import get_supabase, maybe_single_safe
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
    supabase = get_supabase()

    # Verify exam exists
    exam_resp = maybe_single_safe(
        supabase.table("exams").select("id").eq("id", str(data.exam_id))
    )
    if not exam_resp.data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Exam not found"
        )

    # Check if grading is already running (any submission in 'grading' state)
    running_resp = (
        supabase.table("student_submissions")
        .select("id")
        .eq("exam_id", str(data.exam_id))
        .eq("status", "grading")
        .limit(1)
        .execute()
    )
    if running_resp.data:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Grading is already in progress for this exam",
        )

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
    supabase = get_supabase()

    # Verify exam exists
    exam_resp = maybe_single_safe(
        supabase.table("exams").select("id").eq("id", str(exam_id))
    )
    if not exam_resp.data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Exam not found"
        )

    # Count submissions by status
    subs_resp = (
        supabase.table("student_submissions")
        .select("status")
        .eq("exam_id", str(exam_id))
        .execute()
    )
    submissions = subs_resp.data or []
    total_submissions = len(submissions)

    status_counts: dict[str, int] = {}
    for sub in submissions:
        s = sub.get("status", "uploaded")
        status_counts[s] = status_counts.get(s, 0) + 1

    completed = status_counts.get("graded", 0) + status_counts.get("reviewed", 0)
    # Count submissions that errored back to 'parsed' after a failed grading attempt
    # We treat any submission NOT in graded/reviewed/grading as potentially failed
    # from a grading perspective — but only if grading was actually attempted.
    # For simplicity: failed = 0 (no explicit failed status on submissions)
    failed = 0

    # Determine overall grading status
    running_count = status_counts.get("grading", 0)
    if total_submissions == 0:
        grading_status_val = schemas.GradingStatus.idle
        progress_percent = 0.0
    elif running_count > 0:
        grading_status_val = schemas.GradingStatus.running
        progress_percent = round((completed / total_submissions) * 100, 1)
    elif completed == total_submissions:
        grading_status_val = schemas.GradingStatus.completed
        progress_percent = 100.0
    else:
        grading_status_val = schemas.GradingStatus.idle
        progress_percent = round((completed / total_submissions) * 100, 1)

    return schemas.GradingProgressResponse(
        exam_id=exam_id,
        status=grading_status_val,
        total_submissions=total_submissions,
        completed=completed,
        failed=failed,
        progress_percent=progress_percent,
    )

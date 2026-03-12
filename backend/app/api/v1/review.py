"""
Review endpoints — BE-J responsibility (Sprint 3).

GET  /api/v1/review/exams/{exam_id}/submissions      — list with grading summary
GET  /api/v1/review/submissions/{submission_id}      — full detail per student
PUT  /api/v1/review/results/{result_id}/approve      — approve LLM score
PUT  /api/v1/review/results/{result_id}/revise       — override score + feedback
POST /api/v1/review/exams/{exam_id}/approve-all      — bulk approve
GET  /api/v1/review/exams/{exam_id}/export           — CSV export
"""
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse

from app import schemas
from app.dependencies import get_current_user

router = APIRouter()


@router.get("/exams/{exam_id}/submissions", response_model=schemas.SubmissionListResponse)
async def list_submissions_with_summary(
    exam_id: UUID,
    current_user: Annotated[dict, Depends(get_current_user)],
):
    """BE-J: implement in Sprint 3."""
    raise NotImplementedError


@router.get("/submissions/{submission_id}", response_model=schemas.SubmissionDetailResponse)
async def get_submission_detail(
    submission_id: UUID,
    current_user: Annotated[dict, Depends(get_current_user)],
):
    """BE-J: implement in Sprint 3."""
    raise NotImplementedError


@router.put("/results/{result_id}/approve", response_model=schemas.GradingResultResponse)
async def approve_result(
    result_id: UUID,
    current_user: Annotated[dict, Depends(get_current_user)],
):
    """Approve LLM score as-is. BE-J: implement in Sprint 3."""
    raise NotImplementedError


@router.put("/results/{result_id}/revise", response_model=schemas.GradingResultResponse)
async def revise_result(
    result_id: UUID,
    data: schemas.ReviseResultRequest,
    current_user: Annotated[dict, Depends(get_current_user)],
):
    """Override LLM score with expert score + feedback. BE-J: implement in Sprint 3."""
    raise NotImplementedError


@router.post("/exams/{exam_id}/approve-all", response_model=schemas.BulkApproveResponse)
async def bulk_approve(
    exam_id: UUID,
    current_user: Annotated[dict, Depends(get_current_user)],
):
    """Bulk approve all pending grading results for an exam. BE-J: implement in Sprint 3."""
    raise NotImplementedError


@router.get("/exams/{exam_id}/export")
async def export_results_csv(
    exam_id: UUID,
    current_user: Annotated[dict, Depends(get_current_user)],
):
    """Export grading results as CSV. BE-J: implement in Sprint 3.
    Response: text/csv with student name, scores per question, total, status.
    """
    raise NotImplementedError

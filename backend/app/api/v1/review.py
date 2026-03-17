"""
Review endpoints — BE-J responsibility (Sprint 3).

GET  /api/v1/review/exams/{exam_id}/submissions      — list with grading summary
GET  /api/v1/review/submissions/{submission_id}      — full detail per student
PUT  /api/v1/review/results/{result_id}/approve      — approve LLM score
PUT  /api/v1/review/results/{result_id}/revise       — override score + feedback
POST /api/v1/review/exams/{exam_id}/approve-all      — bulk approve
GET  /api/v1/review/exams/{exam_id}/export           — CSV export
"""

import csv
import io
import logging
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse

from app import schemas
from app.database import get_supabase, maybe_single_safe
from app.dependencies import get_current_user

logger = logging.getLogger(__name__)
router = APIRouter()


# ── Helpers ───────────────────────────────────────────────────────────────────


def _get_submission_or_404(submission_id: str) -> dict:
    """Fetch a submission row or raise 404."""
    supabase = get_supabase()
    resp = maybe_single_safe(
        supabase.table("student_submissions")
        .select("*, students(full_name, student_code)")
        .eq("id", submission_id)
    )
    if not resp.data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Submission not found"
        )
    return resp.data


def _get_result_or_404(result_id: str) -> dict:
    """Fetch a grading_result row or raise 404."""
    supabase = get_supabase()
    resp = maybe_single_safe(
        supabase.table("grading_results")
        .select("*, exam_questions(question_number, max_score)")
        .eq("id", result_id)
    )
    if not resp.data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Grading result not found"
        )
    return resp.data


def _build_grading_result_response(row: dict) -> schemas.GradingResultResponse:
    q = row.get("exam_questions") or {}
    return schemas.GradingResultResponse(
        id=row["id"],
        submission_id=row["submission_id"],
        question_id=row["question_id"],
        question_number=q.get("question_number", 0),
        llm_score=row.get("llm_score") or 0.0,
        expert_score=row.get("expert_score"),
        max_score=row.get("llm_max_score") or q.get("max_score", 0.0),
        reasoning=row.get("llm_reasoning") or "",
        expert_feedback=row.get("expert_feedback"),
        status=row.get("status", "pending"),
        created_at=row.get("graded_at") or row.get("created_at"),
    )


# ── Endpoints ─────────────────────────────────────────────────────────────────


@router.get(
    "/exams/{exam_id}/submissions", response_model=schemas.SubmissionListResponse
)
async def list_submissions_with_summary(
    exam_id: UUID,
    current_user: Annotated[dict, Depends(get_current_user)],
):
    """List all submissions for an exam with grading summary."""
    supabase = get_supabase()

    # Verify exam exists and get total_questions
    exam_resp = maybe_single_safe(
        supabase.table("exams").select("id, total_questions").eq("id", str(exam_id))
    )
    if not exam_resp.data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Exam not found"
        )

    total_questions = exam_resp.data.get("total_questions", 0)

    subs_resp = (
        supabase.table("student_submissions")
        .select("id, status, students(full_name, student_code)")
        .eq("exam_id", str(exam_id))
        .order("created_at", desc=False)
        .execute()
    )
    submissions = subs_resp.data or []

    summaries = []
    for sub in submissions:
        sub_id = sub["id"]
        student = sub.get("students") or {}

        gr_resp = (
            supabase.table("grading_results")
            .select("llm_score, expert_score, status, exam_questions(max_score)")
            .eq("submission_id", sub_id)
            .execute()
        )
        results = gr_resp.data or []

        graded_questions = len(results)
        max_total_score = sum(
            (r.get("exam_questions") or {}).get("max_score", 0) for r in results
        )
        scored = [
            r.get("expert_score")
            if r.get("expert_score") is not None
            else r.get("llm_score", 0)
            for r in results
            if r.get("status") in ("approved", "revised")
        ]
        total_score = sum(scored) if scored else None

        summaries.append(
            schemas.SubmissionSummary(
                id=sub_id,
                student_name=student.get("full_name", ""),
                student_code=student.get("student_code", ""),
                status=sub["status"],
                total_score=total_score,
                max_total_score=max_total_score,
                graded_questions=graded_questions,
                total_questions=total_questions,
            )
        )

    return schemas.SubmissionListResponse(submissions=summaries, total=len(summaries))


@router.get(
    "/submissions/{submission_id}", response_model=schemas.SubmissionDetailResponse
)
async def get_submission_detail(
    submission_id: UUID,
    current_user: Annotated[dict, Depends(get_current_user)],
):
    """Full grading detail for a single student submission (Review Panel)."""
    supabase = get_supabase()
    sub = _get_submission_or_404(str(submission_id))
    student = sub.get("students") or {}

    # Fetch grading results with question info
    gr_resp = (
        supabase.table("grading_results")
        .select("*, exam_questions(question_number, max_score)")
        .eq("submission_id", str(submission_id))
        .order("exam_questions(question_number)")
        .execute()
    )
    results = gr_resp.data or []

    grading_results = [_build_grading_result_response(r) for r in results]
    max_total_score = sum(r.max_score for r in grading_results)
    scored = [
        r.expert_score if r.expert_score is not None else r.llm_score
        for r in grading_results
        if r.status in ("approved", "revised")
    ]
    total_score = sum(scored) if scored else None

    return schemas.SubmissionDetailResponse(
        id=sub["id"],
        exam_id=sub["exam_id"],
        student_name=student.get("full_name", ""),
        student_code=student.get("student_code", ""),
        status=sub["status"],
        grading_results=grading_results,
        total_score=total_score,
        max_total_score=max_total_score,
        created_at=sub["created_at"],
    )


@router.put(
    "/results/{result_id}/approve", response_model=schemas.GradingResultResponse
)
async def approve_result(
    result_id: UUID,
    current_user: Annotated[dict, Depends(get_current_user)],
):
    """Approve LLM score as-is — sets status to 'approved'."""
    supabase = get_supabase()
    row = _get_result_or_404(str(result_id))

    updated = (
        supabase.table("grading_results")
        .update({"status": "approved"})
        .eq("id", str(result_id))
        .execute()
    )
    updated_row = updated.data[0]
    # Merge in joined question info from original fetch
    updated_row["exam_questions"] = row.get("exam_questions")
    return _build_grading_result_response(updated_row)


@router.put("/results/{result_id}/revise", response_model=schemas.GradingResultResponse)
async def revise_result(
    result_id: UUID,
    data: schemas.ReviseResultRequest,
    current_user: Annotated[dict, Depends(get_current_user)],
):
    """Override LLM score with expert score + feedback — sets status to 'revised'."""
    supabase = get_supabase()
    row = _get_result_or_404(str(result_id))

    # Validate expert_score does not exceed max_score
    q_info = row.get("exam_questions") or {}
    max_score = row.get("llm_max_score") or q_info.get("max_score", 0)
    if data.expert_score > max_score:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"expert_score ({data.expert_score}) exceeds max_score ({max_score})",
        )

    updated = (
        supabase.table("grading_results")
        .update(
            {
                "expert_score": data.expert_score,
                "expert_feedback": data.expert_feedback,
                "status": "revised",
            }
        )
        .eq("id", str(result_id))
        .execute()
    )
    updated_row = updated.data[0]
    updated_row["exam_questions"] = row.get("exam_questions")
    return _build_grading_result_response(updated_row)


@router.post("/exams/{exam_id}/approve-all", response_model=schemas.BulkApproveResponse)
async def bulk_approve(
    exam_id: UUID,
    current_user: Annotated[dict, Depends(get_current_user)],
):
    """Bulk approve all 'pending' grading results for an exam."""
    supabase = get_supabase()

    # Verify exam exists
    exam_resp = maybe_single_safe(
        supabase.table("exams").select("id").eq("id", str(exam_id))
    )
    if not exam_resp.data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Exam not found"
        )

    # Fetch all pending result IDs for this exam (via submission join)
    pending_resp = (
        supabase.table("grading_results")
        .select("id, student_submissions!inner(exam_id)")
        .eq("student_submissions.exam_id", str(exam_id))
        .eq("status", "pending")
        .execute()
    )
    pending_results = pending_resp.data or []

    if not pending_results:
        return schemas.BulkApproveResponse(
            approved_count=0, message="No pending results to approve"
        )

    pending_ids = [r["id"] for r in pending_results]

    # Bulk update
    supabase.table("grading_results").update({"status": "approved"}).in_(
        "id", pending_ids
    ).execute()

    approved_count = len(pending_ids)
    return schemas.BulkApproveResponse(
        approved_count=approved_count,
        message=f"{approved_count} results approved successfully",
    )


@router.get("/exams/{exam_id}/export")
async def export_results_csv(
    exam_id: UUID,
    current_user: Annotated[dict, Depends(get_current_user)],
):
    """Export grading results as CSV.

    Columns: student_code, student_name, q1_score, q1_max, q2_score, q2_max, ...,
             total_score, max_total, status
    """
    supabase = get_supabase()

    # Verify exam exists
    exam_resp = maybe_single_safe(
        supabase.table("exams")
        .select("id, title, total_questions")
        .eq("id", str(exam_id))
    )
    if not exam_resp.data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Exam not found"
        )

    exam_data = exam_resp.data

    # Fetch questions (to know columns)
    questions_resp = (
        supabase.table("exam_questions")
        .select("id, question_number, max_score")
        .eq("exam_id", str(exam_id))
        .order("question_number")
        .execute()
    )
    questions = questions_resp.data or []
    q_ids = {q["id"]: q for q in questions}
    q_numbers = sorted(q["question_number"] for q in questions)

    # Fetch all submissions
    subs_resp = (
        supabase.table("student_submissions")
        .select("id, status, students(full_name, student_code)")
        .eq("exam_id", str(exam_id))
        .order("created_at")
        .execute()
    )
    submissions = subs_resp.data or []

    # Build CSV in memory
    output = io.StringIO()
    writer = csv.writer(output)

    # Header row
    header = ["student_code", "student_name"]
    for qnum in q_numbers:
        header += [f"q{qnum}_score", f"q{qnum}_max"]
    header += ["total_score", "max_total", "status"]
    writer.writerow(header)

    for sub in submissions:
        sub_id = sub["id"]
        student = sub.get("students") or {}

        # Fetch grading results for this submission
        gr_resp = (
            supabase.table("grading_results")
            .select("question_id, llm_score, expert_score, llm_max_score, status")
            .eq("submission_id", sub_id)
            .execute()
        )
        results_by_qid = {r["question_id"]: r for r in (gr_resp.data or [])}

        row = [student.get("student_code", ""), student.get("full_name", "")]
        total_score = 0.0
        max_total = 0.0

        for qnum in q_numbers:
            # Find the question id for this number
            qid = next(
                (q["id"] for q in questions if q["question_number"] == qnum), None
            )
            if qid and qid in results_by_qid:
                r = results_by_qid[qid]
                effective = (
                    r["expert_score"]
                    if r.get("expert_score") is not None
                    else r.get("llm_score", 0)
                )
                q_max = r.get("llm_max_score") or (q_ids.get(qid) or {}).get(
                    "max_score", 0
                )
                row += [effective, q_max]
                total_score += effective or 0
                max_total += q_max or 0
            else:
                q_max = (q_ids.get(qid) or {}).get("max_score", 0) if qid else 0
                row += ["", q_max]
                max_total += q_max or 0

        row += [total_score, max_total, sub.get("status", "")]
        writer.writerow(row)

    csv_content = output.getvalue()
    filename = f"exam_{exam_id}_results.csv"

    return StreamingResponse(
        iter([csv_content]),
        media_type="text/csv",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )

"""
Document endpoints — BE-S (upload/embed) + BE-J (list/status) responsibility.

POST /api/v1/documents/upload            <- BE-S Sprint 2
GET  /api/v1/documents?exam_id=...       <- BE-J Sprint 2
POST /api/v1/documents/submissions/upload <- BE-J Sprint 2
GET  /api/v1/documents/submissions?exam_id=... <- BE-J Sprint 2
"""

import logging
from typing import Annotated
from uuid import UUID, uuid4

from fastapi import (
    APIRouter,
    BackgroundTasks,
    Depends,
    File,
    Form,
    HTTPException,
    UploadFile,
    status,
)

from app import schemas
from app.database import get_supabase
from app.dependencies import get_current_user
from app.services import embedding_service, pdf_service

logger = logging.getLogger(__name__)
router = APIRouter()


# ── Helpers ───────────────────────────────────────────────────────────────────

def _verify_exam_owner(exam_id: UUID, user_id: str) -> dict:
    """Raise 404 if exam not found, 403 if not owner. Returns exam row."""
    supabase = get_supabase()
    resp = (
        supabase.table("exams")
        .select("id, created_by")
        .eq("id", str(exam_id))
        .maybe_single()
        .execute()
    )
    if not resp.data:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Exam not found")
    if resp.data["created_by"] != user_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")
    return resp.data


# ── Background task: parse + embed reference document ─────────────────────────

async def _embed_document_task(
    doc_id: str,
    exam_id: UUID,
    doc_type: str,
    pdf_bytes: bytes,
    original_filename: str,
) -> None:
    """Parse PDF, embed into Qdrant, update DB status. Runs in BackgroundTasks."""
    supabase = get_supabase()

    # Mark as processing
    supabase.table("documents").update({"embedding_status": "processing"}).eq("id", doc_id).execute()

    try:
        text = pdf_service.parse_pdf_bytes(pdf_bytes, filename=original_filename)
        chunk_count = await embedding_service.embed_document(
            exam_id=exam_id,
            doc_id=UUID(doc_id),
            doc_type=doc_type,
            text=text,
        )
        supabase.table("documents").update(
            {"embedding_status": "completed", "chunk_count": chunk_count}
        ).eq("id", doc_id).execute()
        logger.info("Embedded doc %s — %d chunks", doc_id, chunk_count)
    except Exception as exc:
        logger.exception("Embedding failed for doc %s: %s", doc_id, exc)
        supabase.table("documents").update({"embedding_status": "failed"}).eq("id", doc_id).execute()


# ── Background task: parse student submission ─────────────────────────────────

async def _parse_submission_task(
    submission_id: str,
    pdf_bytes: bytes,
    original_filename: str,
) -> None:
    """Parse student PDF and store text in DB. Runs in BackgroundTasks."""
    supabase = get_supabase()
    try:
        text = pdf_service.parse_pdf_bytes(pdf_bytes, filename=original_filename)
        supabase.table("student_submissions").update(
            {"parsed_text": text, "status": "parsed"}
        ).eq("id", submission_id).execute()
        logger.info("Parsed submission %s", submission_id)
    except Exception as exc:
        logger.exception("Parsing failed for submission %s: %s", submission_id, exc)
        # Leave status as 'uploaded' — can be retried


# ── Reference documents (answer key / rubric / course material) ───────────────


@router.post("/upload", response_model=schemas.DocumentUploadResponse, status_code=202)
async def upload_reference_document(
    background_tasks: BackgroundTasks,
    exam_id: UUID = Form(...),
    doc_type: schemas.DocType = Form(...),
    file: UploadFile = File(..., description="PDF only"),
    current_user: Annotated[dict, Depends(get_current_user)] = None,
):
    """Upload a reference PDF (answer key / rubric / course material).
    Parsing and embedding run asynchronously via BackgroundTasks.
    """
    if file.content_type not in ("application/pdf", "application/octet-stream"):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Only PDF files are accepted",
        )

    _verify_exam_owner(exam_id, current_user["id"])

    pdf_bytes = await file.read()
    if len(pdf_bytes) == 0:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Uploaded file is empty",
        )

    supabase = get_supabase()
    doc_id = str(uuid4())

    # Insert document record with 'pending' status
    resp = (
        supabase.table("documents")
        .insert(
            {
                "id": doc_id,
                "exam_id": str(exam_id),
                "doc_type": doc_type.value,
                "original_filename": file.filename or "upload.pdf",
                "file_path": "",          # Not storing to disk/S3 in this version
                "embedding_status": "pending",
                "chunk_count": None,
            }
        )
        .execute()
    )
    doc_row = resp.data[0]

    # Schedule background parsing + embedding
    background_tasks.add_task(
        _embed_document_task,
        doc_id,
        exam_id,
        doc_type.value,
        pdf_bytes,
        file.filename or "upload.pdf",
    )

    return schemas.DocumentUploadResponse(
        message="Document uploaded. Embedding in progress.",
        document=schemas.DocumentResponse(
            id=doc_row["id"],
            exam_id=doc_row["exam_id"],
            doc_type=doc_row["doc_type"],
            original_filename=doc_row["original_filename"],
            embedding_status=doc_row["embedding_status"],
            chunk_count=doc_row["chunk_count"],
            created_at=doc_row["created_at"],
        ),
    )


@router.get("", response_model=schemas.DocumentListResponse)
async def list_documents(
    exam_id: UUID,
    current_user: Annotated[dict, Depends(get_current_user)] = None,
):
    """List all documents for an exam with their embedding status."""
    supabase = get_supabase()

    # Verify exam exists
    exam_response = (
        supabase.table("exams")
        .select("id")
        .eq("id", str(exam_id))
        .maybe_single()
        .execute()
    )
    if not exam_response.data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Exam not found"
        )

    # Fetch documents
    response = (
        supabase.table("documents")
        .select("*")
        .eq("exam_id", str(exam_id))
        .order("created_at", desc=True)
        .execute()
    )
    documents = response.data

    return schemas.DocumentListResponse(
        documents=[
            schemas.DocumentResponse(
                id=doc["id"],
                exam_id=doc["exam_id"],
                doc_type=doc["doc_type"],
                original_filename=doc["original_filename"],
                embedding_status=doc["embedding_status"],
                chunk_count=doc["chunk_count"],
                created_at=doc["created_at"],
            )
            for doc in documents
        ],
        total=len(documents),
    )


# ── Student submissions ───────────────────────────────────────────────────────


@router.post("/submissions/upload", status_code=202)
async def upload_student_submission(
    background_tasks: BackgroundTasks,
    exam_id: UUID = Form(...),
    student_id: UUID = Form(...),
    file: UploadFile = File(..., description="PDF only"),
    current_user: Annotated[dict, Depends(get_current_user)] = None,
):
    """Upload a student answer PDF. Parses text asynchronously.

    Returns:
        202 { message, submission_id }
    """
    if file.content_type not in ("application/pdf", "application/octet-stream"):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Only PDF files are accepted",
        )

    supabase = get_supabase()

    # Verify exam exists
    exam_resp = (
        supabase.table("exams")
        .select("id")
        .eq("id", str(exam_id))
        .maybe_single()
        .execute()
    )
    if not exam_resp.data:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Exam not found")

    # Verify student exists
    student_resp = (
        supabase.table("students")
        .select("id")
        .eq("id", str(student_id))
        .maybe_single()
        .execute()
    )
    if not student_resp.data:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Student not found")

    pdf_bytes = await file.read()
    if len(pdf_bytes) == 0:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Uploaded file is empty",
        )

    submission_id = str(uuid4())
    original_filename = file.filename or "submission.pdf"

    # Insert submission record with 'uploaded' status
    supabase.table("student_submissions").insert(
        {
            "id": submission_id,
            "exam_id": str(exam_id),
            "student_id": str(student_id),
            "original_filename": original_filename,
            "file_path": "",
            "parsed_text": None,
            "status": "uploaded",
        }
    ).execute()

    # Schedule background PDF parsing
    background_tasks.add_task(
        _parse_submission_task,
        submission_id,
        pdf_bytes,
        original_filename,
    )

    return {
        "message": "Submission uploaded. Parsing in progress.",
        "submission_id": submission_id,
    }


@router.get("/submissions", response_model=schemas.SubmissionListResponse)
async def list_submissions(
    exam_id: UUID,
    current_user: Annotated[dict, Depends(get_current_user)] = None,
):
    """List all student submissions for an exam with grading summary."""
    supabase = get_supabase()

    # Verify exam exists
    exam_resp = (
        supabase.table("exams")
        .select("id, total_questions")
        .eq("id", str(exam_id))
        .maybe_single()
        .execute()
    )
    if not exam_resp.data:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Exam not found")

    total_questions = exam_resp.data.get("total_questions", 0)

    # Fetch submissions with student info
    subs_resp = (
        supabase.table("student_submissions")
        .select("id, student_id, original_filename, status, created_at, students(full_name, student_code)")
        .eq("exam_id", str(exam_id))
        .order("created_at", desc=True)
        .execute()
    )
    submissions = subs_resp.data or []

    summaries = []
    for sub in submissions:
        student = sub.get("students") or {}
        sub_id = sub["id"]

        # Fetch grading results for this submission to compute scores
        gr_resp = (
            supabase.table("grading_results")
            .select("llm_score, expert_score, status, exam_questions(max_score)")
            .eq("submission_id", sub_id)
            .execute()
        )
        results = gr_resp.data or []

        # Compute totals
        graded_questions = len(results)
        max_total_score = sum(
            (r.get("exam_questions") or {}).get("max_score", 0) for r in results
        )
        # Use expert_score if available, otherwise llm_score; only for approved/revised
        total_score: float | None = None
        if results:
            scored = []
            for r in results:
                if r.get("status") in ("approved", "revised"):
                    scored.append(r.get("expert_score") or r.get("llm_score") or 0)
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

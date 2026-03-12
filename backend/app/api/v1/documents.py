"""
Document endpoints — BE-S (upload/embed) + BE-J (list/status) responsibility.

POST /api/v1/documents/upload            ← BE-S Sprint 2
GET  /api/v1/documents?exam_id=...       ← BE-J Sprint 2
POST /api/v1/submissions/upload          ← BE-J Sprint 2
GET  /api/v1/submissions?exam_id=...     ← BE-J Sprint 2
"""
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, BackgroundTasks, Depends, File, Form, UploadFile

from app import schemas
from app.dependencies import get_current_user, get_supabase

router = APIRouter()


# ── Reference documents (answer key / rubric / course material) ───────────────

@router.post("/upload", response_model=schemas.DocumentUploadResponse, status_code=202)
async def upload_reference_document(
    exam_id: UUID = Form(...),
    doc_type: schemas.DocType = Form(...),
    file: UploadFile = File(..., description="PDF only"),
    background_tasks: BackgroundTasks = BackgroundTasks(),
    current_user: Annotated[dict, Depends(get_current_user)] = None,
    supabase=Depends(get_supabase),
):
    """Upload a reference PDF (answer key / rubric / course material).
    Parsing and embedding run asynchronously via BackgroundTasks.
    BE-S: implement in Sprint 2.
    """
    raise NotImplementedError


@router.get("", response_model=schemas.DocumentListResponse)
async def list_documents(
    exam_id: UUID,
    current_user: Annotated[dict, Depends(get_current_user)] = None,
    supabase=Depends(get_supabase),
):
    """List all documents for an exam with their embedding status.
    BE-J: implement in Sprint 2.
    """
    raise NotImplementedError


# ── Student submissions ───────────────────────────────────────────────────────

@router.post("/submissions/upload", status_code=202)
async def upload_student_submission(
    exam_id: UUID = Form(...),
    student_id: UUID = Form(...),
    file: UploadFile = File(..., description="PDF only"),
    background_tasks: BackgroundTasks = BackgroundTasks(),
    current_user: Annotated[dict, Depends(get_current_user)] = None,
    supabase=Depends(get_supabase),
):
    """Upload a student answer PDF. Parses text asynchronously.
    BE-J: implement in Sprint 2.
    """
    raise NotImplementedError


@router.get("/submissions", response_model=schemas.SubmissionListResponse)
async def list_submissions(
    exam_id: UUID,
    current_user: Annotated[dict, Depends(get_current_user)] = None,
    supabase=Depends(get_supabase),
):
    """List all student submissions for an exam.
    BE-J: implement in Sprint 2.
    """
    raise NotImplementedError

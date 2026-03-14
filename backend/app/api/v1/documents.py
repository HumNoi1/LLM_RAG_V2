"""
Document endpoints — BE-S (upload/embed) + BE-J (list/status) responsibility.

POST /api/v1/documents/upload            ← BE-S Sprint 2
GET  /api/v1/documents?exam_id=...       ← BE-J Sprint 2
POST /api/v1/submissions/upload          ← BE-J Sprint 2
GET  /api/v1/submissions?exam_id=...     ← BE-J Sprint 2
"""

import logging
import os
from pathlib import Path
from typing import Annotated
from uuid import UUID

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
from app.config import get_settings
from app.core.exceptions import PDFParseException, EmbeddingException
from app.database import db
from app.dependencies import get_current_user
from app.services.pdf_service import parse_pdf_bytes
from app.services.embedding_service import embed_document

logger = logging.getLogger(__name__)

router = APIRouter()

# Upload directory (relative to backend root)
UPLOAD_DIR = Path("uploads")

# ── ค่า response สำหรับ error ที่ใช้ร่วมกัน ──────────────────────────────────
_auth_error = {
    401: {"model": schemas.ErrorResponse, "description": "ไม่ได้ login หรือ token หมดอายุ"}
}


def _get_upload_dir(exam_id: UUID, sub: str = "documents") -> Path:
    """Return and ensure upload directory exists."""
    upload_path = UPLOAD_DIR / str(exam_id) / sub
    upload_path.mkdir(parents=True, exist_ok=True)
    return upload_path


# ── Background task: parse + embed ────────────────────────────────────────────


async def _process_and_embed_document(
    doc_id: str, exam_id: str, file_data: bytes, filename: str
) -> None:
    """Background task: parse PDF → embed into Qdrant → update DB status."""
    try:
        # Update status → processing
        await db.document.update(
            where={"id": doc_id},
            data={"embeddingStatus": "processing"},
        )

        # Parse PDF
        text = parse_pdf_bytes(file_data, filename)

        # Embed
        doc_record = await db.document.find_unique(where={"id": doc_id})
        chunk_count = await embed_document(
            exam_id=UUID(exam_id),
            doc_id=UUID(doc_id),
            doc_type=doc_record.docType,
            text=text,
        )

        # Update status → completed
        await db.document.update(
            where={"id": doc_id},
            data={
                "embeddingStatus": "completed",
                "chunkCount": chunk_count,
            },
        )
        logger.info(
            "Document %s embedded successfully (%d chunks)", doc_id, chunk_count
        )

    except (PDFParseException, EmbeddingException) as e:
        logger.error("Document processing failed for %s: %s", doc_id, e.message)
        await db.document.update(
            where={"id": doc_id},
            data={"embeddingStatus": "failed"},
        )
    except Exception as e:
        logger.error("Unexpected error processing document %s: %s", doc_id, e)
        await db.document.update(
            where={"id": doc_id},
            data={"embeddingStatus": "failed"},
        )


# ── Reference documents (answer key / rubric / course material) ───────────────


@router.post(
    "/upload",
    response_model=schemas.DocumentUploadResponse,
    status_code=202,
    summary="อัปโหลดเอกสารอ้างอิง (เฉลย/rubric/เนื้อหาวิชา)",
    responses={
        **_auth_error,
        400: {
            "model": schemas.ErrorResponse,
            "description": "ไฟล์ไม่ใช่ PDF หรือขนาดเกิน 50MB",
        },
        404: {"model": schemas.ErrorResponse, "description": "ไม่พบข้อสอบที่ระบุ"},
    },
)
async def upload_reference_document(
    exam_id: UUID = Form(..., description="UUID ของข้อสอบที่เอกสารนี้สังกัด"),
    doc_type: schemas.DocType = Form(
        ..., description="ประเภทเอกสาร: answer_key, rubric, หรือ course_material"
    ),
    file: UploadFile = File(..., description="ไฟล์ PDF เท่านั้น (สูงสุด 50MB)"),
    background_tasks: BackgroundTasks = BackgroundTasks(),
    current_user: Annotated[dict, Depends(get_current_user)] = None,
):
    """อัปโหลดเอกสาร PDF เป็นข้อมูลอ้างอิงสำหรับการตรวจข้อสอบ

    **ขั้นตอนการทำงาน (async):**
    1. บันทึกไฟล์ลง disk
    2. สร้าง record ใน DB (status = `pending`)
    3. ส่ง background task: parse PDF → chunk text → embed ลง Qdrant vector DB
    4. เมื่อเสร็จแล้ว status จะเปลี่ยนเป็น `completed` หรือ `failed`

    **ประเภทเอกสาร:**
    - `answer_key` — เฉลยข้อสอบ
    - `rubric` — เกณฑ์การให้คะแนน
    - `course_material` — เนื้อหาวิชาประกอบ
    """
    # Validate file type
    if not file.filename or not file.filename.lower().endswith(".pdf"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only PDF files are accepted",
        )

    # Validate file size (max 50MB)
    file_data = await file.read()
    max_size = 50 * 1024 * 1024  # 50 MB
    if len(file_data) > max_size:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File size exceeds 50MB limit",
        )

    # Verify exam exists
    exam = await db.exam.find_unique(where={"id": str(exam_id)})
    if not exam:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Exam '{exam_id}' not found",
        )

    # Save file to disk
    upload_dir = _get_upload_dir(exam_id)
    safe_filename = file.filename.replace("/", "_").replace("\\", "_")
    file_path = upload_dir / safe_filename

    # Handle duplicate filenames by appending counter
    counter = 1
    original_stem = file_path.stem
    while file_path.exists():
        file_path = upload_dir / f"{original_stem}_{counter}{file_path.suffix}"
        counter += 1

    file_path.write_bytes(file_data)

    # Create DB record
    doc_record = await db.document.create(
        data={
            "examId": str(exam_id),
            "docType": doc_type.value,
            "originalFilename": safe_filename,
            "filePath": str(file_path),
            "embeddingStatus": "pending",
        }
    )

    # Schedule background processing
    background_tasks.add_task(
        _process_and_embed_document,
        doc_id=doc_record.id,
        exam_id=str(exam_id),
        file_data=file_data,
        filename=safe_filename,
    )

    return schemas.DocumentUploadResponse(
        message="Document uploaded. Embedding in progress.",
        document=schemas.DocumentResponse(
            id=doc_record.id,
            exam_id=doc_record.examId,
            doc_type=doc_record.docType,
            original_filename=doc_record.originalFilename,
            embedding_status=doc_record.embeddingStatus,
            chunk_count=doc_record.chunkCount,
            created_at=doc_record.createdAt,
        ),
    )


@router.get(
    "",
    response_model=schemas.DocumentListResponse,
    summary="ดูรายการเอกสารของข้อสอบ",
    responses={
        **_auth_error,
        404: {"model": schemas.ErrorResponse, "description": "ไม่พบข้อสอบที่ระบุ"},
    },
)
async def list_documents(
    exam_id: UUID,
    current_user: Annotated[dict, Depends(get_current_user)] = None,
):
    """ดึงรายการเอกสารทั้งหมดของข้อสอบ พร้อม embedding status

    - ใช้ query parameter `exam_id` เพื่อกรองตามข้อสอบ
    - แต่ละเอกสารจะแสดง `embedding_status` (pending/processing/completed/failed)

    **สถานะ:** BE-J implement ใน Sprint 2
    """
    raise NotImplementedError


# ── Student submissions ───────────────────────────────────────────────────────


@router.post(
    "/submissions/upload",
    status_code=202,
    summary="อัปโหลดกระดาษคำตอบนักศึกษา",
    responses={
        **_auth_error,
        400: {"model": schemas.ErrorResponse, "description": "ไฟล์ไม่ใช่ PDF"},
        404: {"model": schemas.ErrorResponse, "description": "ไม่พบข้อสอบหรือนักศึกษาที่ระบุ"},
    },
)
async def upload_student_submission(
    exam_id: UUID = Form(..., description="UUID ของข้อสอบ"),
    student_id: UUID = Form(..., description="UUID ของนักศึกษา"),
    file: UploadFile = File(..., description="กระดาษคำตอบ PDF"),
    background_tasks: BackgroundTasks = BackgroundTasks(),
    current_user: Annotated[dict, Depends(get_current_user)] = None,
):
    """อัปโหลด PDF กระดาษคำตอบของนักศึกษา

    **ขั้นตอนการทำงาน (async):**
    1. บันทึกไฟล์ลง disk
    2. สร้าง submission record (status = `uploaded`)
    3. Background task: parse PDF → เก็บ parsed text
    4. Status เปลี่ยนเป็น `parsed` เมื่อเสร็จ

    **สถานะ:** BE-J implement ใน Sprint 2
    """
    raise NotImplementedError


@router.get(
    "/submissions",
    response_model=schemas.SubmissionListResponse,
    summary="ดูรายการกระดาษคำตอบของข้อสอบ",
    responses={
        **_auth_error,
        404: {"model": schemas.ErrorResponse, "description": "ไม่พบข้อสอบที่ระบุ"},
    },
)
async def list_submissions(
    exam_id: UUID,
    current_user: Annotated[dict, Depends(get_current_user)] = None,
):
    """ดึงรายการ submission ทั้งหมดของข้อสอบ

    - ใช้ query parameter `exam_id` เพื่อกรองตามข้อสอบ
    - แสดงข้อมูลนักศึกษา, สถานะ, และสรุปคะแนน

    **สถานะ:** BE-J implement ใน Sprint 2
    """
    raise NotImplementedError

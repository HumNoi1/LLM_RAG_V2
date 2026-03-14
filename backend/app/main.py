import logging

from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from dotenv import load_dotenv

load_dotenv()

from app.config import get_settings
from app.core.exceptions import AppException, to_http_exception
from app.database import connect_db, disconnect_db
from app.api.v1.auth import router as auth_router
from app.api.v1.exams import router as exams_router
from app.api.v1.documents import router as documents_router
from app.api.v1.grading import router as grading_router
from app.api.v1.review import router as review_router

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    await connect_db()
    yield
    await disconnect_db()


settings = get_settings()

# ── Sprint 4: Structured logging config ──────────────────────────────────────
logging.basicConfig(
    level=logging.DEBUG if not settings.is_production else logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(name)s:%(lineno)d | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)

# ── OpenAPI tag metadata ──────────────────────────────────────────────────────
# อธิบายแต่ละกลุ่ม endpoint ใน Swagger UI เพื่อให้ FE เข้าใจการใช้งาน
openapi_tags = [
    {
        "name": "Health",
        "description": "ตรวจสอบสถานะระบบ — ใช้สำหรับ Docker healthcheck, load balancer, และ monitoring",
    },
    {
        "name": "Auth",
        "description": "ระบบยืนยันตัวตน — ลงทะเบียน, เข้าสู่ระบบ, รีเฟรช JWT token, ดูข้อมูลผู้ใช้ปัจจุบัน",
    },
    {
        "name": "Exams",
        "description": "จัดการข้อสอบ (CRUD) — สร้าง, แก้ไข, ลบข้อสอบ และจัดการคำถามย่อย (sub-resource)",
    },
    {
        "name": "Documents",
        "description": (
            "อัปโหลดเอกสาร PDF (เฉลย / rubric / เนื้อหาวิชา) และกระดาษคำตอบนักศึกษา\n\n"
            "เอกสารอ้างอิงจะถูก parse → chunk → embed ลง Qdrant vector DB แบบ async"
        ),
    },
    {
        "name": "Grading",
        "description": (
            "สั่งให้ LLM ตรวจข้อสอบโดยใช้ RAG context จาก Qdrant\n\n"
            "การตรวจทำงานใน background — ใช้ polling endpoint เพื่อดู progress"
        ),
    },
    {
        "name": "Review",
        "description": (
            "ผู้เชี่ยวชาญตรวจสอบผลการให้คะแนนของ LLM\n\n"
            "approve คะแนน LLM ตามเดิม หรือ revise ด้วยคะแนน + feedback ของผู้เชี่ยวชาญ\n"
            "รองรับ bulk approve และ export CSV"
        ),
    },
]

app = FastAPI(
    title="LLM RAG Exam Grading API",
    description=(
        "## ระบบตรวจข้อสอบอัตนัยด้วย AI (RAG + LLM)\n\n"
        "**Tech Stack:** BGE-M3 embeddings + Qdrant vector DB + Groq llama-3.3-70b-versatile\n\n"
        "### ขั้นตอนการใช้งาน\n"
        "1. **สร้างข้อสอบ** — `POST /exams` พร้อมเพิ่มคำถาม\n"
        "2. **อัปโหลดเฉลย/rubric** — `POST /documents/upload` (PDF) → ระบบ embed อัตโนมัติ\n"
        "3. **อัปโหลดกระดาษคำตอบ** — `POST /documents/submissions/upload` (PDF)\n"
        "4. **สั่งตรวจ** — `POST /grading/start` → LLM ตรวจทุก submission แบบ async\n"
        "5. **ตรวจสอบผล** — `GET /review/...` → approve หรือ revise คะแนน\n"
        "6. **ส่งออก** — `GET /review/exams/{id}/export` → CSV\n\n"
        "### Authentication\n"
        "ทุก endpoint (ยกเว้น `/auth/register`, `/auth/login`) ต้องส่ง `Authorization: Bearer <JWT>` header"
    ),
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
    openapi_tags=openapi_tags,
)


# ── Sprint 4: Global exception handlers ──────────────────────────────────────
# จัดการ error ทั้งหมดให้ส่ง JSON response ที่สม่ำเสมอกลับไปหา client


@app.exception_handler(AppException)
async def app_exception_handler(request: Request, exc: AppException):
    """จัดการ AppException ทั้งหมด — แปลงเป็น JSON response ที่มี format เดียวกัน"""
    logger.warning(
        "AppException [%d] %s: %s",
        exc.status_code,
        request.url.path,
        exc.message,
    )
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "detail": exc.message,
            "error_type": type(exc).__name__,
        },
    )


@app.exception_handler(NotImplementedError)
async def not_implemented_handler(request: Request, exc: NotImplementedError):
    """จัดการ endpoint ที่ยังไม่ได้ implement (BE-J stub endpoints)"""
    logger.info("NotImplementedError at %s", request.url.path)
    return JSONResponse(
        status_code=501,
        content={
            "detail": "This endpoint is not yet implemented",
            "error_type": "NotImplementedError",
        },
    )


@app.exception_handler(Exception)
async def generic_exception_handler(request: Request, exc: Exception):
    """จัดการ unexpected errors ทั้งหมด — ไม่ให้ stack trace หลุดไปหา client"""
    logger.error(
        "Unhandled exception at %s: %s",
        request.url.path,
        str(exc),
        exc_info=True,
    )
    return JSONResponse(
        status_code=500,
        content={
            "detail": "Internal server error" if settings.is_production else str(exc),
            "error_type": "InternalServerError",
        },
    )


# ── CORS ─────────────────────────────────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Routers ──────────────────────────────────────────────────────────────────
app.include_router(auth_router, prefix="/api/v1")
app.include_router(exams_router, prefix="/api/v1/exams", tags=["Exams"])
app.include_router(documents_router, prefix="/api/v1/documents", tags=["Documents"])
app.include_router(grading_router, prefix="/api/v1/grading", tags=["Grading"])
app.include_router(review_router, prefix="/api/v1/review", tags=["Review"])


# ── Health Check ─────────────────────────────────────────────────────────────
@app.get(
    "/health",
    tags=["Health"],
    summary="ตรวจสอบสถานะระบบ",
    response_description="สถานะ ok พร้อม environment ปัจจุบัน",
)
async def health_check():
    """ตรวจสอบว่า API server ทำงานอยู่

    - ใช้สำหรับ Docker healthcheck, load balancer, และ monitoring
    - ส่งกลับ `status: ok` และ `env` (development/production)
    """
    return {"status": "ok", "env": settings.app_env}

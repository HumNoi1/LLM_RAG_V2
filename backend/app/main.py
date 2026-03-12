from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

load_dotenv()

from app.config import get_settings
from app.database import connect_db, disconnect_db
from app.api.v1.auth import router as auth_router
from app.api.v1.exams import router as exams_router
from app.api.v1.documents import router as documents_router
from app.api.v1.grading import router as grading_router
from app.api.v1.review import router as review_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    await connect_db()
    yield
    await disconnect_db()


settings = get_settings()

app = FastAPI(
    title="LLM RAG Exam Grading API",
    description="AI-powered essay exam grading system using RAG + LLM (BGE-M3 + Groq llama-3.3)",
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
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
app.include_router(exams_router, prefix="/api/v1/exams", tags=["exams"])
app.include_router(documents_router, prefix="/api/v1/documents", tags=["documents"])
app.include_router(grading_router, prefix="/api/v1/grading", tags=["grading"])
app.include_router(review_router, prefix="/api/v1/review", tags=["review"])


@app.get("/health")
async def health_check():
    return {"status": "ok"}


# ── Health Check ─────────────────────────────────────────────────────────────
@app.get("/health", tags=["health"])
async def health_check():
    return {"status": "ok", "env": settings.app_env}

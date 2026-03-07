from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import get_settings

settings = get_settings()

app = FastAPI(
    title="LLM RAG Exam Grading API",
    description="AI-powered essay exam grading system using RAG + LLM (BGE-M3 + Groq llama-3.3)",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
)

# ── CORS ─────────────────────────────────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",   # Next.js dev server
        "http://127.0.0.1:3000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Routers ───────────────────────────────────────────────────────────────────
# Uncomment each router as it is implemented by the respective developer:

# from app.api.v1 import auth
# app.include_router(auth.router, prefix="/api/v1/auth", tags=["auth"])

# from app.api.v1 import exams
# app.include_router(exams.router, prefix="/api/v1/exams", tags=["exams"])

# from app.api.v1 import documents
# app.include_router(documents.router, prefix="/api/v1/documents", tags=["documents"])

# from app.api.v1 import grading
# app.include_router(grading.router, prefix="/api/v1/grading", tags=["grading"])

# from app.api.v1 import review
# app.include_router(review.router, prefix="/api/v1/review", tags=["review"])


# ── Health Check ─────────────────────────────────────────────────────────────
@app.get("/health", tags=["health"])
async def health_check():
    return {"status": "ok", "env": settings.app_env}

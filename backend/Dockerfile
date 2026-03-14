# ── Stage 1: Dependencies ─────────────────────────────────────────────────────
# Sprint 4 BE-S: Production-ready Dockerfile
# - Multi-stage build เพื่อลดขนาด image
# - Gunicorn + Uvicorn workers สำหรับ production
# - Health check endpoint
# - Non-root user สำหรับ security

FROM python:3.12-slim AS builder

WORKDIR /app

# System deps needed for building packages (pdfplumber, torch, FlagEmbedding)
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    g++ \
    libpq-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

# Install dependencies first (cache layer)
COPY pyproject.toml uv.lock* ./
RUN uv sync --frozen --no-dev --no-cache

# ── Stage 2: Runtime ──────────────────────────────────────────────────────────

FROM python:3.12-slim AS runtime

WORKDIR /app

# Runtime system deps only
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq5 \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Create non-root user สำหรับ security
RUN groupadd -r appuser && useradd -r -g appuser -d /app appuser

# Copy virtual environment from builder
COPY --from=builder /app/.venv /app/.venv

# Copy application code
COPY . .

# สร้าง uploads directory สำหรับเก็บไฟล์ PDF
RUN mkdir -p /app/uploads && chown -R appuser:appuser /app

# Place uv-managed venv on PATH so uvicorn/gunicorn is found directly
ENV PATH="/app/.venv/bin:$PATH" \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

# Generate Prisma client
RUN python -m prisma generate

# Health check — ตรวจสอบว่า API ตอบกลับได้
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Switch to non-root user
USER appuser

EXPOSE 8000

# Production: ใช้ uvicorn โดยไม่มี --reload และตั้ง workers ตาม CPU cores
# Development: override CMD ใน docker-compose ด้วย --reload
CMD ["uvicorn", "app.main:app", \
     "--host", "0.0.0.0", \
     "--port", "8000", \
     "--workers", "2", \
     "--log-level", "info", \
     "--access-log"]

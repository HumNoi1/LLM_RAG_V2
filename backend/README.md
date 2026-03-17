# Backend Setup and Test Guide

FastAPI backend for the LLM RAG exam grading system.

## Prerequisites

- Python 3.12
- `uv` installed
- Docker Desktop running
- Supabase project (PostgreSQL credentials)
- Groq API key

## 1) Start Qdrant (Docker)

Run from repo root:

```bash
docker compose up -d qdrant
```

Check status:

```bash
docker compose ps qdrant
```

Qdrant dashboard: `http://localhost:6333/dashboard`

## 2) Configure environment

`backend/.env` is already prepared as a template. Fill in real values for these keys before running:

- `JWT_SECRET_KEY`
- `SUPABASE_URL`
- `SUPABASE_KEY`
- `SUPABASE_SERVICE_ROLE_KEY`
- `DATABASE_URL`
- `DIRECT_URL`
- `GROQ_API_KEY`

Default local values that you usually keep as-is:

- `APP_ENV="development"`
- `QDRANT_HOST="localhost"`
- `QDRANT_PORT=6333`

## 3) Install dependencies with uv

Run from `backend/`:

```bash
uv sync --dev
```

Generate Prisma client:

```bash
uv run python -m prisma generate
```

If this is first-time DB setup, push schema:

```bash
uv run python -m prisma db push
```

## 4) Run backend

```bash
uv run uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

API docs:

- Swagger: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`
- Health: `http://localhost:8000/health`

## 5) Run tests

From `backend/`:

```bash
uv run pytest tests -q
```

Useful targeted tests:

```bash
uv run pytest tests/test_pdf_service.py -q
uv run pytest tests/test_embedding_service.py -q
uv run pytest tests/test_rag_service.py -q
uv run pytest tests/test_grading_pipeline_integration.py -q
```

## 6) Optional PoC checks

Embedding + Qdrant:

```bash
uv run python poc/test_embedding.py
```

Groq grading:

```bash
uv run python poc/test_grading.py
```

## Notes

- Do not commit `backend/.env` with real keys.
- If backend runs in Docker (`backend-dev` or `backend` service), compose sets `QDRANT_HOST=qdrant` automatically.

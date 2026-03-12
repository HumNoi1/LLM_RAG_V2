# LLM RAG Exam Grading

ระบบตรวจข้อสอบอัตนัยอัตโนมัติด้วย AI — RAG (Retrieval-Augmented Generation) + LLM

---

## Tech Stack

| Layer | Tech |
|-------|------|
| **Frontend** | Next.js 15 (App Router), TypeScript, Tailwind CSS |
| **Backend** | Python 3.12, FastAPI, Prisma ORM |
| **Database** | Supabase (PostgreSQL) |
| **Embedding** | BGE-M3 (`BAAI/bge-m3`) via LlamaIndex |
| **Vector DB** | Qdrant |
| **LLM** | Groq API (`llama-3.3-70b-versatile`) |
| **Auth** | JWT (python-jose HS256) + bcrypt |

---

## Project Structure

```
LLM_RAG_V2/
├── backend/          # FastAPI backend
│   ├── app/
│   │   ├── api/v1/   # Routers (auth, exams, documents, grading, review)
│   │   ├── core/     # security.py (JWT + bcrypt)
│   │   ├── schemas/  # Pydantic schemas
│   │   ├── services/ # Business logic
│   │   ├── config.py
│   │   ├── database.py
│   │   └── main.py
│   ├── prisma/
│   │   └── schema.prisma
│   ├── poc/          # PoC scripts (embedding + grading)
│   └── .env.example
├── frontend/         # Next.js frontend
│   ├── app/
│   │   ├── login/    # Login page (/login)
│   │   └── dashboard/
│   └── src/
│       ├── lib/      # api.ts, auth.tsx
│       ├── components/
│       └── types/
└── docker-compose.yml
```

---

## Quick Start

### 1. Prerequisites

- Python 3.12+
- Node.js 18+
- Docker (for Qdrant)

### 2. Start Qdrant

```bash
docker compose up -d
```

### 3. Backend

```bash
cd backend
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt
prisma generate

cp .env.example .env             # Fill in values
uvicorn app.main:app --reload
```

API docs: http://localhost:8000/docs

### 4. Frontend

```bash
cd frontend
npm install
npm run dev
```

App: http://localhost:3000/login

---

## Environment Variables

Copy `backend/.env.example` → `backend/.env` and fill in:

| Variable | Description |
|----------|-------------|
| `DATABASE_URL` | Supabase connection pooler URL |
| `DIRECT_URL` | Supabase direct connection URL (for migrations) |
| `JWT_SECRET_KEY` | Secret key for JWT signing |
| `GROQ_API_KEY` | Groq API key ([console.groq.com](https://console.groq.com)) |
| `QDRANT_HOST` | Qdrant host (default: `localhost`) |

---

## Team & Sprints

| Sprint | Focus |
|--------|-------|
| **Sprint 1** | Foundation: Auth, DB schema, Docker, PoC |
| **Sprint 2** | Core: PDF upload, Embedding, Exam CRUD |
| **Sprint 3** | Grading Engine + Review/Approve workflow |
| **Sprint 4** | Polish, Testing, Deploy |

See [TASK_ASSIGNMENT.md](TASK_ASSIGNMENT.md) for full task breakdown.

---

## API Contract

See [API_CONTRACT.md](API_CONTRACT.md) for full request/response schemas.

Base URL: `http://localhost:8000/api/v1`

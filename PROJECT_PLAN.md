# 📋 Project Plan: LLM RAG Exam Grading Web App

## TL;DR

สร้างเว็บตรวจข้อสอบอัตนัย (essay) ด้วย LLM + RAG โดยอาจารย์อัปโหลด PDF เฉลย/Rubric/เนื้อหาวิชา เป็น knowledge base จากนั้นอัปโหลด PDF คำตอบนักเรียน ให้ LLM ตรวจให้คะแนนพร้อมเหตุผล แล้วอาจารย์มา review/approve

---

## Architecture Overview

```
┌──────────────────┐     ┌──────────────────────┐     ┌──────────────────┐
│   Next.js 15     │────▶│   FastAPI Backend     │────▶│   Groq LLM API   │
│   (Frontend)     │◀────│   (Python 3.12)       │◀────│   (Qwen3-32B)    │
│   Port: 3000     │     │   Port: 8000          │     └──────────────────┘
└──────────────────┘     │                       │     ┌──────────────────┐
                         │   LlamaIndex          │────▶│   Qdrant         │
                         │   BGE-M3 (local)      │◀────│   (Vector DB)    │
                         │                       │     │   Port: 6333     │
                         │                       │     └──────────────────┘
                         │                       │     ┌──────────────────┐
                         │                       │────▶│   Supabase       │
                         │                       │◀────│                  │
                         └──────────────────────┘     └──────────────────┘
```

## Tech Stack

| Layer | Technology |
|-------|-----------|
| **Frontend** | Next.js 15 (App Router), TypeScript, Tailwind CSS, shadcn/ui, Zustand, react-pdf |
| **Backend** | Python 3.12, FastAPI, LlamaIndex, Pydantic v2 |
| **LLM** | Groq API (llama-3.3-70b-versatile) |
| **Embedding** | BAAI/bge-m3 (local, multilingual/Thai) |
| **Vector DB** | Qdrant (Docker) |
| **SQL DB** | Supabase |
| **Auth** | Custom JWT (python-jose HS256 + bcrypt) |
| **Infra** | Docker Compose |

---

## Project Structure

```
LLM_RAG_V2/
├── backend/
│   ├── app/
│   │   ├── main.py                  # FastAPI app entry
│   │   ├── config.py                # Pydantic Settings
│   │   ├── dependencies.py          # Dependency injection
│   │   ├── api/
│   │   │   └── v1/
│   │   │       ├── auth.py          # Login/register endpoints
│   │   │       ├── exams.py         # Exam CRUD
│   │   │       ├── documents.py     # PDF upload & embedding
│   │   │       ├── grading.py       # Trigger grading & results
│   │   │       └── review.py        # Expert review endpoints
│   │   ├── models/                  # SQLAlchemy models
│   │   │   ├── user.py
│   │   │   ├── exam.py
│   │   │   ├── document.py
│   │   │   └── grading.py
│   │   ├── schemas/                 # Pydantic request/response schemas
│   │   ├── services/
│   │   │   ├── pdf_service.py       # PDF parsing (pdfplumber)
│   │   │   ├── embedding_service.py # BGE-M3 + Qdrant
│   │   │   ├── rag_service.py       # LlamaIndex RAG pipeline
│   │   │   ├── grading_service.py   # LLM grading orchestration
│   │   │   └── auth_service.py      # JWT logic
│   │   └── core/
│   │       ├── security.py          # JWT, password hashing
│   │       └── exceptions.py        # Custom exceptions
│   ├── tests/
│   ├── requirements.txt
│   ├── .env.example
│   └── Dockerfile
├── frontend/
│   ├── src/
│   │   ├── app/                     # Next.js App Router pages
│   │   ├── components/              # Reusable UI components
│   │   ├── lib/                     # API client, auth helpers
│   │   └── types/                   # TypeScript interfaces
│   ├── package.json
│   └── Dockerfile
├── docker-compose.yml
├── .gitignore
├── PROJECT_PLAN.md
├── TASK_ASSIGNMENT.md
└── README.md
```

---

## Phase 1: Project Setup & Infrastructure

### Step 1.1 — Monorepo & Docker
- สร้างโครงสร้าง project ตาม tree ด้านบน
- `docker-compose.yml` — Qdrant (port 6333), Backend (port 8000), Frontend (port 3000)
- Supabase ใช้เป็น hosted service (ไม่อยู่ใน Docker)

### Step 1.2 — Backend Dependencies
```
fastapi, uvicorn[standard]
python-jose[cryptography], passlib[bcrypt]
llama-index, llama-index-vector-stores-qdrant
llama-index-llms-groq, llama-index-embeddings-huggingface
FlagEmbedding (BGE-M3)
qdrant-client, supabase-py
pdfplumber, python-multipart, pydantic-settings
```

### Step 1.3 — Frontend Dependencies
```
next, react, typescript
tailwindcss, shadcn/ui
axios, zustand, react-pdf
```

---

## Phase 2: Database Schema & Auth

### Supabase PostgreSQL Schema

**users**
| Column | Type | Note |
|--------|------|------|
| id | UUID PK | |
| email | varchar | unique |
| password_hash | varchar | bcrypt |
| full_name | varchar | |
| role | enum | 'teacher', 'admin' |
| created_at | timestamp | |
| updated_at | timestamp | |

**exams**
| Column | Type | Note |
|--------|------|------|
| id | UUID PK | |
| title | varchar | |
| subject | varchar | |
| description | text | |
| created_by | UUID FK → users | |
| total_questions | int | |
| created_at | timestamp | |
| updated_at | timestamp | |

**exam_questions**
| Column | Type | Note |
|--------|------|------|
| id | UUID PK | |
| exam_id | UUID FK → exams | |
| question_number | int | |
| question_text | text | |
| max_score | float | |
| created_at | timestamp | |

**rubrics**
| Column | Type | Note |
|--------|------|------|
| id | UUID PK | |
| question_id | UUID FK → exam_questions | |
| criteria_text | text | |
| score_range | varchar | |
| description | text | |

**documents**
| Column | Type | Note |
|--------|------|------|
| id | UUID PK | |
| exam_id | UUID FK → exams | |
| doc_type | enum | 'answer_key', 'rubric', 'course_material' |
| original_filename | varchar | |
| file_path | varchar | |
| embedding_status | enum | 'pending', 'processing', 'completed', 'failed' |
| chunk_count | int | |
| created_at | timestamp | |

**students**
| Column | Type | Note |
|--------|------|------|
| id | UUID PK | |
| student_code | varchar | |
| full_name | varchar | |
| created_by | UUID FK → users | |
| created_at | timestamp | |

**student_submissions**
| Column | Type | Note |
|--------|------|------|
| id | UUID PK | |
| exam_id | UUID FK → exams | |
| student_id | UUID FK → students | |
| original_filename | varchar | |
| file_path | varchar | |
| parsed_text | text | |
| status | enum | 'uploaded', 'parsed', 'grading', 'graded', 'reviewed' |
| created_at | timestamp | |

**grading_results**
| Column | Type | Note |
|--------|------|------|
| id | UUID PK | |
| submission_id | UUID FK → student_submissions | |
| question_id | UUID FK → exam_questions | |
| student_answer_text | text | |
| llm_score | float | |
| llm_max_score | float | |
| llm_reasoning | text | |
| llm_model_used | varchar | |
| expert_score | float | nullable |
| expert_feedback | text | nullable |
| status | enum | 'pending_review', 'approved', 'revised' |
| graded_at | timestamp | |
| reviewed_at | timestamp | nullable |
| reviewed_by | UUID FK → users | nullable |

### Custom JWT Auth
- `POST /api/v1/auth/register` — สร้าง user (admin only)
- `POST /api/v1/auth/login` — return access_token (30min) + refresh_token (7 days)
- `POST /api/v1/auth/refresh` — renew access token
- Middleware: decode JWT → inject `current_user`
- Password: bcrypt via passlib
- Token: python-jose HS256

---

## Phase 3: PDF Processing & RAG Pipeline

### Step 3.1 — PDF Upload & Parsing
- ใช้ `pdfplumber` แปลง PDF → text
- 2 ประเภท:
  1. **Reference docs** (เฉลย, Rubric, เนื้อหาวิชา) → chunk → embed → Qdrant
  2. **Student answer PDFs** → parse เต็ม → เก็บ raw text ลง `student_submissions`

### Step 3.2 — Embedding Pipeline
- LlamaIndex `HuggingFaceEmbedding` with `BAAI/bge-m3`
- Chunking: `SentenceSplitter(chunk_size=512, chunk_overlap=50)`
- Metadata per chunk: `exam_id`, `doc_type`, `question_number`
- Qdrant collection per exam: `exam_{exam_id}`

### Step 3.3 — RAG Query Pipeline
- `VectorStoreIndex` from Qdrant
- `QueryEngine` with Groq LLM
- Custom grading prompt:

```
คุณเป็นผู้เชี่ยวชาญตรวจข้อสอบ ให้ตรวจคำตอบนักเรียนตาม rubric และเฉลยที่ให้มา

โจทย์: {question}
คะแนนเต็ม: {max_score}
คำตอบนักเรียน: {student_answer}

Context (เฉลย + Rubric + เนื้อหา): {context}

ตอบเป็น JSON:
{
  "score": <float>,
  "reasoning": "<string>",
  "covered_points": ["..."],
  "missed_points": ["..."]
}
```

---

## Phase 4: Grading Orchestration

### Grading Service Flow
1. `POST /api/v1/grading/start` — trigger grading for all submissions of an exam
2. For each student submission:
   - Split student text by question (heuristic regex + LLM fallback)
   - For each question: RAG query → retrieve relevant rubric + answer key
   - Construct grading prompt → call Groq API
   - Parse LLM JSON response → save to `grading_results`
3. Use FastAPI `BackgroundTasks` (เพียงพอสำหรับ <50 คน)
4. Update `student_submissions.status` progressively

### Rate Limiting
- Groq API rate limits → retry with exponential backoff
- Process submissions sequentially
- Log failures, allow re-grading

---

## Phase 5: Frontend Pages

| Route | Description |
|-------|------------|
| `/login` | Login page |
| `/dashboard` | Exam list + statistics |
| `/exams/create` | Create exam + add questions |
| `/exams/[id]` | Exam detail (tabs: Info, Documents, Answers, Grading) |
| `/exams/[id]/grading` | Trigger grading + progress monitor |
| `/exams/[id]/results` | Student results table |
| `/exams/[id]/results/[sid]` | **Review Panel** — side-by-side student answer vs LLM score |
| `/admin/users` | User management (admin only) |

### Key UI Components
- **PDF Viewer** — react-pdf preview
- **Grading Dashboard** — table with student, score, status, actions
- **Review Panel** — split layout (student answer LEFT | LLM reasoning + expert override RIGHT)
- **Progress Indicator** — polling/SSE grading status

---

## Phase 6: Expert Review & Export

### Review Endpoints
- `GET /api/v1/review/exams/{exam_id}/submissions` — list all with grading status
- `GET /api/v1/review/submissions/{id}` — full grading detail per student
- `PUT /api/v1/review/results/{id}/approve` — approve LLM score
- `PUT /api/v1/review/results/{id}/revise` — override score + feedback
- `POST /api/v1/review/exams/{exam_id}/approve-all` — bulk approve

### Export
- `GET /api/v1/review/exams/{exam_id}/export` — CSV/Excel with all scores

---

## Verification Checklist

- [ ] **Unit tests** — pytest for grading_service (mock Groq), pdf_service, auth_service
- [ ] **Integration test** — upload PDF → verify Qdrant chunks → trigger grading → verify DB results
- [ ] **Frontend E2E** — login → create exam → upload → grade → review → export
- [ ] **Thai language test** — upload Thai PDF → verify BGE-M3 + Groq handles Thai
- [ ] **API test** — httpx TestClient / Postman for all endpoints
- [ ] **Rate limit test** — 50 submissions → verify all complete without Groq 429 errors

---

## Key Decisions

| Decision | Rationale |
|----------|-----------|
| PDF แยกไฟล์ (เฉลย vs คำตอบ) | สะอาด, ง่ายต่อ pipeline |
| ข้อสอบแบบอัตนัย | LLM ให้เหตุผลประกอบคะแนน |
| RAG ดึง context ทั้งหมด | เฉลย + Rubric + เนื้อหาวิชา |
| 2 roles (Teacher + Admin) | ง่าย, เพียงพอ |
| Custom JWT (ไม่ใช้ Supabase Auth) | python-jose + bcrypt, ยืดหยุ่นกว่า |
| FastAPI BackgroundTasks | เพียงพอสำหรับ <50 คน, ไม่ต้อง Celery |
| BGE-M3 local | multilingual Thai support ดี, ไม่ต้อง API |
| Qdrant collection per exam | isolate vectors, ง่ายต่อ cleanup |

---

## Further Considerations

1. **Thai OCR** — ถ้า PDF เป็นสแกน ต้องเพิ่ม OCR (Tesseract Thai / EasyOCR)
2. **Student answer splitting** — อาจให้อาจารย์ระบุ format หรือใช้ LLM ช่วยแยกข้อ
3. **Groq model selection** — llama-3.3-70b-versatile รองรับ Thai ดีกว่า, อาจเพิ่ม option เลือก model

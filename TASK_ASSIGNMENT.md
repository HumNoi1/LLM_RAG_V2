# 📌 Task Assignment — 3 Developers, 4 Sprints (4 Weeks)

> Sprint Duration: 1 สัปดาห์/sprint | Timeline: 4 สัปดาห์ | Scale: <50 คน/ครั้ง

---

## Team Roles

| Code | Role | ความรับผิดชอบหลัก |
|------|------|------------------|
| **BE-S** | Backend Senior | RAG Pipeline, LLM Grading, Embedding — งาน AI/ML core ทั้งหมด |
| **BE-J** | Backend Junior | Auth, CRUD, Database, PDF parsing — งาน traditional backend |
| **FE** | Frontend Dev | Next.js UI ทุกหน้า, API integration |

**หลักการแบ่ง:**
- BE-S ทำงาน AI/ML ที่ซับซ้อนและ debug ยาก
- BE-J ทำงาน CRUD + Auth ที่มี pattern ชัดเจน
- BE-S review code ของ BE-J + pair programming 30 นาที/วัน

---

## Sprint 1 (Week 1): Foundation

> 🎯 เป้าหมาย: Setup ทุกอย่าง ให้ทุกคนทำงานแยกกันได้ตั้งแต่ Sprint 2

### BE-S (Senior Backend)

- [ ] สร้าง monorepo structure (`backend/`, `frontend/`, `docker-compose.yml`, `.gitignore`, `README.md`)
- [ ] `docker-compose.yml` — Qdrant container (port 6333)
- [ ] `backend/app/config.py` — Pydantic Settings (env vars ทั้งหมด)
- [ ] `backend/.env.example` — template env file
- [ ] `backend/app/main.py` — FastAPI app bootstrap, CORS, router includes
- [ ] PoC: LlamaIndex + BGE-M3 + Qdrant — ทดสอบ embed ข้อความไทย + query ได้จริง
- [ ] PoC: Groq API via LlamaIndex — ทดสอบ call LLM ตรวจข้อสอบ sample ได้จริง
- [ ] กำหนด API contract (request/response schemas) สำหรับทุก endpoint → แชร์ให้ FE

**✅ Deliverable**: Docker Qdrant ทำงานได้, PoC embedding + LLM grading ผ่าน, API contract doc พร้อม

### BE-J (Junior Backend)

- [ ] สร้าง Supabase project + tables ทั้งหมด (users, exams, exam_questions, rubrics, documents, students, student_submissions, grading_results)
- [ ] `backend/app/models/` — SQLAlchemy/Supabase models ทุก table
- [ ] `backend/app/schemas/` — Pydantic schemas ทุก model (request + response)
- [ ] `backend/app/core/security.py` — JWT create/verify (python-jose HS256), password hash (bcrypt)
- [ ] `backend/app/services/auth_service.py` — register, login, refresh logic
- [ ] `backend/app/api/v1/auth.py` — `POST /auth/login`, `/register`, `/refresh`
- [ ] Auth middleware — decode JWT, inject `current_user`, role guard decorator

**✅ Deliverable**: DB schema พร้อม, Auth API ทำงานได้ (login → JWT → protected route)

### FE (Frontend Dev)

- [ ] `npx create-next-app@latest` — App Router + TypeScript + Tailwind
- [ ] Setup shadcn/ui + ติดตั้ง components (Button, Input, Card, Table, Dialog, etc.)
- [ ] `frontend/src/lib/api.ts` — Axios instance + JWT interceptor (auto-attach token, auto-refresh 401)
- [ ] `frontend/src/lib/auth.ts` — Auth context/hook (login, logout, current user state)
- [ ] `frontend/src/types/` — TypeScript interfaces จาก API contract ที่ BE-S ให้
- [ ] Login page (`/login`)
- [ ] Dashboard layout + skeleton page (`/dashboard`)
- [ ] Protected route wrapper (redirect ถ้าไม่มี token)

**✅ Deliverable**: Login ทำงานได้กับ backend auth, Dashboard skeleton พร้อม, API client พร้อมใช้

### Sprint 1 — Dependencies & Sync Points

```
Day 1 เช้า : BE-S สร้าง repo structure ──→ Push ──→ BE-J + FE pull แล้วเริ่มงาน
Day 2      : BE-S แชร์ API contract doc ──→ FE ใช้สร้าง TypeScript types
Day 3-4    : BE-J Auth API เสร็จ ──→ FE integrate login
Day 5      : Sprint Review — ทุกคน demo deliverable
```

---

## Sprint 2 (Week 2): Core Features

> 🎯 เป้าหมาย: PDF Upload → Embed → Exam CRUD ครบ

### BE-S (Senior Backend)

- [ ] `backend/app/services/pdf_service.py` — pdfplumber PDF → text, handle Thai encoding
- [ ] `backend/app/services/embedding_service.py` — BGE-M3 embed + store to Qdrant, chunk with SentenceSplitter(512, 50), metadata tagging (exam_id, doc_type)
- [ ] `backend/app/api/v1/documents.py` — `POST /documents/upload` (upload reference PDF → parse → embed async via BackgroundTasks)
- [ ] `backend/app/services/rag_service.py` — LlamaIndex VectorStoreIndex + Groq QueryEngine, custom grading prompt template
- [ ] Unit tests: pdf_service (sample PDF), embedding_service (mock Qdrant)

**✅ Deliverable**: Upload PDF → parsed → embedded in Qdrant, RAG query returns relevant chunks

### BE-J (Junior Backend)

- [ ] `backend/app/api/v1/exams.py` — CRUD endpoints (create exam, list, get, update, delete)
- [ ] `backend/app/api/v1/exams.py` — exam_questions sub-endpoints (add/edit/delete questions, set max_score)
- [ ] `backend/app/api/v1/documents.py` — embedding status (GET /documents?exam_id=...), list documents per exam
- [ ] `POST /submissions/upload` — upload student answer PDF → parse text → save to student_submissions
- [ ] `GET /submissions?exam_id=...` — list student submissions per exam
- [ ] `backend/app/models/` — ตรวจสอบ + แก้ model relationships (foreign keys, cascade delete)
- [ ] Unit tests: exam CRUD, submission upload

**✅ Deliverable**: Exam CRUD ครบ, Student submission upload ทำงานได้

### FE (Frontend Dev)

- [ ] `/dashboard` — Exam list page (table with title, subject, status, actions)
- [ ] `/exams/create` — Create exam form (title, subject, description) + add questions (dynamic form)
- [ ] `/exams/[id]` — Exam detail page (tabs: Info, Documents, Student Answers, Grading)
- [ ] `/exams/[id]` — Documents tab: drag & drop upload for answer key, rubric, course material + status badges
- [ ] `/exams/[id]` — Student Answers tab: upload area for student PDFs + submission list table
- [ ] PDF preview component (react-pdf)

**✅ Deliverable**: สร้าง exam ได้, upload เอกสารได้, ดู submission list ได้

### Sprint 2 — Dependencies & Sync Points

```
Day 1-2 : BE-S pdf_service เสร็จ ──→ BE-J ใช้ใน submission upload
Day 2-3 : BE-J Exam CRUD เสร็จ ──→ FE integrate exam pages
Day 4   : BE-J Submission upload เสร็จ ──→ FE integrate upload UI
Day 5   : Sprint Review — demo upload + embed flow
```

---

## Sprint 3 (Week 3): Grading Engine + Review

> 🎯 เป้าหมาย: ตรวจข้อสอบ end-to-end + อาจารย์ review/approve ได้

### BE-S (Senior Backend)

- [ ] `backend/app/services/grading_service.py` — orchestrate: iterate submissions → split student text by question → RAG query per question → call Groq → parse JSON → save grading_results
- [ ] `backend/app/api/v1/grading.py` — `POST /grading/start` (trigger via BackgroundTasks), `GET /grading/status/{exam_id}` (progress)
- [ ] Rate limit handling — retry with exponential backoff for Groq 429
- [ ] Student answer splitting logic (heuristic: regex "ข้อ 1", "Question 1" + LLM fallback)
- [ ] Integration test: full pipeline (upload → embed → grade → verify results in DB)
- [ ] SSE endpoint หรือ polling endpoint for grading progress

**✅ Deliverable**: Trigger grading → ทุก submission ถูกตรวจ → results in DB พร้อม score + reasoning

### BE-J (Junior Backend)

- [ ] `backend/app/api/v1/review.py`:
  - [ ] `GET /review/exams/{exam_id}/submissions` — list all with grading summary
  - [ ] `GET /review/submissions/{id}` — full detail per student (all questions + scores + reasoning)
  - [ ] `PUT /review/results/{id}/approve` — approve LLM score
  - [ ] `PUT /review/results/{id}/revise` — override score + expert feedback
  - [ ] `POST /review/exams/{exam_id}/approve-all` — bulk approve
- [ ] `GET /review/exams/{exam_id}/export` — generate CSV export (student name, scores, total, status)
- [ ] Admin endpoints: `GET /admin/users`, `POST /admin/users`, `PUT /admin/users/{id}`
- [ ] Unit tests: review endpoints, export

**✅ Deliverable**: Review API ครบ, Export CSV ทำงานได้, Admin user management เสร็จ

### FE (Frontend Dev)

- [ ] `/exams/[id]/grading` — Trigger grading button + progress bar (poll status)
- [ ] `/exams/[id]/results` — Results table (student name, total score, status badge, actions)
- [ ] `/exams/[id]/results/[sid]` — **Review Panel**: split layout
  - [ ] ซ้าย: student answer per question
  - [ ] ขวา: LLM score + reasoning + expert override form
- [ ] Review Panel: Approve / Revise buttons per question + feedback textarea
- [ ] Bulk approve button on results page
- [ ] Export CSV button

**✅ Deliverable**: ตรวจข้อสอบได้, ดูผลได้, review/approve ได้, export ได้

### Sprint 3 — Dependencies & Sync Points

```
Day 3 : BE-S grading_service เสร็จ ──→ FE test grading flow
Day 3 : BE-J review endpoints เสร็จ ──→ FE integrate review panel
Day 4 : BE-S review code ของ BE-J
Day 5 : Sprint Review — demo full grading + review flow
```

---

## Sprint 4 (Week 4): Polish, Testing & Deploy

> 🎯 เป้าหมาย: Production-ready

### BE-S (Senior Backend)

- [ ] Code review ทุก PR ของ BE-J
- [ ] Performance tuning: embedding batch size, Qdrant query params
- [ ] Grading prompt optimization — ทดสอบกับข้อสอบจริง, tune prompt ให้ถูกต้อง
- [ ] Error handling: graceful failure for Groq timeout, PDF parse failures
- [ ] Integration tests: full E2E pipeline
- [ ] Dockerfile for backend
- [ ] `docker-compose.yml` update — backend + Qdrant production config
- [ ] API documentation (FastAPI auto-docs review + cleanup)

**✅ Deliverable**: Backend production-ready, E2E tests pass

### BE-J (Junior Backend)

- [ ] Fix bugs จาก QA/testing
- [ ] Input validation — file size limit, file type validation, sanitization
- [ ] Logging — structured logging for grading pipeline
- [ ] Unit test coverage เพิ่มเติม (edge cases: empty PDF, duplicate upload, concurrent grading)
- [ ] API rate limiting (optional: ป้องกัน abuse)
- [ ] README.md — setup instructions, API usage guide

**✅ Deliverable**: Bug fixes, input validation, logging, documentation

### FE (Frontend Dev)

- [ ] UI polish — loading states, error toasts, empty states, responsive layout
- [ ] `/admin/users` — User management page (admin only)
- [ ] Error handling — network errors, timeout, graceful degradation
- [ ] Dockerfile for frontend
- [ ] E2E manual testing: full flow (login → create → upload → grade → review → export)
- [ ] Mobile responsiveness (basic)

**✅ Deliverable**: Frontend production-ready, full flow ทำงานได้

---

## Task Summary by Person

### BE-S (Senior Backend) — Total: 27 tasks

| Sprint | จำนวน Tasks | หัวข้อหลัก |
|--------|-------------|-----------|
| Sprint 1 | 8 | Repo setup, Docker, PoC (BGE-M3 + Groq), API contract |
| Sprint 2 | 5 | PDF service, Embedding service, RAG pipeline, Document upload |
| Sprint 3 | 6 | Grading service, Rate limiting, Answer splitting, Integration test |
| Sprint 4 | 8 | Code review, Prompt tuning, Performance, Dockerfile, E2E test |

### BE-J (Junior Backend) — Total: 26 tasks

| Sprint | จำนวน Tasks | หัวข้อหลัก |
|--------|-------------|-----------|
| Sprint 1 | 7 | Supabase setup, Models, Schemas, JWT Auth, Middleware |
| Sprint 2 | 7 | Exam CRUD, Questions, Documents list, Submission upload |
| Sprint 3 | 8 | Review endpoints (5), Export CSV, Admin users, Tests |
| Sprint 4 | 6 | Bug fixes, Validation, Logging, Test coverage, README |

### FE (Frontend Dev) — Total: 24 tasks

| Sprint | จำนวน Tasks | หัวข้อหลัก |
|--------|-------------|-----------|
| Sprint 1 | 8 | Next.js setup, shadcn/ui, API client, Auth, Login, Dashboard |
| Sprint 2 | 6 | Dashboard, Create exam, Exam detail, Upload UI, PDF preview |
| Sprint 3 | 6 | Grading trigger, Results table, Review Panel, Bulk actions |
| Sprint 4 | 6 | UI polish, Admin page, Error handling, Dockerfile, E2E test |

---

## Git Workflow

### Branch Strategy

```
main (production)
 └── develop (integration)
      ├── feature/be-setup          ← BE-S Sprint 1
      ├── feature/be-auth           ← BE-J Sprint 1
      ├── feature/fe-auth           ← FE Sprint 1
      ├── feature/be-rag-pipeline   ← BE-S Sprint 2
      ├── feature/be-exam-crud      ← BE-J Sprint 2
      ├── feature/fe-exam-pages     ← FE Sprint 2
      ├── feature/be-grading        ← BE-S Sprint 3
      ├── feature/be-review         ← BE-J Sprint 3
      ├── feature/fe-review         ← FE Sprint 3
      └── feature/*-polish          ← All Sprint 4
```

### Rules

- [ ] PR → `develop` ต้อง review อย่างน้อย 1 คน
- [ ] BE-S review code ของ BE-J (ทุก PR)
- [ ] BE-J หรือ FE review code ของ BE-S
- [ ] ห้าม push ตรงเข้า `develop` / `main`
- [ ] PR title format: `[BE-S] Sprint 1: Setup monorepo structure`
- [ ] ใช้ conventional commits: `feat:`, `fix:`, `chore:`, `test:`

---

## Daily Standup (15 นาที)

ทุกวัน ถามกัน 3 ข้อ:
1. เมื่อวานทำอะไรเสร็จ?
2. วันนี้จะทำอะไร?
3. มีอะไร block?

---

## Sprint Ceremonies

| Ceremony | เมื่อไหร่ | ระยะเวลา | ใครเข้าร่วม |
|----------|----------|----------|------------|
| **Sprint Planning** | วันจันทร์เช้า | 30 นาที | ทุกคน |
| **Daily Standup** | ทุกวัน | 15 นาที | ทุกคน |
| **Sprint Review** | วันศุกร์ | 30 นาที | ทุกคน (demo ผลงาน) |
| **Pair Programming** | ทุกวัน | 30 นาที | BE-S + BE-J |

---

## Risk & Mitigation

| Risk | ผลกระทบ | การแก้ไข |
|------|---------|---------|
| BGE-M3 model ใหญ่ download ช้า | Block Sprint 1 BE-S | Pre-download model Day 1, cache ใน Docker volume |
| Groq rate limit | Grading ช้า/fail | Exponential backoff + sequential processing |
| PDF Thai text garbled | ตรวจข้อสอบไม่ได้ | Test pdfplumber + Thai PDF ตั้งแต่ Sprint 1 PoC |
| Student answer ไม่แยกข้อชัด | LLM ตรวจผิดข้อ | Heuristic split + LLM fallback + teacher ตรวจ format |
| BE-J ติดปัญหา | Delay Sprint 2-3 | BE-S pair programming 30 min/day + review ช่วยปลด block |
| FE รอ API | Block frontend dev | ใช้ mock API / API contract ทำ UI ก่อน |

---

## Definition of Done (DoD)

แต่ละ task ถือว่า "Done" เมื่อ:
- [ ] Code ทำงานได้ตาม requirement
- [ ] มี unit test (ถ้าเป็น service/API)
- [ ] PR ผ่าน review อย่างน้อย 1 คน
- [ ] Merge เข้า `develop` แล้ว
- [ ] ไม่มี lint errors / type errors

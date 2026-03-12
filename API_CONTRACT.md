# API Contract — LLM RAG Exam Grading

> Base URL: `http://localhost:8000/api/v1`
> Auth: Bearer JWT (ยกเว้น `/auth/login` และ `/auth/register`)
> Content-Type: `application/json` (ยกเว้น endpoint ที่ upload file ใช้ `multipart/form-data`)

---

## Enums

| Enum | Values |
|------|--------|
| `UserRole` | `teacher` · `admin` |
| `DocType` | `answer_key` · `rubric` · `course_material` |
| `EmbeddingStatus` | `pending` · `processing` · `completed` · `failed` |
| `GradingStatus` | `idle` · `running` · `completed` · `failed` |
| `GradingResultStatus` | `pending` · `approved` · `revised` |
| `SubmissionStatus` | `uploaded` · `parsed` · `grading` · `graded` · `reviewed` |

---

## Common Types

```ts
type UUID   = string   // "xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx"
type ISODate = string  // "2026-03-06T12:00:00Z"
```

---

## 1. Auth — `/auth`

### `POST /auth/register`
สร้างบัญชีใหม่ *(ไม่ต้องการ token)*

**Request Body**
```json
{
  "email": "teacher@example.com",
  "password": "min8chars",
  "full_name": "อาจารย์สมชาย",
  "role": "teacher"
}
```

**Response `201`**
```json
{
  "id": "uuid",
  "email": "teacher@example.com",
  "full_name": "อาจารย์สมชาย",
  "role": "teacher",
  "created_at": "ISODate"
}
```

---

### `POST /auth/login`
Login *(ไม่ต้องการ token)*

**Request Body**
```json
{
  "email": "teacher@example.com",
  "password": "mypassword"
}
```

**Response `200`**
```json
{
  "access_token": "eyJ...",
  "refresh_token": "eyJ...",
  "token_type": "bearer"
}
```

**Error `401`** — wrong email/password

---

### `POST /auth/refresh`
Refresh access token

**Request Body**
```json
{
  "refresh_token": "eyJ..."
}
```

**Response `200`** — same as login response (`TokenResponse`)

**Error `401`** — expired/invalid refresh token

---

## 2. Exams — `/exams`

### `POST /exams`
สร้าง exam ใหม่

**Request Body**
```json
{
  "title": "ข้อสอบปลายภาค วิชาชีววิทยา",
  "subject": "ชีววิทยา ม.5",
  "description": "บทที่ 1-5",
  "total_questions": 5
}
```

**Response `201`**
```json
{
  "id": "uuid",
  "title": "ข้อสอบปลายภาค วิชาชีววิทยา",
  "subject": "ชีววิทยา ม.5",
  "description": "บทที่ 1-5",
  "created_by": "uuid",
  "total_questions": 5,
  "created_at": "ISODate",
  "updated_at": "ISODate"
}
```

---

### `GET /exams`
ดู exam ทั้งหมดของ user

**Response `200`**
```json
{
  "exams": [ /* ExamResponse[] */ ],
  "total": 10
}
```

---

### `GET /exams/{exam_id}`
ดู exam พร้อมรายการข้อสอบ

**Response `200`**
```json
{
  "id": "uuid",
  "title": "...",
  "subject": "...",
  "description": "...",
  "created_by": "uuid",
  "total_questions": 3,
  "created_at": "ISODate",
  "updated_at": "ISODate",
  "questions": [
    {
      "id": "uuid",
      "exam_id": "uuid",
      "question_number": 1,
      "question_text": "อธิบายการสังเคราะห์แสง",
      "max_score": 10.0,
      "created_at": "ISODate"
    }
  ]
}
```

**Error `404`** — exam not found

---

### `PUT /exams/{exam_id}`
แก้ไข exam (fields ที่ส่งมาเท่านั้นที่อัปเดต)

**Request Body** *(all optional)*
```json
{
  "title": "ชื่อใหม่",
  "subject": "วิชาใหม่",
  "description": "คำอธิบายใหม่"
}
```

**Response `200`** — `ExamResponse`

---

### `DELETE /exams/{exam_id}`
ลบ exam (cascade ลบ questions, documents, submissions, grading results)

**Response `204`** — No Content

---

### `POST /exams/{exam_id}/questions`
เพิ่มข้อสอบใน exam

**Request Body**
```json
{
  "question_number": 1,
  "question_text": "อธิบายกระบวนการสังเคราะห์แสงและความสำคัญต่อระบบนิเวศ",
  "max_score": 10.0
}
```

**Response `201`** — `QuestionResponse`

---

### `PUT /exams/{exam_id}/questions/{question_id}`
แก้ไขข้อสอบ *(all optional)*

**Request Body**
```json
{
  "question_text": "คำถามใหม่",
  "max_score": 15.0
}
```

**Response `200`** — `QuestionResponse`

---

### `DELETE /exams/{exam_id}/questions/{question_id}`
ลบข้อสอบ

**Response `204`** — No Content

---

## 3. Documents — `/documents`

> ⚠️ ใช้ `multipart/form-data`

### `POST /documents/upload`
อัปโหลด reference PDF (เฉลย / rubric / เนื้อหาวิชา)
→ parse + embed ทำงาน async ใน background

**Form Fields**
| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `exam_id` | UUID | ✅ | |
| `doc_type` | `DocType` | ✅ | `answer_key` / `rubric` / `course_material` |
| `file` | File | ✅ | PDF เท่านั้น |

**Response `202`**
```json
{
  "message": "Document uploaded. Embedding in progress.",
  "document": {
    "id": "uuid",
    "exam_id": "uuid",
    "doc_type": "answer_key",
    "original_filename": "answer_key.pdf",
    "embedding_status": "pending",
    "chunk_count": null,
    "created_at": "ISODate"
  }
}
```

> Poll `GET /documents?exam_id=...` เพื่อดู `embedding_status`

---

### `GET /documents?exam_id={uuid}`
ดูรายการ documents ของ exam พร้อม embedding status

**Response `200`**
```json
{
  "documents": [
    {
      "id": "uuid",
      "exam_id": "uuid",
      "doc_type": "answer_key",
      "original_filename": "answer_key.pdf",
      "embedding_status": "completed",
      "chunk_count": 24,
      "created_at": "ISODate"
    }
  ],
  "total": 3
}
```

---

### `POST /documents/submissions/upload`
อัปโหลด PDF คำตอบนักเรียน → parse async

**Form Fields**
| Field | Type | Required |
|-------|------|----------|
| `exam_id` | UUID | ✅ |
| `student_id` | UUID | ✅ |
| `file` | File (PDF) | ✅ |

**Response `202`**
```json
{
  "message": "Submission uploaded. Parsing in progress.",
  "submission_id": "uuid"
}
```

---

### `GET /documents/submissions?exam_id={uuid}`
ดูรายการ submissions ของ exam

**Response `200`** — `SubmissionListResponse`

```json
{
  "submissions": [
    {
      "id": "uuid",
      "student_name": "สมชาย ใจดี",
      "student_code": "6412345",
      "status": "graded",
      "total_score": 27.5,
      "max_total_score": 30.0,
      "graded_questions": 3,
      "total_questions": 3
    }
  ],
  "total": 25
}
```

---

## 4. Grading — `/grading`

### `POST /grading/start`
เริ่มตรวจข้อสอบทุก submission ของ exam (ทำงาน background)

**Request Body**
```json
{
  "exam_id": "uuid"
}
```

**Response `202`**
```json
{
  "message": "Grading started for exam uuid",
  "exam_id": "uuid"
}
```

**Error `409`** — grading already in progress

> Poll `GET /grading/status/{exam_id}` เพื่อดู progress

---

### `GET /grading/status/{exam_id}`
ดู progress การตรวจ

**Response `200`**
```json
{
  "exam_id": "uuid",
  "status": "running",
  "total_submissions": 25,
  "completed": 12,
  "failed": 0,
  "progress_percent": 48.0
}
```

---

## 5. Review — `/review`

### `GET /review/exams/{exam_id}/submissions`
ดูรายการ submissions พร้อม grading summary ทั้งหมด

**Response `200`** — `SubmissionListResponse` (เหมือน documents/submissions)

---

### `GET /review/submissions/{submission_id}`
ดูผลตรวจรายละเอียดของนักเรียน 1 คน (สำหรับ Review Panel)

**Response `200`**
```json
{
  "id": "uuid",
  "exam_id": "uuid",
  "student_name": "สมชาย ใจดี",
  "student_code": "6412345",
  "status": "graded",
  "total_score": 27.5,
  "max_total_score": 30.0,
  "created_at": "ISODate",
  "grading_results": [
    {
      "id": "uuid",
      "submission_id": "uuid",
      "question_id": "uuid",
      "question_number": 1,
      "llm_score": 8.5,
      "expert_score": null,
      "max_score": 10.0,
      "reasoning": "นักเรียนอธิบายได้ครบถ้วน ระบุวัตถุดิบและผลผลิตได้ถูกต้อง แต่ขาดการอธิบายความสำคัญต่อระบบนิเวศ",
      "expert_feedback": null,
      "status": "pending",
      "created_at": "ISODate"
    }
  ]
}
```

---

### `PUT /review/results/{result_id}/approve`
Approve คะแนน LLM โดยไม่แก้ไข

**Request Body** — empty `{}`

**Response `200`** — `GradingResultResponse` with `status: "approved"`

---

### `PUT /review/results/{result_id}/revise`
แก้คะแนน + ใส่ feedback

**Request Body**
```json
{
  "expert_score": 9.0,
  "expert_feedback": "นักเรียนอธิบายได้ดีมาก ให้คะแนนเพิ่ม"
}
```

**Response `200`** — `GradingResultResponse` with `status: "revised"`, `expert_score: 9.0`

---

### `POST /review/exams/{exam_id}/approve-all`
Bulk approve ทุก result ที่ยัง `pending` ใน exam

**Request Body** — empty `{}`

**Response `200`**
```json
{
  "approved_count": 18,
  "message": "18 results approved successfully"
}
```

---

### `GET /review/exams/{exam_id}/export`
Export ผลตรวจเป็น CSV

**Response `200`**
```
Content-Type: text/csv
Content-Disposition: attachment; filename="exam_{id}_results.csv"
```

**CSV columns:**
```
student_code, student_name, q1_score, q1_max, q2_score, q2_max, ..., total_score, max_total, status
```

---

## Error Responses

Format เดียวกันทุก error:
```json
{
  "detail": "Error message here"
}
```

| Status | ความหมาย |
|--------|---------|
| `400` | Bad Request — validation failed |
| `401` | Unauthorized — missing/expired token |
| `403` | Forbidden — insufficient role |
| `404` | Not Found |
| `409` | Conflict — duplicate / already in progress |
| `422` | Unprocessable Entity — invalid file / PDF parse error |
| `502` | Bad Gateway — LLM API error |
| `503` | Service Unavailable — Qdrant / Supabase down |

---

## Authentication Flow (for FE)

```
1. POST /auth/login → { access_token, refresh_token }
2. เก็บ tokens (localStorage หรือ httpOnly cookie)
3. ทุก request: Header → Authorization: Bearer {access_token}
4. ถ้าได้ 401 → POST /auth/refresh → { access_token ใหม่ } → retry request
5. ถ้า refresh ก็ 401 → logout → redirect /login
```

---

## TypeScript Types (สำหรับ FE)

```ts
// Enums
type UserRole = "teacher" | "admin"
type DocType = "answer_key" | "rubric" | "course_material"
type EmbeddingStatus = "pending" | "processing" | "completed" | "failed"
type GradingStatus = "idle" | "running" | "completed" | "failed"
type GradingResultStatus = "pending" | "approved" | "revised"
type SubmissionStatus = "uploaded" | "parsed" | "grading" | "graded" | "reviewed"

// Auth
interface TokenResponse { access_token: string; refresh_token: string; token_type: string }
interface UserResponse { id: string; email: string; full_name: string; role: UserRole; created_at: string }

// Exams
interface QuestionResponse { id: string; exam_id: string; question_number: number; question_text: string; max_score: number; created_at: string }
interface ExamResponse { id: string; title: string; subject: string; description: string | null; created_by: string; total_questions: number; created_at: string; updated_at: string }
interface ExamDetailResponse extends ExamResponse { questions: QuestionResponse[] }
interface ExamListResponse { exams: ExamResponse[]; total: number }

// Documents
interface DocumentResponse { id: string; exam_id: string; doc_type: DocType; original_filename: string; embedding_status: EmbeddingStatus; chunk_count: number | null; created_at: string }
interface DocumentUploadResponse { message: string; document: DocumentResponse }
interface DocumentListResponse { documents: DocumentResponse[]; total: number }

// Grading
interface GradingProgressResponse { exam_id: string; status: GradingStatus; total_submissions: number; completed: number; failed: number; progress_percent: number }
interface GradingResultResponse { id: string; submission_id: string; question_id: string; question_number: number; llm_score: number; expert_score: number | null; max_score: number; reasoning: string; expert_feedback: string | null; status: GradingResultStatus; created_at: string }

// Review
interface SubmissionSummary { id: string; student_name: string; student_code: string; status: SubmissionStatus; total_score: number | null; max_total_score: number; graded_questions: number; total_questions: number }
interface SubmissionListResponse { submissions: SubmissionSummary[]; total: number }
interface SubmissionDetailResponse { id: string; exam_id: string; student_name: string; student_code: string; status: SubmissionStatus; grading_results: GradingResultResponse[]; total_score: number | null; max_total_score: number; created_at: string }
interface BulkApproveResponse { approved_count: number; message: string }
```

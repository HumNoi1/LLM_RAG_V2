-- ============================================================================
-- Supabase PostgreSQL schema for LLM RAG Exam Grading
-- Run this in Supabase SQL Editor to create all tables.
-- ============================================================================

-- ── Custom enum types ───────────────────────────────────────────────────────

CREATE TYPE user_role        AS ENUM ('teacher', 'admin');
CREATE TYPE doc_type         AS ENUM ('answer_key', 'rubric', 'course_material');
CREATE TYPE embedding_status AS ENUM ('pending', 'processing', 'completed', 'failed');
CREATE TYPE submission_status AS ENUM ('uploaded', 'parsed', 'grading', 'graded', 'reviewed');
CREATE TYPE grading_result_status AS ENUM ('pending_review', 'approved', 'revised');

-- ── users ───────────────────────────────────────────────────────────────────

CREATE TABLE IF NOT EXISTS users (
    id            UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email         VARCHAR(255) NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    full_name     VARCHAR(255) NOT NULL,
    role          user_role NOT NULL DEFAULT 'teacher',
    created_at    TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at    TIMESTAMPTZ
);

-- ── exams ───────────────────────────────────────────────────────────────────

CREATE TABLE IF NOT EXISTS exams (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    title           VARCHAR(255) NOT NULL,
    subject         VARCHAR(255) NOT NULL,
    description     TEXT,
    created_by      UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    total_questions INT NOT NULL DEFAULT 0,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at      TIMESTAMPTZ
);

-- ── exam_questions ──────────────────────────────────────────────────────────

CREATE TABLE IF NOT EXISTS exam_questions (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    exam_id         UUID NOT NULL REFERENCES exams(id) ON DELETE CASCADE,
    question_number INT NOT NULL,
    question_text   TEXT NOT NULL,
    max_score       DOUBLE PRECISION NOT NULL,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE (exam_id, question_number)
);

-- ── rubrics ─────────────────────────────────────────────────────────────────

CREATE TABLE IF NOT EXISTS rubrics (
    id             UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    question_id    UUID NOT NULL REFERENCES exam_questions(id) ON DELETE CASCADE,
    criteria_text  TEXT NOT NULL,
    score_range    VARCHAR(50),
    description    TEXT
);

-- ── documents ───────────────────────────────────────────────────────────────

CREATE TABLE IF NOT EXISTS documents (
    id                UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    exam_id           UUID NOT NULL REFERENCES exams(id) ON DELETE CASCADE,
    doc_type          doc_type NOT NULL,
    original_filename VARCHAR(255) NOT NULL,
    file_path         VARCHAR(1024) NOT NULL DEFAULT '',
    embedding_status  embedding_status NOT NULL DEFAULT 'pending',
    chunk_count       INT NOT NULL DEFAULT 0,
    created_at        TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- ── students ────────────────────────────────────────────────────────────────

CREATE TABLE IF NOT EXISTS students (
    id           UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    student_code VARCHAR(50) NOT NULL,
    full_name    VARCHAR(255) NOT NULL,
    created_by   UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    created_at   TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- ── student_submissions ─────────────────────────────────────────────────────

CREATE TABLE IF NOT EXISTS student_submissions (
    id                UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    exam_id           UUID NOT NULL REFERENCES exams(id) ON DELETE CASCADE,
    student_id        UUID NOT NULL REFERENCES students(id) ON DELETE CASCADE,
    original_filename VARCHAR(255) NOT NULL,
    file_path         VARCHAR(1024) NOT NULL DEFAULT '',
    parsed_text       TEXT,
    status            submission_status NOT NULL DEFAULT 'uploaded',
    created_at        TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- ── grading_results ─────────────────────────────────────────────────────────

CREATE TABLE IF NOT EXISTS grading_results (
    id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    submission_id       UUID NOT NULL REFERENCES student_submissions(id) ON DELETE CASCADE,
    question_id         UUID NOT NULL REFERENCES exam_questions(id) ON DELETE CASCADE,
    student_answer_text TEXT,
    llm_score           DOUBLE PRECISION NOT NULL DEFAULT 0,
    llm_max_score       DOUBLE PRECISION NOT NULL DEFAULT 0,
    llm_reasoning       TEXT,
    llm_model_used      VARCHAR(100),
    expert_score        DOUBLE PRECISION,
    expert_feedback     TEXT,
    status              grading_result_status NOT NULL DEFAULT 'pending_review',
    graded_at           TIMESTAMPTZ,
    reviewed_at         TIMESTAMPTZ,
    reviewed_by         UUID REFERENCES users(id),
    UNIQUE (submission_id, question_id)
);

-- ── Indexes ─────────────────────────────────────────────────────────────────

CREATE INDEX IF NOT EXISTS idx_exams_created_by ON exams(created_by);
CREATE INDEX IF NOT EXISTS idx_exam_questions_exam_id ON exam_questions(exam_id);
CREATE INDEX IF NOT EXISTS idx_documents_exam_id ON documents(exam_id);
CREATE INDEX IF NOT EXISTS idx_students_created_by ON students(created_by);
CREATE INDEX IF NOT EXISTS idx_submissions_exam_id ON student_submissions(exam_id);
CREATE INDEX IF NOT EXISTS idx_submissions_student_id ON student_submissions(student_id);
CREATE INDEX IF NOT EXISTS idx_grading_results_submission_id ON grading_results(submission_id);
CREATE INDEX IF NOT EXISTS idx_grading_results_question_id ON grading_results(question_id);
CREATE INDEX IF NOT EXISTS idx_grading_results_status ON grading_results(status);

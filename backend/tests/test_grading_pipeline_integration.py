"""
Integration-style tests for BE-S grading pipeline (mock external systems).
Sprint 4: เพิ่ม edge case tests — empty PDF, timeout, concurrent grading,
          partial failures, graceful recovery.
"""

from types import SimpleNamespace
from uuid import uuid4

import pytest

from app.api.v1 import documents as documents_api
from app.services import grading_service
from app.core.exceptions import LLMException, GroqTimeoutException


# ── Fake repos (shared between tests) ────────────────────────────────────────


class _FakeDocumentRepo:
    def __init__(self, records: dict[str, SimpleNamespace]):
        self._records = records

    async def update(self, where: dict, data: dict):
        rec = self._records[where["id"]]
        for key, value in data.items():
            setattr(rec, key, value)
        return rec

    async def find_unique(self, where: dict):
        return self._records.get(where["id"])


class _FakeExamQuestionRepo:
    def __init__(self, questions: list[SimpleNamespace]):
        self._questions = questions

    async def find_many(self, where: dict, order_by: dict | None = None):
        exam_id = where.get("examId")
        rows = [q for q in self._questions if q.examId == exam_id]
        if order_by and order_by.get("questionNumber") == "asc":
            rows.sort(key=lambda x: x.questionNumber)
        return rows


class _FakeSubmissionRepo:
    def __init__(self, submissions: list[SimpleNamespace]):
        self._submissions = submissions

    async def find_many(self, where: dict):
        exam_id = where.get("examId")
        status = where.get("status")
        rows = [s for s in self._submissions if s.examId == exam_id]
        if status is not None:
            rows = [s for s in rows if s.status == status]
        return rows

    async def update(self, where: dict, data: dict):
        submission = next(s for s in self._submissions if s.id == where["id"])
        for key, value in data.items():
            setattr(submission, key, value)
        return submission


class _FakeStudentRepo:
    def __init__(self, students: dict[str, SimpleNamespace]):
        self._students = students

    async def find_unique(self, where: dict):
        return self._students.get(where["id"])


class _FakeGradingResultRepo:
    def __init__(self):
        self.rows: list[SimpleNamespace] = []

    async def create(self, data: dict):
        row = SimpleNamespace(**data)
        self.rows.append(row)
        return row


class _FakeDb:
    def __init__(self, *, docs, questions, submissions, students):
        self.document = _FakeDocumentRepo(docs)
        self.examquestion = _FakeExamQuestionRepo(questions)
        self.studentsubmission = _FakeSubmissionRepo(submissions)
        self.student = _FakeStudentRepo(students)
        self.gradingresult = _FakeGradingResultRepo()


def _make_fake_settings(**overrides):
    """สร้าง fake settings object สำหรับ test"""
    defaults = {
        "llm_model": "llama-3.3-70b-versatile",
        "llm_request_timeout": 60,
        "llm_max_retries": 3,
        "llm_retry_base_delay": 0,
    }
    defaults.update(overrides)
    return SimpleNamespace(**defaults)


# ── Test 1: Happy path — embed then grade ────────────────────────────────────


@pytest.mark.asyncio
async def test_pipeline_embed_then_grade_with_mocks(monkeypatch):
    """E2E: อัพโหลด PDF → embed → grade → ตรวจผลลัพธ์"""
    exam_id = uuid4()
    doc_id = str(uuid4())
    student_id = str(uuid4())

    fake_docs = {
        doc_id: SimpleNamespace(
            id=doc_id,
            examId=str(exam_id),
            docType="answer_key",
            embeddingStatus="pending",
            chunkCount=0,
        )
    }

    fake_questions = [
        SimpleNamespace(
            id=str(uuid4()),
            examId=str(exam_id),
            questionNumber=1,
            questionText="อธิบายการสังเคราะห์แสง",
            maxScore=10.0,
        ),
        SimpleNamespace(
            id=str(uuid4()),
            examId=str(exam_id),
            questionNumber=2,
            questionText="บอกวัตถุดิบสำคัญ",
            maxScore=5.0,
        ),
    ]

    fake_submissions = [
        SimpleNamespace(
            id=str(uuid4()),
            examId=str(exam_id),
            studentId=student_id,
            parsedText="ข้อ 1 พืชใช้พลังงานแสง\n\nข้อ 2 ใช้ CO2 น้ำ",
            status="parsed",
        )
    ]

    fake_students = {
        student_id: SimpleNamespace(id=student_id, fullName="Student One"),
    }

    fake_db = _FakeDb(
        docs=fake_docs,
        questions=fake_questions,
        submissions=fake_submissions,
        students=fake_students,
    )

    monkeypatch.setattr(documents_api, "db", fake_db)
    monkeypatch.setattr(grading_service, "db", fake_db)

    def _fake_parse_pdf_bytes(data: bytes, filename: str) -> str:
        return f"parsed::{filename}::{len(data)}"

    async def _fake_embed_document(exam_id, doc_id, doc_type, text):
        assert doc_type == "answer_key"
        assert text.startswith("parsed::")
        return 7

    async def _fake_query_for_grading(
        exam_id, question_text, student_answer, max_score
    ):
        return {
            "score": max_score - 1.0,
            "reasoning": f"graded::{question_text[:10]}",
            "covered_points": ["p1"],
            "missed_points": ["p2"],
        }

    monkeypatch.setattr(documents_api, "parse_pdf_bytes", _fake_parse_pdf_bytes)
    monkeypatch.setattr(documents_api, "embed_document", _fake_embed_document)
    monkeypatch.setattr(grading_service, "query_for_grading", _fake_query_for_grading)
    monkeypatch.setattr(
        grading_service,
        "get_settings",
        lambda: _make_fake_settings(),
    )

    await documents_api._process_and_embed_document(
        doc_id=doc_id,
        exam_id=str(exam_id),
        file_data=b"pdf-bytes",
        filename="answer_key.pdf",
    )

    assert fake_docs[doc_id].embeddingStatus == "completed"
    assert fake_docs[doc_id].chunkCount == 7

    await grading_service.start_grading(exam_id)

    assert fake_submissions[0].status == "graded"
    assert len(fake_db.gradingresult.rows) == 2
    assert all(r.status == "pending_review" for r in fake_db.gradingresult.rows)

    progress = await grading_service.get_grading_status(exam_id)
    assert progress["status"] == "completed"
    assert progress["total_submissions"] == 1
    assert progress["completed"] == 1
    assert progress["progress_percent"] == 100.0


# ── Test 2: Empty PDF text — graceful handling ───────────────────────────────


@pytest.mark.asyncio
async def test_grade_empty_parsed_text(monkeypatch):
    """Sprint 4: Submission ที่มี parsed_text เป็น empty string ควร grade สำเร็จ
    โดยให้คะแนน 0 สำหรับทุกข้อ"""
    exam_id = uuid4()
    student_id = str(uuid4())

    fake_questions = [
        SimpleNamespace(
            id=str(uuid4()),
            examId=str(exam_id),
            questionNumber=1,
            questionText="อธิบายทฤษฎี",
            maxScore=10.0,
        ),
    ]

    fake_submissions = [
        SimpleNamespace(
            id=str(uuid4()),
            examId=str(exam_id),
            studentId=student_id,
            parsedText="",  # Empty!
            status="parsed",
        )
    ]

    fake_students = {
        student_id: SimpleNamespace(id=student_id, fullName="Empty Student"),
    }

    fake_db = _FakeDb(
        docs={},
        questions=fake_questions,
        submissions=fake_submissions,
        students=fake_students,
    )

    monkeypatch.setattr(grading_service, "db", fake_db)
    monkeypatch.setattr(
        grading_service,
        "get_settings",
        lambda: _make_fake_settings(),
    )

    await grading_service.start_grading(exam_id)

    # Should complete without error
    progress = await grading_service.get_grading_status(exam_id)
    assert progress["status"] == "completed"
    assert progress["completed"] == 1
    assert fake_submissions[0].status == "graded"


# ── Test 3: No questions — graceful failure ──────────────────────────────────


@pytest.mark.asyncio
async def test_grade_no_questions(monkeypatch):
    """Sprint 4: Exam ที่ไม่มี questions ควร fail gracefully"""
    exam_id = uuid4()

    fake_db = _FakeDb(
        docs={},
        questions=[],  # ไม่มี questions!
        submissions=[],
        students={},
    )

    monkeypatch.setattr(grading_service, "db", fake_db)
    monkeypatch.setattr(
        grading_service,
        "get_settings",
        lambda: _make_fake_settings(),
    )

    await grading_service.start_grading(exam_id)

    progress = await grading_service.get_grading_status(exam_id)
    assert progress["status"] == "failed"


# ── Test 4: LLM timeout on one question — partial success ───────────────────


@pytest.mark.asyncio
async def test_grade_partial_failure_on_timeout(monkeypatch):
    """Sprint 4: ถ้า LLM timeout ที่ข้อหนึ่ง ข้อที่เหลือควร grade ต่อได้"""
    exam_id = uuid4()
    student_id = str(uuid4())
    call_count = {"n": 0}

    fake_questions = [
        SimpleNamespace(
            id=str(uuid4()),
            examId=str(exam_id),
            questionNumber=1,
            questionText="ข้อที่ 1",
            maxScore=10.0,
        ),
        SimpleNamespace(
            id=str(uuid4()),
            examId=str(exam_id),
            questionNumber=2,
            questionText="ข้อที่ 2",
            maxScore=5.0,
        ),
    ]

    fake_submissions = [
        SimpleNamespace(
            id=str(uuid4()),
            examId=str(exam_id),
            studentId=student_id,
            parsedText="ข้อ 1 คำตอบข้อหนึ่ง\n\nข้อ 2 คำตอบข้อสอง",
            status="parsed",
        )
    ]

    fake_students = {
        student_id: SimpleNamespace(id=student_id, fullName="Partial Student"),
    }

    fake_db = _FakeDb(
        docs={},
        questions=fake_questions,
        submissions=fake_submissions,
        students=fake_students,
    )

    async def _timeout_on_first_question(
        exam_id, question_text, student_answer, max_score
    ):
        call_count["n"] += 1
        if call_count["n"] == 1:
            raise GroqTimeoutException(60)
        return {
            "score": 4.0,
            "reasoning": "graded OK",
            "covered_points": ["p1"],
            "missed_points": [],
        }

    monkeypatch.setattr(grading_service, "db", fake_db)
    monkeypatch.setattr(
        grading_service, "query_for_grading", _timeout_on_first_question
    )
    monkeypatch.setattr(
        grading_service,
        "get_settings",
        lambda: _make_fake_settings(),
    )

    await grading_service.start_grading(exam_id)

    # Submission ควร graded สำเร็จ แม้ข้อ 1 จะ timeout
    assert fake_submissions[0].status == "graded"

    # ควรมี grading result 2 ข้อ (ข้อ 1 timeout → score 0, ข้อ 2 สำเร็จ)
    assert len(fake_db.gradingresult.rows) == 2
    assert fake_db.gradingresult.rows[0].llmScore == 0.0  # timeout → score 0
    assert fake_db.gradingresult.rows[1].llmScore == 4.0

    progress = await grading_service.get_grading_status(exam_id)
    assert progress["status"] == "completed"
    assert progress["failed"] == 1  # 1 question-level failure


# ── Test 5: No submissions to grade ──────────────────────────────────────────


@pytest.mark.asyncio
async def test_grade_no_submissions(monkeypatch):
    """Sprint 4: ไม่มี submission ที่ต้อง grade → completed ทันที"""
    exam_id = uuid4()

    fake_questions = [
        SimpleNamespace(
            id=str(uuid4()),
            examId=str(exam_id),
            questionNumber=1,
            questionText="question",
            maxScore=10.0,
        ),
    ]

    fake_db = _FakeDb(
        docs={},
        questions=fake_questions,
        submissions=[],  # ไม่มี submissions!
        students={},
    )

    monkeypatch.setattr(grading_service, "db", fake_db)
    monkeypatch.setattr(
        grading_service,
        "get_settings",
        lambda: _make_fake_settings(),
    )

    await grading_service.start_grading(exam_id)

    progress = await grading_service.get_grading_status(exam_id)
    assert progress["status"] == "completed"
    assert progress["total_submissions"] == 0


# ── Test 6: Multiple submissions ─────────────────────────────────────────────


@pytest.mark.asyncio
async def test_grade_multiple_submissions(monkeypatch):
    """Sprint 4: Grade หลาย submissions พร้อมกัน"""
    exam_id = uuid4()
    student1 = str(uuid4())
    student2 = str(uuid4())

    fake_questions = [
        SimpleNamespace(
            id=str(uuid4()),
            examId=str(exam_id),
            questionNumber=1,
            questionText="คำถาม",
            maxScore=10.0,
        ),
    ]

    fake_submissions = [
        SimpleNamespace(
            id=str(uuid4()),
            examId=str(exam_id),
            studentId=student1,
            parsedText="คำตอบของนักเรียนคนที่ 1",
            status="parsed",
        ),
        SimpleNamespace(
            id=str(uuid4()),
            examId=str(exam_id),
            studentId=student2,
            parsedText="คำตอบของนักเรียนคนที่ 2",
            status="parsed",
        ),
    ]

    fake_students = {
        student1: SimpleNamespace(id=student1, fullName="Student 1"),
        student2: SimpleNamespace(id=student2, fullName="Student 2"),
    }

    fake_db = _FakeDb(
        docs={},
        questions=fake_questions,
        submissions=fake_submissions,
        students=fake_students,
    )

    async def _fake_query(exam_id, question_text, student_answer, max_score):
        return {
            "score": 7.5,
            "reasoning": "ดี",
            "covered_points": [],
            "missed_points": [],
        }

    monkeypatch.setattr(grading_service, "db", fake_db)
    monkeypatch.setattr(grading_service, "query_for_grading", _fake_query)
    monkeypatch.setattr(
        grading_service,
        "get_settings",
        lambda: _make_fake_settings(),
    )

    await grading_service.start_grading(exam_id)

    assert all(s.status == "graded" for s in fake_submissions)
    assert len(fake_db.gradingresult.rows) == 2

    progress = await grading_service.get_grading_status(exam_id)
    assert progress["status"] == "completed"
    assert progress["total_submissions"] == 2
    assert progress["completed"] == 2
    assert progress["progress_percent"] == 100.0


# ── Test 7: PDF embedding failure ────────────────────────────────────────────


@pytest.mark.asyncio
async def test_embed_failure_marks_document_failed(monkeypatch):
    """Sprint 4: ถ้า embedding fail ควร update document status เป็น 'failed'"""
    from app.core.exceptions import EmbeddingException

    doc_id = str(uuid4())
    exam_id = uuid4()

    fake_docs = {
        doc_id: SimpleNamespace(
            id=doc_id,
            examId=str(exam_id),
            docType="rubric",
            embeddingStatus="pending",
            chunkCount=0,
        )
    }

    fake_db = _FakeDb(
        docs=fake_docs,
        questions=[],
        submissions=[],
        students={},
    )

    monkeypatch.setattr(documents_api, "db", fake_db)

    def _fake_parse(data, filename):
        return "parsed text"

    async def _fake_embed_fail(exam_id, doc_id, doc_type, text):
        raise EmbeddingException("Qdrant connection refused")

    monkeypatch.setattr(documents_api, "parse_pdf_bytes", _fake_parse)
    monkeypatch.setattr(documents_api, "embed_document", _fake_embed_fail)

    await documents_api._process_and_embed_document(
        doc_id=doc_id,
        exam_id=str(exam_id),
        file_data=b"pdf-data",
        filename="rubric.pdf",
    )

    assert fake_docs[doc_id].embeddingStatus == "failed"


# ── Test 8: PDF parse failure ────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_pdf_parse_failure_marks_document_failed(monkeypatch):
    """Sprint 4: ถ้า PDF parse fail ควร update document status เป็น 'failed'"""
    from app.core.exceptions import PDFParseException

    doc_id = str(uuid4())
    exam_id = uuid4()

    fake_docs = {
        doc_id: SimpleNamespace(
            id=doc_id,
            examId=str(exam_id),
            docType="answer_key",
            embeddingStatus="pending",
            chunkCount=0,
        )
    }

    fake_db = _FakeDb(
        docs=fake_docs,
        questions=[],
        submissions=[],
        students={},
    )

    monkeypatch.setattr(documents_api, "db", fake_db)

    def _fake_parse_fail(data, filename):
        raise PDFParseException(filename, "Corrupted file")

    monkeypatch.setattr(documents_api, "parse_pdf_bytes", _fake_parse_fail)

    await documents_api._process_and_embed_document(
        doc_id=doc_id,
        exam_id=str(exam_id),
        file_data=b"corrupted-data",
        filename="bad.pdf",
    )

    assert fake_docs[doc_id].embeddingStatus == "failed"


# ── Test 9: split_answer_by_question edge cases ─────────────────────────────


class TestSplitAnswerByQuestion:
    """Sprint 4: ทดสอบ answer splitting edge cases"""

    def test_empty_text(self):
        result = grading_service.split_answer_by_question("", 3)
        assert result == {}

    def test_zero_questions(self):
        result = grading_service.split_answer_by_question("some text", 0)
        assert result == {}

    def test_single_question_fallback(self):
        """ถ้าแยกไม่ได้ ควรส่งข้อความทั้งหมดเป็นข้อ 1"""
        result = grading_service.split_answer_by_question("just one answer", 1)
        assert 1 in result
        assert "just one answer" in result[1]

    def test_thai_question_markers(self):
        text = "ข้อ 1 คำตอบข้อหนึ่ง\n\nข้อ 2 คำตอบข้อสอง\n\nข้อ 3 คำตอบข้อสาม"
        result = grading_service.split_answer_by_question(text, 3)
        assert len(result) >= 3
        assert 1 in result
        assert 2 in result
        assert 3 in result

    def test_english_question_markers(self):
        text = "Question 1 Answer one\n\nQuestion 2 Answer two"
        result = grading_service.split_answer_by_question(text, 2)
        assert len(result) >= 2


# ── Test 10: Concurrent grading start (409) ──────────────────────────────────


@pytest.mark.asyncio
async def test_concurrent_grading_start_returns_conflict(monkeypatch):
    """P0: เรียก start_grading ซ้ำขณะที่ grading กำลัง run อยู่ ต้องถูกป้องกัน"""
    exam_id = uuid4()

    # Simulate a running grading job
    grading_service.reset_grading_progress(exam_id)
    assert grading_service.is_grading_running(exam_id) is True

    # Verify the guard detects it
    assert grading_service.is_grading_running(exam_id) is True

    # After completion, guard should allow new start
    progress = grading_service.get_grading_progress(exam_id)
    progress.status = "completed"
    assert grading_service.is_grading_running(exam_id) is False

    # Clean up
    grading_service._grading_progress.pop(exam_id, None)


# ── Test 11: LLM failure produces score=0 result for every failed question ──


@pytest.mark.asyncio
async def test_all_questions_have_results_even_on_failure(monkeypatch):
    """P0: ทุก question ต้องมี grading result แม้ LLM error — score=0 พร้อมเหตุผล"""
    exam_id = uuid4()
    student_id = str(uuid4())

    fake_questions = [
        SimpleNamespace(
            id=str(uuid4()),
            examId=str(exam_id),
            questionNumber=1,
            questionText="ข้อที่ 1",
            maxScore=10.0,
        ),
        SimpleNamespace(
            id=str(uuid4()),
            examId=str(exam_id),
            questionNumber=2,
            questionText="ข้อที่ 2",
            maxScore=5.0,
        ),
        SimpleNamespace(
            id=str(uuid4()),
            examId=str(exam_id),
            questionNumber=3,
            questionText="ข้อที่ 3",
            maxScore=8.0,
        ),
    ]

    fake_submissions = [
        SimpleNamespace(
            id=str(uuid4()),
            examId=str(exam_id),
            studentId=student_id,
            parsedText="ข้อ 1 คำตอบ A\n\nข้อ 2 คำตอบ B\n\nข้อ 3 คำตอบ C",
            status="parsed",
        )
    ]

    fake_students = {
        student_id: SimpleNamespace(id=student_id, fullName="Test Student"),
    }

    fake_db = _FakeDb(
        docs={},
        questions=fake_questions,
        submissions=fake_submissions,
        students=fake_students,
    )

    call_count = {"n": 0}

    async def _fail_all(exam_id, question_text, student_answer, max_score):
        call_count["n"] += 1
        if call_count["n"] == 1:
            raise GroqTimeoutException(60)
        elif call_count["n"] == 2:
            raise LLMException("model overloaded")
        else:
            # Q3 succeeds
            return {
                "score": 7.0,
                "reasoning": "ดีมาก",
                "covered_points": ["p1"],
                "missed_points": [],
            }

    monkeypatch.setattr(grading_service, "db", fake_db)
    monkeypatch.setattr(grading_service, "query_for_grading", _fail_all)
    monkeypatch.setattr(
        grading_service,
        "get_settings",
        lambda: _make_fake_settings(),
    )

    await grading_service.start_grading(exam_id)

    # All 3 questions must have a grading result
    assert len(fake_db.gradingresult.rows) == 3

    # Q1: timeout → score 0
    q1_result = fake_db.gradingresult.rows[0]
    assert q1_result.llmScore == 0.0
    assert "ขัดข้อง" in q1_result.llmReasoning

    # Q2: LLM error → score 0
    q2_result = fake_db.gradingresult.rows[1]
    assert q2_result.llmScore == 0.0
    assert "ขัดข้อง" in q2_result.llmReasoning

    # Q3: success → score 7.0
    q3_result = fake_db.gradingresult.rows[2]
    assert q3_result.llmScore == 7.0

    # Submission should be graded (at least 1 question succeeded)
    assert fake_submissions[0].status == "graded"

    progress = await grading_service.get_grading_status(exam_id)
    assert progress["status"] == "completed"
    assert progress["failed"] == 2  # 2 question-level failures


# ── Test 12: Paragraph-based fallback split ──────────────────────────────────


class TestParagraphFallbackSplit:
    """P1: fallback split ต้องแบ่งตาม paragraph ไม่ใช่ตัดด้วยความยาวตัวอักษร"""

    def test_paragraphs_distributed_evenly(self):
        text = "Para A content\n\nPara B content\n\nPara C content\n\nPara D content"
        result = grading_service.split_answer_by_question(text, 2)
        assert len(result) == 2
        # Should not cut in the middle of a word
        assert "Para A" in result[1]
        assert "Para D" in result[2]

    def test_single_paragraph_for_multiple_questions(self):
        """ถ้า paragraph น้อยกว่า question → ส่งทั้งหมดเป็น Q1"""
        text = "Only one paragraph with all content"
        result = grading_service.split_answer_by_question(text, 3)
        assert 1 in result
        assert result[1] == text

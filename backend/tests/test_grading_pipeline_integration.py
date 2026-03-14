"""Integration-style test for BE-S grading pipeline (mock external systems)."""

from types import SimpleNamespace
from uuid import uuid4

import pytest

from app.api.v1 import documents as documents_api
from app.services import grading_service


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


@pytest.mark.asyncio
async def test_pipeline_embed_then_grade_with_mocks(monkeypatch):
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
        lambda: SimpleNamespace(llm_model="llama-3.3-70b-versatile"),
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

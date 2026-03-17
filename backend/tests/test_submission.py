"""
Tests for submission endpoints (app.api.v1.documents)

Covers:
  POST /api/v1/documents/submissions/upload
    - 202 on valid PDF + existing exam + existing student
    - 404 when exam not found
    - 404 when student not found
    - 422 when empty file
    - 422 when non-PDF content type

  GET  /api/v1/documents/submissions?exam_id=...
    - 200 with submission list
    - 404 when exam not found
"""

import io
import pytest
from unittest.mock import MagicMock
from fpdf import FPDF

from tests.conftest import FAKE_USER_ID

EXAM_ID = "cccccccc-cccc-cccc-cccc-cccccccccccc"
STUDENT_ID = "dddddddd-dddd-dddd-dddd-dddddddddddd"
SUBMISSION_ID = "eeeeeeee-eeee-eeee-eeee-eeeeeeeeeeee"
NOW = "2026-03-01T00:00:00+00:00"


def _make_pdf_bytes() -> bytes:
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Helvetica", size=12)
    pdf.cell(200, 10, txt="Student answer text here", ln=True)
    return bytes(pdf.output())


def _exam_row():
    return {"id": EXAM_ID, "total_questions": 2}


def _student_row():
    return {"id": STUDENT_ID}


def _submission_row():
    return {
        "id": SUBMISSION_ID,
        "student_id": STUDENT_ID,
        "original_filename": "answer.pdf",
        "status": "uploaded",
        "created_at": NOW,
        "students": {"full_name": "Alice", "student_code": "STD001"},
    }


# ── POST /api/v1/documents/submissions/upload ─────────────────────────────────


class TestUploadSubmission:
    def test_upload_valid_pdf_returns_202(self, client, mock_supabase):
        _, query = mock_supabase
        call_count = {"n": 0}

        def side_effect():
            call_count["n"] += 1
            resp = MagicMock()
            if call_count["n"] == 1:
                # exam exists
                resp.data = _exam_row()
            elif call_count["n"] == 2:
                # student exists
                resp.data = _student_row()
            else:
                # insert submission
                resp.data = [{"id": SUBMISSION_ID}]
            return resp

        query.execute.side_effect = side_effect

        pdf_data = _make_pdf_bytes()

        resp = client.post(
            "/api/v1/documents/submissions/upload",
            data={"exam_id": EXAM_ID, "student_id": STUDENT_ID},
            files={"file": ("answer.pdf", io.BytesIO(pdf_data), "application/pdf")},
        )
        assert resp.status_code == 202
        body = resp.json()
        assert "submission_id" in body

    def test_upload_exam_not_found_returns_404(self, client, mock_supabase):
        _, query = mock_supabase
        query.execute.return_value.data = None  # exam not found

        pdf_data = _make_pdf_bytes()
        resp = client.post(
            "/api/v1/documents/submissions/upload",
            data={"exam_id": EXAM_ID, "student_id": STUDENT_ID},
            files={"file": ("answer.pdf", io.BytesIO(pdf_data), "application/pdf")},
        )
        assert resp.status_code == 404

    def test_upload_student_not_found_returns_404(self, client, mock_supabase):
        _, query = mock_supabase
        call_count = {"n": 0}

        def side_effect():
            call_count["n"] += 1
            resp = MagicMock()
            resp.data = _exam_row() if call_count["n"] == 1 else None
            return resp

        query.execute.side_effect = side_effect

        pdf_data = _make_pdf_bytes()
        resp = client.post(
            "/api/v1/documents/submissions/upload",
            data={"exam_id": EXAM_ID, "student_id": STUDENT_ID},
            files={"file": ("answer.pdf", io.BytesIO(pdf_data), "application/pdf")},
        )
        assert resp.status_code == 404

    def test_upload_empty_file_returns_422(self, client, mock_supabase):
        _, query = mock_supabase
        call_count = {"n": 0}

        def side_effect():
            call_count["n"] += 1
            resp = MagicMock()
            if call_count["n"] == 1:
                resp.data = _exam_row()
            else:
                resp.data = _student_row()
            return resp

        query.execute.side_effect = side_effect

        resp = client.post(
            "/api/v1/documents/submissions/upload",
            data={"exam_id": EXAM_ID, "student_id": STUDENT_ID},
            files={"file": ("answer.pdf", io.BytesIO(b""), "application/pdf")},
        )
        assert resp.status_code == 422

    def test_upload_non_pdf_returns_422(self, client, mock_supabase):
        resp = client.post(
            "/api/v1/documents/submissions/upload",
            data={"exam_id": EXAM_ID, "student_id": STUDENT_ID},
            files={"file": ("answer.txt", io.BytesIO(b"not a pdf"), "text/plain")},
        )
        assert resp.status_code == 422


# ── GET /api/v1/documents/submissions ────────────────────────────────────────


class TestListSubmissions:
    def test_list_returns_200_with_submissions(self, client, mock_supabase):
        _, query = mock_supabase
        call_count = {"n": 0}

        def side_effect():
            call_count["n"] += 1
            resp = MagicMock()
            if call_count["n"] == 1:
                # exam exists
                resp.data = _exam_row()
            elif call_count["n"] == 2:
                # submissions list
                resp.data = [_submission_row()]
            else:
                # grading results for submission
                resp.data = []
            return resp

        query.execute.side_effect = side_effect

        resp = client.get(f"/api/v1/documents/submissions?exam_id={EXAM_ID}")
        assert resp.status_code == 200
        body = resp.json()
        assert body["total"] == 1
        assert body["submissions"][0]["student_name"] == "Alice"

    def test_list_exam_not_found_returns_404(self, client, mock_supabase):
        _, query = mock_supabase
        query.execute.return_value.data = None

        resp = client.get(f"/api/v1/documents/submissions?exam_id={EXAM_ID}")
        assert resp.status_code == 404

    def test_list_empty_submissions(self, client, mock_supabase):
        _, query = mock_supabase
        call_count = {"n": 0}

        def side_effect():
            call_count["n"] += 1
            resp = MagicMock()
            if call_count["n"] == 1:
                resp.data = _exam_row()
            else:
                resp.data = []
            return resp

        query.execute.side_effect = side_effect

        resp = client.get(f"/api/v1/documents/submissions?exam_id={EXAM_ID}")
        assert resp.status_code == 200
        assert resp.json()["total"] == 0

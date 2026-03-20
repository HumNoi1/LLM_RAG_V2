"""
Tests for CSV export endpoint (app.api.v1.review — export_results_csv)

Covers:
  GET /api/v1/review/exams/{exam_id}/export  — CSV download
"""

import csv
import io
import pytest
from unittest.mock import MagicMock
from tests.conftest import FAKE_USER_ID

EXAM_ID = "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa"
SUB_ID = "cccccccc-cccc-cccc-cccc-cccccccccccc"
Q_ID_1 = "bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb"
Q_ID_2 = "eeeeeeee-eeee-eeee-eeee-eeeeeeeeeeee"
NOW = "2026-03-01T00:00:00+00:00"


def _exam_row():
    return {
        "id": EXAM_ID,
        "title": "Final Exam",
        "total_questions": 2,
        "created_by": FAKE_USER_ID,
    }


def _questions():
    return [
        {"id": Q_ID_1, "question_number": 1, "max_score": 5.0},
        {"id": Q_ID_2, "question_number": 2, "max_score": 10.0},
    ]


def _submission_row():
    return {
        "id": SUB_ID,
        "status": "graded",
        "students": {"full_name": "Student A", "student_code": "S001"},
    }


def _grading_results():
    return [
        {
            "question_id": Q_ID_1,
            "llm_score": 4.0,
            "expert_score": None,
            "llm_max_score": 5.0,
            "status": "approved",
        },
        {
            "question_id": Q_ID_2,
            "llm_score": 8.0,
            "expert_score": 7.5,
            "llm_max_score": 10.0,
            "status": "revised",
        },
    ]


class TestExportCSV:
    def test_export_returns_csv(self, client, mock_supabase):
        _, query = mock_supabase
        call_count = {"n": 0}

        def side_effect():
            call_count["n"] += 1
            resp = MagicMock()
            if call_count["n"] == 1:
                # _verify_exam_access
                resp.data = _exam_row()
            elif call_count["n"] == 2:
                # fetch questions
                resp.data = _questions()
            elif call_count["n"] == 3:
                # fetch submissions
                resp.data = [_submission_row()]
            else:
                # fetch grading results for submission
                resp.data = _grading_results()
            return resp

        query.execute.side_effect = side_effect

        resp = client.get(f"/api/v1/review/exams/{EXAM_ID}/export")
        assert resp.status_code == 200
        assert "text/csv" in resp.headers["content-type"]
        assert "attachment" in resp.headers["content-disposition"]

        # Parse CSV
        reader = csv.reader(io.StringIO(resp.text))
        rows = list(reader)

        # Header
        assert rows[0][0] == "student_code"
        assert rows[0][1] == "student_name"
        assert "q1_score" in rows[0]
        assert "q2_score" in rows[0]

        # Data row
        assert len(rows) == 2  # header + 1 student
        assert rows[1][0] == "S001"
        assert rows[1][1] == "Student A"

    def test_export_exam_not_found_returns_404(self, client, mock_supabase):
        _, query = mock_supabase
        query.execute.return_value.data = None

        resp = client.get(f"/api/v1/review/exams/{EXAM_ID}/export")
        assert resp.status_code == 404

    def test_export_wrong_owner_returns_403(self, client, mock_supabase):
        _, query = mock_supabase
        row = _exam_row()
        row["created_by"] = "other-user-id"
        query.execute.return_value.data = row

        resp = client.get(f"/api/v1/review/exams/{EXAM_ID}/export")
        assert resp.status_code == 403

    def test_export_no_submissions(self, client, mock_supabase):
        _, query = mock_supabase
        call_count = {"n": 0}

        def side_effect():
            call_count["n"] += 1
            resp = MagicMock()
            if call_count["n"] == 1:
                resp.data = _exam_row()
            elif call_count["n"] == 2:
                resp.data = _questions()
            else:
                resp.data = []
            return resp

        query.execute.side_effect = side_effect

        resp = client.get(f"/api/v1/review/exams/{EXAM_ID}/export")
        assert resp.status_code == 200

        reader = csv.reader(io.StringIO(resp.text))
        rows = list(reader)
        # Only header row, no data
        assert len(rows) == 1

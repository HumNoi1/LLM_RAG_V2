"""
Tests for Review endpoints (app.api.v1.review)

Covers:
  GET  /api/v1/review/exams/{exam_id}/submissions  — list with grading summary
  GET  /api/v1/review/submissions/{submission_id}   — full detail per student
  PUT  /api/v1/review/results/{result_id}/approve   — approve LLM score
  PUT  /api/v1/review/results/{result_id}/revise    — override score + feedback
  POST /api/v1/review/exams/{exam_id}/approve-all   — bulk approve
"""

import pytest
from unittest.mock import MagicMock
from tests.conftest import FAKE_USER_ID

EXAM_ID = "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa"
SUB_ID = "cccccccc-cccc-cccc-cccc-cccccccccccc"
RESULT_ID = "dddddddd-dddd-dddd-dddd-dddddddddddd"
QUESTION_ID = "bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb"
NOW = "2026-03-01T00:00:00+00:00"


def _exam_row():
    return {
        "id": EXAM_ID,
        "created_by": FAKE_USER_ID,
        "total_questions": 2,
    }


def _submission_row():
    return {
        "id": SUB_ID,
        "exam_id": EXAM_ID,
        "status": "graded",
        "created_at": NOW,
        "students": {"full_name": "Student A", "student_code": "S001"},
    }


def _grading_result_row():
    return {
        "id": RESULT_ID,
        "submission_id": SUB_ID,
        "question_id": QUESTION_ID,
        "llm_score": 4.0,
        "llm_max_score": 5.0,
        "llm_reasoning": "Good answer",
        "expert_score": None,
        "expert_feedback": None,
        "status": "pending",
        "graded_at": NOW,
        "created_at": NOW,
        "exam_questions": {"question_number": 1, "max_score": 5.0},
    }


# ── GET /api/v1/review/exams/{exam_id}/submissions ──────────────────────────


class TestListSubmissionsWithSummary:
    def test_list_returns_200(self, client, mock_supabase):
        _, query = mock_supabase
        call_count = {"n": 0}

        def side_effect():
            call_count["n"] += 1
            resp = MagicMock()
            if call_count["n"] == 1:
                # _verify_exam_access
                resp.data = _exam_row()
            elif call_count["n"] == 2:
                # fetch submissions
                resp.data = [_submission_row()]
            else:
                # fetch grading_results per submission
                resp.data = [_grading_result_row()]
            return resp

        query.execute.side_effect = side_effect

        resp = client.get(f"/api/v1/review/exams/{EXAM_ID}/submissions")
        assert resp.status_code == 200
        body = resp.json()
        assert body["total"] == 1
        assert body["submissions"][0]["student_name"] == "Student A"

    def test_exam_not_found_returns_404(self, client, mock_supabase):
        _, query = mock_supabase
        query.execute.return_value.data = None

        resp = client.get(f"/api/v1/review/exams/{EXAM_ID}/submissions")
        assert resp.status_code == 404

    def test_wrong_owner_returns_403(self, client, mock_supabase):
        _, query = mock_supabase
        row = _exam_row()
        row["created_by"] = "other-user-id"
        query.execute.return_value.data = row

        resp = client.get(f"/api/v1/review/exams/{EXAM_ID}/submissions")
        assert resp.status_code == 403


# ── GET /api/v1/review/submissions/{submission_id} ──────────────────────────


class TestGetSubmissionDetail:
    def test_detail_returns_200(self, client, mock_supabase):
        _, query = mock_supabase
        call_count = {"n": 0}

        def side_effect():
            call_count["n"] += 1
            resp = MagicMock()
            if call_count["n"] == 1:
                # _get_submission_or_404
                resp.data = _submission_row()
            else:
                # grading results
                resp.data = [_grading_result_row()]
            return resp

        query.execute.side_effect = side_effect

        resp = client.get(f"/api/v1/review/submissions/{SUB_ID}")
        assert resp.status_code == 200
        body = resp.json()
        assert body["student_name"] == "Student A"
        assert len(body["grading_results"]) == 1

    def test_submission_not_found_returns_404(self, client, mock_supabase):
        _, query = mock_supabase
        query.execute.return_value.data = None

        resp = client.get(f"/api/v1/review/submissions/{SUB_ID}")
        assert resp.status_code == 404


# ── PUT /api/v1/review/results/{result_id}/approve ──────────────────────────


class TestApproveResult:
    def test_approve_returns_200(self, client, mock_supabase):
        _, query = mock_supabase
        call_count = {"n": 0}

        def side_effect():
            call_count["n"] += 1
            resp = MagicMock()
            if call_count["n"] == 1:
                # _get_result_or_404
                resp.data = _grading_result_row()
            else:
                # update
                approved = _grading_result_row()
                approved["status"] = "approved"
                resp.data = [approved]
            return resp

        query.execute.side_effect = side_effect

        resp = client.put(f"/api/v1/review/results/{RESULT_ID}/approve")
        assert resp.status_code == 200
        assert resp.json()["status"] == "approved"


# ── PUT /api/v1/review/results/{result_id}/revise ───────────────────────────


class TestReviseResult:
    def test_revise_returns_200(self, client, mock_supabase):
        _, query = mock_supabase
        call_count = {"n": 0}

        def side_effect():
            call_count["n"] += 1
            resp = MagicMock()
            if call_count["n"] == 1:
                # _get_result_or_404
                resp.data = _grading_result_row()
            else:
                # update
                revised = _grading_result_row()
                revised["status"] = "revised"
                revised["expert_score"] = 3.5
                revised["expert_feedback"] = "Needs improvement"
                resp.data = [revised]
            return resp

        query.execute.side_effect = side_effect

        resp = client.put(
            f"/api/v1/review/results/{RESULT_ID}/revise",
            json={"expert_score": 3.5, "expert_feedback": "Needs improvement"},
        )
        assert resp.status_code == 200
        body = resp.json()
        assert body["status"] == "revised"
        assert body["expert_score"] == 3.5

    def test_revise_exceeds_max_score_returns_400(self, client, mock_supabase):
        _, query = mock_supabase
        query.execute.return_value.data = _grading_result_row()

        resp = client.put(
            f"/api/v1/review/results/{RESULT_ID}/revise",
            json={"expert_score": 999, "expert_feedback": "Too high"},
        )
        assert resp.status_code == 400

    def test_revise_missing_feedback_returns_422(self, client, mock_supabase):
        """expert_feedback is required (min_length=1)."""
        resp = client.put(
            f"/api/v1/review/results/{RESULT_ID}/revise",
            json={"expert_score": 3.0},
        )
        assert resp.status_code == 422


# ── POST /api/v1/review/exams/{exam_id}/approve-all ─────────────────────────


class TestBulkApprove:
    def test_bulk_approve_returns_200(self, client, mock_supabase):
        _, query = mock_supabase
        call_count = {"n": 0}

        def side_effect():
            call_count["n"] += 1
            resp = MagicMock()
            if call_count["n"] == 1:
                # _verify_exam_access
                resp.data = _exam_row()
            elif call_count["n"] == 2:
                # fetch pending results
                resp.data = [
                    {"id": RESULT_ID, "student_submissions": {"exam_id": EXAM_ID}},
                ]
            else:
                # bulk update
                resp.data = []
            return resp

        query.execute.side_effect = side_effect

        resp = client.post(f"/api/v1/review/exams/{EXAM_ID}/approve-all")
        assert resp.status_code == 200
        body = resp.json()
        assert body["approved_count"] == 1

    def test_bulk_approve_no_pending(self, client, mock_supabase):
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

        resp = client.post(f"/api/v1/review/exams/{EXAM_ID}/approve-all")
        assert resp.status_code == 200
        assert resp.json()["approved_count"] == 0

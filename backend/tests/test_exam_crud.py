"""
Tests for Exam CRUD endpoints (app.api.v1.exams)

Uses the `client` fixture from conftest.py which overrides get_supabase
and get_current_user so no real DB/network calls are made.

Covers:
  POST   /api/v1/exams              - create exam
  GET    /api/v1/exams              - list exams
  GET    /api/v1/exams/{id}         - get exam (owner + questions)
  PUT    /api/v1/exams/{id}         - update exam
  DELETE /api/v1/exams/{id}         - delete exam
  POST   /api/v1/exams/{id}/questions  - add question (+ duplicate 409)
  DELETE /api/v1/exams/{id}/questions/{qid} - delete question
"""

import pytest
from unittest.mock import MagicMock
from tests.conftest import FAKE_USER_ID

EXAM_ID = "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa"
QUESTION_ID = "bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb"
NOW = "2026-03-01T00:00:00+00:00"


def _exam_row(exam_id=EXAM_ID):
    return {
        "id": exam_id,
        "title": "Midterm",
        "subject": "CS101",
        "description": "Midterm exam",
        "created_by": FAKE_USER_ID,
        "total_questions": 2,
        "created_at": NOW,
        "updated_at": NOW,
    }


def _exam_row_with_questions(exam_id=EXAM_ID):
    row = _exam_row(exam_id)
    row["exam_questions"] = [
        {
            "id": QUESTION_ID,
            "exam_id": exam_id,
            "question_number": 1,
            "question_text": "What is 1+1?",
            "max_score": 5,
            "created_at": NOW,
        }
    ]
    return row


def _question_row():
    return {
        "id": QUESTION_ID,
        "exam_id": EXAM_ID,
        "question_number": 1,
        "question_text": "What is 1+1?",
        "max_score": 5,
        "created_at": NOW,
    }


# ── POST /api/v1/exams ────────────────────────────────────────────────────────


class TestCreateExam:
    def test_create_returns_201(self, client, mock_supabase):
        _, query = mock_supabase
        query.execute.return_value.data = [_exam_row()]

        resp = client.post(
            "/api/v1/exams",
            json={
                "title": "Midterm",
                "subject": "CS101",
                "description": "Midterm exam",
                "total_questions": 2,
            },
        )
        assert resp.status_code == 201
        body = resp.json()
        assert body["title"] == "Midterm"
        assert body["id"] == EXAM_ID

    def test_create_missing_title_returns_422(self, client):
        resp = client.post(
            "/api/v1/exams",
            json={"subject": "CS101", "total_questions": 1},
        )
        assert resp.status_code == 422


# ── GET /api/v1/exams ─────────────────────────────────────────────────────────


class TestListExams:
    def test_list_returns_200(self, client, mock_supabase):
        _, query = mock_supabase
        query.execute.return_value.data = [_exam_row()]

        resp = client.get("/api/v1/exams")
        assert resp.status_code == 200
        body = resp.json()
        assert body["total"] == 1
        assert body["exams"][0]["id"] == EXAM_ID

    def test_list_empty(self, client, mock_supabase):
        _, query = mock_supabase
        query.execute.return_value.data = []

        resp = client.get("/api/v1/exams")
        assert resp.status_code == 200
        assert resp.json()["total"] == 0


# ── GET /api/v1/exams/{id} ────────────────────────────────────────────────────


class TestGetExam:
    def test_get_own_exam_returns_200(self, client, mock_supabase):
        _, query = mock_supabase
        query.execute.return_value.data = _exam_row_with_questions()

        resp = client.get(f"/api/v1/exams/{EXAM_ID}")
        assert resp.status_code == 200
        body = resp.json()
        assert body["id"] == EXAM_ID
        assert len(body["questions"]) == 1

    def test_get_exam_not_found_returns_404(self, client, mock_supabase):
        _, query = mock_supabase
        query.execute.return_value.data = None

        resp = client.get(f"/api/v1/exams/{EXAM_ID}")
        assert resp.status_code == 404

    def test_get_exam_wrong_owner_returns_403(self, client, mock_supabase):
        _, query = mock_supabase
        row = _exam_row_with_questions()
        row["created_by"] = "other-user-id"
        query.execute.return_value.data = row

        resp = client.get(f"/api/v1/exams/{EXAM_ID}")
        assert resp.status_code == 403


# ── PUT /api/v1/exams/{id} ────────────────────────────────────────────────────


class TestUpdateExam:
    def test_update_title_returns_200(self, client, mock_supabase):
        _, query = mock_supabase

        # First call: _verify_exam_owner → _get_exam_or_404 returns exam
        # Second call: update → returns updated row
        updated_row = _exam_row()
        updated_row["title"] = "Updated Title"

        call_count = {"n": 0}
        original_execute = query.execute

        def side_effect():
            call_count["n"] += 1
            resp = MagicMock()
            if call_count["n"] == 1:
                # _get_exam_or_404
                resp.data = _exam_row_with_questions()
            else:
                # update
                resp.data = [updated_row]
            return resp

        query.execute.side_effect = side_effect

        resp = client.put(
            f"/api/v1/exams/{EXAM_ID}",
            json={"title": "Updated Title"},
        )
        assert resp.status_code == 200
        assert resp.json()["title"] == "Updated Title"

    def test_update_no_fields_returns_400(self, client, mock_supabase):
        _, query = mock_supabase
        query.execute.return_value.data = _exam_row_with_questions()

        resp = client.put(f"/api/v1/exams/{EXAM_ID}", json={})
        assert resp.status_code == 400


# ── DELETE /api/v1/exams/{id} ─────────────────────────────────────────────────


class TestDeleteExam:
    def test_delete_returns_204(self, client, mock_supabase):
        _, query = mock_supabase
        # First call verify owner, second call delete
        call_count = {"n": 0}

        def side_effect():
            call_count["n"] += 1
            resp = MagicMock()
            resp.data = _exam_row_with_questions() if call_count["n"] == 1 else []
            return resp

        query.execute.side_effect = side_effect

        resp = client.delete(f"/api/v1/exams/{EXAM_ID}")
        assert resp.status_code == 204


# ── POST /api/v1/exams/{id}/questions ────────────────────────────────────────


class TestAddQuestion:
    def test_add_question_returns_201(self, client, mock_supabase):
        _, query = mock_supabase
        call_count = {"n": 0}

        def side_effect():
            call_count["n"] += 1
            resp = MagicMock()
            if call_count["n"] == 1:
                # _verify_exam_owner → _get_exam_or_404
                resp.data = _exam_row_with_questions()
            elif call_count["n"] == 2:
                # check duplicate question_number → none found
                resp.data = None
            else:
                # insert
                resp.data = [_question_row()]
            return resp

        query.execute.side_effect = side_effect

        resp = client.post(
            f"/api/v1/exams/{EXAM_ID}/questions",
            json={
                "question_number": 1,
                "question_text": "What is 1+1?",
                "max_score": 5,
            },
        )
        assert resp.status_code == 201
        assert resp.json()["question_number"] == 1

    def test_duplicate_question_number_returns_409(self, client, mock_supabase):
        _, query = mock_supabase
        call_count = {"n": 0}

        def side_effect():
            call_count["n"] += 1
            resp = MagicMock()
            if call_count["n"] == 1:
                resp.data = _exam_row_with_questions()
            else:
                # duplicate found
                resp.data = {"id": QUESTION_ID}
            return resp

        query.execute.side_effect = side_effect

        resp = client.post(
            f"/api/v1/exams/{EXAM_ID}/questions",
            json={
                "question_number": 1,
                "question_text": "Dup question",
                "max_score": 5,
            },
        )
        assert resp.status_code == 409


# ── DELETE /api/v1/exams/{id}/questions/{qid} ────────────────────────────────


class TestDeleteQuestion:
    def test_delete_question_returns_204(self, client, mock_supabase):
        _, query = mock_supabase
        call_count = {"n": 0}

        def side_effect():
            call_count["n"] += 1
            resp = MagicMock()
            if call_count["n"] == 1:
                resp.data = _exam_row_with_questions()
            elif call_count["n"] == 2:
                resp.data = {"id": QUESTION_ID}
            else:
                resp.data = []
            return resp

        query.execute.side_effect = side_effect

        resp = client.delete(f"/api/v1/exams/{EXAM_ID}/questions/{QUESTION_ID}")
        assert resp.status_code == 204

    def test_delete_nonexistent_question_returns_404(self, client, mock_supabase):
        _, query = mock_supabase
        call_count = {"n": 0}

        def side_effect():
            call_count["n"] += 1
            resp = MagicMock()
            if call_count["n"] == 1:
                resp.data = _exam_row_with_questions()
            else:
                resp.data = None
            return resp

        query.execute.side_effect = side_effect

        resp = client.delete(f"/api/v1/exams/{EXAM_ID}/questions/{QUESTION_ID}")
        assert resp.status_code == 404

"""
Tests for Admin endpoints (app.api.v1.admin)

Covers:
  GET  /api/v1/admin/users          — list users (admin only)
  POST /api/v1/admin/users          — create user (admin only)
  PUT  /api/v1/admin/users/{id}     — update user (admin only)
  Access control: non-admin gets 403
"""

import pytest
from unittest.mock import MagicMock
from tests.conftest import FAKE_USER_ID, FAKE_ADMIN_ID

USER_ID = "11111111-1111-1111-1111-111111111111"
NOW = "2026-03-01T00:00:00+00:00"


def _user_row(user_id=USER_ID, role="teacher"):
    return {
        "id": user_id,
        "email": "user@example.com",
        "full_name": "Test User",
        "role": role,
        "created_at": NOW,
    }


# ── GET /api/v1/admin/users ─────────────────────────────────────────────────


class TestListUsers:
    def test_admin_can_list_users(self, admin_client, mock_supabase):
        _, query = mock_supabase
        query.execute.return_value.data = [
            _user_row(),
            _user_row(user_id=FAKE_ADMIN_ID, role="admin"),
        ]

        resp = admin_client.get("/api/v1/admin/users")
        assert resp.status_code == 200
        body = resp.json()
        assert body["total"] == 2
        assert len(body["users"]) == 2

    def test_teacher_gets_403(self, client, mock_supabase):
        """Non-admin user should be rejected."""
        resp = client.get("/api/v1/admin/users")
        assert resp.status_code == 403

    def test_list_empty(self, admin_client, mock_supabase):
        _, query = mock_supabase
        query.execute.return_value.data = []

        resp = admin_client.get("/api/v1/admin/users")
        assert resp.status_code == 200
        assert resp.json()["total"] == 0


# ── POST /api/v1/admin/users ────────────────────────────────────────────────


class TestCreateUser:
    def test_create_user_returns_200(self, admin_client, mock_supabase):
        _, query = mock_supabase
        call_count = {"n": 0}

        def side_effect():
            call_count["n"] += 1
            resp = MagicMock()
            if call_count["n"] == 1:
                # check existing email — not found
                resp.data = None
            else:
                # insert
                resp.data = [_user_row()]
            return resp

        query.execute.side_effect = side_effect

        resp = admin_client.post(
            "/api/v1/admin/users",
            json={
                "email": "new@example.com",
                "password": "securepassword",
                "full_name": "New User",
                "role": "teacher",
            },
        )
        assert resp.status_code == 200
        assert resp.json()["email"] == "user@example.com"

    def test_duplicate_email_returns_400(self, admin_client, mock_supabase):
        _, query = mock_supabase
        # email already exists
        query.execute.return_value.data = {"id": USER_ID}

        resp = admin_client.post(
            "/api/v1/admin/users",
            json={
                "email": "existing@example.com",
                "password": "securepassword",
                "full_name": "Existing User",
                "role": "teacher",
            },
        )
        assert resp.status_code == 400

    def test_teacher_cannot_create_user(self, client, mock_supabase):
        resp = client.post(
            "/api/v1/admin/users",
            json={
                "email": "new@example.com",
                "password": "password",
                "full_name": "New",
                "role": "teacher",
            },
        )
        assert resp.status_code == 403


# ── PUT /api/v1/admin/users/{id} ────────────────────────────────────────────


class TestUpdateUser:
    def test_update_user_returns_200(self, admin_client, mock_supabase):
        _, query = mock_supabase
        call_count = {"n": 0}

        def side_effect():
            call_count["n"] += 1
            resp = MagicMock()
            if call_count["n"] == 1:
                # _get_user_or_404
                resp.data = _user_row()
            else:
                # update
                updated = _user_row()
                updated["full_name"] = "Updated Name"
                resp.data = [updated]
            return resp

        query.execute.side_effect = side_effect

        resp = admin_client.put(
            f"/api/v1/admin/users/{USER_ID}",
            json={"full_name": "Updated Name", "role": "teacher"},
        )
        assert resp.status_code == 200
        assert resp.json()["full_name"] == "Updated Name"

    def test_update_nonexistent_user_returns_404(self, admin_client, mock_supabase):
        _, query = mock_supabase
        query.execute.return_value.data = None

        resp = admin_client.put(
            f"/api/v1/admin/users/{USER_ID}",
            json={"full_name": "Ghost", "role": "teacher"},
        )
        assert resp.status_code == 404

    def test_admin_cannot_self_demote(self, admin_client, mock_supabase):
        _, query = mock_supabase
        # Return admin's own row
        query.execute.return_value.data = _user_row(user_id=FAKE_ADMIN_ID, role="admin")

        resp = admin_client.put(
            f"/api/v1/admin/users/{FAKE_ADMIN_ID}",
            json={"full_name": "Admin", "role": "teacher"},
        )
        assert resp.status_code == 400

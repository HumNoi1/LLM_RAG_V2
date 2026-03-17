"""
Shared pytest fixtures for backend tests.

Provides:
  - mock_supabase_query: a pytest fixture that patches get_supabase in all relevant modules
  - mock_current_user: a fake authenticated user dict
  - client: a FastAPI TestClient with get_current_user dependency overridden
"""

import pytest
from unittest.mock import MagicMock, patch
from fastapi.testclient import TestClient

from app.main import app
from app.dependencies import get_current_user


# ── Current-user Fixture ──────────────────────────────────────────────────────

FAKE_USER_ID = "00000000-0000-0000-0000-000000000001"


@pytest.fixture()
def mock_current_user() -> dict:
    return {
        "id": FAKE_USER_ID,
        "email": "test@example.com",
        "role": "teacher",
        "full_name": "Test Teacher",
    }


# ── Supabase query mock builder ───────────────────────────────────────────────


def make_query_mock():
    """Return a fresh fluent-builder mock for supabase-py queries."""
    query = MagicMock()
    query.select.return_value = query
    query.insert.return_value = query
    query.update.return_value = query
    query.delete.return_value = query
    query.eq.return_value = query
    query.neq.return_value = query
    query.order.return_value = query
    query.limit.return_value = query
    query.maybe_single.return_value = query

    # Default: return a MagicMock with .data = None so code doesn't crash on .data access
    default_resp = MagicMock()
    default_resp.data = None
    query.execute.return_value = default_resp

    return query


@pytest.fixture()
def mock_supabase():
    """
    Patches app.database.get_supabase across all router modules so the
    fluent builder mock is returned wherever `get_supabase()` is called.

    Returns (sb_client_mock, query_mock) — tests should configure
    query.execute.return_value.data to set desired responses.
    """
    query = make_query_mock()
    sb = MagicMock()
    sb.table.return_value = query

    targets = [
        "app.api.v1.exams.get_supabase",
        "app.api.v1.documents.get_supabase",
        "app.dependencies.get_supabase",
    ]

    patches = [patch(t, return_value=sb) for t in targets]
    for p in patches:
        p.start()

    yield sb, query

    for p in patches:
        p.stop()


# ── TestClient Fixture ────────────────────────────────────────────────────────


@pytest.fixture()
def client(mock_supabase, mock_current_user):
    """
    FastAPI TestClient with get_current_user overridden → fake authenticated user.
    get_supabase is patched at module level by mock_supabase fixture.
    """
    app.dependency_overrides[get_current_user] = lambda: mock_current_user

    with TestClient(app) as c:
        yield c

    app.dependency_overrides.clear()

"""
Supabase client singleton — replaces Prisma ORM.

Uses supabase-py SDK to access Supabase PostgreSQL via PostgREST.
Service role key is used to bypass RLS for server-side operations.
"""

from dataclasses import dataclass, field
from typing import Any

from supabase import create_client, Client
from app.config import get_settings

_client: Client | None = None


def get_supabase() -> Client:
    """Get or create the Supabase client singleton.

    Uses service_role_key when available (bypasses RLS for server-side ops),
    falls back to anon/publishable key for development.
    """
    global _client
    if _client is None:
        settings = get_settings()
        key = settings.supabase_service_role_key or settings.supabase_key
        if not settings.supabase_url or not key:
            raise RuntimeError(
                "SUPABASE_URL and SUPABASE_KEY (or SUPABASE_SERVICE_ROLE_KEY) must be set"
            )
        _client = create_client(settings.supabase_url, key)
    return _client


# ── Safe maybe_single helper ─────────────────────────────────────────────────


@dataclass
class _SafeResponse:
    """Minimal API response wrapper so callers can always access .data."""

    data: Any = None


def maybe_single_safe(builder) -> _SafeResponse:
    """Execute a PostgREST query with maybe_single(), safely handling the case
    where supabase-py returns *None* (no matching row) instead of a response
    object.  Callers can always do ``resp.data`` without a None guard.

    Usage::

        from app.database import get_supabase, maybe_single_safe

        resp = maybe_single_safe(
            supabase.table("users").select("*").eq("email", email)
        )
        if resp.data:
            ...
    """
    raw = builder.maybe_single().execute()
    if raw is None:
        return _SafeResponse(data=None)
    return raw

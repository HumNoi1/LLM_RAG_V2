"""
Supabase client singleton — replaces Prisma ORM.

Uses supabase-py SDK to access Supabase PostgreSQL via PostgREST.
Service role key is used to bypass RLS for server-side operations.
"""

from supabase import create_client, Client
from app.config import get_settings

_client: Client | None = None


def get_supabase() -> Client:
    """Get or create the Supabase client singleton."""
    global _client
    if _client is None:
        settings = get_settings()
        _client = create_client(
            settings.supabase_url, settings.supabase_service_role_key
        )
    return _client

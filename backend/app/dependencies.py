from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from app.core.security import decode_token
from app.database import db

security_scheme = HTTPBearer()


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security_scheme),
):
    payload = decode_token(credentials.credentials)
    if not payload or payload.get("type") != "access":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
        )

    user_id = payload.get("sub")
    user = await db.user.find_unique(where={"id": user_id})
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
        )

    return user


def require_role(*allowed_roles: str):
    """Returns a FastAPI Depends that enforces role-based access control.

    Usage:
        @router.get("/admin/something")
        async def endpoint(current_user=require_role("admin")):
            ...
    """
    async def role_checker(current_user=Depends(get_current_user)):
        if current_user.role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions",
            )
        return current_user

    return Depends(role_checker)
"""
FastAPI dependency injection — shared dependencies across all routers.

Usage:
    from app.dependencies import get_current_user, get_supabase

    @router.get("/me")
    async def me(current_user = Depends(get_current_user)):
        ...
"""
from typing import Annotated

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.config import Settings, get_settings

bearer_scheme = HTTPBearer()

# ── Settings ─────────────────────────────────────────────────────────────────

def get_config() -> Settings:
    return get_settings()


# ── Supabase client ───────────────────────────────────────────────────────────
# Implemented in Sprint 1 by BE-J after Supabase project is set up.

def get_supabase():
    """Return a Supabase client instance."""
    settings = get_settings()
    if not settings.supabase_url or not settings.supabase_key:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Supabase is not configured",
        )
    from supabase import create_client
    return create_client(settings.supabase_url, settings.supabase_key)


# ── Current user (JWT) ────────────────────────────────────────────────────────
# Full implementation is BE-J's responsibility (Sprint 1: auth_service + security.py).
# Stub is here so routers can reference it early.

async def get_current_user(
    credentials: Annotated[HTTPAuthorizationCredentials, Depends(bearer_scheme)],
    settings: Annotated[Settings, Depends(get_config)],
):
    """Decode JWT and return the current user dict.
    BE-J: replace this stub with the full implementation in app/core/security.py
    """
    from app.core.security import decode_access_token
    payload = decode_access_token(credentials.credentials, settings.secret_key)
    if payload is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return payload


async def require_admin(
    current_user: Annotated[dict, Depends(get_current_user)],
):
    """Guard: only allow users with role='admin'."""
    if current_user.get("role") != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required",
        )
    return current_user

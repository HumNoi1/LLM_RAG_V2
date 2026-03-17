"""
FastAPI dependency injection — shared dependencies across all routers.
"""

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from app.config import Settings, get_settings
from app.core.security import decode_token
from app.database import get_supabase, maybe_single_safe

security_scheme = HTTPBearer()


# ── Settings ─────────────────────────────────────────────────────────────────


def get_config() -> Settings:
    return get_settings()


# ── Current User ─────────────────────────────────────────────────────────────


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
    supabase = get_supabase()
    response = maybe_single_safe(supabase.table("users").select("*").eq("id", user_id))
    user = response.data

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
        )

    return user


# ── Role Guard ───────────────────────────────────────────────────────────────


def require_role(*allowed_roles: str):
    """Returns a FastAPI Depends that enforces role-based access control.

    Usage:
        @router.get("/admin/something")
        async def endpoint(current_user=require_role("admin")):
            ...
    """

    async def role_checker(current_user=Depends(get_current_user)):
        if current_user["role"] not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions",
            )
        return current_user

    return Depends(role_checker)

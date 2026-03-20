"""
Admin endpoints — BE-J responsibility (Sprint 3).

Admin user management functionality:
GET  /api/v1/admin/users          — list users
POST /api/v1/admin/users          — create new user
PUT  /api/v1/admin/users/{id}     — update user

Only admin users can access these endpoints.
"""

import logging
from datetime import datetime, timezone
from typing import Annotated, List
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field

from app import schemas
from app.schemas.auth import UserRole, UserCreate, UserResponse
from app.core.security import hash_password
from app.database import get_supabase, maybe_single_safe
from app.dependencies import get_current_user

logger = logging.getLogger(__name__)
router = APIRouter()


# ── Admin-only access control ────────────────────────────────────────────────


def require_admin_user(current_user: dict = Depends(get_current_user)):
    """Dependency to ensure only admin users can access admin endpoints"""
    if current_user.get("role") != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Admin access required"
        )
    return current_user


# ── Admin-specific schemas ───────────────────────────────────────────────────


class UserUpdateRequest(BaseModel):
    full_name: str = Field(..., min_length=1, max_length=255)
    role: UserRole
    # Note: email and password updates can be added later if needed


class UserListResponse(BaseModel):
    users: List[UserResponse]
    total: int


# ── Helper functions ──────────────────────────────────────────────────────────


def _get_user_or_404(user_id: str) -> dict:
    """Fetch a user row or raise 404."""
    supabase = get_supabase()
    resp = maybe_single_safe(supabase.table("users").select("*").eq("id", user_id))
    if not resp.data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
        )
    return resp.data


# ── Admin endpoints ──────────────────────────────────────────────────────────


@router.get("/users", response_model=UserListResponse)
async def list_users(
    admin_user: Annotated[dict, Depends(require_admin_user)],
):
    """List all users in the system (admin only)"""
    supabase = get_supabase()

    users_resp = (
        supabase.table("users")
        .select("id, email, full_name, role, created_at")
        .order("created_at", desc=False)
        .execute()
    )
    users = users_resp.data or []

    user_responses = [
        UserResponse(
            id=user["id"],
            email=user["email"],
            full_name=user["full_name"],
            role=user["role"],
            created_at=user["created_at"],
        )
        for user in users
    ]

    return UserListResponse(users=user_responses, total=len(user_responses))


@router.post("/users", response_model=UserResponse)
async def create_user(
    user_data: UserCreate,
    admin_user: Annotated[dict, Depends(require_admin_user)],
):
    """Create a new user (admin only)"""
    supabase = get_supabase()

    # Check if email already exists
    existing_resp = maybe_single_safe(
        supabase.table("users").select("id").eq("email", user_data.email)
    )
    if existing_resp.data:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Email already registered"
        )

    # Hash password
    hashed_password = hash_password(user_data.password)

    # Create user
    create_resp = (
        supabase.table("users")
        .insert(
            {
                "email": user_data.email,
                "password_hash": hashed_password,
                "full_name": user_data.full_name,
                "role": user_data.role.value,
            }
        )
        .execute()
    )

    if not create_resp.data:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create user",
        )

    created_user = create_resp.data[0]

    return UserResponse(
        id=created_user["id"],
        email=created_user["email"],
        full_name=created_user["full_name"],
        role=created_user["role"],
        created_at=created_user["created_at"],
    )


@router.put("/users/{user_id}", response_model=UserResponse)
async def update_user(
    user_id: UUID,
    user_data: UserUpdateRequest,
    admin_user: Annotated[dict, Depends(require_admin_user)],
):
    """Update user information (admin only)"""
    supabase = get_supabase()

    # Verify user exists
    existing_user = _get_user_or_404(str(user_id))

    # Prevent admin from demoting themselves (optional safety check)
    if (
        existing_user["id"] == admin_user["id"]
        and existing_user["role"] == "admin"
        and user_data.role != UserRole.admin
    ):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot demote your own admin privileges",
        )

    # Update user
    update_resp = (
        supabase.table("users")
        .update(
            {
                "full_name": user_data.full_name,
                "role": user_data.role.value,
                "updated_at": datetime.now(timezone.utc).isoformat(),
            }
        )
        .eq("id", str(user_id))
        .execute()
    )

    if not update_resp.data:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update user",
        )

    updated_user = update_resp.data[0]

    return UserResponse(
        id=updated_user["id"],
        email=updated_user["email"],
        full_name=updated_user["full_name"],
        role=updated_user["role"],
        created_at=updated_user["created_at"],
    )

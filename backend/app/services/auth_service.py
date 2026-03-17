from datetime import datetime, timezone
from uuid import uuid4

from app.database import get_supabase, maybe_single_safe
from app.core.security import (
    hash_password,
    verify_password,
    create_access_token,
    create_refresh_token,
    decode_token,
)
from app.schemas.auth import UserCreate, UserResponse, TokenResponse
from fastapi import HTTPException, status


async def register_user(data: UserCreate) -> UserResponse:
    supabase = get_supabase()

    # Check if email already registered
    existing = maybe_single_safe(
        supabase.table("users").select("id").eq("email", data.email)
    )
    if existing.data:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Email already registered",
        )

    # Create new user
    now = datetime.now(timezone.utc).isoformat()
    response = (
        supabase.table("users")
        .insert(
            {
                "id": str(uuid4()),
                "email": data.email,
                "password_hash": hash_password(data.password),
                "full_name": data.full_name,
                "role": data.role.value,
                "created_at": now,
                "updated_at": now,
            }
        )
        .execute()
    )
    user = response.data[0]

    return UserResponse(
        id=user["id"],
        email=user["email"],
        full_name=user["full_name"],
        role=user["role"],
        created_at=user["created_at"],
    )


async def login_user(email: str, password: str) -> TokenResponse:
    supabase = get_supabase()

    response = maybe_single_safe(supabase.table("users").select("*").eq("email", email))
    user = response.data

    if not user or not verify_password(password, user["password_hash"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
        )

    access_token = create_access_token(user["id"], user["role"])
    refresh_token = create_refresh_token(user["id"])

    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
    )


async def refresh_access_token(refresh_token: str) -> TokenResponse:
    payload = decode_token(refresh_token)
    if not payload or payload.get("type") != "refresh":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token",
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

    new_access_token = create_access_token(user["id"], user["role"])
    new_refresh_token = create_refresh_token(user["id"])

    return TokenResponse(
        access_token=new_access_token,
        refresh_token=new_refresh_token,
    )

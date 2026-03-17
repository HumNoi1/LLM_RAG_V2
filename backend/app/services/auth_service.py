from app.database import get_supabase
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
    existing = (
        supabase.table("users")
        .select("id")
        .eq("email", data.email)
        .maybe_single()
        .execute()
    )
    if existing.data:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered",
        )

    # Create new user
    response = (
        supabase.table("users")
        .insert(
            {
                "email": data.email,
                "password_hash": hash_password(data.password),
                "full_name": data.full_name,
                "role": data.role.value,
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

    response = (
        supabase.table("users").select("*").eq("email", email).maybe_single().execute()
    )
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
    response = (
        supabase.table("users").select("*").eq("id", user_id).maybe_single().execute()
    )
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

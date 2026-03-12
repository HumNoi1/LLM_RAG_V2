from fastapi import APIRouter, Depends
from app.schemas import (
    UserCreate,
    UserLogin,
    UserResponse,
    TokenResponse,
    TokenRefreshRequest,
)
from app.services.auth_service import register_user, login_user, refresh_access_token
from app.dependencies import get_current_user

router = APIRouter(prefix="/auth", tags=["Auth"])


@router.post("/register", response_model=UserResponse, status_code=201)
async def register(data: UserCreate):
    return await register_user(data)


@router.post("/login", response_model=TokenResponse)
async def login(data: UserLogin):
    return await login_user(data.email, data.password)


@router.post("/refresh", response_model=TokenResponse)
async def refresh(data: TokenRefreshRequest):
    return await refresh_access_token(data.refresh_token)


@router.get("/me", response_model=UserResponse)
async def get_me(current_user=Depends(get_current_user)):
    return UserResponse(
        id=current_user.id,
        email=current_user.email,
        full_name=current_user.fullName,
        role=current_user.role,
        created_at=current_user.createdAt,
    )
"""
Auth endpoints — BE-J responsibility (Sprint 1).

POST /api/v1/auth/register
POST /api/v1/auth/login
POST /api/v1/auth/refresh
"""
from fastapi import APIRouter, Depends

from app import schemas
from app.dependencies import get_config, get_supabase
from app.services import auth_service

router = APIRouter()


@router.post("/register", response_model=schemas.UserResponse, status_code=201)
async def register(
    data: schemas.RegisterRequest,
    supabase=Depends(get_supabase),
):
    """Register a new teacher account. BE-J: implement in Sprint 1."""
    return await auth_service.register(data, supabase)


@router.post("/login", response_model=schemas.TokenResponse)
async def login(
    data: schemas.LoginRequest,
    supabase=Depends(get_supabase),
    settings=Depends(get_config),
):
    """Login and receive JWT tokens. BE-J: implement in Sprint 1."""
    return await auth_service.login(data, supabase, settings)


@router.post("/refresh", response_model=schemas.TokenResponse)
async def refresh(
    data: schemas.RefreshRequest,
    settings=Depends(get_config),
):
    """Refresh access token using refresh token. BE-J: implement in Sprint 1."""
    return await auth_service.refresh(data.refresh_token, settings)

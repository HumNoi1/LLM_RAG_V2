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

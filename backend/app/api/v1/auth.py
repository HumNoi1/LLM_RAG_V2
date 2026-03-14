from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse

from app.schemas import ErrorResponse
from app.schemas.auth import (
    UserCreate,
    UserLogin,
    UserResponse,
    TokenResponse,
    TokenRefreshRequest,
)
from app.services.auth_service import register_user, login_user, refresh_access_token
from app.dependencies import get_current_user

router = APIRouter(prefix="/auth", tags=["Auth"])


@router.post(
    "/register",
    response_model=UserResponse,
    status_code=201,
    summary="ลงทะเบียนผู้ใช้ใหม่",
    responses={
        409: {"model": ErrorResponse, "description": "อีเมลนี้ถูกใช้ไปแล้ว"},
        422: {"description": "ข้อมูลไม่ถูกต้อง (validation error)"},
    },
)
async def register(data: UserCreate):
    """สร้างบัญชีผู้ใช้ใหม่ในระบบ

    - ไม่ต้องการ JWT token
    - รหัสผ่านต้องมีอย่างน้อย 8 ตัวอักษร
    - role เริ่มต้นเป็น `teacher`
    """
    return await register_user(data)


@router.post(
    "/login",
    response_model=TokenResponse,
    summary="เข้าสู่ระบบ",
    responses={
        401: {"model": ErrorResponse, "description": "อีเมลหรือรหัสผ่านไม่ถูกต้อง"},
    },
)
async def login(data: UserLogin):
    """เข้าสู่ระบบด้วยอีเมลและรหัสผ่าน

    - ไม่ต้องการ JWT token
    - ส่งกลับ access_token และ refresh_token
    - ใช้ access_token ใน header `Authorization: Bearer <token>`
    """
    return await login_user(data.email, data.password)


@router.post(
    "/refresh",
    response_model=TokenResponse,
    summary="รีเฟรช access token",
    responses={
        401: {"model": ErrorResponse, "description": "refresh token ไม่ถูกต้องหรือหมดอายุ"},
    },
)
async def refresh(data: TokenRefreshRequest):
    """ใช้ refresh token เพื่อขอ access token ใหม่

    - ส่ง refresh_token ที่ได้จาก login
    - ส่งกลับ token คู่ใหม่ (access + refresh)
    """
    return await refresh_access_token(data.refresh_token)


@router.get(
    "/me",
    response_model=UserResponse,
    summary="ดูข้อมูลผู้ใช้ปัจจุบัน",
    responses={
        401: {"model": ErrorResponse, "description": "ไม่ได้ login หรือ token หมดอายุ"},
    },
)
async def get_me(current_user=Depends(get_current_user)):
    """ดึงข้อมูลโปรไฟล์ของผู้ใช้ที่ login อยู่

    - ต้องส่ง JWT token ใน Authorization header
    """
    return UserResponse(
        id=current_user.id,
        email=current_user.email,
        full_name=current_user.fullName,
        role=current_user.role,
        created_at=current_user.createdAt,
    )

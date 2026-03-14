from datetime import datetime
from enum import Enum

from pydantic import BaseModel, EmailStr, Field


class UserRole(str, Enum):
    """บทบาทผู้ใช้ในระบบ"""

    teacher = "teacher"
    admin = "admin"


# ── Requests ──────────────────────────────────────────────────────────────────


class UserCreate(BaseModel):
    """ข้อมูลสำหรับลงทะเบียนผู้ใช้ใหม่"""

    email: EmailStr = Field(..., description="อีเมลสำหรับเข้าสู่ระบบ (ต้องไม่ซ้ำ)")
    password: str = Field(..., min_length=8, description="รหัสผ่าน (อย่างน้อย 8 ตัวอักษร)")
    full_name: str = Field(..., min_length=1, max_length=255, description="ชื่อ-นามสกุล")
    role: UserRole = Field(UserRole.teacher, description="บทบาท: teacher หรือ admin")


class UserLogin(BaseModel):
    """ข้อมูลสำหรับเข้าสู่ระบบ"""

    email: EmailStr = Field(..., description="อีเมลที่ลงทะเบียนไว้")
    password: str = Field(..., description="รหัสผ่าน")


class TokenRefreshRequest(BaseModel):
    """ข้อมูลสำหรับรีเฟรช token"""

    refresh_token: str = Field(..., description="refresh token ที่ได้จากการ login")


# ── Responses ─────────────────────────────────────────────────────────────────


class UserResponse(BaseModel):
    """ข้อมูลโปรไฟล์ผู้ใช้"""

    id: str = Field(..., description="UUID ของผู้ใช้")
    email: str = Field(..., description="อีเมล")
    full_name: str = Field(..., description="ชื่อ-นามสกุล")
    role: UserRole = Field(..., description="บทบาท")
    created_at: datetime = Field(..., description="วันที่สร้างบัญชี")

    model_config = {"from_attributes": True}


class TokenResponse(BaseModel):
    """JWT token pair ที่ได้จากการ login หรือ refresh"""

    access_token: str = Field(
        ..., description="JWT access token (ใช้ใน Authorization header)"
    )
    refresh_token: str = Field(
        ..., description="JWT refresh token (ใช้สำหรับขอ access token ใหม่)"
    )
    token_type: str = Field("bearer", description="ประเภท token (เสมอเป็น 'bearer')")

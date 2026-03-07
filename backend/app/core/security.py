"""
Security utilities — JWT + password hashing.
BE-J responsibility (Sprint 1). Stub provided here for import resolution.
"""
from datetime import datetime, timedelta, timezone
from typing import Optional

from jose import JWTError, jwt
from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

ALGORITHM = "HS256"


# ── Password ──────────────────────────────────────────────────────────────────

def hash_password(plain: str) -> str:
    return pwd_context.hash(plain)


def verify_password(plain: str, hashed: str) -> bool:
    return pwd_context.verify(plain, hashed)


# ── JWT ───────────────────────────────────────────────────────────────────────

def create_access_token(payload: dict, secret_key: str, expires_minutes: int) -> str:
    data = payload.copy()
    data["exp"] = datetime.now(timezone.utc) + timedelta(minutes=expires_minutes)
    data["type"] = "access"
    return jwt.encode(data, secret_key, algorithm=ALGORITHM)


def create_refresh_token(payload: dict, secret_key: str, expires_days: int) -> str:
    data = payload.copy()
    data["exp"] = datetime.now(timezone.utc) + timedelta(days=expires_days)
    data["type"] = "refresh"
    return jwt.encode(data, secret_key, algorithm=ALGORITHM)


def decode_access_token(token: str, secret_key: str) -> Optional[dict]:
    try:
        payload = jwt.decode(token, secret_key, algorithms=[ALGORITHM])
        if payload.get("type") != "access":
            return None
        return payload
    except JWTError:
        return None


def decode_refresh_token(token: str, secret_key: str) -> Optional[dict]:
    try:
        payload = jwt.decode(token, secret_key, algorithms=[ALGORITHM])
        if payload.get("type") != "refresh":
            return None
        return payload
    except JWTError:
        return None

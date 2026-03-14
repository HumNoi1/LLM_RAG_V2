"""Security utilities — JWT + password hashing."""

from datetime import datetime, timedelta, timezone
from typing import Optional, cast

from jose import JWTError, jwt
from passlib.context import CryptContext

from app.config import get_settings

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def _jwt_settings() -> tuple[str, str, int, int]:
    settings = get_settings()
    secret = cast(str, settings.jwt_secret_key)
    if not secret:
        raise RuntimeError("JWT secret key is required")
    return (
        secret,
        settings.jwt_algorithm,
        settings.jwt_access_token_expire_minutes,
        settings.jwt_refresh_token_expire_days,
    )


# ── Password ──────────────────────────────────────────────────────────────────


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


# ── JWT ───────────────────────────────────────────────────────────────────────


def create_access_token(user_id: str, role: str) -> str:
    secret, algorithm, access_minutes, _ = _jwt_settings()
    expire = datetime.now(timezone.utc) + timedelta(minutes=access_minutes)
    payload = {
        "sub": user_id,
        "role": role,
        "type": "access",
        "exp": expire,
    }
    return jwt.encode(payload, secret, algorithm=algorithm)


def create_refresh_token(user_id: str) -> str:
    secret, algorithm, _, refresh_days = _jwt_settings()
    expire = datetime.now(timezone.utc) + timedelta(days=refresh_days)
    payload = {
        "sub": user_id,
        "type": "refresh",
        "exp": expire,
    }
    return jwt.encode(payload, secret, algorithm=algorithm)


def decode_token(token: str) -> Optional[dict]:
    """Decode and verify a JWT token (access or refresh)."""
    secret, algorithm, _, _ = _jwt_settings()
    try:
        payload = jwt.decode(token, secret, algorithms=[algorithm])
        return payload
    except JWTError:
        return None

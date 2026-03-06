"""
Auth Service — register, login, token refresh logic.
BE-J responsibility (Sprint 1).
"""
from app.schemas.auth import LoginRequest, RegisterRequest, TokenResponse


async def register(data: RegisterRequest, supabase) -> dict:
    """Create a new user. Hashes password before storing.
    BE-J: implement in Sprint 1.
    """
    raise NotImplementedError("auth_service.register — BE-J implement in Sprint 1")


async def login(data: LoginRequest, supabase, settings) -> TokenResponse:
    """Verify credentials and return JWT tokens.
    BE-J: implement in Sprint 1.
    """
    raise NotImplementedError("auth_service.login — BE-J implement in Sprint 1")


async def refresh(refresh_token: str, settings) -> TokenResponse:
    """Verify refresh token and issue a new access token.
    BE-J: implement in Sprint 1.
    """
    raise NotImplementedError("auth_service.refresh — BE-J implement in Sprint 1")

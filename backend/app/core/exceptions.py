from fastapi import HTTPException, status


class AppException(Exception):
    """Base application exception."""

    def __init__(self, message: str, status_code: int = 500):
        self.message = message
        self.status_code = status_code
        super().__init__(message)


class NotFoundException(AppException):
    def __init__(self, resource: str, resource_id: str = ""):
        detail = f"{resource} not found"
        if resource_id:
            detail = f"{resource} '{resource_id}' not found"
        super().__init__(detail, status.HTTP_404_NOT_FOUND)


class UnauthorizedException(AppException):
    def __init__(self, message: str = "Not authenticated"):
        super().__init__(message, status.HTTP_401_UNAUTHORIZED)


class ForbiddenException(AppException):
    def __init__(self, message: str = "Insufficient permissions"):
        super().__init__(message, status.HTTP_403_FORBIDDEN)


class ConflictException(AppException):
    def __init__(self, message: str):
        super().__init__(message, status.HTTP_409_CONFLICT)


class BadRequestException(AppException):
    def __init__(self, message: str):
        super().__init__(message, status.HTTP_400_BAD_REQUEST)


class ServiceUnavailableException(AppException):
    def __init__(self, service: str):
        super().__init__(
            f"{service} is currently unavailable",
            status.HTTP_503_SERVICE_UNAVAILABLE,
        )


# ── Grading-specific exceptions ───────────────────────────────────────────────


class GradingInProgressException(AppException):
    def __init__(self, exam_id: str):
        super().__init__(
            f"Grading is already in progress for exam '{exam_id}'",
            status.HTTP_409_CONFLICT,
        )


class PDFParseException(AppException):
    """Sprint 4: เพิ่ม filename attribute สำหรับ logging ที่ดีขึ้น"""

    def __init__(self, filename: str, reason: str = ""):
        self.filename = filename
        msg = f"Failed to parse PDF '{filename}'"
        if reason:
            msg += f": {reason}"
        super().__init__(msg, status.HTTP_422_UNPROCESSABLE_CONTENT)


class EmbeddingException(AppException):
    def __init__(self, message: str):
        super().__init__(f"Embedding error: {message}", 500)


class LLMException(AppException):
    def __init__(self, message: str):
        super().__init__(f"LLM error: {message}", status.HTTP_502_BAD_GATEWAY)


class GroqTimeoutException(LLMException):
    """Sprint 4: เฉพาะเจาะจงสำหรับ Groq API timeout — ให้ client รู้ว่าควร retry"""

    def __init__(self, timeout_seconds: int = 60):
        super().__init__(
            f"Groq API request timed out after {timeout_seconds}s. "
            "Please try again later."
        )
        self.timeout_seconds = timeout_seconds


class GroqRateLimitException(LLMException):
    """Sprint 4: เฉพาะเจาะจงสำหรับ Groq rate limit — ให้ client รู้ว่าต้องรอ"""

    def __init__(self, retry_after: int | None = None):
        msg = "Groq API rate limit exceeded."
        if retry_after:
            msg += f" Retry after {retry_after}s."
        super().__init__(msg)
        self.retry_after = retry_after


def to_http_exception(exc: AppException) -> HTTPException:
    return HTTPException(status_code=exc.status_code, detail=exc.message)

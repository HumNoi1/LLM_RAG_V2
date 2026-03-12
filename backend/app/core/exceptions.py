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
    def __init__(self, filename: str, reason: str = ""):
        msg = f"Failed to parse PDF '{filename}'"
        if reason:
            msg += f": {reason}"
        super().__init__(msg, status.HTTP_422_UNPROCESSABLE_ENTITY)


class EmbeddingException(AppException):
    def __init__(self, message: str):
        super().__init__(f"Embedding error: {message}", 500)


class LLMException(AppException):
    def __init__(self, message: str):
        super().__init__(f"LLM error: {message}", status.HTTP_502_BAD_GATEWAY)


def to_http_exception(exc: AppException) -> HTTPException:
    return HTTPException(status_code=exc.status_code, detail=exc.message)

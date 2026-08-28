"""
Error definitions and exception handling for Aegis Journal.
"""
from http import HTTPStatus
import logging

logger = logging.getLogger("aegis_journal.errors")


class AegisJournalException(Exception):
    """Base exception for Aegis Journal application."""
    def __init__(self, message: str, status_code: int = HTTPStatus.INTERNAL_SERVER_ERROR):
        super().__init__(message)
        self.message = message
        self.status_code = status_code


class AuthenticationError(AegisJournalException):
    """Raised when authentication fails (missing, invalid, expired token)."""
    def __init__(self, message: str = "Invalid or expired authentication token"):
        super().__init__(message, status_code=HTTPStatus.UNAUTHORIZED)


class AuthorizationError(AegisJournalException):
    """Raised when access to a resource is denied (cross-user or forbidden)."""
    def __init__(self, message: str = "Access denied"):
        super().__init__(message, status_code=HTTPStatus.FORBIDDEN)


class NotFoundError(AegisJournalException):
    """Raised when a requested resource is not found."""
    def __init__(self, message: str = "Resource not found"):
        super().__init__(message, status_code=HTTPStatus.NOT_FOUND)


class ValidationError(AegisJournalException):
    """Raised when user input violates validation bounds or schema constraints."""
    def __init__(self, message: str = "Validation failed"):
        super().__init__(message, status_code=HTTPStatus.BAD_REQUEST)


class SecurityError(AegisJournalException):
    """Raised when prompt injection or security policy violation is detected."""
    def __init__(self, message: str = "Security policy violation detected"):
        super().__init__(message, status_code=HTTPStatus.BAD_REQUEST)


class PromptInjectionError(SecurityError):
    """Specific alias for prompt injection detection."""
    def __init__(self, message: str = "Prompt injection pattern detected"):
        super().__init__(message)


class UnauthorizedError(AuthenticationError):
    """Alias for Unauthorized."""
    pass


class RateLimitError(AegisJournalException):
    """Raised when client exceeds rate limit thresholds."""
    def __init__(self, message: str = "Rate limit exceeded. Please try again later."):
        super().__init__(message, status_code=HTTPStatus.TOO_MANY_REQUESTS)


class GeminiServiceError(AegisJournalException):
    """Raised when Gemini API synthesis fails."""
    def __init__(self, message: str = "AI service temporarily unavailable"):
        super().__init__(message, status_code=HTTPStatus.SERVICE_UNAVAILABLE)


async def aegis_exception_handler(request, exc: AegisJournalException):
    """Handles AegisJournalException instances and formats clean, secure JSON responses."""
    from fastapi.responses import JSONResponse
    logger.warning(f"Handled error: {exc.__class__.__name__} - {exc.message}")
    return JSONResponse(
        status_code=exc.status_code,
        content={"error": exc.message, "status_code": exc.status_code},
    )


async def general_exception_handler(request, exc: Exception):
    """Handles uncaught server exceptions without leaking internal stack traces or secrets."""
    from fastapi.responses import JSONResponse
    logger.error(f"Unhandled server exception: {str(exc)}", exc_info=False)
    return JSONResponse(
        status_code=500,
        content={"error": "An internal server error occurred", "status_code": 500},
    )


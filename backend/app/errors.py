"""
Error definitions and exception handling for Aegis Journal.
"""
from fastapi import Request, status
from fastapi.responses import JSONResponse
import logging

logger = logging.getLogger("aegis_journal.errors")


class AegisJournalException(Exception):
    """Base exception for Aegis Journal application."""
    def __init__(self, message: str, status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR):
        super().__init__(message)
        self.message = message
        self.status_code = status_code


class AuthenticationError(AegisJournalException):
    """Raised when authentication fails (missing, invalid, expired token)."""
    def __init__(self, message: str = "Invalid or expired authentication token"):
        super().__init__(message, status_code=status.HTTP_401_UNAUTHORIZED)


class AuthorizationError(AegisJournalException):
    """Raised when access to a resource is denied (cross-user or forbidden)."""
    def __init__(self, message: str = "Access denied"):
        super().__init__(message, status_code=status.HTTP_403_FORBIDDEN)


class NotFoundError(AegisJournalException):
    """Raised when a requested resource is not found."""
    def __init__(self, message: str = "Resource not found"):
        super().__init__(message, status_code=status.HTTP_404_NOT_FOUND)


class ValidationError(AegisJournalException):
    """Raised when user input violates validation bounds or schema constraints."""
    def __init__(self, message: str = "Validation failed"):
        super().__init__(message, status_code=status.HTTP_400_BAD_REQUEST)


class SecurityError(AegisJournalException):
    """Raised when prompt injection or security policy violation is detected."""
    def __init__(self, message: str = "Security policy violation detected"):
        super().__init__(message, status_code=status.HTTP_400_BAD_REQUEST)


class RateLimitError(AegisJournalException):
    """Raised when client exceeds rate limit thresholds."""
    def __init__(self, message: str = "Rate limit exceeded. Please try again later."):
        super().__init__(message, status_code=status.HTTP_429_TOO_MANY_REQUESTS)


class GeminiServiceError(AegisJournalException):
    """Raised when Gemini API synthesis fails."""
    def __init__(self, message: str = "AI service temporarily unavailable"):
        super().__init__(message, status_code=status.HTTP_503_SERVICE_UNAVAILABLE)


async def aegis_exception_handler(request: Request, exc: AegisJournalException) -> JSONResponse:
    """Handles AegisJournalException instances and formats clean, secure JSON responses."""
    logger.warning(f"Handled error: {exc.__class__.__name__} - {exc.message}")
    return JSONResponse(
        status_code=exc.status_code,
        content={"error": exc.message, "status_code": exc.status_code},
    )


async def general_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Handles uncaught server exceptions without leaking internal stack traces or secrets."""
    logger.error(f"Unhandled server exception: {str(exc)}", exc_info=False)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"error": "An internal server error occurred", "status_code": 500},
    )

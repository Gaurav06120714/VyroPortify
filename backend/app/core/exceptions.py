"""Domain exceptions for VyroPortify.

All business-logic errors should raise one of these rather than FastAPI's
HTTPException directly. A global handler in main.py converts them to
structured JSON responses including the correlation_id.

Usage:
    from app.core.exceptions import ResourceNotFound, PlanLimitExceeded

    raise ResourceNotFound("Resume not found")
    raise PlanLimitExceeded("Free plan allows 3 portfolios. Upgrade to Pro.")
"""

from __future__ import annotations

class PortifyBaseException(Exception):
    """Base for all domain exceptions."""

    status_code: int = 500
    error_code: str = "INTERNAL_ERROR"
    message: str = "An unexpected error occurred"

    def __init__(self, message: str | None = None) -> None:
        self.message = message or self.__class__.message
        super().__init__(self.message)

class ResourceNotFound(PortifyBaseException):
    status_code = 404
    error_code = "NOT_FOUND"
    message = "Resource not found"

class ForbiddenError(PortifyBaseException):
    status_code = 403
    error_code = "FORBIDDEN"
    message = "You do not have permission to access this resource"

class PlanLimitExceeded(PortifyBaseException):
    status_code = 403
    error_code = "PLAN_LIMIT_EXCEEDED"
    message = "Your plan limit has been exceeded. Upgrade to continue."

class DomainValidationError(PortifyBaseException):
    status_code = 422
    error_code = "VALIDATION_ERROR"
    message = "Validation failed"

class ExternalServiceError(PortifyBaseException):
    status_code = 503
    error_code = "EXTERNAL_SERVICE_ERROR"
    message = "An external service is temporarily unavailable"

class ConflictError(PortifyBaseException):
    status_code = 409
    error_code = "CONFLICT"
    message = "Resource conflict"

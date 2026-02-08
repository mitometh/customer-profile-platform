from uuid import UUID


class AppError(Exception):
    """Base application error. All domain/application exceptions inherit from this."""

    def __init__(
        self,
        code: str,
        message: str,
        status_code: int = 500,
        details: dict | None = None,
    ) -> None:
        self.code = code
        self.message = message
        self.status_code = status_code
        self.details = details or {}
        super().__init__(message)


class NotFoundError(AppError):
    """Raised when a requested entity does not exist (or is soft-deleted)."""

    def __init__(
        self,
        entity_type: str,
        entity_id: str | UUID,
        details: dict | None = None,
    ) -> None:
        super().__init__(
            code="NOT_FOUND",
            message=f"{entity_type} with id '{entity_id}' not found",
            status_code=404,
            details=details,
        )


class ValidationError(AppError):
    """Raised when input data fails business-rule validation."""

    def __init__(self, message: str, details: dict | None = None) -> None:
        super().__init__(
            code="VALIDATION_ERROR",
            message=message,
            status_code=400,
            details=details,
        )


class UnauthorizedError(AppError):
    """Raised when authentication is missing or invalid."""

    def __init__(
        self,
        message: str = "Authentication required",
        details: dict | None = None,
    ) -> None:
        super().__init__(
            code="UNAUTHORIZED",
            message=message,
            status_code=401,
            details=details,
        )


class ForbiddenError(AppError):
    """Raised when the authenticated user lacks a required permission."""

    def __init__(
        self,
        permission: str,
        details: dict | None = None,
    ) -> None:
        super().__init__(
            code="FORBIDDEN",
            message=f"Permission '{permission}' required",
            status_code=403,
            details=details,
        )


class ConflictError(AppError):
    """Raised when an operation conflicts with existing state (e.g. duplicate)."""

    def __init__(self, message: str, details: dict | None = None) -> None:
        super().__init__(
            code="CONFLICT",
            message=message,
            status_code=409,
            details=details,
        )


class RateLimitedError(AppError):
    """Raised when a client exceeds the allowed request rate."""

    def __init__(
        self,
        message: str = "Rate limit exceeded. Please try again later.",
        details: dict | None = None,
    ) -> None:
        super().__init__(
            code="RATE_LIMITED",
            message=message,
            status_code=429,
            details=details,
        )


class LLMUnavailableError(AppError):
    """Raised when the LLM provider is unreachable or returns an error."""

    def __init__(
        self,
        message: str = "LLM service is temporarily unavailable",
        details: dict | None = None,
    ) -> None:
        super().__init__(
            code="LLM_UNAVAILABLE",
            message=message,
            status_code=503,
            details=details,
        )

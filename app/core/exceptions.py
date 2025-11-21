"""
Custom exception classes for the application.
"""
from typing import Any, Optional


class AppException(Exception):
    """Base exception for application errors."""

    def __init__(
        self,
        message: str,
        status_code: int = 500,
        error_code: Optional[str] = None,
        details: Optional[dict[str, Any]] = None
    ):
        """
        Initialize application exception.

        Args:
            message: Human-readable error message
            status_code: HTTP status code
            error_code: Application-specific error code
            details: Additional error details
        """
        self.message = message
        self.status_code = status_code
        self.error_code = error_code or self.__class__.__name__
        self.details = details or {}
        super().__init__(self.message)


class NotFoundError(AppException):
    """Resource not found error."""

    def __init__(self, resource: str, identifier: Any):
        """
        Initialize not found error.

        Args:
            resource: Resource type (e.g., "User", "Organization")
            identifier: Resource identifier
        """
        super().__init__(
            message=f"{resource} with id '{identifier}' not found",
            status_code=404,
            error_code="NOT_FOUND",
            details={"resource": resource, "identifier": str(identifier)}
        )


class AlreadyExistsError(AppException):
    """Resource already exists error."""

    def __init__(self, resource: str, field: str, value: Any):
        """
        Initialize already exists error.

        Args:
            resource: Resource type
            field: Field name
            value: Field value
        """
        super().__init__(
            message=f"{resource} with {field} '{value}' already exists",
            status_code=409,
            error_code="ALREADY_EXISTS",
            details={"resource": resource, "field": field, "value": str(value)}
        )


class AuthenticationError(AppException):
    """Authentication error."""

    def __init__(self, message: str = "Authentication failed"):
        """
        Initialize authentication error.

        Args:
            message: Error message
        """
        super().__init__(
            message=message,
            status_code=401,
            error_code="AUTHENTICATION_FAILED"
        )


class AuthorizationError(AppException):
    """Authorization error."""

    def __init__(self, message: str = "Insufficient permissions"):
        """
        Initialize authorization error.

        Args:
            message: Error message
        """
        super().__init__(
            message=message,
            status_code=403,
            error_code="AUTHORIZATION_FAILED"
        )


class ValidationError(AppException):
    """Validation error."""

    def __init__(self, message: str, field: Optional[str] = None):
        """
        Initialize validation error.

        Args:
            message: Error message
            field: Field name that failed validation
        """
        details = {"field": field} if field else {}
        super().__init__(
            message=message,
            status_code=400,
            error_code="VALIDATION_ERROR",
            details=details
        )


class BusinessLogicError(AppException):
    """Business logic error."""

    def __init__(self, message: str, error_code: str = "BUSINESS_LOGIC_ERROR"):
        """
        Initialize business logic error.

        Args:
            message: Error message
            error_code: Specific error code
        """
        super().__init__(
            message=message,
            status_code=400,
            error_code=error_code
        )


class ConflictError(AppException):
    """Conflict error (resource state conflict)."""

    def __init__(self, message: str, error_code: str = "CONFLICT"):
        """
        Initialize conflict error.

        Args:
            message: Error message
            error_code: Specific error code
        """
        super().__init__(
            message=message,
            status_code=409,
            error_code=error_code
        )


class DatabaseError(AppException):
    """Database operation error."""

    def __init__(self, message: str = "Database operation failed"):
        """
        Initialize database error.

        Args:
            message: Error message
        """
        super().__init__(
            message=message,
            status_code=500,
            error_code="DATABASE_ERROR"
        )


class RateLimitError(AppException):
    """Rate limit exceeded error."""

    def __init__(self, retry_after: Optional[int] = None):
        """
        Initialize rate limit error.

        Args:
            retry_after: Seconds to wait before retrying
        """
        message = "Rate limit exceeded"
        if retry_after:
            message += f". Retry after {retry_after} seconds"

        super().__init__(
            message=message,
            status_code=429,
            error_code="RATE_LIMIT_EXCEEDED",
            details={"retry_after": retry_after} if retry_after else {}
        )


class InvalidTokenError(AuthenticationError):
    """Invalid or expired token error."""

    def __init__(self, message: str = "Invalid or expired token"):
        """
        Initialize invalid token error.

        Args:
            message: Error message
        """
        super().__init__(message=message)
        self.error_code = "INVALID_TOKEN"


class OrganizationAccessError(AuthorizationError):
    """Organization access denied error."""

    def __init__(self, organization_id: str):
        """
        Initialize organization access error.

        Args:
            organization_id: Organization ID
        """
        super().__init__(
            message=f"Access denied to organization '{organization_id}'"
        )
        self.error_code = "ORGANIZATION_ACCESS_DENIED"
        self.details = {"organization_id": organization_id}


class OwnershipError(AuthorizationError):
    """Resource ownership error."""

    def __init__(self, resource: str, resource_id: str):
        """
        Initialize ownership error.

        Args:
            resource: Resource type
            resource_id: Resource ID
        """
        super().__init__(
            message=f"You don't have permission to modify this {resource.lower()}"
        )
        self.error_code = "OWNERSHIP_ERROR"
        self.details = {"resource": resource, "resource_id": resource_id}

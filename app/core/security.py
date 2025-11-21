"""
Security utilities for password hashing and verification.
"""
from passlib.context import CryptContext
from app.core.config import settings


# Password hashing context with bcrypt
pwd_context = CryptContext(
    schemes=["bcrypt"],
    deprecated="auto",
    bcrypt__rounds=settings.bcrypt_rounds
)


def hash_password(password: str) -> str:
    """
    Hash a password using bcrypt.

    Args:
        password: Plain text password

    Returns:
        Hashed password
    """
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verify a password against a hash.

    Args:
        plain_password: Plain text password
        hashed_password: Hashed password

    Returns:
        True if password matches, False otherwise
    """
    return pwd_context.verify(plain_password, hashed_password)


def validate_password_strength(password: str) -> tuple[bool, str]:
    """
    Validate password strength.

    Requirements:
    - Minimum 8 characters
    - At least one uppercase letter
    - At least one lowercase letter
    - At least one digit

    Args:
        password: Password to validate

    Returns:
        Tuple of (is_valid, error_message)
    """
    if len(password) < 8:
        return False, "Password must be at least 8 characters long"

    if not any(c.isupper() for c in password):
        return False, "Password must contain at least one uppercase letter"

    if not any(c.islower() for c in password):
        return False, "Password must contain at least one lowercase letter"

    if not any(c.isdigit() for c in password):
        return False, "Password must contain at least one digit"

    return True, ""

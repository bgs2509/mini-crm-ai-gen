"""
JWT token creation and validation utilities.
"""
from datetime import datetime, timedelta, UTC
from typing import Optional, Any
from uuid import UUID, uuid4

from jose import JWTError, jwt

from app.core.config import settings
from app.core.exceptions import InvalidTokenError


def create_access_token(user_id: UUID, additional_claims: Optional[dict[str, Any]] = None) -> str:
    """
    Create JWT access token.

    Args:
        user_id: User UUID
        additional_claims: Additional claims to include in token

    Returns:
        Encoded JWT token
    """
    expires_delta = timedelta(minutes=settings.access_token_expire_minutes)
    expire = datetime.now(UTC) + expires_delta

    to_encode = {
        "sub": str(user_id),
        "exp": expire,
        "iat": datetime.now(UTC),
        "jti": str(uuid4()),  # Add unique JWT ID
        "type": "access"
    }

    if additional_claims:
        to_encode.update(additional_claims)

    encoded_jwt = jwt.encode(
        to_encode,
        settings.secret_key,
        algorithm=settings.algorithm
    )
    return encoded_jwt


def create_refresh_token(user_id: UUID) -> str:
    """
    Create JWT refresh token.

    Args:
        user_id: User UUID

    Returns:
        Encoded JWT token
    """
    expires_delta = timedelta(days=settings.refresh_token_expire_days)
    expire = datetime.now(UTC) + expires_delta

    to_encode = {
        "sub": str(user_id),
        "exp": expire,
        "iat": datetime.now(UTC),
        "jti": str(uuid4()),  # Add unique JWT ID
        "type": "refresh"
    }

    encoded_jwt = jwt.encode(
        to_encode,
        settings.secret_key,
        algorithm=settings.algorithm
    )
    return encoded_jwt


def decode_token(token: str) -> dict[str, Any]:
    """
    Decode and validate JWT token.

    Args:
        token: JWT token to decode

    Returns:
        Decoded token payload

    Raises:
        InvalidTokenError: If token is invalid or expired
    """
    try:
        payload = jwt.decode(
            token,
            settings.secret_key,
            algorithms=[settings.algorithm]
        )
        return payload
    except JWTError as e:
        raise InvalidTokenError(f"Could not validate token: {str(e)}")


def get_user_id_from_token(token: str) -> UUID:
    """
    Extract user ID from JWT token.

    Args:
        token: JWT token

    Returns:
        User UUID

    Raises:
        InvalidTokenError: If token is invalid or doesn't contain user ID
    """
    payload = decode_token(token)
    user_id_str: Optional[str] = payload.get("sub")

    if user_id_str is None:
        raise InvalidTokenError("Token does not contain user ID")

    try:
        return UUID(user_id_str)
    except ValueError:
        raise InvalidTokenError("Invalid user ID format in token")


def verify_token_type(token: str, expected_type: str) -> bool:
    """
    Verify that token is of expected type (access or refresh).

    Args:
        token: JWT token
        expected_type: Expected token type ("access" or "refresh")

    Returns:
        True if token type matches, False otherwise

    Raises:
        InvalidTokenError: If token is invalid
    """
    payload = decode_token(token)
    token_type = payload.get("type")
    return token_type == expected_type


def create_token_pair(user_id: UUID) -> dict[str, str]:
    """
    Create both access and refresh tokens.

    Args:
        user_id: User UUID

    Returns:
        Dictionary with access_token and refresh_token
    """
    return {
        "access_token": create_access_token(user_id),
        "refresh_token": create_refresh_token(user_id),
        "token_type": "bearer"
    }

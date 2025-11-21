"""
Unit tests for JWT token functionality.
"""
import time
from uuid import uuid4

import pytest

from app.core.jwt import (
    create_access_token,
    create_refresh_token,
    decode_token,
    get_user_id_from_token,
)
from app.core.exceptions import AuthenticationError


class TestTokenCreation:
    """Test JWT token creation."""

    def test_create_access_token(self):
        """Test access token creation."""
        user_id = uuid4()
        token = create_access_token(user_id)

        assert token is not None
        assert isinstance(token, str)
        assert len(token) > 0

    def test_create_refresh_token(self):
        """Test refresh token creation."""
        user_id = uuid4()
        token = create_refresh_token(user_id)

        assert token is not None
        assert isinstance(token, str)
        assert len(token) > 0

    def test_tokens_are_different(self):
        """Test that access and refresh tokens are different."""
        user_id = uuid4()
        access_token = create_access_token(user_id)
        refresh_token = create_refresh_token(user_id)

        assert access_token != refresh_token


class TestTokenDecoding:
    """Test JWT token decoding."""

    def test_decode_access_token(self):
        """Test decoding valid access token."""
        user_id = uuid4()
        token = create_access_token(user_id)

        payload = decode_token(token)

        assert payload is not None
        assert "sub" in payload
        assert payload["sub"] == str(user_id)
        assert payload["type"] == "access"
        assert "exp" in payload

    def test_decode_refresh_token(self):
        """Test decoding valid refresh token."""
        user_id = uuid4()
        token = create_refresh_token(user_id)

        payload = decode_token(token)

        assert payload is not None
        assert "sub" in payload
        assert payload["sub"] == str(user_id)
        assert payload["type"] == "refresh"
        assert "exp" in payload

    def test_decode_invalid_token(self):
        """Test decoding invalid token raises error."""
        with pytest.raises(AuthenticationError, match="Could not validate token"):
            decode_token("invalid.token.here")

    def test_decode_empty_token(self):
        """Test decoding empty token raises error."""
        with pytest.raises(AuthenticationError):
            decode_token("")

    def test_decode_malformed_token(self):
        """Test decoding malformed token raises error."""
        with pytest.raises(AuthenticationError):
            decode_token("not-a-jwt-token")


class TestGetUserIdFromToken:
    """Test extracting user ID from token."""

    def test_get_user_id_from_access_token(self):
        """Test extracting user ID from access token."""
        user_id = uuid4()
        token = create_access_token(user_id)

        extracted_id = get_user_id_from_token(token)

        assert extracted_id == user_id

    def test_get_user_id_from_refresh_token(self):
        """Test extracting user ID from refresh token."""
        user_id = uuid4()
        token = create_refresh_token(user_id)

        extracted_id = get_user_id_from_token(token)

        assert extracted_id == user_id

    def test_get_user_id_from_invalid_token(self):
        """Test extracting user ID from invalid token raises error."""
        with pytest.raises(AuthenticationError):
            get_user_id_from_token("invalid.token.here")

    def test_get_user_id_preserves_uuid_type(self):
        """Test that extracted user ID is UUID type."""
        from uuid import UUID

        user_id = uuid4()
        token = create_access_token(user_id)
        extracted_id = get_user_id_from_token(token)

        assert isinstance(extracted_id, UUID)


class TestTokenExpiration:
    """Test token expiration behavior."""

    def test_access_token_expiration_set(self):
        """Test that access token has expiration set."""
        user_id = uuid4()
        token = create_access_token(user_id)
        payload = decode_token(token)

        assert "exp" in payload
        # Access token should expire in future
        assert payload["exp"] > time.time()

    def test_refresh_token_expiration_set(self):
        """Test that refresh token has expiration set."""
        user_id = uuid4()
        token = create_refresh_token(user_id)
        payload = decode_token(token)

        assert "exp" in payload
        # Refresh token should expire in future
        assert payload["exp"] > time.time()

    def test_refresh_token_longer_expiration(self):
        """Test that refresh token expires later than access token."""
        user_id = uuid4()
        access_token = create_access_token(user_id)
        refresh_token = create_refresh_token(user_id)

        access_payload = decode_token(access_token)
        refresh_payload = decode_token(refresh_token)

        # Refresh token should have later expiration
        assert refresh_payload["exp"] > access_payload["exp"]


class TestTokenType:
    """Test token type validation."""

    def test_access_token_has_correct_type(self):
        """Test that access token has type 'access'."""
        user_id = uuid4()
        token = create_access_token(user_id)
        payload = decode_token(token)

        assert payload["type"] == "access"

    def test_refresh_token_has_correct_type(self):
        """Test that refresh token has type 'refresh'."""
        user_id = uuid4()
        token = create_refresh_token(user_id)
        payload = decode_token(token)

        assert payload["type"] == "refresh"

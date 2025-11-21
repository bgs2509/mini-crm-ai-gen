"""
Integration tests for authentication API endpoints.
"""
import pytest
from httpx import AsyncClient


class TestRegisterEndpoint:
    """Test user registration endpoint."""

    @pytest.mark.asyncio
    async def test_register_success(self, client: AsyncClient):
        """Test successful user registration."""
        data = {
            "email": "newuser@example.com",
            "password": "SecurePass123",
            "name": "New User",
            "organization_name": "New Org"
        }

        response = await client.post("/api/v1/auth/register", json=data)

        assert response.status_code == 201
        result = response.json()

        assert "user" in result
        assert result["user"]["email"] == data["email"]
        assert result["user"]["name"] == data["name"]

        assert "organization" in result
        assert result["organization"]["name"] == data["organization_name"]

        assert "tokens" in result
        assert "access_token" in result["tokens"]
        assert "refresh_token" in result["tokens"]

    @pytest.mark.asyncio
    async def test_register_duplicate_email(self, client: AsyncClient, test_user):
        """Test registration with duplicate email fails."""
        data = {
            "email": test_user.email,
            "password": "SecurePass123",
            "name": "Duplicate User",
            "organization_name": "Duplicate Org"
        }

        response = await client.post("/api/v1/auth/register", json=data)

        assert response.status_code == 409
        assert "already exists" in response.json()["message"].lower()

    @pytest.mark.asyncio
    async def test_register_weak_password(self, client: AsyncClient):
        """Test registration with weak password fails."""
        data = {
            "email": "weakpass@example.com",
            "password": "weak",
            "name": "Weak Pass User",
            "organization_name": "Test Org"
        }

        response = await client.post("/api/v1/auth/register", json=data)

        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_register_invalid_email(self, client: AsyncClient):
        """Test registration with invalid email fails."""
        data = {
            "email": "invalid-email",
            "password": "SecurePass123",
            "name": "Invalid Email User",
            "organization_name": "Test Org"
        }

        response = await client.post("/api/v1/auth/register", json=data)

        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_register_missing_fields(self, client: AsyncClient):
        """Test registration with missing fields fails."""
        data = {
            "email": "incomplete@example.com",
            "password": "SecurePass123"
            # Missing name and organization_name
        }

        response = await client.post("/api/v1/auth/register", json=data)

        assert response.status_code == 422


class TestLoginEndpoint:
    """Test user login endpoint."""

    @pytest.mark.asyncio
    async def test_login_success(self, client: AsyncClient, test_user, test_organization, test_membership):
        """Test successful login."""
        data = {
            "email": test_user.email,
            "password": "TestPass123"
        }

        response = await client.post("/api/v1/auth/login", json=data)

        assert response.status_code == 200
        result = response.json()

        assert "user" in result
        assert result["user"]["email"] == test_user.email

        assert "organizations" in result
        assert len(result["organizations"]) > 0

        assert "tokens" in result
        assert "access_token" in result["tokens"]
        assert "refresh_token" in result["tokens"]

    @pytest.mark.asyncio
    async def test_login_wrong_password(self, client: AsyncClient, test_user):
        """Test login with wrong password fails."""
        data = {
            "email": test_user.email,
            "password": "WrongPassword123"
        }

        response = await client.post("/api/v1/auth/login", json=data)

        assert response.status_code == 401
        assert "invalid" in response.json()["message"].lower()

    @pytest.mark.asyncio
    async def test_login_nonexistent_user(self, client: AsyncClient):
        """Test login with nonexistent user fails."""
        data = {
            "email": "nonexistent@example.com",
            "password": "SomePass123"
        }

        response = await client.post("/api/v1/auth/login", json=data)

        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_login_invalid_email_format(self, client: AsyncClient):
        """Test login with invalid email format fails."""
        data = {
            "email": "not-an-email",
            "password": "SomePass123"
        }

        response = await client.post("/api/v1/auth/login", json=data)

        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_login_empty_password(self, client: AsyncClient, test_user):
        """Test login with empty password fails."""
        data = {
            "email": test_user.email,
            "password": ""
        }

        response = await client.post("/api/v1/auth/login", json=data)

        assert response.status_code == 422


class TestRefreshEndpoint:
    """Test token refresh endpoint."""

    @pytest.mark.asyncio
    async def test_refresh_token_success(self, client: AsyncClient, test_user, test_organization, test_membership):
        """Test successful token refresh."""
        # First login to get refresh token
        login_data = {
            "email": test_user.email,
            "password": "TestPass123"
        }

        login_response = await client.post("/api/v1/auth/login", json=login_data)
        refresh_token = login_response.json()["tokens"]["refresh_token"]

        # Use refresh token
        refresh_data = {
            "refresh_token": refresh_token
        }

        response = await client.post("/api/v1/auth/refresh", json=refresh_data)

        assert response.status_code == 200
        result = response.json()

        assert "access_token" in result
        assert "refresh_token" in result
        assert result["access_token"] != login_response.json()["tokens"]["access_token"]

    @pytest.mark.asyncio
    async def test_refresh_invalid_token(self, client: AsyncClient):
        """Test refresh with invalid token fails."""
        data = {
            "refresh_token": "invalid.token.here"
        }

        response = await client.post("/api/v1/auth/refresh", json=data)

        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_refresh_access_token_instead(self, client: AsyncClient, test_user, test_organization, test_membership):
        """Test refresh with access token instead of refresh token fails."""
        # Login to get access token
        login_data = {
            "email": test_user.email,
            "password": "TestPass123"
        }

        login_response = await client.post("/api/v1/auth/login", json=login_data)
        access_token = login_response.json()["tokens"]["access_token"]

        # Try to refresh with access token
        refresh_data = {
            "refresh_token": access_token
        }

        response = await client.post("/api/v1/auth/refresh", json=refresh_data)

        assert response.status_code == 401

"""
Integration tests for contacts API endpoints.
"""
from uuid import uuid4

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.contact import Contact


class TestListContactsEndpoint:
    """Test listing contacts endpoint."""

    @pytest.mark.asyncio
    async def test_list_contacts_empty(self, client: AsyncClient, auth_headers):
        """Test listing contacts when none exist."""
        response = await client.get("/api/v1/contacts", headers=auth_headers)

        assert response.status_code == 200
        result = response.json()

        assert "items" in result
        assert len(result["items"]) == 0
        assert result["total"] == 0

    @pytest.mark.asyncio
    async def test_list_contacts_with_data(
        self,
        client: AsyncClient,
        auth_headers,
        db_session: AsyncSession,
        test_organization,
        test_user
    ):
        """Test listing contacts with existing data."""
        # Create test contacts
        contact1 = Contact(
            id=uuid4(),
            organization_id=test_organization.id,
            owner_id=test_user.id,
            name="John Doe",
            email="john@example.com"
        )
        contact2 = Contact(
            id=uuid4(),
            organization_id=test_organization.id,
            owner_id=test_user.id,
            name="Jane Smith",
            email="jane@example.com"
        )

        db_session.add(contact1)
        db_session.add(contact2)
        await db_session.commit()

        response = await client.get("/api/v1/contacts", headers=auth_headers)

        assert response.status_code == 200
        result = response.json()

        assert len(result["items"]) == 2
        assert result["total"] == 2

    @pytest.mark.asyncio
    async def test_list_contacts_with_search(
        self,
        client: AsyncClient,
        auth_headers,
        db_session: AsyncSession,
        test_organization,
        test_user
    ):
        """Test searching contacts."""
        # Create test contacts
        contact1 = Contact(
            id=uuid4(),
            organization_id=test_organization.id,
            owner_id=test_user.id,
            name="John Doe",
            email="john@example.com"
        )
        contact2 = Contact(
            id=uuid4(),
            organization_id=test_organization.id,
            owner_id=test_user.id,
            name="Jane Smith",
            email="jane@example.com"
        )

        db_session.add(contact1)
        db_session.add(contact2)
        await db_session.commit()

        response = await client.get(
            "/api/v1/contacts?search=John",
            headers=auth_headers
        )

        assert response.status_code == 200
        result = response.json()

        assert len(result["items"]) == 1
        assert result["items"][0]["name"] == "John Doe"

    @pytest.mark.asyncio
    async def test_list_contacts_pagination(
        self,
        client: AsyncClient,
        auth_headers,
        db_session: AsyncSession,
        test_organization,
        test_user
    ):
        """Test contact pagination."""
        # Create multiple contacts
        for i in range(15):
            contact = Contact(
                id=uuid4(),
                organization_id=test_organization.id,
                owner_id=test_user.id,
                name=f"Contact {i}",
                email=f"contact{i}@example.com"
            )
            db_session.add(contact)

        await db_session.commit()

        # First page
        response = await client.get(
            "/api/v1/contacts?limit=10",
            headers=auth_headers
        )

        assert response.status_code == 200
        result = response.json()

        assert len(result["items"]) == 10
        assert result["total"] == 15

        # Second page
        response = await client.get(
            "/api/v1/contacts?skip=10&limit=10",
            headers=auth_headers
        )

        assert response.status_code == 200
        result = response.json()

        assert len(result["items"]) == 5

    @pytest.mark.asyncio
    async def test_list_contacts_no_auth(self, client: AsyncClient):
        """Test listing contacts without authentication fails."""
        response = await client.get("/api/v1/contacts")

        assert response.status_code == 401


class TestCreateContactEndpoint:
    """Test creating contact endpoint."""

    @pytest.mark.asyncio
    async def test_create_contact_success(self, client: AsyncClient, auth_headers):
        """Test successful contact creation."""
        data = {
            "name": "New Contact",
            "email": "new@example.com",
            "phone": "+1234567890"
        }

        response = await client.post("/api/v1/contacts", headers=auth_headers, json=data)

        assert response.status_code == 201
        result = response.json()

        assert result["name"] == data["name"]
        assert result["email"] == data["email"]
        assert result["phone"] == data["phone"]
        assert "id" in result

    @pytest.mark.asyncio
    async def test_create_contact_minimal_data(self, client: AsyncClient, auth_headers):
        """Test creating contact with minimal required data."""
        data = {
            "name": "Minimal Contact",
            "email": "minimal@example.com"
        }

        response = await client.post("/api/v1/contacts", headers=auth_headers, json=data)

        assert response.status_code == 201
        result = response.json()

        assert result["name"] == data["name"]
        assert result["email"] == data["email"]
        assert result["phone"] is None

    @pytest.mark.asyncio
    async def test_create_contact_invalid_email(self, client: AsyncClient, auth_headers):
        """Test creating contact with invalid email fails."""
        data = {
            "name": "Invalid Email Contact",
            "email": "not-an-email"
        }

        response = await client.post("/api/v1/contacts", headers=auth_headers, json=data)

        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_create_contact_no_auth(self, client: AsyncClient):
        """Test creating contact without authentication fails."""
        data = {
            "name": "Unauthorized Contact"
        }

        response = await client.post("/api/v1/contacts", json=data)

        assert response.status_code == 401


class TestGetContactEndpoint:
    """Test getting single contact endpoint."""

    @pytest.mark.asyncio
    async def test_get_contact_success(
        self,
        client: AsyncClient,
        auth_headers,
        db_session: AsyncSession,
        test_organization,
        test_user
    ):
        """Test getting contact by ID."""
        # Create test contact
        contact = Contact(
            id=uuid4(),
            organization_id=test_organization.id,
            owner_id=test_user.id,
            name="Test Contact",
            email="test@example.com"
        )

        db_session.add(contact)
        await db_session.commit()

        response = await client.get(f"/api/v1/contacts/{contact.id}", headers=auth_headers)

        assert response.status_code == 200
        result = response.json()

        assert result["id"] == str(contact.id)
        assert result["name"] == contact.name
        assert result["email"] == contact.email

    @pytest.mark.asyncio
    async def test_get_contact_not_found(self, client: AsyncClient, auth_headers):
        """Test getting nonexistent contact."""
        fake_id = uuid4()

        response = await client.get(f"/api/v1/contacts/{fake_id}", headers=auth_headers)

        assert response.status_code == 404


class TestUpdateContactEndpoint:
    """Test updating contact endpoint."""

    @pytest.mark.asyncio
    async def test_update_contact_success(
        self,
        client: AsyncClient,
        auth_headers,
        db_session: AsyncSession,
        test_organization,
        test_user
    ):
        """Test successful contact update."""
        # Create test contact
        contact = Contact(
            id=uuid4(),
            organization_id=test_organization.id,
            owner_id=test_user.id,
            name="Original Name",
            email="original@example.com"
        )

        db_session.add(contact)
        await db_session.commit()

        # Update contact
        update_data = {
            "name": "Updated Name",
            "email": "updated@example.com"
        }

        response = await client.put(
            f"/api/v1/contacts/{contact.id}",
            headers=auth_headers,
            json=update_data
        )

        assert response.status_code == 200
        result = response.json()

        assert result["name"] == update_data["name"]
        assert result["email"] == update_data["email"]

    @pytest.mark.asyncio
    async def test_update_contact_not_found(self, client: AsyncClient, auth_headers):
        """Test updating nonexistent contact."""
        fake_id = uuid4()
        update_data = {
            "name": "Updated Name"
        }

        response = await client.put(
            f"/api/v1/contacts/{fake_id}",
            headers=auth_headers,
            json=update_data
        )

        assert response.status_code == 404


class TestDeleteContactEndpoint:
    """Test deleting contact endpoint."""

    @pytest.mark.asyncio
    async def test_delete_contact_success(
        self,
        client: AsyncClient,
        auth_headers,
        db_session: AsyncSession,
        test_organization,
        test_user
    ):
        """Test successful contact deletion."""
        # Create test contact
        contact = Contact(
            id=uuid4(),
            organization_id=test_organization.id,
            owner_id=test_user.id,
            name="To Delete",
            email="delete@example.com"
        )

        db_session.add(contact)
        await db_session.commit()

        response = await client.delete(f"/api/v1/contacts/{contact.id}", headers=auth_headers)

        assert response.status_code == 204

        # Verify deletion
        get_response = await client.get(f"/api/v1/contacts/{contact.id}", headers=auth_headers)
        assert get_response.status_code == 404

    @pytest.mark.asyncio
    async def test_delete_contact_not_found(self, client: AsyncClient, auth_headers):
        """Test deleting nonexistent contact."""
        fake_id = uuid4()

        response = await client.delete(f"/api/v1/contacts/{fake_id}", headers=auth_headers)

        assert response.status_code == 404

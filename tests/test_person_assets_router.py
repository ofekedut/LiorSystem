import uuid
import pytest
import pytest_asyncio
from datetime import datetime
from httpx import AsyncClient
from fastapi import status

from server.api import app
from server.database.database import get_connection


class TestPersonAssetsRouter:
    """Test suite for person assets endpoints"""

    @pytest_asyncio.fixture
    async def created_asset_type_id(self):
        """Create an asset type for testing and return its ID"""
        conn = await get_connection()
        try:
            # Try to get existing asset type or create a new one
            asset_type_name = "Test Asset Type"
            asset_type_value = "test-asset-type"
            
            existing = await conn.fetchrow(
                """SELECT id FROM asset_types WHERE value = $1""",
                asset_type_value
            )
            
            if existing:
                return existing['id']
            else:
                # Create a new asset type
                result = await conn.fetchrow(
                    """INSERT INTO asset_types (id, name, value) 
                       VALUES (gen_random_uuid(), $1, $2) 
                       RETURNING id""",
                    asset_type_name, asset_type_value
                )
                return result['id']
        finally:
            await conn.close()

    @pytest_asyncio.fixture
    async def created_person_id(self, async_client: AsyncClient, created_case_id: uuid.UUID):
        """Create a person for testing and return its ID"""
        # Create a new person for the case
        # Get a role_id first
        conn = await get_connection()
        try:
            # Try to get a role_id for 'primary'
            role_result = await conn.fetchrow(
                """SELECT id FROM person_roles WHERE value = 'primary'"""
            )
            role_id = role_result['id'] if role_result else None
        finally:
            await conn.close()
            
        if not role_id:
            # If role doesn't exist, create it
            conn = await get_connection()
            try:
                role_result = await conn.fetchrow(
                    """INSERT INTO person_roles (id, name, value) 
                       VALUES (gen_random_uuid(), 'Primary', 'primary') 
                       RETURNING id"""
                )
                role_id = role_result['id']
            finally:
                await conn.close()
        
        payload = {
            "case_id": str(created_case_id),
            "first_name": "Test",
            "last_name": "Person",
            "id_number": str(uuid.uuid4())[:8],
            "gender": "male",
            "role_id": str(role_id),  # Use role_id instead of role
            "birth_date": "1990-01-01",
            "phone": "+123456789",
            "email": "test@example.com",
            "status": "active"
        }
        
        response = await async_client.post(f"/cases/{created_case_id}/persons", json=payload)
        assert response.status_code == 201
        return response.json()["id"]

    @pytest_asyncio.fixture
    def person_asset_payload(self, created_person_id: uuid.UUID, created_asset_type_id: uuid.UUID):
        """Create a payload for a new person asset"""
        return {
            "person_id": str(created_person_id),
            "asset_type_id": str(created_asset_type_id),
            "description": "Test asset description"
        }

    @pytest.mark.asyncio
    async def test_create_person_asset(
            self, async_client: AsyncClient, created_person_id: uuid.UUID, person_asset_payload: dict
        ):
        """Test creating a new person asset"""
        response = await async_client.post(
            f"/persons/{created_person_id}/assets", 
            json=person_asset_payload
        )
        
        assert response.status_code == 201
        data = response.json()
        assert "id" in data
        assert data["person_id"] == person_asset_payload["person_id"]
        assert data["asset_type_id"] == person_asset_payload["asset_type_id"]
        assert data["description"] == person_asset_payload["description"]
        assert "created_at" in data
        assert "updated_at" in data

    @pytest.mark.asyncio
    async def test_get_person_assets(
            self, async_client: AsyncClient, created_person_id: uuid.UUID, person_asset_payload: dict
        ):
        """Test retrieving all assets for a person"""
        # First create an asset
        create_response = await async_client.post(
            f"/persons/{created_person_id}/assets", 
            json=person_asset_payload
        )
        assert create_response.status_code == 201
        
        # Now get all assets for this person
        response = await async_client.get(f"/persons/{created_person_id}/assets")
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) >= 1
        
        # Check that our created asset is in the list
        created_asset = create_response.json()
        matching_assets = [asset for asset in data if asset["id"] == created_asset["id"]]
        assert len(matching_assets) == 1
        assert matching_assets[0]["description"] == person_asset_payload["description"]

    @pytest.mark.asyncio
    async def test_get_person_asset_by_id(
            self, async_client: AsyncClient, created_person_id: uuid.UUID, person_asset_payload: dict
        ):
        """Test retrieving a specific asset by ID"""
        # First create an asset
        create_response = await async_client.post(
            f"/persons/{created_person_id}/assets", 
            json=person_asset_payload
        )
        assert create_response.status_code == 201
        created_asset = create_response.json()
        
        # Now get this specific asset
        response = await async_client.get(
            f"/persons/{created_person_id}/assets/{created_asset['id']}"
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == created_asset["id"]
        assert data["person_id"] == person_asset_payload["person_id"]
        assert data["description"] == person_asset_payload["description"]

    @pytest.mark.asyncio
    async def test_get_person_asset_invalid_id(
            self, async_client: AsyncClient, created_person_id: uuid.UUID
        ):
        """Test retrieving an asset with an invalid ID"""
        invalid_id = str(uuid.uuid4())
        response = await async_client.get(
            f"/persons/{created_person_id}/assets/{invalid_id}"
        )
        
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_update_person_asset(
            self, async_client: AsyncClient, created_person_id: uuid.UUID, person_asset_payload: dict, created_asset_type_id: uuid.UUID
        ):
        """Test updating an existing person asset"""
        # First create an asset
        create_response = await async_client.post(
            f"/persons/{created_person_id}/assets", 
            json=person_asset_payload
        )
        assert create_response.status_code == 201
        created_asset = create_response.json()
        
        # Update payload
        update_payload = {
            "description": "Updated asset description"
        }
        
        # Now update the asset
        response = await async_client.put(
            f"/persons/{created_person_id}/assets/{created_asset['id']}", 
            json=update_payload
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == created_asset["id"]
        assert data["description"] == update_payload["description"]
        assert data["asset_type_id"] == person_asset_payload["asset_type_id"]

    @pytest.mark.asyncio
    async def test_delete_person_asset(
            self, async_client: AsyncClient, created_person_id: uuid.UUID, person_asset_payload: dict
        ):
        """Test deleting a person asset"""
        # First create an asset
        create_response = await async_client.post(
            f"/persons/{created_person_id}/assets", 
            json=person_asset_payload
        )
        assert create_response.status_code == 201
        created_asset = create_response.json()
        
        # Now delete the asset
        response = await async_client.delete(
            f"/persons/{created_person_id}/assets/{created_asset['id']}"
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        
        # Verify it's deleted by trying to get it
        get_response = await async_client.get(
            f"/persons/{created_person_id}/assets/{created_asset['id']}"
        )
        assert get_response.status_code == 404

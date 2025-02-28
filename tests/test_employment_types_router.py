# tests/test_employment_types_router.py
import pytest
from httpx import AsyncClient
import uuid
from server.routers.employment_types_router import EmploymentTypeInCreate, EmploymentTypeInUpdate


@pytest.mark.asyncio
class TestEmploymentTypesRouter:
    """Tests for the employment_types_router endpoints."""

    async def test_create_employment_type(self, async_client: AsyncClient, admin_token):
        """Test creating a new employment type."""
        headers = {"Authorization": f"Bearer {admin_token}"}
        new_type = {
            "name": "Test Employment Type",
            "value": "test_employment_type"
        }
        
        # Create the employment type
        response = await async_client.post("/employment_types/", json=new_type, headers=headers)
        assert response.status_code == 201, response.text
        
        data = response.json()
        assert data['name'] == new_type['name']
        assert data['value'] == new_type['value']
        assert 'id' in data
        
        # Clean up - delete the created employment type
        delete_response = await async_client.delete(f"/employment_types/{data['id']}", headers=headers)
        assert delete_response.status_code == 204

    async def test_read_employment_types(self, async_client: AsyncClient, admin_token):
        """Test listing all employment types."""
        headers = {"Authorization": f"Bearer {admin_token}"}
        
        # Create a test employment type first
        new_type = {
            "name": "Test Employment Type List",
            "value": "test_employment_type_list"
        }
        create_response = await async_client.post("/employment_types/", json=new_type, headers=headers)
        assert create_response.status_code == 201
        created_type = create_response.json()
        
        # Get all employment types
        response = await async_client.get("/employment_types/", headers=headers)
        assert response.status_code == 200
        
        data = response.json()
        assert isinstance(data, list)
        assert len(data) > 0
        
        # Verify our created type is in the list
        found = False
        for item in data:
            if item['id'] == created_type['id']:
                found = True
                assert item['name'] == new_type['name']
                assert item['value'] == new_type['value']
                break
        
        assert found, "Created employment type not found in the list"
        
        # Clean up
        delete_response = await async_client.delete(f"/employment_types/{created_type['id']}", headers=headers)
        assert delete_response.status_code == 204

    async def test_read_employment_type_by_id(self, async_client: AsyncClient, admin_token):
        """Test getting a specific employment type by ID."""
        headers = {"Authorization": f"Bearer {admin_token}"}
        
        # Create a test employment type first
        new_type = {
            "name": "Test Employment Type Get",
            "value": "test_employment_type_get"
        }
        create_response = await async_client.post("/employment_types/", json=new_type, headers=headers)
        assert create_response.status_code == 201
        created_type = create_response.json()
        
        # Get the employment type by ID
        response = await async_client.get(f"/employment_types/{created_type['id']}", headers=headers)
        assert response.status_code == 200
        
        data = response.json()
        assert data['id'] == created_type['id']
        assert data['name'] == new_type['name']
        assert data['value'] == new_type['value']
        
        # Clean up
        delete_response = await async_client.delete(f"/employment_types/{created_type['id']}", headers=headers)
        assert delete_response.status_code == 204

    async def test_read_employment_type_not_found(self, async_client: AsyncClient, admin_token):
        """Test getting a non-existent employment type."""
        headers = {"Authorization": f"Bearer {admin_token}"}
        
        # Generate a random UUID that doesn't exist
        random_id = str(uuid.uuid4())
        
        # Try to get a non-existent employment type
        response = await async_client.get(f"/employment_types/{random_id}", headers=headers)
        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()

    async def test_update_employment_type(self, async_client: AsyncClient, admin_token):
        """Test updating an employment type."""
        headers = {"Authorization": f"Bearer {admin_token}"}
        
        # Create a test employment type first
        new_type = {
            "name": "Test Employment Type Update",
            "value": "test_employment_type_update"
        }
        create_response = await async_client.post("/employment_types/", json=new_type, headers=headers)
        assert create_response.status_code == 201
        created_type = create_response.json()
        
        # Update the employment type
        update_data = {
            "name": "Updated Employment Type",
            "value": "updated_employment_type"
        }
        response = await async_client.put(f"/employment_types/{created_type['id']}", json=update_data, headers=headers)
        assert response.status_code == 200
        
        updated_type = response.json()
        assert updated_type['id'] == created_type['id']
        assert updated_type['name'] == update_data['name']
        assert updated_type['value'] == update_data['value']
        
        # Verify the update by getting the employment type
        get_response = await async_client.get(f"/employment_types/{created_type['id']}", headers=headers)
        assert get_response.status_code == 200
        get_data = get_response.json()
        assert get_data['name'] == update_data['name']
        assert get_data['value'] == update_data['value']
        
        # Clean up
        delete_response = await async_client.delete(f"/employment_types/{created_type['id']}", headers=headers)
        assert delete_response.status_code == 204

    async def test_update_employment_type_partial(self, async_client: AsyncClient, admin_token):
        """Test partially updating an employment type."""
        headers = {"Authorization": f"Bearer {admin_token}"}
        
        # Create a test employment type first
        new_type = {
            "name": "Test Employment Type Partial Update",
            "value": "test_employment_type_partial_update"
        }
        create_response = await async_client.post("/employment_types/", json=new_type, headers=headers)
        assert create_response.status_code == 201
        created_type = create_response.json()
        
        # Update only the name
        update_data = {
            "name": "Partially Updated Employment Type"
        }
        response = await async_client.put(f"/employment_types/{created_type['id']}", json=update_data, headers=headers)
        assert response.status_code == 200
        
        updated_type = response.json()
        assert updated_type['id'] == created_type['id']
        assert updated_type['name'] == update_data['name']
        assert updated_type['value'] == new_type['value']  # Value should remain unchanged
        
        # Clean up
        delete_response = await async_client.delete(f"/employment_types/{created_type['id']}", headers=headers)
        assert delete_response.status_code == 204

    async def test_update_employment_type_not_found(self, async_client: AsyncClient, admin_token):
        """Test updating a non-existent employment type."""
        headers = {"Authorization": f"Bearer {admin_token}"}
        
        # Generate a random UUID that doesn't exist
        random_id = str(uuid.uuid4())
        
        # Try to update a non-existent employment type
        update_data = {
            "name": "Non-existent Employment Type",
            "value": "non_existent_employment_type"
        }
        response = await async_client.put(f"/employment_types/{random_id}", json=update_data, headers=headers)
        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()

    async def test_delete_employment_type(self, async_client: AsyncClient, admin_token):
        """Test deleting an employment type."""
        headers = {"Authorization": f"Bearer {admin_token}"}
        
        # Create a test employment type first
        new_type = {
            "name": "Test Employment Type Delete",
            "value": "test_employment_type_delete"
        }
        create_response = await async_client.post("/employment_types/", json=new_type, headers=headers)
        assert create_response.status_code == 201
        created_type = create_response.json()
        
        # Delete the employment type
        delete_response = await async_client.delete(f"/employment_types/{created_type['id']}", headers=headers)
        assert delete_response.status_code == 204
        
        # Verify it's deleted by trying to get it
        get_response = await async_client.get(f"/employment_types/{created_type['id']}", headers=headers)
        assert get_response.status_code == 404

    async def test_delete_employment_type_not_found(self, async_client: AsyncClient, admin_token):
        """Test deleting a non-existent employment type."""
        headers = {"Authorization": f"Bearer {admin_token}"}
        
        # Generate a random UUID that doesn't exist
        random_id = str(uuid.uuid4())
        
        # Try to delete a non-existent employment type
        response = await async_client.delete(f"/employment_types/{random_id}", headers=headers)
        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()

# tests/test_bank_account_type_router.py
import pytest
from httpx import AsyncClient
import uuid
from server.routers.bank_account_type_router import BankAccountTypeInCreate, BankAccountTypeInUpdate


@pytest.mark.asyncio
class TestBankAccountTypeRouter:
    """Tests for the bank_account_type_router endpoints."""

    async def test_create_bank_account_type(self, async_client: AsyncClient, admin_token):
        """Test creating a new bank account type."""
        headers = {"Authorization": f"Bearer {admin_token}"}
        new_type = {
            "name": "Test Bank Account Type",
            "value": "test_bank_account_type"
        }
        
        # Create the bank account type
        response = await async_client.post("/bank_account_type/", json=new_type, headers=headers)
        assert response.status_code == 201, response.text
        
        data = response.json()
        assert data['name'] == new_type['name']
        assert data['value'] == new_type['value']
        assert 'id' in data
        
        # Clean up - delete the created bank account type
        delete_response = await async_client.delete(f"/bank_account_type/{data['id']}", headers=headers)
        assert delete_response.status_code == 204

    async def test_read_bank_account_types(self, async_client: AsyncClient, admin_token):
        """Test listing all bank account types."""
        headers = {"Authorization": f"Bearer {admin_token}"}
        
        # Create a test bank account type first
        new_type = {
            "name": "Test Bank Account Type List",
            "value": "test_bank_account_type_list"
        }
        create_response = await async_client.post("/bank_account_type/", json=new_type, headers=headers)
        assert create_response.status_code == 201
        created_type = create_response.json()
        
        # Get all bank account types
        response = await async_client.get("/bank_account_type/", headers=headers)
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
        
        assert found, "Created bank account type not found in the list"
        
        # Clean up
        delete_response = await async_client.delete(f"/bank_account_type/{created_type['id']}", headers=headers)
        assert delete_response.status_code == 204

    async def test_read_bank_account_type_by_id(self, async_client: AsyncClient, admin_token):
        """Test getting a specific bank account type by ID."""
        headers = {"Authorization": f"Bearer {admin_token}"}
        
        # Create a test bank account type first
        new_type = {
            "name": "Test Bank Account Type Get",
            "value": "test_bank_account_type_get"
        }
        create_response = await async_client.post("/bank_account_type/", json=new_type, headers=headers)
        assert create_response.status_code == 201
        created_type = create_response.json()
        
        # Get the bank account type by ID
        response = await async_client.get(f"/bank_account_type/{created_type['id']}", headers=headers)
        assert response.status_code == 200
        
        data = response.json()
        assert data['id'] == created_type['id']
        assert data['name'] == new_type['name']
        assert data['value'] == new_type['value']
        
        # Clean up
        delete_response = await async_client.delete(f"/bank_account_type/{created_type['id']}", headers=headers)
        assert delete_response.status_code == 204

    async def test_read_bank_account_type_not_found(self, async_client: AsyncClient, admin_token):
        """Test getting a non-existent bank account type."""
        headers = {"Authorization": f"Bearer {admin_token}"}
        
        # Generate a random UUID that doesn't exist
        random_id = str(uuid.uuid4())
        
        # Try to get a non-existent bank account type
        response = await async_client.get(f"/bank_account_type/{random_id}", headers=headers)
        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()

    async def test_update_bank_account_type(self, async_client: AsyncClient, admin_token):
        """Test updating a bank account type."""
        headers = {"Authorization": f"Bearer {admin_token}"}
        
        # Create a test bank account type first
        new_type = {
            "name": "Test Bank Account Type Update",
            "value": "test_bank_account_type_update"
        }
        create_response = await async_client.post("/bank_account_type/", json=new_type, headers=headers)
        assert create_response.status_code == 201
        created_type = create_response.json()
        
        # Update the bank account type
        update_data = {
            "name": "Updated Bank Account Type",
            "value": "updated_bank_account_type"
        }
        response = await async_client.put(f"/bank_account_type/{created_type['id']}", json=update_data, headers=headers)
        assert response.status_code == 200
        
        updated_type = response.json()
        assert updated_type['id'] == created_type['id']
        assert updated_type['name'] == update_data['name']
        assert updated_type['value'] == update_data['value']
        
        # Verify the update by getting the bank account type
        get_response = await async_client.get(f"/bank_account_type/{created_type['id']}", headers=headers)
        assert get_response.status_code == 200
        get_data = get_response.json()
        assert get_data['name'] == update_data['name']
        assert get_data['value'] == update_data['value']
        
        # Clean up
        delete_response = await async_client.delete(f"/bank_account_type/{created_type['id']}", headers=headers)
        assert delete_response.status_code == 204

    async def test_update_bank_account_type_partial(self, async_client: AsyncClient, admin_token):
        """Test partially updating a bank account type."""
        headers = {"Authorization": f"Bearer {admin_token}"}
        
        # Create a test bank account type first
        new_type = {
            "name": "Test Bank Account Type Partial Update",
            "value": "test_bank_account_type_partial_update"
        }
        create_response = await async_client.post("/bank_account_type/", json=new_type, headers=headers)
        assert create_response.status_code == 201
        created_type = create_response.json()
        
        # Update only the name
        update_data = {
            "name": "Partially Updated Bank Account Type"
        }
        response = await async_client.put(f"/bank_account_type/{created_type['id']}", json=update_data, headers=headers)
        assert response.status_code == 200
        
        updated_type = response.json()
        assert updated_type['id'] == created_type['id']
        assert updated_type['name'] == update_data['name']
        assert updated_type['value'] == new_type['value']  # Value should remain unchanged
        
        # Clean up
        delete_response = await async_client.delete(f"/bank_account_type/{created_type['id']}", headers=headers)
        assert delete_response.status_code == 204

    async def test_update_bank_account_type_not_found(self, async_client: AsyncClient, admin_token):
        """Test updating a non-existent bank account type."""
        headers = {"Authorization": f"Bearer {admin_token}"}
        
        # Generate a random UUID that doesn't exist
        random_id = str(uuid.uuid4())
        
        # Try to update a non-existent bank account type
        update_data = {
            "name": "Non-existent Bank Account Type",
            "value": "non_existent_bank_account_type"
        }
        response = await async_client.put(f"/bank_account_type/{random_id}", json=update_data, headers=headers)
        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()

    async def test_delete_bank_account_type(self, async_client: AsyncClient, admin_token):
        """Test deleting a bank account type."""
        headers = {"Authorization": f"Bearer {admin_token}"}
        
        # Create a test bank account type first
        new_type = {
            "name": "Test Bank Account Type Delete",
            "value": "test_bank_account_type_delete"
        }
        create_response = await async_client.post("/bank_account_type/", json=new_type, headers=headers)
        assert create_response.status_code == 201
        created_type = create_response.json()
        
        # Delete the bank account type
        delete_response = await async_client.delete(f"/bank_account_type/{created_type['id']}", headers=headers)
        assert delete_response.status_code == 204
        
        # Verify it's deleted by trying to get it
        get_response = await async_client.get(f"/bank_account_type/{created_type['id']}", headers=headers)
        assert get_response.status_code == 404

    async def test_delete_bank_account_type_not_found(self, async_client: AsyncClient, admin_token):
        """Test deleting a non-existent bank account type."""
        headers = {"Authorization": f"Bearer {admin_token}"}
        
        # Generate a random UUID that doesn't exist
        random_id = str(uuid.uuid4())
        
        # Try to delete a non-existent bank account type
        response = await async_client.delete(f"/bank_account_type/{random_id}", headers=headers)
        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()

# tests/test_person_roles_router.py
import pytest
from httpx import AsyncClient
import uuid
from server.database.person_roles_database import PersonRoleInCreate, PersonRoleInUpdate


@pytest.mark.asyncio
class TestPersonRolesRouter:
    """Tests for the person_roles_router endpoints."""

    async def test_create_person_role(self, async_client: AsyncClient, admin_token):
        """Test creating a new person role."""
        headers = {"Authorization": f"Bearer {admin_token}"}
        new_role = PersonRoleInCreate(
            name="Test Person Role",
            value="test_person_role"
        )
        
        # Create the person role
        response = await async_client.post("/person_roles/", json=new_role.model_dump(), headers=headers)
        assert response.status_code == 201, response.text
        
        data = response.json()
        assert data['name'] == new_role.name
        assert data['value'] == new_role.value
        assert 'id' in data
        
        # Clean up - delete the created person role
        delete_response = await async_client.delete(f"/person_roles/{data['id']}", headers=headers)
        assert delete_response.status_code == 204

    async def test_read_person_roles(self, async_client: AsyncClient, admin_token):
        """Test listing all person roles."""
        headers = {"Authorization": f"Bearer {admin_token}"}
        
        # Create a test person role first
        new_role = PersonRoleInCreate(
            name="Test Person Role List",
            value="test_person_role_list"
        )
        create_response = await async_client.post("/person_roles/", json=new_role.model_dump(), headers=headers)
        assert create_response.status_code == 201
        created_role = create_response.json()
        
        # Get all person roles
        response = await async_client.get("/person_roles/", headers=headers)
        assert response.status_code == 200
        
        data = response.json()
        assert isinstance(data, list)
        assert len(data) > 0
        
        # Verify our created role is in the list
        found = False
        for item in data:
            if item['id'] == created_role['id']:
                found = True
                assert item['name'] == new_role.name
                assert item['value'] == new_role.value
                break
        
        assert found, "Created person role not found in the list"
        
        # Clean up
        delete_response = await async_client.delete(f"/person_roles/{created_role['id']}", headers=headers)
        assert delete_response.status_code == 204

    async def test_read_person_role_by_id(self, async_client: AsyncClient, admin_token):
        """Test getting a specific person role by ID."""
        headers = {"Authorization": f"Bearer {admin_token}"}
        
        # Create a test person role first
        new_role = PersonRoleInCreate(
            name="Test Person Role Get",
            value="test_person_role_get"
        )
        create_response = await async_client.post("/person_roles/", json=new_role.model_dump(), headers=headers)
        assert create_response.status_code == 201
        created_role = create_response.json()
        
        # Get the person role by ID
        response = await async_client.get(f"/person_roles/{created_role['id']}", headers=headers)
        assert response.status_code == 200
        
        data = response.json()
        assert data['id'] == created_role['id']
        assert data['name'] == new_role.name
        assert data['value'] == new_role.value
        
        # Clean up
        delete_response = await async_client.delete(f"/person_roles/{created_role['id']}", headers=headers)
        assert delete_response.status_code == 204
        
    async def test_read_person_role_by_value(self, async_client: AsyncClient, admin_token):
        """Test getting a specific person role by value."""
        headers = {"Authorization": f"Bearer {admin_token}"}
        
        # Create a test person role first
        new_role = PersonRoleInCreate(
            name="Test Person Role Value",
            value="test_person_role_value"
        )
        create_response = await async_client.post("/person_roles/", json=new_role.model_dump(), headers=headers)
        assert create_response.status_code == 201
        created_role = create_response.json()
        
        # Get the person role by value
        response = await async_client.get(f"/person_roles/value/test_person_role_value", headers=headers)
        assert response.status_code == 200
        
        data = response.json()
        assert data['id'] == created_role['id']
        assert data['name'] == new_role.name
        assert data['value'] == new_role.value
        
        # Clean up
        delete_response = await async_client.delete(f"/person_roles/{created_role['id']}", headers=headers)
        assert delete_response.status_code == 204

    async def test_read_person_role_not_found(self, async_client: AsyncClient, admin_token):
        """Test getting a non-existent person role."""
        headers = {"Authorization": f"Bearer {admin_token}"}
        
        # Generate a random UUID that doesn't exist
        random_id = str(uuid.uuid4())
        
        response = await async_client.get(f"/person_roles/{random_id}", headers=headers)
        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()
        
    async def test_read_person_role_by_value_not_found(self, async_client: AsyncClient, admin_token):
        """Test getting a non-existent person role by value."""
        headers = {"Authorization": f"Bearer {admin_token}"}
        
        # Try to get a role with a value that doesn't exist
        response = await async_client.get("/person_roles/value/non_existent_value", headers=headers)
        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()

    async def test_update_person_role(self, async_client: AsyncClient, admin_token):
        """Test updating a person role."""
        headers = {"Authorization": f"Bearer {admin_token}"}
        
        # Create a test person role first
        new_role = PersonRoleInCreate(
            name="Test Person Role Update",
            value="test_person_role_update"
        )
        create_response = await async_client.post("/person_roles/", json=new_role.model_dump(), headers=headers)
        assert create_response.status_code == 201
        created_role = create_response.json()
        
        # Update data
        update_data = PersonRoleInUpdate(
            name="Updated Person Role",
            value="updated_person_role"
        )
        
        # Update the person role
        response = await async_client.put(f"/person_roles/{created_role['id']}", json=update_data.model_dump(), headers=headers)
        assert response.status_code == 200
        
        data = response.json()
        assert data['id'] == created_role['id']
        assert data['name'] == update_data.name
        assert data['value'] == update_data.value
        
        # Verify the update persisted by getting the person role
        get_response = await async_client.get(f"/person_roles/{created_role['id']}", headers=headers)
        assert get_response.status_code == 200
        get_data = get_response.json()
        assert get_data['name'] == update_data.name
        assert get_data['value'] == update_data.value
        
        # Clean up
        delete_response = await async_client.delete(f"/person_roles/{created_role['id']}", headers=headers)
        assert delete_response.status_code == 204

    async def test_update_person_role_partial(self, async_client: AsyncClient, admin_token):
        """Test partially updating a person role."""
        headers = {"Authorization": f"Bearer {admin_token}"}
        
        # Create a test person role first
        new_role = PersonRoleInCreate(
            name="Test Person Role Partial Update",
            value="test_person_role_partial_update"
        )
        create_response = await async_client.post("/person_roles/", json=new_role.model_dump(), headers=headers)
        assert create_response.status_code == 201
        created_role = create_response.json()
        
        # Update only the name
        update_data = PersonRoleInUpdate(
            name="Partially Updated Person Role"
        )
        
        # Update the person role
        response = await async_client.put(f"/person_roles/{created_role['id']}", json=update_data.model_dump(), headers=headers)
        assert response.status_code == 200
        
        data = response.json()
        assert data['id'] == created_role['id']
        assert data['name'] == update_data.name
        assert data['value'] == new_role.value  # Value should remain unchanged
        
        # Update only the value
        update_data = PersonRoleInUpdate(
            value="partially_updated_person_role"
        )
        
        response = await async_client.put(f"/person_roles/{created_role['id']}", json=update_data.model_dump(), headers=headers)
        assert response.status_code == 200
        
        data = response.json()
        assert data['id'] == created_role['id']
        assert data['name'] == "Partially Updated Person Role"  # Name should remain the updated value
        assert data['value'] == update_data.value
        
        # Clean up
        delete_response = await async_client.delete(f"/person_roles/{created_role['id']}", headers=headers)
        assert delete_response.status_code == 204

    async def test_update_person_role_not_found(self, async_client: AsyncClient, admin_token):
        """Test updating a non-existent person role."""
        headers = {"Authorization": f"Bearer {admin_token}"}
        
        # Generate a random UUID that doesn't exist
        random_id = str(uuid.uuid4())
        
        update_data = PersonRoleInUpdate(
            name="Non-existent Person Role",
            value="non_existent_person_role"
        )
        
        response = await async_client.put(f"/person_roles/{random_id}", json=update_data.model_dump(), headers=headers)
        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()

    async def test_delete_person_role(self, async_client: AsyncClient, admin_token):
        """Test deleting a person role."""
        headers = {"Authorization": f"Bearer {admin_token}"}
        
        # Create a test person role first
        new_role = PersonRoleInCreate(
            name="Test Person Role Delete",
            value="test_person_role_delete"
        )
        create_response = await async_client.post("/person_roles/", json=new_role.model_dump(), headers=headers)
        assert create_response.status_code == 201
        created_role = create_response.json()
        
        # Delete the person role
        delete_response = await async_client.delete(f"/person_roles/{created_role['id']}", headers=headers)
        assert delete_response.status_code == 204
        
        # Verify the person role was deleted
        get_response = await async_client.get(f"/person_roles/{created_role['id']}", headers=headers)
        assert get_response.status_code == 404

    async def test_delete_person_role_not_found(self, async_client: AsyncClient, admin_token):
        """Test deleting a non-existent person role."""
        headers = {"Authorization": f"Bearer {admin_token}"}
        
        # Generate a random UUID that doesn't exist
        random_id = str(uuid.uuid4())
        
        response = await async_client.delete(f"/person_roles/{random_id}", headers=headers)
        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()

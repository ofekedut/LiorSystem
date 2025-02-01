# tests/test_user_router.py
import pytest
from httpx import AsyncClient
import uuid

from server.database.users_database import delete_user, get_user_by_email


@pytest.mark.asyncio
class TestUserRouter:
    """Tests for the user_router endpoints."""

    @pytest.mark.parametrize(
        "role, status_code",
        [
            ("ADMIN", 200),
            ("USER", 403),
        ],
    )
    async def test_list_users(self, async_client: AsyncClient, admin_token, user_token, role, status_code):
        """Test listing users with different roles."""
        headers = {"Authorization": f"Bearer {admin_token}"} if role == "ADMIN" else {"Authorization": f"Bearer {user_token}"}
        response = await async_client.get("/api/v1/users", headers=headers)
        assert response.status_code == status_code
        if response.status_code == 200:
            assert isinstance(response.json()['items'], list)

    async def test_create_new_user_as_admin(self, async_client: AsyncClient, admin_token):
        """Test creating a new user as an admin."""
        headers = {"Authorization": f"Bearer {admin_token}"}
        new_user = {
            "email": "ofekedut86@gmail.com",
            "password": "123456qQ!",
            "first_name": "Test",
            "last_name": "CreateUser",
        }
        found = await get_user_by_email(new_user["email"])
        if found:
            await delete_user(found.id)
        response = await async_client.post("/api/v1/users", json=new_user, headers=headers)
        found = await get_user_by_email(new_user["email"])
        if found:
            await delete_user(found.id)
        assert response.status_code == 201, response.text
        data = response.json()
        assert data['email'] == new_user['email']
        assert "password_hash" not in data

    async def test_create_new_user_as_regular_user(self, async_client: AsyncClient, user_token):
        """Test that regular users cannot create new users."""
        headers = {"Authorization": f"Bearer {user_token}"}
        new_user = {
            "email": "anotheruser",
            "password": "123456qQ!",
            "first_name": "Tes2t",
            "last_name": "Creat2eUser",
            # Add other required fields
        }
        response = await async_client.post("/api/v1/users", json=new_user, headers=headers)
        assert response.status_code == 403

    async def test_get_user_profile_self(self, async_client: AsyncClient, regular_user, user_token):
        """Test retrieving own user profile."""
        headers = {"Authorization": f"Bearer {user_token}"}
        response = await async_client.get(f"/api/v1/users/{regular_user.id}", headers=headers)
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == str(regular_user.id)
        assert data["email"] == regular_user.email

    async def test_get_user_profile_admin(self, async_client: AsyncClient, admin_token, regular_user):
        """Test admin retrieving another user's profile."""
        headers = {"Authorization": f"Bearer {admin_token}"}
        response = await async_client.get(f"/api/v1/users/{regular_user.id}", headers=headers)
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == str(regular_user.id)
        assert data["email"] == regular_user.email

    async def test_get_user_profile_unauthorized(self, async_client: AsyncClient, user_token):
        """Test retrieving another user's profile as a regular user."""
        headers = {"Authorization": f"Bearer {user_token}"}
        fake_user_id = uuid.uuid4()
        response = await async_client.get(f"/api/v1/users/{fake_user_id}", headers=headers)
        assert response.status_code == 403

    async def test_update_user_profile_self(self, async_client: AsyncClient, regular_user, user_token):
        """Test updating own profile."""
        headers = {"Authorization": f"Bearer {user_token}"}
        update_data = {
            "last_name": "Kaki",
        }
        response = await async_client.put(f"/api/v1/users/{regular_user.id}", json=update_data, headers=headers)
        assert response.status_code == 200
        data = response.json()
        assert data["last_name"] == update_data["last_name"]

    async def test_update_user_profile_admin(self, async_client: AsyncClient, admin_token, regular_user):
        """Test admin updating another user's profile."""
        headers = {"Authorization": f"Bearer {admin_token}"}
        update_data = {
            "last_name": "Kaki",
        }
        response = await async_client.put(f"/api/v1/users/{regular_user.id}", json=update_data, headers=headers)
        assert response.status_code == 200
        data = response.json()
        assert data["last_name"] == update_data["last_name"]

    async def test_delete_user_as_admin(self, async_client: AsyncClient, admin_token, regular_user):
        """Test admin deleting a user."""
        headers = {"Authorization": f"Bearer {admin_token}"}
        response = await async_client.delete(f"/api/v1/users/{regular_user.id}", headers=headers)
        assert response.status_code == 204

        # Verify deletion
        response = await async_client.get(f"/api/v1/users/{regular_user.id}", headers=headers)
        assert response.status_code == 404

    async def test_delete_user_as_regular_user(self, async_client: AsyncClient, user_token):
        """Test that regular users cannot delete users."""
        headers = {"Authorization": f"Bearer {user_token}"}
        fake_user_id = uuid.uuid4()
        response = await async_client.delete(f"/api/v1/users/{fake_user_id}", headers=headers)
        assert response.status_code == 403


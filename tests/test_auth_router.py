import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
class TestAuthRouter:

    async def test_login_success(self, async_client: AsyncClient, admin_user):
        """Test successful login."""
        login_data = {
            "username": admin_user.email,
            "password": "123456qQ!",  # Ensure this matches the password in fixture
        }
        response = await async_client.post("/api/v1/auth/token", data=login_data)
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert "refresh_token" in data
        assert data["token_type"] == "bearer"

    async def test_login_invalid_credentials(self, async_client: AsyncClient):
        """Test login with invalid credentials."""
        login_data = {
            "username": "nonexistentuser",
            "password": "wrongpass",
        }
        response = await async_client.post("/api/v1/auth/token", data=login_data)
        assert response.status_code == 403 or response.status_code == 401

    async def test_login_account_locked(self, async_client: AsyncClient, regular_user):
        login_data = {
            "username": regular_user.email,
            "password": "wrongpass",
        }
        for _ in range(5):  # Assuming 5 attempts lock the account
            await async_client.post("/api/v1/auth/token", data=login_data)

        response = await async_client.post("/api/v1/auth/token", data=login_data)
        assert response.status_code == 403
        assert response.json()["detail"] == "Account temporarily locked"

    async def test_refresh_token_success(self, async_client: AsyncClient, admin_user):
        login_data = {
            "username": admin_user.email,
            "password": "123456qQ!",
        }
        response = await async_client.post("/api/v1/auth/token", data=login_data)
        assert response.status_code == 200
        refresh_token = response.json()["refresh_token"]

        # Now, refresh the access token
        response = await async_client.post("/api/v1/auth/refresh", json={"refresh_token": refresh_token})
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"

    async def test_refresh_token_invalid(self, async_client: AsyncClient):
        """Test refreshing access token with an invalid refresh token."""
        response = await async_client.post("/api/v1/auth/refresh", json={"refresh_token": "invalidtoken"})
        assert response.status_code == 401
        assert response.json()["detail"] == "Invalid refresh token"

    async def test_logout_success(self, async_client: AsyncClient, admin_user):
        """Test successful logout."""
        # Login to get refresh token
        login_data = {
            "username": admin_user.email,
            "password": "123456qQ!",
        }
        response = await async_client.post("/api/v1/auth/token", data=login_data)
        assert response.status_code == 200
        refresh_token = response.json()["refresh_token"]

        # Logout
        response = await async_client.post("/api/v1/auth/logout", json={"refresh_token": refresh_token})
        assert response.status_code == 200
        assert response.json()["message"] == "Successfully logged out"

        # Attempt to refresh token after logout
        response = await async_client.post("/api/v1/auth/refresh", json={"refresh_token": refresh_token})
        assert response.status_code == 401
        assert response.json()["detail"] == "Token has been revoked"

    async def test_logout_invalid_token(self, async_client: AsyncClient):
        """Test logout with an invalid token."""
        response = await async_client.post("/api/v1/auth/logout", json={"refresh_token": "invalidtoken"})
        assert response.status_code == 401
        assert response.json()["detail"] == "Invalid token"


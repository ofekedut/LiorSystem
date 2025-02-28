# tests/test_fin_org_router.py
import pytest
from httpx import AsyncClient
import uuid
from server.routers.fin_org_router import FinOrgCreate, FinOrgUpdate

@pytest.mark.asyncio
class TestFinOrgRouter:
    async def test_create_fin_org_type(self, async_client: AsyncClient, admin_token):
        headers = {"Authorization": f"Bearer {admin_token}"}
        new_type = {"name": "Bank", "value": "bank"}
        response = await async_client.post("/fin_org_types/", json=new_type, headers=headers)
        assert response.status_code == 201
        data = response.json()
        assert data['name'] == "Bank"
        
        # Cleanup
        await async_client.delete(f"/fin_org_types/{data['id']}", headers=headers)

    async def test_get_fin_org_types(self, async_client: AsyncClient, admin_token):
        headers = {"Authorization": f"Bearer {admin_token}"}
        # Create test data
        create_res = await async_client.post("/fin_org_types/", json={"name": "Credit Union", "value": "credit_union"}, headers=headers)
        
        # Test list
        response = await async_client.get("/fin_org_types/", headers=headers)
        assert response.status_code == 200
        assert len(response.json()) > 0
        
        # Cleanup
        await async_client.delete(f"/fin_org_types/{create_res.json()['id']}", headers=headers)

    async def test_update_fin_org_type(self, async_client: AsyncClient, admin_token):
        headers = {"Authorization": f"Bearer {admin_token}"}
        # Setup
        create_res = await async_client.post("/fin_org_types/", json={"name": "Initial", "value": "initial"}, headers=headers)
        created_id = create_res.json()['id']
        
        # Update
        update_data = {"name": "Updated", "value": "updated"}
        response = await async_client.put(f"/fin_org_types/{created_id}", json=update_data, headers=headers)
        assert response.status_code == 200
        assert response.json()['name'] == "Updated"
        
        # Cleanup
        await async_client.delete(f"/fin_org_types/{created_id}", headers=headers)

    async def test_delete_fin_org_type(self, async_client: AsyncClient, admin_token):
        headers = {"Authorization": f"Bearer {admin_token}"}
        # Setup
        create_res = await async_client.post("/fin_org_types/", json={"name": "To Delete", "value": "to_delete"}, headers=headers)
        created_id = create_res.json()['id']
        
        # Delete
        delete_res = await async_client.delete(f"/fin_org_types/{created_id}", headers=headers)
        assert delete_res.status_code == 204
        
        # Verify deletion
        get_res = await async_client.get(f"/fin_org_types/{created_id}", headers=headers)
        assert get_res.status_code == 404

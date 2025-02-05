# finorg_router_test.py
import uuid
import pytest
import pytest_asyncio
from datetime import datetime
from uuid import UUID
from httpx import AsyncClient
from fastapi import status

# Import the main FastAPI app that includes the finorg router.
# Adjust the import below to match your project structure.
from server.api import app

# -----------------------------------------------------------------------------
# Fixtures for Async Client and Payloads
# -----------------------------------------------------------------------------
@pytest_asyncio.fixture
async def async_client():
    async with AsyncClient(app=app, base_url="http://testserver") as client:
        yield client

@pytest.fixture
def new_finorg_payload():
    return {
        "name": "Router Test FinOrg " + str(uuid.uuid4())[:8],
        "type": "bank",
        "settings": {"currency": "USD", "region": "NA"}
    }

@pytest_asyncio.fixture
async def created_finorg(async_client: AsyncClient, new_finorg_payload: dict):
    resp = await async_client.post("/fin_orgs", json=new_finorg_payload)
    assert resp.status_code == status.HTTP_201_CREATED
    return resp.json()

@pytest.fixture
def new_contact_payload(created_finorg):
    unique_fragment = str(uuid.uuid4())[:8]
    return {
        "fin_org_id": created_finorg["id"],
        "full_name": "Test Contact " + unique_fragment,
        "email": f"contact{unique_fragment}@example.com",
        "phone": "+15551234567"
    }

@pytest_asyncio.fixture
async def created_contact(async_client: AsyncClient, created_finorg, new_contact_payload: dict):
    url = f"/fin_orgs/{created_finorg['id']}/contacts"
    resp = await async_client.post(url, json=new_contact_payload)
    assert resp.status_code == status.HTTP_201_CREATED
    return resp.json()

# -----------------------------------------------------------------------------
# Tests for FinOrg Router Endpoints
# -----------------------------------------------------------------------------
@pytest.mark.asyncio
class TestFinOrgRouter:
    async def test_create_finorg(self, async_client: AsyncClient, new_finorg_payload: dict):
        resp = await async_client.post("/fin_orgs", json=new_finorg_payload)
        assert resp.status_code == status.HTTP_201_CREATED
        data = resp.json()
        assert "id" in data
        assert data["name"] == new_finorg_payload["name"]

    async def test_list_fin_orgs(self, async_client: AsyncClient, created_finorg):
        resp = await async_client.get("/fin_orgs")
        assert resp.status_code == status.HTTP_200_OK
        orgs = resp.json()
        assert isinstance(orgs, list)
        assert any(org["id"] == created_finorg["id"] for org in orgs)

    async def test_get_finorg(self, async_client: AsyncClient, created_finorg):
        org_id = created_finorg["id"]
        resp = await async_client.get(f"/fin_orgs/{org_id}")
        assert resp.status_code == status.HTTP_200_OK
        data = resp.json()
        assert data["id"] == org_id

    async def test_update_finorg(self, async_client: AsyncClient, created_finorg):
        org_id = created_finorg["id"]
        update_payload = {"name": "Updated FinOrg Name", "settings": {"currency": "EUR"}}
        resp = await async_client.put(f"/fin_orgs/{org_id}", json=update_payload)
        assert resp.status_code == status.HTTP_200_OK
        updated = resp.json()
        assert updated["name"] == "Updated FinOrg Name"
        assert updated["settings"]["currency"] == "EUR"

    async def test_delete_finorg(self, async_client: AsyncClient, created_finorg):
        org_id = created_finorg["id"]
        del_resp = await async_client.delete(f"/fin_orgs/{org_id}")
        assert del_resp.status_code == status.HTTP_204_NO_CONTENT
        get_resp = await async_client.get(f"/fin_orgs/{org_id}")
        assert get_resp.status_code == status.HTTP_404_NOT_FOUND

# -----------------------------------------------------------------------------
# Tests for FinOrgContact Router Endpoints
# -----------------------------------------------------------------------------
@pytest.mark.asyncio
class TestFinOrgContactRouter:
    async def test_create_contact(self, async_client: AsyncClient, created_finorg, new_contact_payload: dict):
        url = f"/fin_orgs/{created_finorg['id']}/contacts"
        resp = await async_client.post(url, json=new_contact_payload)
        assert resp.status_code == status.HTTP_201_CREATED
        data = resp.json()
        assert data["id"] is not None
        assert data["fin_org_id"] == created_finorg["id"]

    async def test_list_contacts(self, async_client: AsyncClient, created_finorg, created_contact):
        url = f"/fin_orgs/{created_finorg['id']}/contacts"
        resp = await async_client.get(url)
        assert resp.status_code == status.HTTP_200_OK
        contacts = resp.json()
        assert isinstance(contacts, list)
        assert any(contact["id"] == created_contact["id"] for contact in contacts)

    async def test_get_contact(self, async_client: AsyncClient, created_contact):
        contact_id = created_contact["id"]
        resp = await async_client.get(f"/fin_contacts/{contact_id}")
        assert resp.status_code == status.HTTP_200_OK
        data = resp.json()
        assert data["id"] == contact_id

    async def test_update_contact(self, async_client: AsyncClient, created_contact):
        contact_id = created_contact["id"]
        update_payload = {"full_name": "Updated Contact Name", "phone": "+15559876543"}
        resp = await async_client.put(f"/fin_contacts/{contact_id}", json=update_payload)
        assert resp.status_code == status.HTTP_200_OK
        updated = resp.json()
        assert updated["full_name"] == "Updated Contact Name"
        assert updated["phone"] == "+15559876543"

    async def test_delete_contact(self, async_client: AsyncClient, created_contact):
        contact_id = created_contact["id"]
        del_resp = await async_client.delete(f"/fin_contacts/{contact_id}")
        assert del_resp.status_code == status.HTTP_204_NO_CONTENT
        get_resp = await async_client.get(f"/fin_contacts/{contact_id}")
        assert get_resp.status_code == status.HTTP_404_NOT_FOUND

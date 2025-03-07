import uuid
import pytest
import pytest_asyncio

from database.d_migrations import FIN_ORG_TYPES_BANK_UID
from server.database.finorg_database import (
    create_fin_org,
    get_fin_org,
    list_fin_orgs,
    update_fin_org,
    delete_fin_org,
    FinOrgCreate,
    FinOrgUpdate,
    create_fin_org_contact,
    get_fin_org_contact,
    list_fin_org_contacts,
    update_fin_org_contact,
    delete_fin_org_contact,
    FinOrgContactCreate,
    FinOrgContactUpdate, create_fin_org_type, FinOrgTypeCreate,
)


@pytest_asyncio.fixture
async def created_fin_org_type():
    return await create_fin_org_type(FinOrgTypeCreate(
        name='bank',
        value='bank',
    ))


@pytest_asyncio.fixture
async def new_finorg_payload(created_fin_org_type: any) -> dict:
    return {
        "name": "Test Financial Org " + str(uuid.uuid4())[:8],
        "type_id": created_fin_org_type.id,
        "settings": {"currency": "USD", "region": "North America"},
    }


@pytest_asyncio.fixture
async def created_finorg(new_finorg_payload: dict):
    org_in = FinOrgCreate(**new_finorg_payload)
    org = await create_fin_org(org_in)
    assert org.id is not None
    return org


# -----------------------------------------------------------------------------
# Fixtures for FinOrgContact
# -----------------------------------------------------------------------------
@pytest_asyncio.fixture
async def new_finorg_contact_payload(created_finorg: any) -> dict:
    # Ensure uniqueness for email by appending a uuid fragment.
    unique_fragment = str(uuid.uuid4())[:8]
    return {
        "fin_org_id": str(created_finorg.id),
        "full_name": "John Doe " + unique_fragment,
        "email": f"john{unique_fragment}@example.com",
        "phone": "+15551234567",
    }


@pytest_asyncio.fixture
async def created_finorg_contact(created_finorg: any, new_finorg_contact_payload: dict):
    contact_in = FinOrgContactCreate(**new_finorg_contact_payload)
    contact = await create_fin_org_contact(contact_in)
    assert contact.id is not None
    return contact


# -----------------------------------------------------------------------------
# Tests for FinOrg CRUD Operations
# -----------------------------------------------------------------------------
@pytest.mark.asyncio
class TestFinOrgDatabase:
    async def test_create_finorg(self, new_finorg_payload: dict):
        org_in = FinOrgCreate(**new_finorg_payload)
        org = await create_fin_org(org_in)
        assert org.id is not None
        assert org.name == new_finorg_payload["name"]

    async def test_get_finorg(self, created_finorg):
        org = await get_fin_org(created_finorg.id)
        assert org is not None
        assert org.id == created_finorg.id

    async def test_list_finorgs(self, created_finorg):
        orgs = await list_fin_orgs()
        assert isinstance(orgs, list)
        assert any(str(org.id) == str(created_finorg.id) for org in orgs)

    async def test_update_finorg(self, created_finorg):
        update_payload = FinOrgUpdate(name="Updated FinOrg Name", settings={"currency": "EUR"})
        updated_org = await update_fin_org(created_finorg.id, update_payload)
        assert updated_org is not None
        assert updated_org.name == "Updated FinOrg Name"
        # settings should update; compare after loading JSON if needed.
        assert updated_org.settings["currency"] == "EUR"

    async def test_delete_finorg(self, created_finorg):
        success = await delete_fin_org(created_finorg.id)
        assert success is True
        org = await get_fin_org(created_finorg.id)
        assert org is None


# -----------------------------------------------------------------------------
# Tests for FinOrgContact CRUD Operations
# -----------------------------------------------------------------------------
@pytest.mark.asyncio
class TestFinOrgContactDatabase:
    async def test_create_finorg_contact(self, created_finorg, new_finorg_contact_payload: dict):
        contact_in = FinOrgContactCreate(**new_finorg_contact_payload)
        contact = await create_fin_org_contact(contact_in)
        assert contact.id is not None
        assert str(contact.fin_org_id) == new_finorg_contact_payload["fin_org_id"]

    async def test_get_finorg_contact(self, created_finorg_contact):
        contact = await get_fin_org_contact(created_finorg_contact.id)
        assert contact is not None
        assert contact.id == created_finorg_contact.id

    async def test_list_finorg_contacts(self, created_finorg, created_finorg_contact):
        contacts = await list_fin_org_contacts(created_finorg.id)
        assert isinstance(contacts, list)
        assert any(str(contact.id) == str(created_finorg_contact.id) for contact in contacts)

    async def test_update_finorg_contact(self, created_finorg_contact):
        update_payload = FinOrgContactUpdate(full_name="Jane Doe Updated", phone="+15557654321")
        updated_contact = await update_fin_org_contact(created_finorg_contact.id, update_payload)
        assert updated_contact is not None
        assert updated_contact.full_name == "Jane Doe Updated"
        assert updated_contact.phone == "+15557654321"

    async def test_delete_finorg_contact(self, created_finorg_contact):
        success = await delete_fin_org_contact(created_finorg_contact.id)
        assert success is True
        contact = await get_fin_org_contact(created_finorg_contact.id)
        assert contact is None

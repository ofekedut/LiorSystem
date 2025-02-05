# finorg_router.py
from typing import List
from uuid import UUID

from fastapi import APIRouter, HTTPException

from server.database.finorg_database import (
    create_fin_org,
    get_fin_org,
    list_fin_orgs,
    update_fin_org,
    delete_fin_org,
    FinOrgCreate,
    FinOrgInDB,
    FinOrgUpdate,

    create_fin_org_contact,
    get_fin_org_contact,
    list_fin_org_contacts,
    update_fin_org_contact,
    delete_fin_org_contact,
    FinOrgContactCreate,
    FinOrgContactInDB,
    FinOrgContactUpdate,
)

router = APIRouter()


# -----------------------------------------------------------------------------
# FinOrg Endpoints
# -----------------------------------------------------------------------------

@router.get("/fin_orgs", response_model=List[FinOrgInDB])
async def read_fin_orgs() -> List[FinOrgInDB]:
    """
    Retrieve all financial organizations.
    """
    return await list_fin_orgs()


@router.post("/fin_orgs", response_model=FinOrgInDB, status_code=201)
async def create_new_fin_org(org_in: FinOrgCreate) -> FinOrgInDB:
    """
    Create a new financial organization.
    """
    return await create_fin_org(org_in)


@router.get("/fin_orgs/{org_id}", response_model=FinOrgInDB)
async def read_fin_org(org_id: UUID) -> FinOrgInDB:
    """
    Retrieve a specific financial organization by its UUID.
    """
    org = await get_fin_org(org_id)
    if not org:
        raise HTTPException(status_code=404, detail="Financial organization not found")
    return org


@router.put("/fin_orgs/{org_id}", response_model=FinOrgInDB)
async def update_fin_org_endpoint(org_id: UUID, org_update: FinOrgUpdate) -> FinOrgInDB:
    """
    Update an existing financial organization.
    """
    updated_org = await update_fin_org(org_id, org_update)
    if not updated_org:
        raise HTTPException(status_code=404, detail="Financial organization not found or not updated")
    return updated_org


@router.delete("/fin_orgs/{org_id}", status_code=204)
async def delete_fin_org_endpoint(org_id: UUID):
    """
    Delete a financial organization.
    """
    success = await delete_fin_org(org_id)
    if not success:
        raise HTTPException(status_code=404, detail="Financial organization not found")
    return None


# -----------------------------------------------------------------------------
# FinOrgContact Endpoints
# -----------------------------------------------------------------------------

@router.get("/fin_orgs/{org_id}/contacts", response_model=List[FinOrgContactInDB])
async def read_fin_org_contacts(org_id: UUID) -> List[FinOrgContactInDB]:
    """
    Retrieve all contacts for a given financial organization.
    """
    # Optionally, you could check if the org exists.
    org = await get_fin_org(org_id)
    if not org:
        raise HTTPException(status_code=404, detail="Financial organization not found")
    return await list_fin_org_contacts(org_id)


@router.post("/fin_orgs/{org_id}/contacts", response_model=FinOrgContactInDB, status_code=201)
async def create_contact_for_fin_org(org_id: UUID, contact_in: FinOrgContactCreate) -> FinOrgContactInDB:
    """
    Create a new contact for a financial organization.
    """
    if contact_in.fin_org_id != org_id:
        raise HTTPException(status_code=400, detail="fin_org_id mismatch")
    org = await get_fin_org(org_id)
    if not org:
        raise HTTPException(status_code=404, detail="Financial organization not found")
    return await create_fin_org_contact(contact_in)


@router.get("/fin_contacts/{contact_id}", response_model=FinOrgContactInDB)
async def read_fin_org_contact(contact_id: UUID) -> FinOrgContactInDB:
    """
    Retrieve a single financial organization contact by its UUID.
    """
    contact = await get_fin_org_contact(contact_id)
    if not contact:
        raise HTTPException(status_code=404, detail="Financial organization contact not found")
    return contact


@router.put("/fin_contacts/{contact_id}", response_model=FinOrgContactInDB)
async def update_fin_org_contact_endpoint(contact_id: UUID, contact_update: FinOrgContactUpdate) -> FinOrgContactInDB:
    """
    Update an existing financial organization contact.
    """
    updated = await update_fin_org_contact(contact_id, contact_update)
    if not updated:
        raise HTTPException(status_code=404, detail="Financial organization contact not found or not updated")
    return updated


@router.delete("/fin_contacts/{contact_id}", status_code=204)
async def delete_fin_org_contact_endpoint(contact_id: UUID):
    """
    Delete a financial organization contact.
    """
    success = await delete_fin_org_contact(contact_id)
    if not success:
        raise HTTPException(status_code=404, detail="Financial organization contact not found")
    return None

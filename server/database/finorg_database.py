# finorg_database.py
import json
from typing import List, Optional, Any, Dict
from uuid import UUID
from datetime import datetime

from pydantic import BaseModel, EmailStr
from server.database.database import get_connection


# -----------------------------------------------------------------------------
# 1. Pydantic Models for FinOrg
# -----------------------------------------------------------------------------

class FinOrgBase(BaseModel):
    name: str
    type: str
    settings: Optional[Dict[str, Any]] = None


class FinOrgCreate(BaseModel):
    name: str
    type: str
    settings: Optional[Dict[str, Any]] = None


class FinOrgInDB(FinOrgBase):
    id: UUID
    created_at: datetime
    updated_at: datetime


class FinOrgUpdate(BaseModel):
    name: Optional[str] = None
    type: Optional[str] = None
    settings: Optional[Dict[str, Any]] = None


# -----------------------------------------------------------------------------
# 2. Pydantic Models for FinOrgContact
# -----------------------------------------------------------------------------

class FinOrgContactBase(BaseModel):
    fin_org_id: UUID
    full_name: str
    email: EmailStr
    phone: Optional[str] = None


class FinOrgContactCreate(FinOrgContactBase):
    pass


class FinOrgContactInDB(FinOrgContactBase):
    id: UUID
    created_at: datetime
    updated_at: datetime


class FinOrgContactUpdate(BaseModel):
    full_name: Optional[str] = None
    email: Optional[EmailStr] = None
    phone: Optional[str] = None


# -----------------------------------------------------------------------------
# 3. CRUD Functions for FinOrg
# -----------------------------------------------------------------------------

async def create_fin_org(org_in: FinOrgCreate) -> FinOrgInDB:
    conn = await get_connection()
    try:
        async with conn.transaction():
            row = await conn.fetchrow(
                """
                INSERT INTO fin_orgs (name, type, settings)
                VALUES ($1, $2, $3)
                RETURNING *
                """,
                org_in.name,
                org_in.type,
                json.dumps(org_in.settings) if org_in.settings else {}
            )
            d = dict(row)
            d['settings'] = org_in.settings
            return FinOrgInDB(**d)
    finally:
        await conn.close()


async def get_fin_org(org_id: UUID) -> Optional[FinOrgInDB]:
    conn = await get_connection()
    try:
        row = await conn.fetchrow("SELECT * FROM fin_orgs WHERE id = $1", org_id)
        if row:
            d = dict(row)
            d['settings'] = json.loads(d['settings']) if d['settings'] else {}
            return FinOrgInDB(**d)
        else:
            return None
    finally:
        await conn.close()


async def list_fin_orgs() -> List[FinOrgInDB]:
    conn = await get_connection()
    try:
        rows = await conn.fetch("SELECT * FROM fin_orgs ORDER BY created_at DESC")
        res = []
        for row in rows:
            d = dict(row)
            d['settings'] = json.loads(d['settings']) if d['settings'] else {}
            res.append(FinOrgInDB(**d))
        return res
    finally:
        await conn.close()


async def update_fin_org(org_id: UUID, org_update: FinOrgUpdate) -> Optional[FinOrgInDB]:
    existing = await get_fin_org(org_id)
    if not existing:
        return None
    updated_data = existing.copy(update=org_update.dict(exclude_unset=True))
    conn = await get_connection()
    try:
        async with conn.transaction():
            row = await conn.fetchrow(
                """
                UPDATE fin_orgs
                SET name = $1,
                    type = $2,
                    settings = $3,
                    updated_at = NOW()
                WHERE id = $4
                RETURNING *
                """,
                updated_data.name,
                updated_data.type,
                json.dumps(updated_data.settings) if updated_data.settings else None,
                org_id,
            )
            if row:
                d = dict(row)
                d['settings'] = json.loads(d['settings']) if d['settings'] else {}
                return FinOrgInDB(**d)
            return None
    finally:
        await conn.close()


async def delete_fin_org(org_id: UUID) -> bool:
    conn = await get_connection()
    try:
        async with conn.transaction():
            result = await conn.execute("DELETE FROM fin_orgs WHERE id = $1", org_id)
            return "DELETE 1" in result
    finally:
        await conn.close()


# -----------------------------------------------------------------------------
# 4. CRUD Functions for FinOrgContact
# -----------------------------------------------------------------------------

async def create_fin_org_contact(contact_in: FinOrgContactCreate) -> FinOrgContactInDB:
    conn = await get_connection()
    try:
        async with conn.transaction():
            row = await conn.fetchrow(
                """
                INSERT INTO fin_org_contacts (fin_org_id, full_name, email, phone)
                VALUES ($1, $2, $3, $4)
                RETURNING *
                """,
                contact_in.fin_org_id,
                contact_in.full_name,
                contact_in.email,
                contact_in.phone
            )
            return FinOrgContactInDB(**dict(row))
    finally:
        await conn.close()


async def get_fin_org_contact(contact_id: UUID) -> Optional[FinOrgContactInDB]:
    conn = await get_connection()
    try:
        row = await conn.fetchrow("SELECT * FROM fin_org_contacts WHERE id = $1", contact_id)
        return FinOrgContactInDB(**dict(row)) if row else None
    finally:
        await conn.close()


async def list_fin_org_contacts(fin_org_id: UUID) -> List[FinOrgContactInDB]:
    conn = await get_connection()
    try:
        rows = await conn.fetch("SELECT * FROM fin_org_contacts WHERE fin_org_id = $1", fin_org_id)
        return [FinOrgContactInDB(**dict(row)) for row in rows]
    finally:
        await conn.close()


async def update_fin_org_contact(contact_id: UUID, contact_update: FinOrgContactUpdate) -> Optional[FinOrgContactInDB]:
    existing = await get_fin_org_contact(contact_id)
    if not existing:
        return None
    updated_data = existing.copy(update=contact_update.dict(exclude_unset=True))
    conn = await get_connection()
    try:
        async with conn.transaction():
            row = await conn.fetchrow(
                """
                UPDATE fin_org_contacts
                SET full_name = $1,
                    email = $2,
                    phone = $3,
                    updated_at = NOW()
                WHERE id = $4
                RETURNING *
                """,
                updated_data.full_name,
                updated_data.email,
                updated_data.phone,
                contact_id,
            )
            return FinOrgContactInDB(**dict(row)) if row else None
    finally:
        await conn.close()


async def delete_fin_org_contact(contact_id: UUID) -> bool:
    conn = await get_connection()
    try:
        async with conn.transaction():
            result = await conn.execute("DELETE FROM fin_org_contacts WHERE id = $1", contact_id)
            return "DELETE 1" in result
    finally:
        await conn.close()

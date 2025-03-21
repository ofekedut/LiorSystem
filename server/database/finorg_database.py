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
    type_id: UUID  # References lior_dropdown_options.id
    settings: Optional[Dict[str, Any]] = None


class FinOrgCreate(BaseModel):
    name: str
    type_id: UUID  # References lior_dropdown_options.id
    settings: Optional[Dict[str, Any]] = None


class FinOrgInDB(FinOrgBase):
    id: UUID
    created_at: datetime
    updated_at: datetime


class FinOrgUpdate(BaseModel):
    name: Optional[str] = None
    id: Optional[UUID] = None
    settings: Optional[Dict[str, Any]] = None
    type_id: Optional[UUID] = None


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

async def create_fin_org(org_in: FinOrgCreate) -> FinOrgInDB | None:
    conn = await get_connection()
    try:
        async with conn.transaction():
            row = await conn.fetchrow(
                """
                INSERT INTO fin_orgs (name, type_id, settings)
                VALUES ($1, $2, $3)
                RETURNING *
                """,
                org_in.name,
                org_in.type_id,
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


async def list_fin_orgs() -> List[FinOrgInDB] | None:
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
                    type_id = $2,
                    settings = $3,
                    updated_at = NOW()
                WHERE id = $4
                RETURNING *
                """,
                updated_data.name,
                updated_data.type_id,
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
            result = await conn.fetchrow("DELETE FROM fin_orgs WHERE id = $1 returning id", org_id)
            return bool(result)
    except Exception as e:
        print(e)
    finally:
        await conn.close()


# -----------------------------------------------------------------------------
# 4. CRUD Functions for FinOrgContact
# -----------------------------------------------------------------------------

async def create_fin_org_contact(contact_in: FinOrgContactCreate) -> FinOrgContactInDB | None:
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


async def list_fin_org_contacts(fin_org_id: UUID) -> List[FinOrgContactInDB] | None:
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


async def delete_fin_org_contact(contact_id: UUID) -> bool | None:
    conn = await get_connection()
    try:
        async with conn.transaction():
            result = await conn.execute("DELETE FROM fin_org_contacts WHERE id = $1", contact_id)
            return "DELETE 1" in result
    finally:
        await conn.close()


# -----------------------------------------------------------------------------
# 5. Pydantic Models for FinOrgType
# -----------------------------------------------------------------------------

class FinOrgTypeBase(BaseModel):
    name: str
    value: str


class FinOrgTypeCreate(FinOrgTypeBase):
    pass


class FinOrgTypeUpdate(BaseModel):
    name: Optional[str] = None
    value: Optional[str] = None


class FinOrgTypeInDB(FinOrgTypeBase):
    id: UUID
    created_at: datetime
    updated_at: datetime


# -----------------------------------------------------------------------------
# 6. CRUD Functions for FinOrgType - Updated to use lior_dropdown_options
# -----------------------------------------------------------------------------

async def create_fin_org_type(type_in: FinOrgTypeCreate) -> FinOrgTypeInDB | None:
    conn = await get_connection()
    try:
        async with conn.transaction():
            row = await conn.fetchrow(
                """
                INSERT INTO lior_dropdown_options (category, name, value)
                VALUES ('fin_org_types', $1, $2)
                RETURNING id, name, value, created_at, updated_at
                """,
                type_in.name,
                type_in.value
            )
            return FinOrgTypeInDB(**dict(row))
    finally:
        await conn.close()


async def get_fin_org_type(type_id: UUID) -> Optional[FinOrgTypeInDB]:
    conn = await get_connection()
    try:
        row = await conn.fetchrow(
            """
            SELECT id, name, value, created_at, updated_at 
            FROM lior_dropdown_options 
            WHERE id = $1 AND category = 'fin_org_types'
            """,
            type_id
        )
        return FinOrgTypeInDB(**dict(row)) if row else None
    finally:
        await conn.close()


async def list_fin_org_types() -> List[FinOrgTypeInDB] | None:
    conn = await get_connection()
    try:
        rows = await conn.fetch(
            """
            SELECT id, name, value, created_at, updated_at 
            FROM lior_dropdown_options 
            WHERE category = 'fin_org_types'
            ORDER BY name
            """
        )
        return [FinOrgTypeInDB(**dict(row)) for row in rows]
    finally:
        await conn.close()


async def update_fin_org_type(type_id: UUID, type_update: FinOrgTypeUpdate) -> Optional[FinOrgTypeInDB]:
    update_fields = []
    values = [type_id]
    counter = 2  # Start from $2 since $1 is type_id

    if type_update.name is not None:
        update_fields.append(f"name = ${counter}")
        values.append(type_update.name)
        counter += 1

    if type_update.value is not None:
        update_fields.append(f"value = ${counter}")
        values.append(type_update.value)
        counter += 1

    if not update_fields:
        # If no fields to update, just return the current fin_org type
        return await get_fin_org_type(type_id)

    # Always update the updated_at timestamp
    update_fields.append("updated_at = NOW()")

    query = f"""
    UPDATE lior_dropdown_options
    SET {", ".join(update_fields)}
    WHERE id = $1 AND category = 'fin_org_types'
    RETURNING id, name, value, created_at, updated_at
    """

    conn = await get_connection()
    try:
        row = await conn.fetchrow(query, *values)
        return FinOrgTypeInDB(**dict(row)) if row else None
    finally:
        await conn.close()


async def delete_fin_org_type(type_id: UUID) -> bool | None:
    conn = await get_connection()
    try:
        async with conn.transaction():
            result = await conn.execute(
                "DELETE FROM lior_dropdown_options WHERE id = $1 AND category = 'fin_org_types'",
                type_id
            )
            return "DELETE 1" in result
    finally:
        await conn.close()
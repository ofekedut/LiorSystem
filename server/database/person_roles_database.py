"""
Database operations for person roles using the lior_dropdown_options table
"""
import uuid
from typing import List, Optional
from pydantic import BaseModel

from server.database.database import get_connection


class PersonRoleBase(BaseModel):
    name: str
    value: str


class PersonRoleInCreate(PersonRoleBase):
    pass


class PersonRoleInUpdate(BaseModel):
    name: Optional[str] = None
    value: Optional[str] = None


class PersonRole(PersonRoleBase):
    id: uuid.UUID

    class Config:
        from_attributes = True


async def create_person_role(payload: PersonRoleInCreate) -> PersonRole:
    """
    Create a new person role in the dropdown options table
    """
    query = """
    INSERT INTO lior_dropdown_options (id, category, name, value)
    VALUES ($1, $2, $3, $4)
    RETURNING id, name, value
    """
    role_id = uuid.uuid4()
    values = [role_id, 'person_roles', payload.name, payload.value]

    conn = await get_connection()
    try:
        row = await conn.fetchrow(query, *values)
        return PersonRole.model_validate(dict(row))
    finally:
        await conn.close()


async def get_person_roles() -> List[PersonRole]:
    """
    Get all person roles from the dropdown options table
    """
    query = """
    SELECT id, name, value
    FROM lior_dropdown_options
    WHERE category = 'person_roles'
    ORDER BY name
    """
    conn = await get_connection()
    try:
        rows = await conn.fetch(query)
        return [PersonRole.model_validate(dict(row)) for row in rows]
    finally:
        await conn.close()


async def get_person_role(person_role_id: uuid.UUID) -> Optional[PersonRole]:
    """
    Get a specific person role by ID from the dropdown options table
    """
    query = """
    SELECT id, name, value
    FROM lior_dropdown_options
    WHERE id = $1 AND category = 'person_roles'
    """
    conn = await get_connection()
    try:
        row = await conn.fetchrow(query, person_role_id)
        if row:
            return PersonRole.model_validate(dict(row))
        return None
    finally:
        await conn.close()


async def get_person_role_by_value(value: str) -> Optional[PersonRole]:
    """
    Get a specific person role by value from the dropdown options table
    """
    query = """
    SELECT id, name, value
    FROM lior_dropdown_options
    WHERE value = $1 AND category = 'person_roles'
    """
    conn = await get_connection()
    try:
        row = await conn.fetchrow(query, value)
        if row:
            return PersonRole.model_validate(dict(row))
        return None
    finally:
        await conn.close()


async def update_person_role(person_role_id: uuid.UUID, payload: PersonRoleInUpdate) -> Optional[PersonRole]:
    """
    Update an existing person role in the dropdown options table
    """
    # Build the update sets dynamically based on what fields are provided
    update_fields = []
    values = [person_role_id]
    counter = 2  # Start from $2 since $1 is person_role_id

    if payload.name is not None:
        update_fields.append(f"name = ${counter}")
        values.append(payload.name)
        counter += 1

    if payload.value is not None:
        update_fields.append(f"value = ${counter}")
        values.append(payload.value)
        counter += 1

    if not update_fields:
        # If no fields to update, just return the current person role
        return await get_person_role(person_role_id)

    query = f"""
    UPDATE lior_dropdown_options
    SET {", ".join(update_fields)}, updated_at = NOW()
    WHERE id = $1 AND category = 'person_roles'
    RETURNING id, name, value
    """

    conn = await get_connection()
    try:
        row = await conn.fetchrow(query, *values)
        if row:
            return PersonRole.model_validate(dict(row))
        return None
    finally:
        await conn.close()


async def delete_person_role(person_role_id: uuid.UUID) -> bool:
    """
    Delete a person role from the dropdown options table
    """
    query = """
    DELETE FROM lior_dropdown_options
    WHERE id = $1 AND category = 'person_roles'
    RETURNING id
    """
    conn = await get_connection()
    try:
        row = await conn.fetchrow(query, person_role_id)
        return row is not None
    finally:
        await conn.close()
"""
Database operations for employment history
"""
import uuid
from typing import List, Optional
from pydantic import BaseModel
from datetime import datetime, date

from server.database.database import get_connection


class EmploymentHistoryBase(BaseModel):
    person_id: uuid.UUID
    employer_name: str
    position: str
    employment_type_id: uuid.UUID
    current_employer: bool = False
    employment_since: date
    employment_until: Optional[date] = None


class EmploymentHistoryInCreate(EmploymentHistoryBase):
    pass


class EmploymentHistoryInDB(EmploymentHistoryBase):
    id: uuid.UUID
    created_at: datetime
    updated_at: datetime


class EmploymentHistoryInUpdate(BaseModel):
    employer_name: Optional[str] = None
    position: Optional[str] = None
    employment_type_id: Optional[uuid.UUID] = None
    current_employer: Optional[bool] = None
    employment_since: Optional[date] = None
    employment_until: Optional[date] = None


async def create_employment_history(payload: EmploymentHistoryInCreate) -> EmploymentHistoryInDB:
    """
    Create a new employment history record for a person
    """
    query = """
    INSERT INTO person_employment_history (
        id, person_id, employer_name, position, employment_type_id, current_employer,
        employment_since, employment_until
    )
    VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
    RETURNING id, person_id, employer_name, position, employment_type_id, current_employer,
              employment_since, employment_until, created_at, updated_at
    """

    employment_id = uuid.uuid4()
    values = [
        employment_id,
        payload.person_id,
        payload.employer_name,
        payload.position,
        payload.employment_type_id,
        payload.current_employer,
        payload.employment_since,
        payload.employment_until
    ]

    conn = await get_connection()
    try:
        row = await conn.fetchrow(query, *values)
        return EmploymentHistoryInDB.model_validate(dict(row))
    finally:
        await conn.close()


async def get_employment_history_by_id(employment_id: uuid.UUID) -> Optional[EmploymentHistoryInDB]:
    """
    Get a specific employment history record by ID
    """
    query = """
    SELECT id, person_id, employer_name, position, employment_type_id, current_employer,
           employment_since, employment_until, created_at, updated_at
    FROM person_employment_history
    WHERE id = $1
    """

    conn = await get_connection()
    try:
        row = await conn.fetchrow(query, employment_id)
        if row:
            return EmploymentHistoryInDB.model_validate(dict(row))
        return None
    finally:
        await conn.close()


async def get_employment_history_by_person(person_id: uuid.UUID) -> List[EmploymentHistoryInDB]:
    """
    Get all employment history records for a specific person
    """
    query = """
    SELECT id, person_id, employer_name, position, employment_type_id, current_employer,
           employment_since, employment_until, created_at, updated_at
    FROM person_employment_history
    WHERE person_id = $1
    ORDER BY current_employer DESC, employment_since DESC
    """

    conn = await get_connection()
    try:
        rows = await conn.fetch(query, person_id)
        return [EmploymentHistoryInDB.model_validate(dict(row)) for row in rows]
    finally:
        await conn.close()


async def update_employment_history(
        employment_id: uuid.UUID,
        payload: EmploymentHistoryInUpdate
) -> Optional[EmploymentHistoryInDB]:
    """
    Update an employment history record
    """
    existing = await get_employment_history_by_id(employment_id)
    if not existing:
        return None

    # Build SET clause dynamically based on provided fields
    set_parts = []
    values = [employment_id]  # First parameter is always the ID
    param_index = 2  # Start parameter index at 2

    if payload.employer_name is not None:
        set_parts.append(f"employer_name = ${param_index}")
        values.append(payload.employer_name)
        param_index += 1

    if payload.position is not None:
        set_parts.append(f"position = ${param_index}")
        values.append(payload.position)
        param_index += 1

    if payload.employment_type_id is not None:
        set_parts.append(f"employment_type_id = ${param_index}")
        values.append(payload.employment_type_id)
        param_index += 1

    if payload.current_employer is not None:
        set_parts.append(f"current_employer = ${param_index}")
        values.append(payload.current_employer)
        param_index += 1
        
    if payload.employment_since is not None:
        set_parts.append(f"employment_since = ${param_index}")
        values.append(payload.employment_since)
        param_index += 1
        
    if payload.employment_until is not None:
        set_parts.append(f"employment_until = ${param_index}")
        values.append(payload.employment_until)
        param_index += 1

    # If nothing to update, return existing record
    if not set_parts:
        return existing

    # Always update updated_at timestamp
    set_parts.append("updated_at = NOW()")

    query = f"""
    UPDATE person_employment_history
    SET {", ".join(set_parts)}
    WHERE id = $1
    RETURNING id, person_id, employer_name, position, employment_type_id, current_employer,
              employment_since, employment_until, created_at, updated_at
    """

    conn = await get_connection()
    try:
        row = await conn.fetchrow(query, *values)
        if row:
            return EmploymentHistoryInDB.model_validate(dict(row))
        return None
    finally:
        await conn.close()


async def delete_employment_history(employment_id: uuid.UUID) -> bool:
    """
    Delete an employment history record
    """
    query = """
    DELETE FROM person_employment_history
    WHERE id = $1
    RETURNING id
    """

    conn = await get_connection()
    try:
        row = await conn.fetchrow(query, employment_id)
        return row is not None
    finally:
        await conn.close()

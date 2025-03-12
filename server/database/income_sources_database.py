"""
Database operations for person income sources
"""
import uuid
from typing import List, Optional
from pydantic import BaseModel
from datetime import datetime

from server.database.database import get_connection


class IncomeSourceBase(BaseModel):
    person_id: uuid.UUID
    label: str
    income_source_type_id: uuid.UUID


class IncomeSourceInCreate(IncomeSourceBase):
    pass


class IncomeSourceInDB(IncomeSourceBase):
    id: uuid.UUID
    created_at: datetime
    updated_at: datetime


class IncomeSourceInUpdate(BaseModel):
    label: Optional[str] = None
    income_source_type_id: Optional[uuid.UUID] = None


async def create_income_source(payload: IncomeSourceInCreate) -> IncomeSourceInDB:
    """
    Create a new income source for a person
    """
    query = """
    INSERT INTO person_income_sources (
        id, person_id, label, income_source_type_id
    )
    VALUES ($1, $2, $3, $4)
    RETURNING id, person_id, label, income_source_type_id, created_at, updated_at
    """

    income_id = uuid.uuid4()
    values = [
        income_id,
        payload.person_id,
        payload.label,
        payload.income_source_type_id,
    ]

    conn = await get_connection()
    try:
        row = await conn.fetchrow(query, *values)
        return IncomeSourceInDB.model_validate(dict(row))
    finally:
        await conn.close()


async def get_income_source_by_id(income_id: uuid.UUID) -> Optional[IncomeSourceInDB]:
    """
    Get a specific income source by ID
    """
    query = """
    SELECT id, person_id, label, income_source_type_id, created_at, updated_at
    FROM person_income_sources
    WHERE id = $1
    """

    conn = await get_connection()
    try:
        row = await conn.fetchrow(query, income_id)
        if row:
            return IncomeSourceInDB.model_validate(dict(row))
        return None
    finally:
        await conn.close()


async def get_income_sources_by_person(person_id: uuid.UUID) -> List[IncomeSourceInDB]:
    """
    Get all income sources for a specific person
    """
    query = """
    SELECT id, person_id, label, income_source_type_id, created_at, updated_at
    FROM person_income_sources
    WHERE person_id = $1
    ORDER BY created_at DESC
    """

    conn = await get_connection()
    try:
        rows = await conn.fetch(query, person_id)
        return [IncomeSourceInDB.model_validate(dict(row)) for row in rows]
    finally:
        await conn.close()


async def update_income_source(
        income_id: uuid.UUID,
        payload: IncomeSourceInUpdate
) -> Optional[IncomeSourceInDB]:
    """
    Update an income source record
    """
    existing = await get_income_source_by_id(income_id)
    if not existing:
        return None

    # Build SET clause dynamically based on provided fields
    set_parts = []
    values = [income_id]  # First parameter is always the ID
    param_index = 2  # Start parameter index at 2

    if payload.label is not None:
        set_parts.append(f"label = ${param_index}")
        values.append(payload.label)
        param_index += 1

    if payload.income_source_type_id is not None:
        set_parts.append(f"income_source_type_id = ${param_index}")
        values.append(payload.income_source_type_id)
        param_index += 1

    # If nothing to update, return existing record
    if not set_parts:
        return existing

    # Always update updated_at timestamp
    set_parts.append("updated_at = NOW()")

    query = f"""
    UPDATE person_income_sources
    SET {", ".join(set_parts)}
    WHERE id = $1
    RETURNING id, person_id, label, income_source_type_id, created_at, updated_at
    """

    conn = await get_connection()
    try:
        row = await conn.fetchrow(query, *values)
        if row:
            return IncomeSourceInDB.model_validate(dict(row))
        return None
    finally:
        await conn.close()


async def delete_income_source(income_id: uuid.UUID) -> bool:
    """
    Delete an income source record
    """
    query = """
    DELETE FROM person_income_sources
    WHERE id = $1
    RETURNING id
    """

    conn = await get_connection()
    try:
        row = await conn.fetchrow(query, income_id)
        return row is not None
    finally:
        await conn.close()
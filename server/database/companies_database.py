"""
Database operations for case companies
"""
import uuid
from typing import List, Optional
from pydantic import BaseModel
from datetime import datetime

from server.database.database import get_connection


class CompanyBase(BaseModel):
    case_id: uuid.UUID
    name: str
    company_type_id: uuid.UUID
    company_id_num: str  # Added as primary identification field as per PRD
    role_id: Optional[uuid.UUID] = None


class CompanyInCreate(CompanyBase):
    pass


class CompanyInDB(CompanyBase):
    id: uuid.UUID
    created_at: datetime
    updated_at: datetime


class CompanyInUpdate(BaseModel):
    name: Optional[str] = None
    company_type_id: Optional[uuid.UUID] = None
    company_id_num: Optional[str] = None  # Added as primary identification field as per PRD
    role_id: Optional[uuid.UUID] = None


async def create_company(payload: CompanyInCreate) -> CompanyInDB:
    """
    Create a new company for a case
    """
    query = """
    INSERT INTO case_companies (
        id, case_id, name, company_type_id, company_id_num, role_id
    )
    VALUES ($1, $2, $3, $4, $5, $6)
    RETURNING id, case_id, name, company_type_id, company_id_num, role_id, created_at, updated_at
    """

    company_id = uuid.uuid4()
    values = [
        company_id,
        payload.case_id,
        payload.name,
        payload.company_type_id,
        payload.company_id_num,
        payload.role_id
    ]

    conn = await get_connection()
    try:
        row = await conn.fetchrow(query, *values)
        return CompanyInDB.model_validate(dict(row))
    finally:
        await conn.close()


async def get_company_by_id(company_id: uuid.UUID) -> Optional[CompanyInDB]:
    """
    Get a specific company by ID
    """
    query = """
    SELECT id, case_id, name, company_type_id, company_id_num, role_id, created_at, updated_at
    FROM case_companies
    WHERE id = $1
    """

    conn = await get_connection()
    try:
        row = await conn.fetchrow(query, company_id)
        if row:
            return CompanyInDB.model_validate(dict(row))
        return None
    finally:
        await conn.close()


async def get_companies_by_case(case_id: uuid.UUID) -> List[CompanyInDB]:
    """
    Get all companies for a specific case
    """
    query = """
    SELECT id, case_id, name, company_type_id, company_id_num, role_id, created_at, updated_at
    FROM case_companies
    WHERE case_id = $1
    ORDER BY created_at DESC
    """

    conn = await get_connection()
    try:
        rows = await conn.fetch(query, case_id)
        return [CompanyInDB.model_validate(dict(row)) for row in rows]
    finally:
        await conn.close()


async def update_company(
        company_id: uuid.UUID,
        payload: CompanyInUpdate
) -> Optional[CompanyInDB]:
    """
    Update a company record
    """
    existing = await get_company_by_id(company_id)
    if not existing:
        return None

    # Build SET clause dynamically based on provided fields
    set_parts = []
    values = [company_id]  # First parameter is always the ID
    param_index = 2  # Start parameter index at 2

    if payload.name is not None:
        set_parts.append(f"name = ${param_index}")
        values.append(payload.name)
        param_index += 1

    if payload.company_type_id is not None:
        set_parts.append(f"company_type_id = ${param_index}")
        values.append(payload.company_type_id)
        param_index += 1

    if payload.company_id_num is not None:
        set_parts.append(f"company_id_num = ${param_index}")
        values.append(payload.company_id_num)
        param_index += 1
        
    if payload.role_id is not None:
        set_parts.append(f"role_id = ${param_index}")
        values.append(payload.role_id)
        param_index += 1

    # If nothing to update, return existing record
    if not set_parts:
        return existing

    # Always update updated_at timestamp
    set_parts.append("updated_at = NOW()")

    query = f"""
    UPDATE case_companies
    SET {", ".join(set_parts)}
    WHERE id = $1
    RETURNING id, case_id, name, company_type_id, company_id_num, role_id, created_at, updated_at
    """

    conn = await get_connection()
    try:
        row = await conn.fetchrow(query, *values)
        if row:
            return CompanyInDB.model_validate(dict(row))
        return None
    finally:
        await conn.close()


async def delete_company(company_id: uuid.UUID) -> bool:
    """
    Delete a company record
    """
    query = """
    DELETE FROM case_companies
    WHERE id = $1
    RETURNING id
    """

    conn = await get_connection()
    try:
        row = await conn.fetchrow(query, company_id)
        return row is not None
    finally:
        await conn.close()
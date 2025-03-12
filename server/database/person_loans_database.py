"""
Database operations for person loans
"""
import uuid
from typing import List, Optional
from pydantic import BaseModel
from datetime import datetime

from server.database.database import get_connection


class PersonLoanBase(BaseModel):
    person_id: uuid.UUID
    loan_type_id: uuid.UUID
    lender: str


class PersonLoanInCreate(PersonLoanBase):
    pass


class PersonLoanInDB(PersonLoanBase):
    id: uuid.UUID
    created_at: datetime
    updated_at: datetime


class PersonLoanInUpdate(BaseModel):
    loan_type_id: Optional[uuid.UUID] = None
    lender: Optional[str] = None


async def create_person_loan(payload: PersonLoanInCreate) -> PersonLoanInDB:
    """
    Create a new loan for a person
    """
    query = """
    INSERT INTO person_loans (
        id, person_id, loan_type_id, lender
    )
    VALUES ($1, $2, $3, $4)
    RETURNING id, person_id, loan_type_id, lender, created_at, updated_at
    """

    loan_id = uuid.uuid4()
    values = [
        loan_id,
        payload.person_id,
        payload.loan_type_id,
        payload.lender
    ]

    conn = await get_connection()
    try:
        row = await conn.fetchrow(query, *values)
        return PersonLoanInDB.model_validate(dict(row))
    finally:
        await conn.close()


async def get_person_loan_by_id(loan_id: uuid.UUID) -> Optional[PersonLoanInDB]:
    """
    Get a specific loan by ID
    """
    query = """
    SELECT id, person_id, loan_type_id, lender, created_at, updated_at
    FROM person_loans
    WHERE id = $1
    """

    conn = await get_connection()
    try:
        row = await conn.fetchrow(query, loan_id)
        if row:
            return PersonLoanInDB.model_validate(dict(row))
        return None
    finally:
        await conn.close()


async def get_person_loans_by_person(person_id: uuid.UUID) -> List[PersonLoanInDB]:
    """
    Get all loans for a specific person
    """
    query = """
    SELECT id, person_id, loan_type_id, lender, created_at, updated_at
    FROM person_loans
    WHERE person_id = $1
    ORDER BY created_at DESC
    """

    conn = await get_connection()
    try:
        rows = await conn.fetch(query, person_id)
        return [PersonLoanInDB.model_validate(dict(row)) for row in rows]
    finally:
        await conn.close()


async def update_person_loan(
        loan_id: uuid.UUID,
        payload: PersonLoanInUpdate
) -> Optional[PersonLoanInDB]:
    """
    Update a loan record
    """
    existing = await get_person_loan_by_id(loan_id)
    if not existing:
        return None

    # Build SET clause dynamically based on provided fields
    set_parts = []
    values = [loan_id]  # First parameter is always the ID
    param_index = 2  # Start parameter index at 2

    if payload.loan_type_id is not None:
        set_parts.append(f"loan_type_id = ${param_index}")
        values.append(payload.loan_type_id)
        param_index += 1

    if payload.lender is not None:
        set_parts.append(f"lender = ${param_index}")
        values.append(payload.lender)
        param_index += 1

    # If nothing to update, return existing record
    if not set_parts:
        return existing

    # Always update updated_at timestamp
    set_parts.append("updated_at = NOW()")

    query = f"""
    UPDATE person_loans
    SET {", ".join(set_parts)}
    WHERE id = $1
    RETURNING id, person_id, loan_type_id, lender, created_at, updated_at
    """

    conn = await get_connection()
    try:
        row = await conn.fetchrow(query, *values)
        if row:
            return PersonLoanInDB.model_validate(dict(row))
        return None
    finally:
        await conn.close()


async def delete_person_loan(loan_id: uuid.UUID) -> bool:
    """
    Delete a loan record
    """
    query = """
    DELETE FROM person_loans
    WHERE id = $1
    RETURNING id
    """

    conn = await get_connection()
    try:
        row = await conn.fetchrow(query, loan_id)
        return row is not None
    finally:
        await conn.close()
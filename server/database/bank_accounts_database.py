"""
Database operations for person bank accounts
"""
import uuid
from typing import List, Optional
from pydantic import BaseModel
from datetime import datetime

from server.database.database import get_connection


class BankAccountBase(BaseModel):
    person_id: uuid.UUID
    account_type_id: uuid.UUID
    bank_name: str
    account_number: str


class BankAccountInCreate(BankAccountBase):
    pass


class BankAccountInDB(BankAccountBase):
    id: uuid.UUID
    created_at: datetime
    updated_at: datetime


class BankAccountInUpdate(BaseModel):
    account_type_id: Optional[uuid.UUID] = None
    bank_name: Optional[str] = None
    account_number: Optional[str] = None


async def create_bank_account(payload: BankAccountInCreate) -> BankAccountInDB:
    """
    Create a new bank account for a person
    """
    query = """
    INSERT INTO person_bank_accounts (
        id, person_id, account_type_id, bank_name, account_number
    )
    VALUES ($1, $2, $3, $4, $5)
    RETURNING id, person_id, account_type_id, bank_name, account_number, created_at, updated_at
    """

    account_id = uuid.uuid4()
    values = [
        account_id,
        payload.person_id,
        payload.account_type_id,
        payload.bank_name,
        payload.account_number
    ]

    conn = await get_connection()
    try:
        row = await conn.fetchrow(query, *values)
        return BankAccountInDB.model_validate(dict(row))
    finally:
        await conn.close()


async def get_bank_account_by_id(account_id: uuid.UUID) -> Optional[BankAccountInDB]:
    """
    Get a specific bank account by ID
    """
    query = """
    SELECT id, person_id, account_type_id, bank_name, account_number, created_at, updated_at
    FROM person_bank_accounts
    WHERE id = $1
    """

    conn = await get_connection()
    try:
        row = await conn.fetchrow(query, account_id)
        if row:
            return BankAccountInDB.model_validate(dict(row))
        return None
    finally:
        await conn.close()


async def get_bank_accounts_by_person(person_id: uuid.UUID) -> List[BankAccountInDB]:
    """
    Get all bank accounts for a specific person
    """
    query = """
    SELECT id, person_id, account_type_id, bank_name, account_number, created_at, updated_at
    FROM person_bank_accounts
    WHERE person_id = $1
    ORDER BY created_at DESC
    """

    conn = await get_connection()
    try:
        rows = await conn.fetch(query, person_id)
        return [BankAccountInDB.model_validate(dict(row)) for row in rows]
    finally:
        await conn.close()


async def update_bank_account(
        account_id: uuid.UUID,
        payload: BankAccountInUpdate
) -> Optional[BankAccountInDB]:
    """
    Update a bank account record
    """
    existing = await get_bank_account_by_id(account_id)
    if not existing:
        return None

    # Build SET clause dynamically based on provided fields
    set_parts = []
    values = [account_id]  # First parameter is always the ID
    param_index = 2  # Start parameter index at 2

    if payload.account_type_id is not None:
        set_parts.append(f"account_type_id = ${param_index}")
        values.append(payload.account_type_id)
        param_index += 1

    if payload.bank_name is not None:
        set_parts.append(f"bank_name = ${param_index}")
        values.append(payload.bank_name)
        param_index += 1

    if payload.account_number is not None:
        set_parts.append(f"account_number = ${param_index}")
        values.append(payload.account_number)
        param_index += 1

    # If nothing to update, return existing record
    if not set_parts:
        return existing

    # Always update updated_at timestamp
    set_parts.append("updated_at = NOW()")

    query = f"""
    UPDATE person_bank_accounts
    SET {", ".join(set_parts)}
    WHERE id = $1
    RETURNING id, person_id, account_type_id, bank_name, account_number, created_at, updated_at
    """

    conn = await get_connection()
    try:
        row = await conn.fetchrow(query, *values)
        if row:
            return BankAccountInDB.model_validate(dict(row))
        return None
    finally:
        await conn.close()


async def delete_bank_account(account_id: uuid.UUID) -> bool:
    """
    Delete a bank account record
    """
    query = """
    DELETE FROM person_bank_accounts
    WHERE id = $1
    RETURNING id
    """

    conn = await get_connection()
    try:
        row = await conn.fetchrow(query, account_id)
        return row is not None
    finally:
        await conn.close()
"""
Database operations for person credit cards
"""
import uuid
from typing import List, Optional
from pydantic import BaseModel, Field, validator
from datetime import datetime

from server.database.database import get_connection


class CreditCardBase(BaseModel):
    person_id: uuid.UUID
    issuer: str
    card_type_id: uuid.UUID
    last_four: int = Field(..., ge=0, le=9999)

    @validator('last_four')
    def validate_last_four(cls, v):
        if not 0 <= v <= 9999:
            raise ValueError("Last four digits must be between 0 and 9999")
        return v


class CreditCardInCreate(CreditCardBase):
    pass


class CreditCardInDB(CreditCardBase):
    id: uuid.UUID
    created_at: datetime
    updated_at: datetime


class CreditCardInUpdate(BaseModel):
    issuer: Optional[str] = None
    card_type_id: Optional[uuid.UUID] = None
    last_four: Optional[int] = Field(None, ge=0, le=9999)

    @validator('last_four')
    def validate_last_four(cls, v):
        if v is not None and not 0 <= v <= 9999:
            raise ValueError("Last four digits must be between 0 and 9999")
        return v


async def create_credit_card(payload: CreditCardInCreate) -> CreditCardInDB:
    """
    Create a new credit card for a person
    """
    query = """
    INSERT INTO person_credit_cards (
        id, person_id, issuer, card_type_id, last_four
    )
    VALUES ($1, $2, $3, $4, $5)
    RETURNING id, person_id, issuer, card_type_id, last_four, created_at, updated_at
    """

    card_id = uuid.uuid4()
    values = [
        card_id,
        payload.person_id,
        payload.issuer,
        payload.card_type_id,
        payload.last_four
    ]

    conn = await get_connection()
    try:
        row = await conn.fetchrow(query, *values)
        return CreditCardInDB.model_validate(dict(row))
    finally:
        await conn.close()


async def get_credit_card_by_id(card_id: uuid.UUID) -> Optional[CreditCardInDB]:
    """
    Get a specific credit card by ID
    """
    query = """
    SELECT id, person_id, issuer, card_type_id, last_four, created_at, updated_at
    FROM person_credit_cards
    WHERE id = $1
    """

    conn = await get_connection()
    try:
        row = await conn.fetchrow(query, card_id)
        if row:
            return CreditCardInDB.model_validate(dict(row))
        return None
    finally:
        await conn.close()


async def get_credit_cards_by_person(person_id: uuid.UUID) -> List[CreditCardInDB]:
    """
    Get all credit cards for a specific person
    """
    query = """
    SELECT id, person_id, issuer, card_type_id, last_four, created_at, updated_at
    FROM person_credit_cards
    WHERE person_id = $1
    ORDER BY created_at DESC
    """

    conn = await get_connection()
    try:
        rows = await conn.fetch(query, person_id)
        return [CreditCardInDB.model_validate(dict(row)) for row in rows]
    finally:
        await conn.close()


async def update_credit_card(
        card_id: uuid.UUID,
        payload: CreditCardInUpdate
) -> Optional[CreditCardInDB]:
    """
    Update a credit card record
    """
    existing = await get_credit_card_by_id(card_id)
    if not existing:
        return None

    # Build SET clause dynamically based on provided fields
    set_parts = []
    values = [card_id]  # First parameter is always the ID
    param_index = 2  # Start parameter index at 2

    if payload.issuer is not None:
        set_parts.append(f"issuer = ${param_index}")
        values.append(payload.issuer)
        param_index += 1

    if payload.card_type_id is not None:
        set_parts.append(f"card_type_id = ${param_index}")
        values.append(payload.card_type_id)
        param_index += 1

    if payload.last_four is not None:
        set_parts.append(f"last_four = ${param_index}")
        values.append(payload.last_four)
        param_index += 1

    # If nothing to update, return existing record
    if not set_parts:
        return existing

    # Always update updated_at timestamp
    set_parts.append("updated_at = NOW()")

    query = f"""
    UPDATE person_credit_cards
    SET {", ".join(set_parts)}
    WHERE id = $1
    RETURNING id, person_id, issuer, card_type_id, last_four, created_at, updated_at
    """

    conn = await get_connection()
    try:
        row = await conn.fetchrow(query, *values)
        if row:
            return CreditCardInDB.model_validate(dict(row))
        return None
    finally:
        await conn.close()


async def delete_credit_card(card_id: uuid.UUID) -> bool:
    """
    Delete a credit card record
    """
    query = """
    DELETE FROM person_credit_cards
    WHERE id = $1
    RETURNING id
    """

    conn = await get_connection()
    try:
        row = await conn.fetchrow(query, card_id)
        return row is not None
    finally:
        await conn.close()
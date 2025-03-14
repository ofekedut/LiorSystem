from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field
import uuid
from typing import List, Optional
from server.database.database import get_connection



router = APIRouter(
    prefix="/credit_card_types",
    tags=["credit_card_types"]
)

class CreditCardTypeBase(BaseModel):
    name: str
    value: str

class CreditCardTypeInCreate(CreditCardTypeBase):
    pass

class CreditCardTypeInUpdate(BaseModel):
    name: Optional[str] = None
    value: Optional[str] = None

class CreditCardTypeInDB(CreditCardTypeBase):
    id: uuid.UUID = Field(default_factory=uuid.uuid4)

@router.get("/", response_model=List[CreditCardTypeInDB])
async def read_credit_card_types():
    conn = await get_connection()
    try:
        rows = await conn.fetch("SELECT id, name, value FROM credit_card_types")
        return [dict(row) for row in rows]
    finally:
        await conn.close()

@router.get("/{credit_card_type_id}", response_model=CreditCardTypeInDB)
async def read_credit_card_type(credit_card_type_id: uuid.UUID):
    conn = await get_connection()
    try:
        row = await conn.fetchrow("SELECT id, name, value FROM credit_card_types WHERE id = $1", str(credit_card_type_id))
        if row is None:
            raise HTTPException(status_code=404, detail="Credit card type not found")
        return dict(row)
    finally:
        await conn.close()

@router.post("/", response_model=CreditCardTypeInDB, status_code=status.HTTP_201_CREATED)
async def create_credit_card_type(payload: CreditCardTypeInCreate):
    new_id = uuid.uuid4()
    conn = await get_connection()
    try:
        row = await conn.fetchrow(
            "INSERT INTO credit_card_types (id, name, value) VALUES ($1, $2, $3) RETURNING id, name, value",
            str(new_id), payload.name, payload.value
        )
        return dict(row)
    finally:
        await conn.close()

@router.put("/{credit_card_type_id}", response_model=CreditCardTypeInDB)
async def update_credit_card_type(credit_card_type_id: uuid.UUID, payload: CreditCardTypeInUpdate):
    conn = await get_connection()
    try:
        existing = await conn.fetchrow("SELECT id, name, value FROM credit_card_types WHERE id = $1", str(credit_card_type_id))
        if existing is None:
            raise HTTPException(status_code=404, detail="Credit card type not found")
        current = dict(existing)
        new_name = payload.name if payload.name is not None else current["name"]
        new_value = payload.value if payload.value is not None else current["value"]
        updated = await conn.fetchrow(
            "UPDATE credit_card_types SET name = $1, value = $2 WHERE id = $3 RETURNING id, name, value",
            new_name, new_value, str(credit_card_type_id)
        )
        return dict(updated)
    finally:
        await conn.close()

@router.delete("/{credit_card_type_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_credit_card_type(credit_card_type_id: uuid.UUID):
    conn = await get_connection()
    try:
        result = await conn.execute("DELETE FROM credit_card_types WHERE id = $1", str(credit_card_type_id))
        if result.split()[-1] == "0":
            raise HTTPException(status_code=404, detail="Credit card type not found")
    finally:
        await conn.close()

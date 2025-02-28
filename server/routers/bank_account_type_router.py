from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field
import uuid
from typing import List, Optional
from server.database.database import get_connection

router = APIRouter(
    prefix="/bank_account_type",
    tags=["bank_account_type"]
)


class BankAccountTypeBase(BaseModel):
    name: str
    value: str


class BankAccountTypeInCreate(BankAccountTypeBase):
    pass


class BankAccountTypeInUpdate(BaseModel):
    name: Optional[str] = None
    value: Optional[str] = None


class BankAccountTypeInDB(BankAccountTypeBase):
    id: uuid.UUID = Field(default_factory=uuid.uuid4)


@router.get("/", response_model=List[BankAccountTypeInDB])
async def read_bank_account_types():
    conn = await get_connection()
    try:
        rows = await conn.fetch("SELECT id, name, value FROM bank_account_type")
        return [dict(row) for row in rows]
    finally:
        await conn.close()


@router.get("/{bank_account_type_id}", response_model=BankAccountTypeInDB)
async def read_bank_account_type(bank_account_type_id: uuid.UUID):
    conn = await get_connection()
    try:
        row = await conn.fetchrow("SELECT id, name, value FROM bank_account_type WHERE id = $1", str(bank_account_type_id))
        if row is None:
            raise HTTPException(status_code=404, detail="Bank account type not found")
        return dict(row)
    finally:
        await conn.close()


@router.post("/", response_model=BankAccountTypeInDB, status_code=status.HTTP_201_CREATED)
async def create_bank_account_type(payload: BankAccountTypeInCreate):
    new_id = uuid.uuid4()
    conn = await get_connection()
    try:
        row = await conn.fetchrow(
            "INSERT INTO bank_account_type (id, name, value) VALUES ($1, $2, $3) RETURNING id, name, value",
            str(new_id), payload.name, payload.value
        )
        return dict(row)
    finally:
        await conn.close()


@router.put("/{bank_account_type_id}", response_model=BankAccountTypeInDB)
async def update_bank_account_type(bank_account_type_id: uuid.UUID, payload: BankAccountTypeInUpdate):
    conn = await get_connection()
    try:
        existing = await conn.fetchrow("SELECT id, name, value FROM bank_account_type WHERE id = $1", str(bank_account_type_id))
        if existing is None:
            raise HTTPException(status_code=404, detail="Bank account type not found")
        current = dict(existing)
        new_name = payload.name if payload.name is not None else current["name"]
        new_value = payload.value if payload.value is not None else current["value"]
        updated = await conn.fetchrow(
            "UPDATE bank_account_type SET name = $1, value = $2 WHERE id = $3 RETURNING id, name, value",
            new_name, new_value, str(bank_account_type_id)
        )
        return dict(updated)
    finally:
        await conn.close()


@router.delete("/{bank_account_type_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_bank_account_type(bank_account_type_id: uuid.UUID):
    conn = await get_connection()
    try:
        result = await conn.execute("DELETE FROM bank_account_type WHERE id = $1", str(bank_account_type_id))
        if result.split()[-1] == "0":
            raise HTTPException(status_code=404, detail="Bank account type not found")
    finally:
        await conn.close()

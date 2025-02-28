from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field
import uuid
from typing import List, Optional
from server.database.database import get_connection

router = APIRouter(
    prefix="/income_sources_types",
    tags=["income_sources_types"]
)

class IncomeSourceTypeBase(BaseModel):
    name: str
    value: str

class IncomeSourceTypeInCreate(IncomeSourceTypeBase):
    pass

class IncomeSourceTypeInUpdate(BaseModel):
    name: Optional[str] = None
    value: Optional[str] = None

class IncomeSourceTypeInDB(IncomeSourceTypeBase):
    id: uuid.UUID = Field(default_factory=uuid.uuid4)

@router.get("/", response_model=List[IncomeSourceTypeInDB])
async def read_income_sources_types():
    conn = await get_connection()
    try:
        rows = await conn.fetch("SELECT id, name, value FROM income_sources_types")
        return [dict(row) for row in rows]
    finally:
        await conn.close()

@router.get("/{income_source_type_id}", response_model=IncomeSourceTypeInDB)
async def read_income_source_type(income_source_type_id: uuid.UUID):
    conn = await get_connection()
    try:
        row = await conn.fetchrow("SELECT id, name, value FROM income_sources_types WHERE id = $1", str(income_source_type_id))
        if row is None:
            raise HTTPException(status_code=404, detail="Income source type not found")
        return dict(row)
    finally:
        await conn.close()

@router.post("/", response_model=IncomeSourceTypeInDB, status_code=status.HTTP_201_CREATED)
async def create_income_source_type(payload: IncomeSourceTypeInCreate):
    new_id = uuid.uuid4()
    conn = await get_connection()
    try:
        row = await conn.fetchrow(
            "INSERT INTO income_sources_types (id, name, value) VALUES ($1, $2, $3) RETURNING id, name, value",
            str(new_id), payload.name, payload.value
        )
        return dict(row)
    finally:
        await conn.close()

@router.put("/{income_source_type_id}", response_model=IncomeSourceTypeInDB)
async def update_income_source_type(income_source_type_id: uuid.UUID, payload: IncomeSourceTypeInUpdate):
    conn = await get_connection()
    try:
        existing = await conn.fetchrow("SELECT id, name, value FROM income_sources_types WHERE id = $1", str(income_source_type_id))
        if existing is None:
            raise HTTPException(status_code=404, detail="Income source type not found")
        current = dict(existing)
        new_name = payload.name if payload.name is not None else current["name"]
        new_value = payload.value if payload.value is not None else current["value"]
        updated = await conn.fetchrow(
            "UPDATE income_sources_types SET name = $1, value = $2 WHERE id = $3 RETURNING id, name, value",
            new_name, new_value, str(income_source_type_id)
        )
        return dict(updated)
    finally:
        await conn.close()

@router.delete("/{income_source_type_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_income_source_type(income_source_type_id: uuid.UUID):
    conn = await get_connection()
    try:
        result = await conn.execute("DELETE FROM income_sources_types WHERE id = $1", str(income_source_type_id))
        if result.split()[-1] == "0":
            raise HTTPException(status_code=404, detail="Income source type not found")
    finally:
        await conn.close()

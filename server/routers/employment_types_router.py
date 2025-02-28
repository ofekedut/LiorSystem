from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field
import uuid
from typing import List, Optional
from server.database.database import get_connection



router = APIRouter(
    prefix="/employment_types",
    tags=["employment_types"]
)

class EmploymentTypeBase(BaseModel):
    name: str
    value: str

class EmploymentTypeInCreate(EmploymentTypeBase):
    pass

class EmploymentTypeInUpdate(BaseModel):
    name: Optional[str] = None
    value: Optional[str] = None

class EmploymentTypeInDB(EmploymentTypeBase):
    id: uuid.UUID = Field(default_factory=uuid.uuid4)

@router.get("/", response_model=List[EmploymentTypeInDB])
async def read_employment_types():
    conn = await get_connection()
    try:
        rows = await conn.fetch("SELECT id, name, value FROM employment_types")
        return [dict(row) for row in rows]
    finally:
        await conn.close()

@router.get("/{employment_type_id}", response_model=EmploymentTypeInDB)
async def read_employment_type(employment_type_id: uuid.UUID):
    conn = await get_connection()
    try:
        row = await conn.fetchrow("SELECT id, name, value FROM employment_types WHERE id = $1", str(employment_type_id))
        if row is None:
            raise HTTPException(status_code=404, detail="Employment type not found")
        return dict(row)
    finally:
        await conn.close()

@router.post("/", response_model=EmploymentTypeInDB, status_code=status.HTTP_201_CREATED)
async def create_employment_type(payload: EmploymentTypeInCreate):
    new_id = uuid.uuid4()
    conn = await get_connection()
    try:
        row = await conn.fetchrow(
            "INSERT INTO employment_types (id, name, value) VALUES ($1, $2, $3) RETURNING id, name, value",
            str(new_id), payload.name, payload.value
        )
        return dict(row)
    finally:
        await conn.close()

@router.put("/{employment_type_id}", response_model=EmploymentTypeInDB)
async def update_employment_type(employment_type_id: uuid.UUID, payload: EmploymentTypeInUpdate):
    conn = await get_connection()
    try:
        existing = await conn.fetchrow("SELECT id, name, value FROM employment_types WHERE id = $1", str(employment_type_id))
        if existing is None:
            raise HTTPException(status_code=404, detail="Employment type not found")
        current = dict(existing)
        new_name = payload.name if payload.name is not None else current["name"]
        new_value = payload.value if payload.value is not None else current["value"]
        updated = await conn.fetchrow(
            "UPDATE employment_types SET name = $1, value = $2 WHERE id = $3 RETURNING id, name, value",
            new_name, new_value, str(employment_type_id)
        )
        return dict(updated)
    finally:
        await conn.close()

@router.delete("/{employment_type_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_employment_type(employment_type_id: uuid.UUID):
    conn = await get_connection()
    try:
        result = await conn.execute("DELETE FROM employment_types WHERE id = $1", str(employment_type_id))
        if result.split()[-1] == "0":
            raise HTTPException(status_code=404, detail="Employment type not found")
    finally:
        await conn.close()

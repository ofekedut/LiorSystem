from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field
import uuid
from typing import List, Optional
from server.database.database import get_connection

router = APIRouter(
    prefix="/person_martial_statuses",
    tags=["person_martial_statuses"]
)

class PersonMaritalStatusBase(BaseModel):
    name: str
    value: str

class PersonMaritalStatusInCreate(PersonMaritalStatusBase):
    pass

class PersonMaritalStatusInUpdate(BaseModel):
    name: Optional[str] = None
    value: Optional[str] = None

class PersonMaritalStatusInDB(PersonMaritalStatusBase):
    id: uuid.UUID = Field(default_factory=uuid.uuid4)

@router.get("/", response_model=List[PersonMaritalStatusInDB])
async def read_person_martial_statuses():
    conn = await get_connection()
    try:
        rows = await conn.fetch("SELECT id, name, value FROM person_martial_statuses")
        return [dict(row) for row in rows]
    finally:
        await conn.close()

@router.get("/{status_id}", response_model=PersonMaritalStatusInDB)
async def read_person_martial_status(status_id: uuid.UUID):
    conn = await get_connection()
    try:
        row = await conn.fetchrow("SELECT id, name, value FROM person_martial_statuses WHERE id = $1", str(status_id))
        if row is None:
            raise HTTPException(status_code=404, detail="Person marital status not found")
        return dict(row)
    finally:
        await conn.close()

@router.post("/", response_model=PersonMaritalStatusInDB, status_code=status.HTTP_201_CREATED)
async def create_person_martial_status(payload: PersonMaritalStatusInCreate):
    new_id = uuid.uuid4()
    conn = await get_connection()
    try:
        row = await conn.fetchrow(
            "INSERT INTO person_martial_statuses (id, name, value) VALUES ($1, $2, $3) RETURNING id, name, value",
            str(new_id), payload.name, payload.value
        )
        return dict(row)
    finally:
        await conn.close()

@router.put("/{status_id}", response_model=PersonMaritalStatusInDB)
async def update_person_martial_status(status_id: uuid.UUID, payload: PersonMaritalStatusInUpdate):
    conn = await get_connection()
    try:
        existing = await conn.fetchrow("SELECT id, name, value FROM person_martial_statuses WHERE id = $1", str(status_id))
        if existing is None:
            raise HTTPException(status_code=404, detail="Person marital status not found")
        current = dict(existing)
        new_name = payload.name if payload.name is not None else current["name"]
        new_value = payload.value if payload.value is not None else current["value"]
        updated = await conn.fetchrow(
            "UPDATE person_martial_statuses SET name = $1, value = $2 WHERE id = $3 RETURNING id, name, value",
            new_name, new_value, str(status_id)
        )
        return dict(updated)
    finally:
        await conn.close()

@router.delete("/{status_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_person_martial_status(status_id: uuid.UUID):
    conn = await get_connection()
    try:
        result = await conn.execute("DELETE FROM person_martial_statuses WHERE id = $1", str(status_id))
        if result.split()[-1] == "0":
            raise HTTPException(status_code=404, detail="Person marital status not found")
    finally:
        await conn.close()

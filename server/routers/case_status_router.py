from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field
import uuid
from typing import List, Optional
from server.database.database import get_connection

router = APIRouter(
    prefix="/case_status",
    tags=["case_status"]
)

class CaseStatus(BaseModel):
    name: str
    value: str

class CaseStatusInCreate(CaseStatus):
    pass

class CaseStatusInUpdate(BaseModel):
    name: Optional[str] = None
    value: Optional[str] = None

class CaseStatusInDB(CaseStatus):
    id: uuid.UUID = Field(default_factory=uuid.uuid4)

@router.get("/", response_model=List[CaseStatusInDB])
async def read_case_statuses():
    conn = await get_connection()
    try:
        rows = await conn.fetch("SELECT id, name, value FROM case_status")
        return [dict(row) for row in rows]
    finally:
        await conn.close()

@router.get("/{status_id}", response_model=CaseStatusInDB)
async def read_case_status(status_id: uuid.UUID):
    conn = await get_connection()
    try:
        row = await conn.fetchrow("SELECT id, name, value FROM case_status WHERE id = $1", str(status_id))
        if row is None:
            raise HTTPException(status_code=404, detail="Case status not found")
        return dict(row)
    finally:
        await conn.close()

@router.post("/", response_model=CaseStatusInDB, status_code=status.HTTP_201_CREATED)
async def create_case_status(payload: CaseStatusInCreate):
    new_id = uuid.uuid4()
    conn = await get_connection()
    try:
        row = await conn.fetchrow(
            "INSERT INTO case_status (id, name, value) VALUES ($1, $2, $3) RETURNING id, name, value",
            str(new_id), payload.name, payload.value
        )
        return dict(row)
    finally:
        await conn.close()

@router.put("/{status_id}", response_model=CaseStatusInDB)
async def update_case_status(status_id: uuid.UUID, payload: CaseStatusInUpdate):
    conn = await get_connection()
    try:
        existing = await conn.fetchrow("SELECT id, name, value FROM case_status WHERE id = $1", str(status_id))
        if existing is None:
            raise HTTPException(status_code=404, detail="Case status not found")
        current = dict(existing)
        new_name = payload.name if payload.name is not None else current["name"]
        new_value = payload.value if payload.value is not None else current["value"]
        updated = await conn.fetchrow(
            "UPDATE case_status SET name = $1, value = $2 WHERE id = $3 RETURNING id, name, value",
            new_name, new_value, str(status_id)
        )
        return dict(updated)
    finally:
        await conn.close()

@router.delete("/{status_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_case_status(status_id: uuid.UUID):
    conn = await get_connection()
    try:
        result = await conn.execute("DELETE FROM case_status WHERE id = $1", str(status_id))
        if result.split()[-1] == "0":
            raise HTTPException(status_code=404, detail="Case status not found")
    finally:
        await conn.close()
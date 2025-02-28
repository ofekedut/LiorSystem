from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field
import uuid
from typing import List, Optional
from server.database.database import get_connection

router = APIRouter(
    prefix="/loan_goals",
    tags=["loan_goals"]
)

class LoanGoalBase(BaseModel):
    name: str
    value: str

class LoanGoalInCreate(LoanGoalBase):
    pass

class LoanGoalInUpdate(BaseModel):
    name: Optional[str] = None
    value: Optional[str] = None

class LoanGoalInDB(LoanGoalBase):
    id: uuid.UUID = Field(default_factory=uuid.uuid4)

@router.get("/", response_model=List[LoanGoalInDB])
async def read_loan_goals():
    conn = await get_connection()
    try:
        rows = await conn.fetch("SELECT id, name, value FROM loan_goals")
        return [dict(row) for row in rows]
    finally:
        await conn.close()

@router.get("/{loan_goal_id}", response_model=LoanGoalInDB)
async def read_loan_goal(loan_goal_id: uuid.UUID):
    conn = await get_connection()
    try:
        row = await conn.fetchrow("SELECT id, name, value FROM loan_goals WHERE id = $1", str(loan_goal_id))
        if row is None:
            raise HTTPException(status_code=404, detail="Loan goal not found")
        return dict(row)
    finally:
        await conn.close()

@router.post("/", response_model=LoanGoalInDB, status_code=status.HTTP_201_CREATED)
async def create_loan_goal(payload: LoanGoalInCreate):
    new_id = uuid.uuid4()
    conn = await get_connection()
    try:
        row = await conn.fetchrow(
            "INSERT INTO loan_goals (id, name, value) VALUES ($1, $2, $3) RETURNING id, name, value",
            str(new_id), payload.name, payload.value
        )
        return dict(row)
    finally:
        await conn.close()

@router.put("/{loan_goal_id}", response_model=LoanGoalInDB)
async def update_loan_goal(loan_goal_id: uuid.UUID, payload: LoanGoalInUpdate):
    conn = await get_connection()
    try:
        existing = await conn.fetchrow("SELECT id, name, value FROM loan_goals WHERE id = $1", str(loan_goal_id))
        if existing is None:
            raise HTTPException(status_code=404, detail="Loan goal not found")
        current = dict(existing)
        new_name = payload.name if payload.name is not None else current["name"]
        new_value = payload.value if payload.value is not None else current["value"]
        updated = await conn.fetchrow(
            "UPDATE loan_goals SET name = $1, value = $2 WHERE id = $3 RETURNING id, name, value",
            new_name, new_value, str(loan_goal_id)
        )
        return dict(updated)
    finally:
        await conn.close()

@router.delete("/{loan_goal_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_loan_goal(loan_goal_id: uuid.UUID):
    conn = await get_connection()
    try:
        result = await conn.execute("DELETE FROM loan_goals WHERE id = $1", str(loan_goal_id))
        if result.split()[-1] == "0":
            raise HTTPException(status_code=404, detail="Loan goal not found")
    finally:
        await conn.close()

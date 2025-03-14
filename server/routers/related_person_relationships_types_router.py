from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field
import uuid
from typing import List, Optional
from server.database.database import get_connection

router = APIRouter(
    prefix="/related_person_relationships_types",
    tags=["related_person_relationships_types"]
)

class RelatedPersonRelationshipTypeBase(BaseModel):
    name: str
    value: str

class RelatedPersonRelationshipTypeInCreate(RelatedPersonRelationshipTypeBase):
    pass

class RelatedPersonRelationshipTypeInUpdate(BaseModel):
    name: Optional[str] = None
    value: Optional[str] = None

class RelatedPersonRelationshipTypeInDB(RelatedPersonRelationshipTypeBase):
    id: uuid.UUID = Field(default_factory=uuid.uuid4)

class RelatedPersonRelationShipTypesDB:
    @classmethod
    async def get_all(cls) -> List[RelatedPersonRelationshipTypeInDB]:
        conn = await get_connection()
        try:
            rows = await conn.fetch("SELECT id, name, value FROM related_person_relationships_types")
            return [dict(row) for row in rows]
        finally:
            await conn.close()

    @classmethod
    async def get_by_id(cls, relationship_type_id: uuid.UUID) -> RelatedPersonRelationshipTypeInDB:
        conn = await get_connection()
        try:
            row = await conn.fetchrow(
                "SELECT id, name, value FROM related_person_relationships_types WHERE id = $1",
                str(relationship_type_id)
            )
            if row is None:
                raise HTTPException(status_code=404, detail="Related person relationship type not found")
            return dict(row)
        finally:
            await conn.close()

    @classmethod
    async def create(cls, payload: RelatedPersonRelationshipTypeInCreate) -> RelatedPersonRelationshipTypeInDB:
        new_id = uuid.uuid4()
        conn = await get_connection()
        try:
            row = await conn.fetchrow(
                "INSERT INTO related_person_relationships_types (id, name, value) VALUES ($1, $2, $3) RETURNING id, name, value",
                str(new_id), payload.name, payload.value
            )
            return dict(row)
        finally:
            await conn.close()

    @classmethod
    async def update(cls, relationship_type_id: uuid.UUID, payload: RelatedPersonRelationshipTypeInUpdate) -> RelatedPersonRelationshipTypeInDB:
        conn = await get_connection()
        try:
            existing = await conn.fetchrow(
                "SELECT id, name, value FROM related_person_relationships_types WHERE id = $1",
                str(relationship_type_id)
            )
            if existing is None:
                raise HTTPException(status_code=404, detail="Related person relationship type not found")
            current = dict(existing)
            new_name = payload.name if payload.name is not None else current["name"]
            new_value = payload.value if payload.value is not None else current["value"]
            updated = await conn.fetchrow(
                "UPDATE related_person_relationships_types SET name = $1, value = $2 WHERE id = $3 RETURNING id, name, value",
                new_name, new_value, str(relationship_type_id)
            )
            return dict(updated)
        finally:
            await conn.close()

    @classmethod
    async def delete(cls, relationship_type_id: uuid.UUID) -> None:
        conn = await get_connection()
        try:
            result = await conn.execute(
                "DELETE FROM related_person_relationships_types WHERE id = $1",
                str(relationship_type_id)
            )
            if result.split()[-1] == "0":
                raise HTTPException(status_code=404, detail="Related person relationship type not found")
        finally:
            await conn.close()

    @classmethod
    async def get_by_value(cls, value):
        conn = await get_connection()
        try:
            row = await conn.fetchrow(
                "SELECT id, name, value FROM related_person_relationships_types WHERE value = $1",
                value
            )
            if row is None:
                raise HTTPException(status_code=404, detail="Related person relationship type not found")
            return dict(row)
        finally:
            await conn.close()


# Router endpoints now just call the DB class methods
@router.get("/", response_model=List[RelatedPersonRelationshipTypeInDB])
async def read_related_person_relationships_types():
    return await RelatedPersonRelationShipTypesDB.get_all()

@router.get("/{relationship_type_id}", response_model=RelatedPersonRelationshipTypeInDB)
async def read_related_person_relationship_type(relationship_type_id: uuid.UUID):
    return await RelatedPersonRelationShipTypesDB.get_by_id(relationship_type_id)

@router.post("/", response_model=RelatedPersonRelationshipTypeInDB, status_code=status.HTTP_201_CREATED)
async def create_related_person_relationship_type(payload: RelatedPersonRelationshipTypeInCreate):
    return await RelatedPersonRelationShipTypesDB.create(payload)

@router.put("/{relationship_type_id}", response_model=RelatedPersonRelationshipTypeInDB)
async def update_related_person_relationship_type(relationship_type_id: uuid.UUID, payload: RelatedPersonRelationshipTypeInUpdate):
    return await RelatedPersonRelationShipTypesDB.update(relationship_type_id, payload)

@router.delete("/{relationship_type_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_related_person_relationship_type(relationship_type_id: uuid.UUID):
    await RelatedPersonRelationShipTypesDB.delete(relationship_type_id)
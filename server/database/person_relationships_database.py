"""
Database operations for person relationships
"""
import uuid
from typing import List, Optional, Dict, Any
from pydantic import BaseModel

from server.database.database import get_connection


class RelationshipBase(BaseModel):
    from_person_id: uuid.UUID
    to_person_id: uuid.UUID
    relationship_type_id: uuid.UUID


class RelationshipInCreate(RelationshipBase):
    pass


class RelationshipInDB(RelationshipBase):
    pass


class RelationshipInUpdate(BaseModel):
    relationship_type_id: uuid.UUID


class RelationshipExtended(RelationshipInDB):
    """Extended model with person and relationship type details"""
    relationship_type_name: str
    relationship_type_value: str
    person_first_name: str
    person_last_name: str


async def create_relationship(payload: RelationshipInCreate) -> RelationshipInDB:
    """
    Create a new relationship between two persons
    """
    query = """
    INSERT INTO case_person_relations (from_person_id, to_person_id, relationship_type_id)
    VALUES ($1, $2, $3)
    RETURNING from_person_id, to_person_id, relationship_type_id
    """

    values = [
        payload.from_person_id,
        payload.to_person_id,
        payload.relationship_type_id
    ]

    conn = await get_connection()
    try:
        row = await conn.fetchrow(query, *values)
        return RelationshipInDB.model_validate(dict(row))
    finally:
        await conn.close()


async def get_relationship(from_person_id: uuid.UUID, to_person_id: uuid.UUID) -> Optional[RelationshipInDB]:
    """
    Get a specific relationship between two persons
    """
    query = """
    SELECT from_person_id, to_person_id, relationship_type_id
    FROM case_person_relations
    WHERE from_person_id = $1 AND to_person_id = $2
    """

    conn = await get_connection()
    try:
        row = await conn.fetchrow(query, from_person_id, to_person_id)
        if row:
            return RelationshipInDB.model_validate(dict(row))
        return None
    finally:
        await conn.close()


async def get_relationships_for_person(person_id: uuid.UUID) -> List[RelationshipExtended]:
    """
    Get all relationships where the person is either the source or target,
    including details about the related person and relationship type
    """
    # Updated query to use lior_dropdown_options instead of related_person_relationships_types
    query = """
    SELECT 
        r.from_person_id, 
        r.to_person_id,
        r.relationship_type_id,
        rt.name as relationship_type_name,
        rt.value as relationship_type_value,
        p.first_name as person_first_name,
        p.last_name as person_last_name
    FROM 
        case_person_relations r
    JOIN 
        lior_dropdown_options rt ON r.relationship_type_id = rt.id AND rt.category = 'related_person_relationships_types'
    JOIN 
        case_persons p ON (
            CASE 
                WHEN r.from_person_id = $1 THEN r.to_person_id = p.id
                ELSE r.from_person_id = p.id
            END
        )
    WHERE 
        r.from_person_id = $1 OR r.to_person_id = $1
    """

    conn = await get_connection()
    try:
        rows = await conn.fetch(query, person_id)
        result = []
        for row in rows:
            data = dict(row)
            result.append(RelationshipExtended.model_validate(data))
        return result
    finally:
        await conn.close()


async def update_relationship(
        from_person_id: uuid.UUID,
        to_person_id: uuid.UUID,
        payload: RelationshipInUpdate
) -> Optional[RelationshipInDB]:
    """
    Update a relationship between two persons
    """
    query = """
    UPDATE case_person_relations
    SET relationship_type_id = $3
    WHERE from_person_id = $1 AND to_person_id = $2
    RETURNING from_person_id, to_person_id, relationship_type_id
    """

    conn = await get_connection()
    try:
        row = await conn.fetchrow(query, from_person_id, to_person_id, payload.relationship_type_id)
        if row:
            return RelationshipInDB.model_validate(dict(row))
        return None
    finally:
        await conn.close()


async def delete_relationship(from_person_id: uuid.UUID, to_person_id: uuid.UUID) -> bool:
    """
    Delete a relationship between two persons
    """
    query = """
    DELETE FROM case_person_relations
    WHERE from_person_id = $1 AND to_person_id = $2
    RETURNING from_person_id
    """

    conn = await get_connection()
    try:
        row = await conn.fetchrow(query, from_person_id, to_person_id)
        return row is not None
    finally:
        await conn.close()


async def check_persons_in_same_case(person_id1: uuid.UUID, person_id2: uuid.UUID) -> Optional[uuid.UUID]:
    """
    Check if two persons belong to the same case and return the case_id if they do
    """
    query = """
    SELECT p1.case_id
    FROM case_persons p1
    JOIN case_persons p2 ON p1.case_id = p2.case_id
    WHERE p1.id = $1 AND p2.id = $2
    """

    conn = await get_connection()
    try:
        row = await conn.fetchrow(query, person_id1, person_id2)
        if row:
            return row['case_id']
        return None
    finally:
        await conn.close()
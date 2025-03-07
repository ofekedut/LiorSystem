import uuid
from typing import List, Optional
from pydantic import BaseModel
from datetime import datetime

from server.database.database import get_connection


class PersonAsset(BaseModel):
    id: uuid.UUID
    person_id: uuid.UUID
    asset_type_id: uuid.UUID
    description: str
    created_at: datetime
    updated_at: datetime


class PersonAssetInCreate(BaseModel):
    person_id: uuid.UUID
    asset_type_id: uuid.UUID
    description: str


class PersonAssetInUpdate(BaseModel):
    asset_type_id: Optional[uuid.UUID] = None
    description: Optional[str] = None


async def create_person_asset(payload: PersonAssetInCreate) -> PersonAsset | None:
    """Create a new person asset record in the database"""
    query = """
    INSERT INTO person_assets (id, person_id, asset_type_id, description, created_at, updated_at)
    VALUES ($1, $2, $3, $4, NOW(), NOW())
    RETURNING id, person_id, asset_type_id, description, created_at, updated_at
    """
    
    conn = await get_connection()
    try:
        async with conn.transaction():
            asset_id = uuid.uuid4()
            row = await conn.fetchrow(
                query, 
                asset_id, 
                payload.person_id, 
                payload.asset_type_id, 
                payload.description
            )
            
            if row:
                return PersonAsset.model_validate(dict(row))
            return None
    except Exception as e:
        # Log the exception or handle it as needed
        print(f"Error creating person asset: {str(e)}")
        return None
    finally:
        await conn.close()


async def get_person_assets_by_person_id(person_id: uuid.UUID) -> List[PersonAsset] | None:
    """Get all assets for a specific person"""
    query = """
    SELECT id, person_id, asset_type_id, description, created_at, updated_at
    FROM person_assets
    WHERE person_id = $1
    """
    
    conn = await get_connection()
    try:
        async with conn.transaction():
            rows = await conn.fetch(query, person_id)
            
            if rows:
                return [PersonAsset.model_validate(dict(row)) for row in rows]
            return []
    except Exception as e:
        # Log the exception or handle it as needed
        print(f"Error getting person assets: {str(e)}")
        return None
    finally:
        await conn.close()


async def get_person_asset_by_id(asset_id: uuid.UUID) -> Optional[PersonAsset]:
    """Get a specific person asset by its ID"""
    query = """
    SELECT id, person_id, asset_type_id, description, created_at, updated_at
    FROM person_assets
    WHERE id = $1
    """
    
    conn = await get_connection()
    try:
        async with conn.transaction():
            row = await conn.fetchrow(query, asset_id)
            
            if row:
                return PersonAsset.model_validate(dict(row))
            return None
    except Exception as e:
        # Log the exception or handle it as needed
        print(f"Error getting person asset: {str(e)}")
        return None
    finally:
        await conn.close()


async def update_person_asset(asset_id: uuid.UUID, payload: PersonAssetInUpdate) -> Optional[PersonAsset]:
    """Update an existing person asset"""
    # Build the SET clause dynamically based on provided fields
    set_clauses = []
    values = [asset_id]
    param_index = 2  # Start from $2 since $1 is asset_id
    
    if payload.asset_type_id is not None:
        set_clauses.append(f"asset_type_id = ${param_index}")
        values.append(payload.asset_type_id)
        param_index += 1
        
    if payload.description is not None:
        set_clauses.append(f"description = ${param_index}")
        values.append(payload.description)
        param_index += 1
    
    # If no fields to update, return the existing record
    if not set_clauses:
        return await get_person_asset_by_id(asset_id)
    
    # Add updated_at timestamp to SET clause
    set_clauses.append("updated_at = NOW()")
    
    # Build the final query
    query = f"""
    UPDATE person_assets
    SET {", ".join(set_clauses)}
    WHERE id = $1
    RETURNING id, person_id, asset_type_id, description, created_at, updated_at
    """
    
    conn = await get_connection()
    try:
        async with conn.transaction():
            row = await conn.fetchrow(query, *values)
            
            if row:
                return PersonAsset.model_validate(dict(row))
            return None
    except Exception as e:
        # Log the exception or handle it as needed
        print(f"Error updating person asset: {str(e)}")
        return None
    finally:
        await conn.close()


async def delete_person_asset(asset_id: uuid.UUID) -> bool:
    """Delete a person asset by its ID"""
    query = """
    DELETE FROM person_assets
    WHERE id = $1
    RETURNING id
    """
    
    conn = await get_connection()
    try:
        async with conn.transaction():
            row = await conn.fetchrow(query, asset_id)
            return row is not None
    except Exception as e:
        # Log the exception or handle it as needed
        print(f"Error deleting person asset: {str(e)}")
        return False
    finally:
        await conn.close()

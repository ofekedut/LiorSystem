import uuid
from typing import List, Optional
from pydantic import BaseModel

from server.database.database import get_connection


class AssetType(BaseModel):
    id: uuid.UUID
    name: str
    value: str


class AssetTypeInCreate(BaseModel):
    name: str
    value: str


class AssetTypeInUpdate(BaseModel):
    name: Optional[str] = None
    value: Optional[str] = None


async def create_asset_type(payload: AssetTypeInCreate) -> AssetType | None:
    query = """
    INSERT INTO asset_types (id, name, value)
    VALUES ($1, $2, $3)
    RETURNING id, name, value
    """
    role_id = uuid.uuid4()
    values = [role_id, payload.name, payload.value]

    conn = await get_connection()
    try:
        row = await conn.fetchrow(query, *values)
        return AssetType.model_validate(dict(row))
    finally:
        await conn.close()


async def get_asset_types() -> List[AssetType] | None:
    query = """
    SELECT id, name, value
    FROM asset_types
    """

    conn = await get_connection()
    try:
        rows = await conn.fetch(query)
        return [AssetType.model_validate(dict(row)) for row in rows]
    finally:
        await conn.close()


async def get_asset_type_by_id(asset_type_id: uuid.UUID) -> Optional[AssetType]:
    query = """
    SELECT id, name, value
    FROM asset_types
    WHERE id = $1
    """

    conn = await get_connection()
    try:
        row = await conn.fetchrow(query, asset_type_id)
        if row:
            return AssetType.model_validate(dict(row))
        return None
    finally:
        await conn.close()


async def get_asset_type_by_value(value: str) -> Optional[AssetType]:
    query = """
    SELECT id, name, value
    FROM asset_types
    WHERE value = $1
    """

    conn = await get_connection()
    try:
        row = await conn.fetchrow(query, value)
        if row:
            return AssetType.model_validate(dict(row))
        return None
    finally:
        await conn.close()


async def update_asset_type(asset_type_id: uuid.UUID, payload: AssetTypeInUpdate) -> Optional[AssetType]:
    update_parts = []
    values = [asset_type_id]
    param_index = 2

    if payload.name is not None:
        update_parts.append(f"name = ${param_index}")
        values.append(payload.name)
        param_index += 1

    if payload.value is not None:
        update_parts.append(f"value = ${param_index}")
        values.append(payload.value)
        param_index += 1

    if not update_parts:
        # Nothing to update
        return await get_asset_type_by_id(asset_type_id)

    update_clause = ", ".join(update_parts)
    query = f"""
    UPDATE asset_types
    SET {update_clause}
    WHERE id = $1
    RETURNING id, name, value
    """

    conn = await get_connection()
    try:
        row = await conn.fetchrow(query, *values)
        if row:
            await conn.close()
            return AssetType.model_validate(dict(row))
        return None
    finally:
        await conn.close()


async def delete_asset_type(asset_type_id: uuid.UUID) -> bool:
    query = """
    DELETE FROM asset_types
    WHERE id = $1
    RETURNING id
    """
    conn = await get_connection()
    try:
        row = await conn.fetchrow(query, asset_type_id)
        await conn.close()
        return row is not None
    finally:
        await conn.close()
        return  False

import datetime
import uuid
from typing import List, Optional

from pydantic import BaseModel, Field

from server.database.database import get_connection


class DocumentCategoryBase(BaseModel):
    name: str
    value: str


class DocumentCategoryInCreate(DocumentCategoryBase):
    pass


class DocumentCategoryInUpdate(BaseModel):
    name: Optional[str] = None
    value: Optional[str] = None


class DocumentCategory(DocumentCategoryBase):
    id: uuid.UUID
    created_at: datetime.datetime
    updated_at: datetime.datetime

    class Config:
        from_attributes = True


async def create_document_category(payload: DocumentCategoryInCreate) -> DocumentCategory:
    query = """
    INSERT INTO document_categories (name, value)
    VALUES ($1, $2)
    RETURNING id, name, value, created_at, updated_at
    """
    values = [payload.name, payload.value]
    
    conn = await get_connection()
    try:
        row = await conn.fetchrow(query, *values)
        return DocumentCategory.model_validate(dict(row))
    finally:
        await conn.close()


async def get_document_categories() -> List[DocumentCategory]:
    query = """
    SELECT id, name, value, created_at, updated_at
    FROM document_categories
    ORDER BY name
    """
    conn = await get_connection()
    try:
        rows = await conn.fetch(query)
        return [DocumentCategory.model_validate(dict(row)) for row in rows]
    finally:
        await conn.close()


async def get_document_category(document_category_id: uuid.UUID) -> Optional[DocumentCategory]:
    query = """
    SELECT id, name, value, created_at, updated_at
    FROM document_categories
    WHERE id = $1
    """
    conn = await get_connection()
    try:
        row = await conn.fetchrow(query, document_category_id)
        if row:
            return DocumentCategory.model_validate(dict(row))
        return None
    finally:
        await conn.close()


async def get_document_category_by_value(value: str) -> Optional[DocumentCategory]:
    query = """
    SELECT id, name, value, created_at, updated_at
    FROM document_categories
    WHERE value = $1
    """
    conn = await get_connection()
    try:
        row = await conn.fetchrow(query, value)
        if row:
            return DocumentCategory.model_validate(dict(row))
        return None
    finally:
        await conn.close()


async def update_document_category(document_category_id: uuid.UUID, payload: DocumentCategoryInUpdate) -> Optional[DocumentCategory]:
    # Build the update sets dynamically based on what fields are provided
    update_fields = []
    values = [document_category_id]
    counter = 2  # Start from $2 since $1 is document_category_id
    
    if payload.name is not None:
        update_fields.append(f"name = ${counter}")
        values.append(payload.name)
        counter += 1
    
    if payload.value is not None:
        update_fields.append(f"value = ${counter}")
        values.append(payload.value)
        counter += 1
    
    if not update_fields:
        # If no fields to update, just return the current document category
        return await get_document_category(document_category_id)
    
    query = f"""
    UPDATE document_categories
    SET {", ".join(update_fields)}
    WHERE id = $1
    RETURNING id, name, value, created_at, updated_at
    """
    
    conn = await get_connection()
    try:
        row = await conn.fetchrow(query, *values)
        if row:
            return DocumentCategory.model_validate(dict(row))
        return None
    finally:
        await conn.close()


async def delete_document_category(document_category_id: uuid.UUID) -> bool:
    query = """
    DELETE FROM document_categories
    WHERE id = $1
    RETURNING id
    """
    conn = await get_connection()
    try:
        row = await conn.fetchrow(query, document_category_id)
        return row is not None
    finally:
        await conn.close()

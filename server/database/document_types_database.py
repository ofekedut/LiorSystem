import datetime
import uuid
from typing import List, Optional

from pydantic import BaseModel, Field

from server.database.database import get_connection


class DocumentTypeBase(BaseModel):
    name: str
    value: str


class DocumentTypeInCreate(DocumentTypeBase):
    pass


class DocumentTypeInUpdate(BaseModel):
    name: Optional[str] = None
    value: Optional[str] = None


class DocumentType(DocumentTypeBase):
    id: uuid.UUID
    created_at: datetime.datetime
    updated_at: datetime.datetime

    class Config:
        from_attributes = True


async def create_document_type(payload: DocumentTypeInCreate) -> DocumentType:
    query = """
    INSERT INTO document_types (name, value)
    VALUES ($1, $2)
    RETURNING id, name, value, created_at, updated_at
    """
    values = [payload.name, payload.value]
    
    conn = await get_connection()
    try:
        row = await conn.fetchrow(query, *values)
        return DocumentType.model_validate(dict(row))
    finally:
        await conn.close()


async def get_document_types() -> List[DocumentType]:
    query = """
    SELECT id, name, value, created_at, updated_at
    FROM document_types
    ORDER BY name
    """
    conn = await get_connection()
    try:
        rows = await conn.fetch(query)
        return [DocumentType.model_validate(dict(row)) for row in rows]
    finally:
        await conn.close()


async def get_document_type(document_type_id: uuid.UUID) -> Optional[DocumentType]:
    query = """
    SELECT id, name, value, created_at, updated_at
    FROM document_types
    WHERE id = $1
    """
    conn = await get_connection()
    try:
        row = await conn.fetchrow(query, document_type_id)
        if row:
            return DocumentType.model_validate(dict(row))
        return None
    finally:
        await conn.close()


async def update_document_type(document_type_id: uuid.UUID, payload: DocumentTypeInUpdate) -> Optional[DocumentType]:
    # Build the update sets dynamically based on what fields are provided
    update_fields = []
    values = [document_type_id]
    counter = 2  # Start from $2 since $1 is document_type_id
    
    if payload.name is not None:
        update_fields.append(f"name = ${counter}")
        values.append(payload.name)
        counter += 1
    
    if payload.value is not None:
        update_fields.append(f"value = ${counter}")
        values.append(payload.value)
        counter += 1
    
    if not update_fields:
        # If no fields to update, just return the current document type
        return await get_document_type(document_type_id)
    
    query = f"""
    UPDATE document_types
    SET {", ".join(update_fields)}
    WHERE id = $1
    RETURNING id, name, value, created_at, updated_at
    """
    
    conn = await get_connection()
    try:
        row = await conn.fetchrow(query, *values)
        if row:
            return DocumentType.model_validate(dict(row))
        return None
    finally:
        await conn.close()


async def delete_document_type(document_type_id: uuid.UUID) -> bool:
    query = """
    DELETE FROM document_types
    WHERE id = $1
    RETURNING id
    """
    conn = await get_connection()
    try:
        row = await conn.fetchrow(query, document_type_id)
        return row is not None
    finally:
        await conn.close()

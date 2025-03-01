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
    ON CONFLICT (value) DO UPDATE 
    SET name = $1
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


async def update_document_category(document_category_id: uuid.UUID, payload: DocumentCategoryInUpdate, cascade_updates: bool = False) -> Optional[DocumentCategory]:
    """Update a document category.
    
    Args:
        document_category_id: The UUID of the category to update
        payload: The update data containing new name and/or value
        cascade_updates: If True, documents using this category will have their references updated
                        If False, will block updates to categories that are in use
    
    Returns:
        The updated DocumentCategory or None if not found
        
    Raises:
        ValueError: If the update would conflict with existing categories or if
                   cascade_updates=False and the category is in use
    """
    # Get the current document category
    current = await get_document_category(document_category_id)
    if not current:
        return None

    # Determine what values to update
    name = payload.name if payload.name is not None else current.name
    value = payload.value if payload.value is not None else current.value
    
    conn = await get_connection()
    try:
        # For unique constraints, we'll handle manually
        # If we're changing the value, first check if it would conflict
        if payload.value is not None and payload.value != current.value:
            # Check if the new value already exists
            check_query = "SELECT id FROM document_categories WHERE value = $1 AND id != $2"
            existing = await conn.fetchrow(check_query, payload.value, document_category_id)
            if existing:
                raise ValueError(f"Document category with value '{payload.value}' already exists")
            
            # Check if there are any documents using this category
            check_references_query = "SELECT COUNT(*) FROM documents WHERE category = $1"
            referenced_count = await conn.fetchval(check_references_query, current.value)
            if referenced_count > 0:
                if not cascade_updates:
                    # Block the change if cascading is not enabled
                    raise ValueError(f"Cannot change value of category '{current.value}' because it is used by {referenced_count} document(s). Update the documents first to use a different category or enable cascade_updates.")
                else:
                    # Update the documents to use the new category value
                    update_docs_query = "UPDATE documents SET category = $1 WHERE category = $2"
                    await conn.execute(update_docs_query, value, current.value)
        
        update_query = """
        UPDATE document_categories
        SET name = $2, value = $3, updated_at = NOW()
        WHERE id = $1
        RETURNING id, name, value, created_at, updated_at
        """
        
        row = await conn.fetchrow(update_query, document_category_id, name, value)
        if row:
            return DocumentCategory.model_validate(dict(row))
        return None
    finally:
        await conn.close()


async def delete_document_category(document_category_id: uuid.UUID, cascade_delete: bool = False) -> bool:
    """Delete a document category.
    
    Args:
        document_category_id: The UUID of the category to delete
        cascade_delete: If True, documents using this category will also be deleted.
                        If False, will block deletion of categories that are in use.
    
    Returns:
        True if deleted, False if not found
        
    Raises:
        ValueError: If cascade_delete=False and the category is in use by documents
    """
    conn = await get_connection()
    try:
        # First get the category value
        category = await get_document_category(document_category_id)
        if not category:
            return False
            
        # Check if there are documents using this category
        check_query = "SELECT COUNT(*) FROM documents WHERE category = $1"
        referenced_count = await conn.fetchval(check_query, category.value)
        if referenced_count > 0:
            if not cascade_delete:
                raise ValueError(f"Cannot delete category '{category.value}' because it is used by {referenced_count} document(s). Update or delete those documents first, or use cascade_delete=True.")
            else:
                # Delete all documents with this category
                delete_docs_query = "DELETE FROM documents WHERE category = $1"
                await conn.execute(delete_docs_query, category.value)
        
        # If no references, proceed with deletion
        delete_query = """
        DELETE FROM document_categories
        WHERE id = $1
        RETURNING id
        """
        row = await conn.fetchrow(delete_query, document_category_id)
        return row is not None
    finally:
        await conn.close()

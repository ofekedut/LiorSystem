import uuid
from typing import List

from fastapi import APIRouter, HTTPException, status

from server.database.document_categories_database import (
    DocumentCategory,
    DocumentCategoryInCreate,
    DocumentCategoryInUpdate,
    create_document_category,
    delete_document_category,
    get_document_category,
    get_document_categories,
    update_document_category,
    get_document_category_by_value,
)

router = APIRouter(prefix="/document_categories", tags=["document_categories"])


@router.post("/", response_model=DocumentCategory, status_code=status.HTTP_201_CREATED)
async def create_document_category_endpoint(payload: DocumentCategoryInCreate):
    """
    Create a new document category.
    """
    return await create_document_category(payload)


@router.get("/", response_model=List[DocumentCategory])
async def read_document_categories():
    """
    Retrieve all document categories.
    """
    return await get_document_categories()


@router.get("/value/{value}", response_model=DocumentCategory)
async def read_document_category_by_value(value: str):
    """
    Retrieve a document category by its value.
    """
    document_category = await get_document_category_by_value(value)
    if document_category is None:
        raise HTTPException(status_code=404, detail="Document category not found")
    return document_category


@router.get("/{document_category_id}", response_model=DocumentCategory)
async def read_document_category(document_category_id: uuid.UUID):
    """
    Retrieve a document category by ID.
    """
    document_category = await get_document_category(document_category_id)
    if document_category is None:
        raise HTTPException(status_code=404, detail="Document category not found")
    return document_category


@router.put("/{document_category_id}", response_model=DocumentCategory)
async def update_document_category_endpoint(document_category_id: uuid.UUID, payload: DocumentCategoryInUpdate):
    """
    Update a document category.
    """
    try:
        document_category = await update_document_category(document_category_id, payload)
        if document_category is None:
            raise HTTPException(status_code=404, detail="Document category not found")
        return document_category
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))


@router.delete("/{document_category_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_document_category_endpoint(document_category_id: uuid.UUID):
    """
    Delete a document category.
    """
    deleted = await delete_document_category(document_category_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Document category not found")
    return None

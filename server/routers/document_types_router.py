import uuid
from typing import List

from fastapi import APIRouter, HTTPException, status

from server.database.document_types_database import (
    DocumentType,
    DocumentTypeInCreate,
    DocumentTypeInUpdate,
    create_document_type,
    delete_document_type,
    get_document_type,
    get_document_types,
    update_document_type,
)

router = APIRouter(prefix="/document_types", tags=["document_types"])


@router.post("/", response_model=DocumentType, status_code=status.HTTP_201_CREATED)
async def create_document_type_endpoint(payload: DocumentTypeInCreate):
    """
    Create a new document type.
    """
    return await create_document_type(payload)


@router.get("/", response_model=List[DocumentType])
async def read_document_types():
    """
    Retrieve all document types.
    """
    return await get_document_types()


@router.get("/{document_type_id}", response_model=DocumentType)
async def read_document_type(document_type_id: uuid.UUID):
    """
    Retrieve a document type by ID.
    """
    document_type = await get_document_type(document_type_id)
    if document_type is None:
        raise HTTPException(status_code=404, detail="Document type not found")
    return document_type


@router.put("/{document_type_id}", response_model=DocumentType)
async def update_document_type_endpoint(document_type_id: uuid.UUID, payload: DocumentTypeInUpdate):
    """
    Update a document type.
    """
    document_type = await update_document_type(document_type_id, payload)
    if document_type is None:
        raise HTTPException(status_code=404, detail="Document type not found")
    return document_type


@router.delete("/{document_type_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_document_type_endpoint(document_type_id: uuid.UUID):
    """
    Delete a document type.
    """
    deleted = await delete_document_type(document_type_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Document type not found")
    return None

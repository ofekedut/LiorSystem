"""
API endpoints for unique document types management.
"""
from typing import List, Optional, Dict, Any
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form
from fastapi.responses import JSONResponse

from server.database.auth_database import get_current_user_id
from server.database.unique_docs_database import (
    UniqueDocTypeCreate,
    UniqueDocTypeUpdate,
    UniqueDocTypeInDB,
    create_unique_doc_type,
    get_unique_doc_type,
    update_unique_doc_type,
    delete_unique_doc_type,
    list_unique_doc_types,
    filter_by_category,
    filter_by_target_object,
    DocumentCategory,
    DocumentTargetObject,
    import_doc_types_from_csv
)

router = APIRouter(
    prefix="/unique-docs",
    tags=["unique_documents"]
)


@router.get("", response_model=List[UniqueDocTypeInDB])
async def get_all_document_types():
    """
    Get all unique document types.
    """
    return await list_unique_doc_types()


@router.get("/{doc_type_id}", response_model=UniqueDocTypeInDB)
async def get_document_type(doc_type_id: UUID):
    """
    Get a specific unique document type by ID.
    """
    doc_type = await get_unique_doc_type(doc_type_id)
    if not doc_type:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Document type with ID {doc_type_id} not found"
        )
    return doc_type


@router.post("", response_model=UniqueDocTypeInDB, status_code=status.HTTP_201_CREATED)
async def create_document_type(doc_type: UniqueDocTypeCreate):
    """
    Create a new unique document type.
    """
    try:
        return await create_unique_doc_type(doc_type)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.put("/{doc_type_id}", response_model=UniqueDocTypeInDB)
async def update_document_type(doc_type_id: UUID, doc_type: UniqueDocTypeUpdate):
    """
    Update an existing unique document type.
    """
    try:
        updated_doc_type = await update_unique_doc_type(doc_type_id, doc_type)
        if not updated_doc_type:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Document type with ID {doc_type_id} not found"
            )
        return updated_doc_type
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.delete("/{doc_type_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_document_type(doc_type_id: UUID):
    """
    Delete a unique document type.
    """
    try:
        deleted = await delete_unique_doc_type(doc_type_id)
        if not deleted:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Document type with ID {doc_type_id} not found"
            )
        return JSONResponse(status_code=status.HTTP_204_NO_CONTENT, content=None)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(e)
        )


@router.get("/category/{category}", response_model=List[UniqueDocTypeInDB])
async def get_document_types_by_category(category: str):
    """
    Get unique document types by category.
    """
    # Validate category
    try:
        category_enum = DocumentCategory(category)
    except ValueError:
        valid_categories = [cat.value for cat in DocumentCategory]
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid category. Valid categories are: {valid_categories}"
        )

    return await filter_by_category(category)


@router.get("/target/{target_object}", response_model=List[UniqueDocTypeInDB])
async def get_document_types_by_target_object(target_object: str):
    """
    Get unique document types by target object.
    """
    # Validate target object
    try:
        target_object_enum = DocumentTargetObject(target_object)
    except ValueError:
        valid_targets = [target.value for target in DocumentTargetObject]
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid target object. Valid target objects are: {valid_targets}"
        )

    return await filter_by_target_object(target_object)


@router.post("/import", response_model=Dict[str, Any])
async def import_document_types_from_csv(file: UploadFile = File(...)):
    """
    Import document types from a CSV file.
    This implements the "Import document types in bulk via CSV" feature mentioned in the PRD.
    
    The CSV should have the following columns:
    - display_name: Name of the document type
    - category: One of the valid document categories
    - target_object: Entity type the document relates to
    - document_type: Type of document (one_time, updatable, recurring)
    - is_recurring: Whether the document is recurring (true/false)
    - frequency: Required if is_recurring is true (monthly, quarterly, yearly)
    - issuer: Optional issuer of the document
    - required_for: Comma-separated list of groups this document is required for
    """
    # Validate file type
    if not file.filename.endswith('.csv'):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only CSV files are accepted for import"
        )
    
    # Read file content
    csv_content = await file.read()
    
    try:
        # Try to decode as UTF-8
        csv_text = csv_content.decode('utf-8')
    except UnicodeDecodeError:
        # If UTF-8 decoding fails, try other common encodings
        try:
            csv_text = csv_content.decode('latin-1')
        except Exception:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Unable to decode CSV file. Please ensure it is a valid CSV file with UTF-8 or Latin-1 encoding."
            )
    
    # Process the CSV content
    try:
        result = await import_doc_types_from_csv(csv_text)
        return result
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error processing CSV: {str(e)}"
        )

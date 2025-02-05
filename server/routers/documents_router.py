from typing import List
from uuid import UUID

from fastapi import APIRouter, HTTPException

from server.database.documents_databse import (
    list_documents,
    get_document,
    create_document,
    update_document,
    delete_document,
    get_document_fields,
    create_document_field,
    delete_document_field,
    get_validation_rules,
    create_validation_rule,
    delete_validation_rule,
    DocumentInCreate,
    DocumentUpdate,
    DocumentInDB,
    DocumentFieldCreate,
    DocumentField,
    ValidationRuleCreate,
    ValidationRule,
)

router = APIRouter()


@router.get("/documents", response_model=List[DocumentInDB])
async def read_documents():
    """
    Retrieve all documents.
    """
    return await list_documents()


@router.get("/documents/{document_id}", response_model=DocumentInDB)
async def read_document(document_id: UUID):
    """
    Get a specific document by ID.
    """
    doc = await get_document(document_id)
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    return doc


@router.post("/documents", response_model=DocumentInDB, status_code=201)
async def create_new_document(document_in: DocumentInCreate):
    """
    Create a new document.
    """
    return await create_document(document_in)


@router.put("/documents/{document_id}", response_model=DocumentInDB)
async def update_existing_document(document_id: UUID, document_update: DocumentUpdate):
    """
    Update an existing document by ID.
    """
    updated = await update_document(document_id, document_update)
    if not updated:
        raise HTTPException(status_code=404, detail="Document not found or not updated")
    return updated


@router.delete("/documents/{document_id}", status_code=204)
async def remove_document(document_id: UUID):
    """
    Delete a document by ID.
    """
    success = await delete_document(document_id)
    if not success:
        raise HTTPException(status_code=404, detail="Document not found")
    return None  # 204: No Content


# -------------------------------------------------
# 3. Document Fields Endpoints
# -------------------------------------------------

@router.get("/documents/{document_id}/fields", response_model=List[DocumentField])
async def read_document_fields(document_id: UUID):
    """
    Retrieve all fields for a given document.
    """
    doc = await get_document(document_id)
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")

    return await get_document_fields(document_id)


@router.post("/documents/{document_id}/fields", response_model=DocumentField, status_code=201)
async def create_field_for_document(document_id: UUID, field_in: DocumentFieldCreate):
    """
    Create a new field for a given document.
    """
    if field_in.document_id != document_id:
        raise HTTPException(status_code=400, detail="document_id mismatch")

    doc = await get_document(document_id)
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")

    return await create_document_field(field_in)


@router.delete("/fields/{field_id}", status_code=204)
async def remove_document_field(field_id: UUID):
    """
    Delete a single field by its ID.
    """
    success = await delete_document_field(field_id)
    if not success:
        raise HTTPException(status_code=404, detail="Field not found")
    return None


# -------------------------------------------------
# 4. Validation Rules Endpoints
# -------------------------------------------------

@router.get("/documents/{document_id}/validation_rules", response_model=List[ValidationRule])
async def read_validation_rules(document_id: UUID):
    """
    Retrieve all validation rules for a given document.
    """
    doc = await get_document(document_id)
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")

    return await get_validation_rules(document_id)


@router.post("/documents/{document_id}/validation_rules", response_model=ValidationRule, status_code=201)
async def create_rule_for_document(document_id: UUID, rule_in: ValidationRuleCreate):
    """
    Create a new validation rule for a given document.
    """
    if rule_in.document_id != document_id:
        raise HTTPException(status_code=400, detail="document_id mismatch")

    doc = await get_document(document_id)
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")

    return await create_validation_rule(rule_in)


@router.delete("/validation_rules/{rule_id}", status_code=204)
async def remove_validation_rule(rule_id: UUID):
    """
    Delete a validation rule by ID.
    """
    success = await delete_validation_rule(rule_id)
    if not success:
        raise HTTPException(status_code=404, detail="Validation rule not found")
    return None

"""
Database operations for bulk document upload and management.
This implements the bulk document upload capability mentioned in the PRD.
"""
import uuid
import os
from typing import List, Optional, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field

from server.database.database import get_connection
from server.database.case_documents_database import (
    CaseDocumentCreate,
    CaseDocumentInDB,
    CaseDocumentWithTypeInfo,
    CaseDocumentUpdate,
    create_case_document,
    update_case_document,
    get_case_document
)


# -----------------------------------------------------------------------------
# Bulk Upload Data Models
# -----------------------------------------------------------------------------

class BulkDocumentUploadRequest(BaseModel):
    """Request model for bulk document upload"""
    case_id: uuid.UUID
    process_immediately: bool = False  # Whether to attempt automatic classification


class BulkUploadedDocument(BaseModel):
    """Information about a single uploaded document in a bulk upload"""
    id: uuid.UUID
    case_id: uuid.UUID
    filename: str
    file_path: str
    status: str = "pending"
    processing_status: str = "unidentified"
    uploaded_at: datetime = Field(default_factory=datetime.utcnow)
    doc_type_id: Optional[uuid.UUID] = None
    target_object_type: Optional[str] = None
    target_object_id: Optional[uuid.UUID] = None


class BulkUploadResult(BaseModel):
    """Result of a bulk document upload operation"""
    case_id: uuid.UUID
    uploaded_count: int
    documents: List[BulkUploadedDocument]
    success: bool
    errors: Optional[List[str]] = Field(default_factory=list)


class BulkDocumentClassification(BaseModel):
    """Request model for classifying a bulk-uploaded document"""
    document_id: uuid.UUID
    doc_type_id: uuid.UUID
    target_object_type: Optional[str] = None
    target_object_id: Optional[uuid.UUID] = None
    status: str = "received"


class BulkClassificationResult(BaseModel):
    """Result of a bulk document classification operation"""
    classified_count: int
    documents: List[CaseDocumentWithTypeInfo]
    success: bool
    errors: Optional[List[str]] = Field(default_factory=list)


# -----------------------------------------------------------------------------
# Bulk Upload Database Operations
# -----------------------------------------------------------------------------

async def create_bulk_documents(
    case_id: uuid.UUID,
    file_paths: List[str]
) -> BulkUploadResult:
    """
    Create multiple unidentified documents for a case in a single operation.

    Args:
        case_id: UUID of the case
        file_paths: List of file paths where the uploaded documents are stored

    Returns:
        BulkUploadResult: Result of the operation
    """
    conn = await get_connection()
    uploaded_documents = []
    errors = []

    try:
        # For each file, create an unidentified document in the case
        for file_path in file_paths:
            try:
                # Extract filename from path
                filename = os.path.basename(file_path)

                # Create a case document record with minimal information
                doc_data = CaseDocumentCreate(
                    case_id=case_id,
                    document_id=None,  # This will be created or linked later during classification
                    doc_type_id=None,  # Unidentified initially
                    status="pending",
                    target_object_type=None,  # Unlinked initially
                    target_object_id=None,  # Unlinked initially
                    file_path=file_path
                )

                doc = await create_case_document(doc_data)

                # Create the BulkUploadedDocument record
                uploaded_doc = BulkUploadedDocument(
                    id=doc.id,
                    case_id=case_id,
                    filename=filename,
                    file_path=file_path,
                    status=doc.status,
                    processing_status="unidentified"
                )

                uploaded_documents.append(uploaded_doc)

            except Exception as e:
                errors.append(f"Error processing file {file_path}: {str(e)}")
                # Continue with other files

        return BulkUploadResult(
            case_id=case_id,
            uploaded_count=len(uploaded_documents),
            documents=uploaded_documents,
            success=len(errors) == 0,
            errors=errors
        )

    finally:
        await conn.close()


async def get_unidentified_documents(case_id: uuid.UUID) -> List[CaseDocumentInDB]:
    """
    Get all unidentified documents for a case.

    Args:
        case_id: UUID of the case

    Returns:
        List[CaseDocumentInDB]: List of unidentified documents
    """
    conn = await get_connection()
    try:
        query = """
        SELECT id, case_id, document_id, doc_type_id, status,
               target_object_type, target_object_id, processing_status,
               uploaded_at, reviewed_at, file_path, created_at, updated_at,
               is_current_version, version_number, replace_version_id
        FROM case_documents
        WHERE case_id = $1 AND doc_type_id IS NULL
        ORDER BY uploaded_at DESC
        """

        rows = await conn.fetch(query, case_id)

        return [CaseDocumentInDB(**dict(row)) for row in rows]
    finally:
        await conn.close()


async def get_unlinked_documents(case_id: uuid.UUID) -> List[CaseDocumentInDB]:
    """
    Get all documents that have been identified (have doc_type_id) but not linked to an entity.

    Args:
        case_id: UUID of the case

    Returns:
        List[CaseDocumentInDB]: List of unlinked documents
    """
    conn = await get_connection()
    try:
        query = """
        SELECT id, case_id, document_id, doc_type_id, status,
               target_object_type, target_object_id, processing_status,
               uploaded_at, reviewed_at, file_path, created_at, updated_at,
               is_current_version, version_number, replace_version_id
        FROM case_documents
        WHERE case_id = $1
          AND doc_type_id IS NOT NULL
          AND (target_object_type IS NULL OR target_object_id IS NULL)
        ORDER BY uploaded_at DESC
        """

        rows = await conn.fetch(query, case_id)

        return [CaseDocumentInDB(**dict(row)) for row in rows]
    finally:
        await conn.close()


async def classify_bulk_documents(
    case_id: uuid.UUID,
    classifications: List[BulkDocumentClassification]
) -> BulkClassificationResult:
    """
    Classify multiple documents in a case in a single operation.

    Args:
        case_id: UUID of the case
        classifications: List of document classifications

    Returns:
        BulkClassificationResult: Result of the operation
    """
    classified_documents = []
    errors = []

    try:
        # For each classification, update the corresponding document
        for classification in classifications:
            try:
                # Create update data
                update_data = CaseDocumentUpdate(
                    doc_type_id=classification.doc_type_id,
                    status=classification.status,
                    target_object_type=classification.target_object_type,
                    target_object_id=classification.target_object_id,
                    processing_status="identified" if not classification.target_object_id else "processed"
                )

                # Update the document
                updated_doc = await update_case_document(classification.document_id, update_data)

                if updated_doc:
                    # Get full document info with type details
                    from server.database.unique_docs_database import get_unique_doc_type

                    # Convert to CaseDocumentWithTypeInfo
                    doc_with_type = CaseDocumentWithTypeInfo(**updated_doc.model_dump())

                    # Get the document type details if available
                    if updated_doc.doc_type_id:
                        doc_type = await get_unique_doc_type(updated_doc.doc_type_id)
                        doc_with_type.document_type = doc_type

                    # Add simple target object info
                    if updated_doc.target_object_type and updated_doc.target_object_id:
                        doc_with_type.target_object = {
                            "id": str(updated_doc.target_object_id),
                            "type": updated_doc.target_object_type
                        }

                    classified_documents.append(doc_with_type)
                else:
                    errors.append(f"Document with ID {classification.document_id} not found or not updated")

            except Exception as e:
                errors.append(f"Error classifying document {classification.document_id}: {str(e)}")
                # Continue with other documents

        return BulkClassificationResult(
            classified_count=len(classified_documents),
            documents=classified_documents,
            success=len(errors) == 0,
            errors=errors
        )

    except Exception as e:
        errors.append(f"Error in bulk classification: {str(e)}")
        return BulkClassificationResult(
            classified_count=0,
            documents=[],
            success=False,
            errors=errors
        )

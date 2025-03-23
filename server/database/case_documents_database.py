"""
Database operations for case documents management.
"""
from typing import List, Optional, Dict, Any, Union
from uuid import UUID
from datetime import datetime
from pydantic import BaseModel, Field, computed_field

from server.database.database import get_connection
from server.database.unique_docs_database import UniqueDocTypeInDB, get_unique_doc_type, DocumentType


# ------------------------------------------------
# Pydantic Models
# ------------------------------------------------
class CaseDocumentBase(BaseModel):
    case_id: UUID
    document_id: Optional[UUID] = None
    doc_type_id: Optional[UUID] = None
    status: str
    target_object_type: Optional[str] = None
    target_object_id: Optional[UUID] = None
    file_path: Optional[str] = None


class CaseDocumentCreate(CaseDocumentBase):
    pass


class CaseDocumentUpdate(BaseModel):
    doc_type_id: Optional[UUID] = None
    status: Optional[str] = None
    target_object_type: Optional[str] = None
    target_object_id: Optional[UUID] = None
    file_path: Optional[str] = None
    processing_status: Optional[str] = None
    reviewed_at: Optional[datetime] = None


class CaseDocumentInDB(CaseDocumentBase):
    id: UUID
    processing_status: str
    uploaded_at: datetime
    reviewed_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime
    is_current_version: bool = True
    version_number: int = 1
    replace_version_id: Optional[UUID] = None


class DocumentVersionHistory(BaseModel):
    """Document version history record for tracking updatable document versions"""
    id: UUID
    case_document_id: UUID
    version_number: int
    file_path: str
    uploaded_at: datetime
    uploaded_by: Optional[UUID] = None
    created_at: datetime


class CaseDocumentWithTypeInfo(CaseDocumentInDB):
    document_type: Optional[UniqueDocTypeInDB] = None
    previous_versions: Optional[List[DocumentVersionHistory]] = None

    @computed_field
    @property
    def has_valid_type(self) -> bool:
        """Indicates if the document has a valid document type."""
        return self.document_type is not None

    @computed_field
    @property
    def has_target_linkage(self) -> bool:
        """Indicates if the document is linked to a target object."""
        return self.target_object_id is not None and self.target_object_type is not None
        
    @computed_field
    @property
    def has_version_history(self) -> bool:
        """Indicates if the document has a version history."""
        return self.previous_versions is not None and len(self.previous_versions) > 0


# ------------------------------------------------
# CRUD Operations
# ------------------------------------------------
async def create_case_document(doc: CaseDocumentCreate) -> CaseDocumentInDB:
    """
    Create a new case document in the database.
    """
    conn = await get_connection()
    try:
        # Insert the case document record
        query = """
        INSERT INTO case_documents (
            case_id, document_id, doc_type_id, status, target_object_type,
            target_object_id, file_path
        )
        VALUES ($1, $2, $3, $4, $5, $6, $7)
        RETURNING id, case_id, document_id, doc_type_id, status,
                  target_object_type, target_object_id, processing_status,
                  uploaded_at, reviewed_at, file_path, created_at, updated_at,
                  is_current_version, version_number, replace_version_id
        """
        record = await conn.fetchrow(
            query,
            doc.case_id,
            doc.document_id,
            doc.doc_type_id,
            doc.status,
            doc.target_object_type,
            doc.target_object_id,
            doc.file_path
        )

        return CaseDocumentInDB(**dict(record))
    finally:
        await conn.close()


async def get_case_document(doc_id: UUID) -> Optional[CaseDocumentInDB]:
    """
    Get a specific case document by ID.
    """
    conn = await get_connection()
    try:
        query = """
        SELECT id, case_id, document_id, doc_type_id, status,
               target_object_type, target_object_id, processing_status,
               uploaded_at, reviewed_at, file_path, created_at, updated_at,
               is_current_version, version_number, replace_version_id
        FROM case_documents
        WHERE id = $1
        """
        record = await conn.fetchrow(query, doc_id)

        if not record:
            return None

        return CaseDocumentInDB(**dict(record))
    finally:
        await conn.close()


async def get_document_version_history(doc_id: UUID) -> List[DocumentVersionHistory]:
    """
    Get version history for a document.
    This implements the history tracking for updatable documents mentioned in the PRD.
    """
    conn = await get_connection()
    try:
        query = """
        SELECT id, case_document_id, version_number, file_path, 
               uploaded_at, uploaded_by, created_at
        FROM document_version_history
        WHERE case_document_id = $1
        ORDER BY version_number DESC
        """
        records = await conn.fetch(query, doc_id)
        
        return [DocumentVersionHistory(**dict(record)) for record in records]
    finally:
        await conn.close()


async def add_document_to_version_history(
    doc_id: UUID, 
    version_number: int,
    file_path: str,
    uploaded_by: Optional[UUID] = None
) -> DocumentVersionHistory:
    """
    Add a document version to the history tracking.
    This implements the history tracking for updatable documents mentioned in the PRD.
    """
    conn = await get_connection()
    try:
        query = """
        INSERT INTO document_version_history (
            case_document_id, version_number, file_path, uploaded_by
        )
        VALUES ($1, $2, $3, $4)
        RETURNING id, case_document_id, version_number, file_path, 
                  uploaded_at, uploaded_by, created_at
        """
        record = await conn.fetchrow(query, doc_id, version_number, file_path, uploaded_by)
        
        return DocumentVersionHistory(**dict(record))
    finally:
        await conn.close()


async def update_case_document(doc_id: UUID, doc_update: CaseDocumentUpdate) -> Optional[CaseDocumentInDB]:
    """
    Update an existing case document by ID.
    If the document is of type "updatable" and file_path is being updated, 
    the previous version is stored in version history.
    """
    conn = await get_connection()
    try:
        # Get the existing document to check if it's an updatable type
        existing_doc = await get_case_document(doc_id)
        if not existing_doc:
            return None
            
        # Get document type to check if it's updatable
        is_updatable = False
        if existing_doc.doc_type_id:
            doc_type = await get_unique_doc_type(existing_doc.doc_type_id)
            if doc_type and doc_type.document_type == DocumentType.UPDATABLE:
                is_updatable = True
        
        # If this is an updatable document and file_path is being updated, 
        # we need to archive the current version
        if is_updatable and doc_update.file_path and doc_update.file_path != existing_doc.file_path:
            # Add current version to history before updating
            await add_document_to_version_history(
                doc_id,
                existing_doc.version_number,
                existing_doc.file_path,
                None  # We don't know who uploaded the original
            )
            
            # Increment version number for the update
            new_version = existing_doc.version_number + 1
            
            # Add version number to the update fields
            doc_update.version_number = new_version

        # Build update query dynamically based on provided fields
        fields_to_update = []
        params = []
        param_idx = 1

        # Add fields if they are provided in the update
        if doc_update.doc_type_id is not None:
            fields_to_update.append(f"doc_type_id = ${param_idx}")
            params.append(doc_update.doc_type_id)
            param_idx += 1

        if doc_update.status is not None:
            fields_to_update.append(f"status = ${param_idx}")
            params.append(doc_update.status)
            param_idx += 1

        if doc_update.target_object_type is not None:
            fields_to_update.append(f"target_object_type = ${param_idx}")
            params.append(doc_update.target_object_type)
            param_idx += 1

        if doc_update.target_object_id is not None:
            fields_to_update.append(f"target_object_id = ${param_idx}")
            params.append(doc_update.target_object_id)
            param_idx += 1

        if doc_update.file_path is not None:
            fields_to_update.append(f"file_path = ${param_idx}")
            params.append(doc_update.file_path)
            param_idx += 1

        if doc_update.processing_status is not None:
            fields_to_update.append(f"processing_status = ${param_idx}")
            params.append(doc_update.processing_status)
            param_idx += 1

        if doc_update.reviewed_at is not None:
            fields_to_update.append(f"reviewed_at = ${param_idx}")
            params.append(doc_update.reviewed_at)
            param_idx += 1
            
        # Add version update fields if this is an updatable document with file change
        if is_updatable and doc_update.file_path and doc_update.file_path != existing_doc.file_path:
            fields_to_update.append(f"version_number = ${param_idx}")
            params.append(new_version)
            param_idx += 1

        # If there are fields to update, execute the update query
        if fields_to_update:
            update_query = f"""
                UPDATE case_documents
                SET {", ".join(fields_to_update)}
                WHERE id = ${param_idx}
                RETURNING id, case_id, document_id, doc_type_id, status,
                        target_object_type, target_object_id, processing_status,
                        uploaded_at, reviewed_at, file_path, created_at, updated_at,
                        is_current_version, version_number, replace_version_id
            """
            params.append(doc_id)
            record = await conn.fetchrow(update_query, *params)

            if not record:
                return None

            return CaseDocumentInDB(**dict(record))

        # If no fields to update, just return the current state
        return existing_doc
    finally:
        await conn.close()


async def delete_case_document(doc_id: UUID) -> bool:
    """
    Delete a case document by ID.
    Returns True if the document was deleted, False if not found.
    """
    conn = await get_connection()
    try:
        query = "DELETE FROM case_documents WHERE id = $1"
        result = await conn.execute(query, doc_id)
        return "DELETE 1" in result
    finally:
        await conn.close()


async def get_case_documents(case_id: UUID) -> List[CaseDocumentInDB]:
    """
    Get all documents for a specific case.
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
        """
        records = await conn.fetch(query, case_id)

        return [CaseDocumentInDB(**dict(record)) for record in records]
    finally:
        await conn.close()


async def get_documents_by_doc_type(doc_type_id: UUID) -> List[CaseDocumentInDB]:
    """
    Get all case documents with a specific document type.
    """
    conn = await get_connection()
    try:
        query = """
        SELECT id, case_id, document_id, doc_type_id, status,
               target_object_type, target_object_id, processing_status,
               uploaded_at, reviewed_at, file_path, created_at, updated_at,
               is_current_version, version_number, replace_version_id
        FROM case_documents
        WHERE doc_type_id = $1
        """
        records = await conn.fetch(query, doc_type_id)

        return [CaseDocumentInDB(**dict(record)) for record in records]
    finally:
        await conn.close()


async def get_documents_by_target_object(target_object_type: str, target_object_id: UUID) -> List[CaseDocumentInDB]:
    """
    Get all case documents linked to a specific target object.
    """
    conn = await get_connection()
    try:
        query = """
        SELECT id, case_id, document_id, doc_type_id, status,
               target_object_type, target_object_id, processing_status,
               uploaded_at, reviewed_at, file_path, created_at, updated_at,
               is_current_version, version_number, replace_version_id
        FROM case_documents
        WHERE target_object_type = $1 AND target_object_id = $2
        """
        records = await conn.fetch(query, target_object_type, target_object_id)

        return [CaseDocumentInDB(**dict(record)) for record in records]
    finally:
        await conn.close()


async def get_case_document_with_type_info(doc_id: UUID) -> Optional[CaseDocumentWithTypeInfo]:
    """
    Get a case document with its document type information and version history.
    This enhanced function provides the document type details and version history
    for updatable documents as specified in the PRD.
    """
    conn = await get_connection()
    try:
        # Get the document first
        document = await get_case_document(doc_id)
        if not document:
            return None
            
        # Create the enhanced document info
        document_info = CaseDocumentWithTypeInfo(**document.model_dump())
        
        # Add document type info if available
        if document.doc_type_id:
            document_info.document_type = await get_unique_doc_type(document.doc_type_id)
            
            # If this is an updatable document, get its version history
            if document_info.document_type and document_info.document_type.document_type == DocumentType.UPDATABLE:
                document_info.previous_versions = await get_document_version_history(doc_id)
                
        return document_info
    finally:
        await conn.close()

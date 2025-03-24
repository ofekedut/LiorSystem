"""
Router for bulk document upload and management.
This implements the bulk document upload functionality mentioned in the PRD.
"""
import os
import uuid
import logging
import shutil
from typing import List, Dict, Any, Optional
from fastapi import (
    APIRouter, 
    Depends, 
    HTTPException, 
    status, 
    UploadFile, 
    File, 
    Form
)
from pydantic import BaseModel, Field

from server.database.bulk_documents_database import (
    BulkDocumentUploadRequest,
    BulkUploadResult,
    BulkDocumentClassification,
    BulkClassificationResult,
    create_bulk_documents,
    get_unidentified_documents,
    get_unlinked_documents,
    classify_bulk_documents
)
from server.database.cases_database import (
    get_case,
    CaseDocumentInDB
)
from server.features.users.security import get_current_active_user, oauth2_scheme
from server.database.users_database import UserPublic
from server.database.unique_docs_database import (
    get_unique_doc_type,
    filter_by_target_object
)

# Setup logging
logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/bulk-documents",
    tags=["bulk_documents"],
    dependencies=[Depends(oauth2_scheme)]
)

# -----------------------------------------------------------------------------
# Helper Models
# -----------------------------------------------------------------------------

class EntityCreationRequest(BaseModel):
    """Request to create a new entity during document classification"""
    entity_type: str
    entity_data: Dict[str, Any]
    

class DocumentClassificationWithNewEntity(BaseModel):
    """Request to classify a document with a new entity"""
    document_id: uuid.UUID
    doc_type_id: uuid.UUID
    target_object_type: str
    create_new_entity: EntityCreationRequest
    status: str = "received"


# -----------------------------------------------------------------------------
# API Endpoints
# -----------------------------------------------------------------------------

@router.post(
    "/upload/{case_id}",
    response_model=BulkUploadResult,
    status_code=status.HTTP_201_CREATED
)
async def bulk_upload_documents(
    case_id: uuid.UUID,
    files: List[UploadFile] = File(...),
    current_user: UserPublic = Depends(get_current_active_user)
) -> BulkUploadResult:
    """
    Upload multiple documents for a specific case without immediate classification.
    
    This implements the "Bulk Upload Flow" described in the PRD (section 5.3):
    1. Documents are uploaded in bulk
    2. Documents remain unidentified and unlinked until processed later
    """
    try:
        # Check if the case exists
        case = await get_case(case_id)
        if not case:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Case with ID {case_id} not found"
            )
            
        # Create directory structure for file storage
        base_dir = f"./mortgage_system/uploaded_files/{case_id}"
        os.makedirs(base_dir, exist_ok=True)
        
        # Process all uploaded files
        file_paths = []
        errors = []
        
        for file in files:
            try:
                # Ensure the file extension is valid (PDF or image)
                filename = file.filename
                if not filename:
                    errors.append(f"Missing filename for uploaded file")
                    continue
                    
                ext = os.path.splitext(filename.lower())[1]
                valid_extensions = ['.pdf', '.jpg', '.jpeg', '.png', '.gif', '.bmp', '.tiff', '.tif']
                
                if ext not in valid_extensions:
                    errors.append(f"Invalid file type for file {filename}. Only PDF and image files are allowed.")
                    continue
                
                # Ensure file is not larger than 25MB
                file_size = 0
                content = await file.read()
                file_size = len(content)
                
                if file_size > 25 * 1024 * 1024:  # 25MB in bytes
                    errors.append(f"File {filename} exceeds the maximum allowed size of 25MB")
                    continue
                
                # Reset file position for saving
                await file.seek(0)
                
                # Save file to disk
                destination_path = os.path.join(base_dir, filename)
                
                # Handle filename collisions
                if os.path.exists(destination_path):
                    base_name, ext = os.path.splitext(filename)
                    timestamp = uuid.uuid4().hex[:8]
                    filename = f"{base_name}_{timestamp}{ext}"
                    destination_path = os.path.join(base_dir, filename)
                
                # Save the file
                with open(destination_path, "wb") as buffer:
                    shutil.copyfileobj(file.file, buffer)
                
                file_paths.append(destination_path)
                
            except Exception as e:
                errors.append(f"Error processing file {file.filename}: {str(e)}")
        
        # If no files were successfully processed, return error
        if not file_paths:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"No valid files were uploaded: {'; '.join(errors)}"
            )
        
        # Create bulk document records
        result = await create_bulk_documents(case_id, file_paths)
        
        # Add any file processing errors
        result.errors.extend(errors)
        result.success = len(errors) == 0 and result.success
        
        return result
        
    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    except Exception as e:
        logger.error(f"Error in bulk document upload: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An unexpected error occurred: {str(e)}"
        )


@router.get(
    "/{case_id}/unidentified",
    response_model=List[CaseDocumentInDB]
)
async def get_unidentified_documents_endpoint(
    case_id: uuid.UUID,
    current_user: UserPublic = Depends(get_current_active_user)
) -> List[CaseDocumentInDB]:
    """
    Get all unidentified documents for a specific case.
    
    These are documents that have been uploaded but not yet classified with a document type.
    """
    try:
        # Check if the case exists
        case = await get_case(case_id)
        if not case:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Case with ID {case_id} not found"
            )
            
        return await get_unidentified_documents(case_id)
        
    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    except Exception as e:
        logger.error(f"Error getting unidentified documents: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An unexpected error occurred: {str(e)}"
        )


@router.get(
    "/{case_id}/unlinked",
    response_model=List[CaseDocumentInDB]
)
async def get_unlinked_documents_endpoint(
    case_id: uuid.UUID,
    current_user: UserPublic = Depends(get_current_active_user)
) -> List[CaseDocumentInDB]:
    """
    Get all unlinked documents for a specific case.
    
    These are documents that have been identified with a document type,
    but not yet linked to a specific entity.
    """
    try:
        # Check if the case exists
        case = await get_case(case_id)
        if not case:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Case with ID {case_id} not found"
            )
            
        return await get_unlinked_documents(case_id)
        
    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    except Exception as e:
        logger.error(f"Error getting unlinked documents: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An unexpected error occurred: {str(e)}"
        )


@router.post(
    "/{case_id}/classify",
    response_model=BulkClassificationResult
)
async def classify_documents_endpoint(
    case_id: uuid.UUID,
    classifications: List[BulkDocumentClassification],
    current_user: UserPublic = Depends(get_current_active_user)
) -> BulkClassificationResult:
    """
    Classify multiple documents in a specific case.
    
    This is used to assign document types and link to entities for documents 
    that were previously uploaded via bulk upload.
    """
    try:
        # Check if the case exists
        case = await get_case(case_id)
        if not case:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Case with ID {case_id} not found"
            )
            
        # Classify the documents
        return await classify_bulk_documents(case_id, classifications)
        
    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    except Exception as e:
        logger.error(f"Error classifying documents: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An unexpected error occurred: {str(e)}"
        )


@router.post(
    "/{case_id}/classify-with-new-entity",
    response_model=BulkClassificationResult
)
async def classify_with_new_entity_endpoint(
    case_id: uuid.UUID,
    requests: List[DocumentClassificationWithNewEntity],
    current_user: UserPublic = Depends(get_current_active_user)
) -> BulkClassificationResult:
    """
    Classify documents and create new entities on-the-fly.
    
    This implements the ability to "create new entities on-the-fly during document identification"
    as specified in the PRD (section 3.2.3).
    """
    try:
        # Check if the case exists
        case = await get_case(case_id)
        if not case:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Case with ID {case_id} not found"
            )
        
        # Process each request by first creating the entity, then classifying the document
        classifications = []
        errors = []
        
        for req in requests:
            try:
                # Create the new entity - simplified example without actual entity creation
                # This would need to be replaced with actual entity creation logic
                entity_id = uuid.uuid4()  # Just use a placeholder UUID
                
                if entity_id:
                    # Add to classifications with the new entity ID
                    classification = BulkDocumentClassification(
                        document_id=req.document_id,
                        doc_type_id=req.doc_type_id,
                        target_object_type=req.target_object_type,
                        target_object_id=entity_id,
                        status=req.status
                    )
                    
                    classifications.append(classification)
                else:
                    errors.append(f"Failed to create new entity for document {req.document_id}")
                    
            except Exception as e:
                errors.append(f"Error processing document {req.document_id}: {str(e)}")
        
        # Classify the documents
        result = await classify_bulk_documents(case_id, classifications)
        
        # Add any processing errors
        result.errors.extend(errors)
        
        return result
        
    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    except Exception as e:
        logger.error(f"Error classifying documents with new entities: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An unexpected error occurred: {str(e)}"
        )


@router.get(
    "/document-types-for-target/{target_object}",
    response_model=List[Dict[str, Any]]
)
async def get_document_types_for_target_endpoint(
    target_object: str,
    current_user: UserPublic = Depends(get_current_active_user)
) -> List[Dict[str, Any]]:
    """
    Get all document types applicable for a specific target object type.
    
    This is used to help with document classification by showing only 
    relevant document types for a given entity type.
    """
    try:
        # Get document types for the target object
        doc_types = await filter_by_target_object(target_object)
        
        # Convert to simplified format
        return [
            {
                "id": str(doc_type.id),
                "display_name": doc_type.display_name,
                "category": doc_type.category,
                "target_object": doc_type.target_object,
                "document_type": doc_type.document_type,
                "is_recurring": doc_type.is_recurring,
                "frequency": doc_type.frequency
            }
            for doc_type in doc_types
        ]
        
    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    except Exception as e:
        logger.error(f"Error getting document types for target {target_object}: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An unexpected error occurred: {str(e)}"
        )

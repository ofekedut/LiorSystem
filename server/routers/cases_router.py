# cases_router.py
from typing import List
from uuid import UUID
import os
import logging

from server.features.docs_processing.detect_doc_type import classify_document
from server.features.docs_processing.document_processing_db import get_labels

from fastapi import (
    APIRouter,
    BackgroundTasks,
    File,
    HTTPException,
    UploadFile,
)
from starlette import status

from server.database.cases_database import (
    create_case,
    get_case,
    list_cases,
    update_case,
    delete_case,
    CaseInCreate,
    CaseInDB,
    CaseUpdate,

    # Case Persons
    create_case_person,
    get_case_person,
    list_case_persons,
    update_case_person,
    delete_case_person,
    CasePersonCreate,
    CasePersonInDB,
    CasePersonUpdate,

    # Case Person Relations
    create_person_relation,
    list_person_relations,
    delete_person_relation,
    CasePersonRelationCreate,
    CasePersonRelationInDB,

    # Case Documents
    create_case_document,
    get_case_document,
    list_case_documents,
    update_case_document,
    delete_case_document,
    CaseDocumentCreate,
    CaseDocumentInDB,
    CaseDocumentUpdate,

    # Case Loans
    create_case_loan,
    get_case_loan,
    list_case_loans,
    update_case_loan,
    delete_case_loan,
    CaseLoanCreate,
    CaseLoanInDB,
    CaseLoanUpdate,
    
    # Case Person Documents
    create_case_person_document,
    get_case_person_document,
    list_case_person_documents,
    update_case_person_document,
    delete_case_person_document,
    CasePersonDocumentCreate,
    CasePersonDocumentInDB,
    CasePersonDocumentUpdate,
DocumentProcessingStatus
)


# ----------------------------------------------------------------
# Fixed user ID function to use instead of auth
# ----------------------------------------------------------------
def get_fixed_user_id() -> UUID:
    """
    Returns a fixed user ID for development purposes.
    """
    # Fixed user ID for testing
    return UUID("00000000-0000-0000-0000-000000000000")


router = APIRouter()


# =============================================================================
# 1. Cases Endpoints
# =============================================================================

@router.get("/cases", response_model=List[CaseInDB])
async def read_cases() -> List[CaseInDB]:
    """
    Retrieve all cases.
    """
    return await list_cases()


@router.post("/cases", response_model=CaseInDB, status_code=201)
async def create_new_case(case_in: CaseInCreate) -> CaseInDB:
    """
    Create a new case.
    """
    return await create_case(case_in)


@router.get("/cases/{case_id}", response_model=CaseInDB)
async def read_case(case_id: UUID) -> CaseInDB:
    """
    Retrieve a single case by its UUID.
    """
    existing = await get_case(case_id)
    if not existing:
        raise HTTPException(status_code=404, detail="Case not found")
    return existing


@router.put("/cases/{case_id}", response_model=CaseInDB)
async def update_existing_case(case_id: UUID, case_update: CaseUpdate) -> CaseInDB:
    """
    Update an existing case by ID.
    """
    updated = await update_case(case_id, case_update)
    if not updated:
        raise HTTPException(status_code=404, detail="Case not found or not updated")
    return updated


@router.delete("/cases/{case_id}", status_code=204)
async def remove_case(case_id: UUID):
    """
    Delete a case by ID.
    """
    success = await delete_case(case_id)
    if not success:
        raise HTTPException(status_code=404, detail="Case not found")
    return None  # 204: No Content


# =============================================================================
# 2. Case Persons Endpoints
# =============================================================================

@router.get("/cases/{case_id}/persons", response_model=List[CasePersonInDB])
async def read_case_persons(case_id: UUID) -> List[CasePersonInDB]:
    """
    Retrieve all persons for a given case by case_id.
    """
    # Optional: check if case exists
    existing = await get_case(case_id)
    if not existing:
        raise HTTPException(status_code=404, detail="Case not found")

    return await list_case_persons(case_id)


@router.post("/cases/{case_id}/persons", response_model=CasePersonInDB, status_code=201)
async def create_person_for_case(
        case_id: UUID,
        person_in: CasePersonCreate
) -> CasePersonInDB:
    """
    Create a new person record linked to a specific case.
    """
    # Ensure the 'case_id' in person_in matches the URL param
    if person_in.case_id != case_id:
        raise HTTPException(status_code=400, detail="case_id mismatch")

    # Optional: check if case exists
    existing = await get_case(case_id)
    if not existing:
        raise HTTPException(status_code=404, detail="Case not found")

    return await create_case_person(person_in)


@router.get("/persons/{person_id}", response_model=CasePersonInDB)
async def read_case_person(person_id: UUID) -> CasePersonInDB:
    """
    Retrieve a single case person by their ID.
    """
    person = await get_case_person(person_id)
    if not person:
        raise HTTPException(status_code=404, detail="Case person not found")
    return person


@router.put("/persons/{person_id}", response_model=CasePersonInDB)
async def update_case_person_endpoint(
        person_id: UUID,
        person_update: CasePersonUpdate
) -> CasePersonInDB:
    """
    Update an existing case person by their ID.
    """
    updated = await update_case_person(person_id, person_update)
    if not updated:
        raise HTTPException(status_code=404, detail="Case person not found or not updated")
    return updated


@router.delete("/persons/{person_id}", status_code=204)
async def remove_case_person_endpoint(person_id: UUID):
    """
    Delete a case person by their ID.
    """
    success = await delete_case_person(person_id)
    if not success:
        raise HTTPException(status_code=404, detail="Case person not found")
    return None


# =============================================================================
# 3. Case Person Relations
# =============================================================================

@router.post("/person_relations", response_model=CasePersonRelationInDB, status_code=201)
async def create_person_relation_endpoint(
        rel_in: CasePersonRelationCreate
) -> CasePersonRelationInDB:
    """
    Create a relationship record between two persons.
    """
    # Optionally verify that both persons exist, or that they're in the same case
    return await create_person_relation(rel_in)


@router.get("/person_relations/{person_id}", response_model=List[CasePersonRelationInDB])
async def read_person_relations(person_id: UUID) -> List[CasePersonRelationInDB]:
    """
    List all person-to-person relationships for a given person ID.
    """
    return await list_person_relations(person_id)


@router.delete("/person_relations", status_code=204)
async def remove_person_relation(
        from_person_id: UUID,
        to_person_id: UUID
):
    """
    Delete a relationship record between two persons.
    Accepts the two person IDs as query parameters.
    Example: DELETE /person_relations?from_person_id=...&to_person_id=...
    """
    success = await delete_person_relation(from_person_id, to_person_id)
    if not success:
        raise HTTPException(status_code=404, detail="Relationship not found")
    return None


# =============================================================================
# 4. Case Documents Endpoints
# =============================================================================

@router.get("/cases/{case_id}/documents", response_model=List[CaseDocumentInDB])
async def read_case_documents(case_id: UUID) -> List[CaseDocumentInDB]:
    """
    List all documents linked to a particular case.
    """
    existing = await get_case(case_id)
    if not existing:
        raise HTTPException(status_code=404, detail="Case not found")

    return await list_case_documents(case_id)


@router.post("/cases/{case_id}/documents", response_model=CaseDocumentInDB, status_code=201)
async def create_document_for_case(
    case_id: UUID, 
    doc_in: CaseDocumentCreate
) -> CaseDocumentInDB:
    """
    Create a new case-document link for a given case.
    """
    if doc_in.case_id != case_id:
        raise HTTPException(status_code=400, detail="case_id mismatch")

    existing = await get_case(case_id)
    if not existing:
        raise HTTPException(status_code=404, detail="Case not found")

    return await create_case_document(doc_in)


@router.get("/cases/{case_id}/documents/{document_id}", response_model=CaseDocumentInDB)
async def read_case_document(case_id: UUID, document_id: UUID) -> CaseDocumentInDB:
    """
    Retrieve a single case-document link by case_id and document_id.
    """
    doc_link = await get_case_document(case_id, document_id)
    if not doc_link:
        raise HTTPException(status_code=404, detail="Case document not found")
    return doc_link


@router.put("/cases/{case_id}/documents/{document_id}", response_model=CaseDocumentInDB)
async def update_case_document_endpoint(
        case_id: UUID,
        document_id: UUID,
        doc_update: CaseDocumentUpdate
) -> CaseDocumentInDB:
    """
    Update status or processing info for an existing case-document link.
    """
    updated = await update_case_document(case_id, document_id, doc_update)
    if not updated:
        raise HTTPException(status_code=404, detail="Case document not found or not updated")
    return updated


@router.delete("/cases/{case_id}/documents/{document_id}", status_code=204)
async def remove_case_document_endpoint(case_id: UUID, document_id: UUID):
    """
    Delete a case-document link by case_id and document_id.
    """
    success = await delete_case_document(case_id, document_id)
    if not success:
        raise HTTPException(status_code=404, detail="Case document not found")
    return None


# -----------------------------------------------------------------------------
# 4B. Case Documents: Upload File Endpoint
# -----------------------------------------------------------------------------
@router.post(
    "/cases/{case_id}/documents/{document_id}/upload",
    response_model=CaseDocumentInDB,
    status_code=status.HTTP_201_CREATED
)
async def upload_case_document_file(
        case_id: UUID,
        document_id: UUID,
        file: UploadFile = File(...),
        background_tasks: BackgroundTasks = BackgroundTasks()
):
    """
    Upload the actual file for a case document. The file will be stored on the
    filesystem in a path like:
        /mortgage_system/uploaded_files/{case_id}/{file.filename}

    Then we update the `file_path` in the `case_documents` table.
    """
    # 1. Check that the case_document link exists
    doc_link = await get_case_document(case_id, document_id)
    if not doc_link:
        raise HTTPException(status_code=404, detail="Case document link not found")

    # 2. Define a local upload path
    base_dir = "./mortgage_system/uploaded_files"
    upload_dir = os.path.join(base_dir, str(case_id))
    os.makedirs(upload_dir, exist_ok=True)

    # 3. Save the file to disk
    file_path = os.path.join(upload_dir, file.filename)
    try:
        content = await file.read()
        with open(file_path, "wb") as out_file:
            out_file.write(content)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"File upload failed: {e}")

    # 4. Update the DB record so `file_path` is stored
    doc_update = CaseDocumentUpdate(file_path=file_path)
    updated_doc = await update_case_document(case_id, document_id, doc_update)
    if not updated_doc:
        raise HTTPException(status_code=404, detail="Could not update file path")

    # Run document classification in the background
    background_tasks.add_task(classify_document_background, file_path, case_id, document_id)

    # Return the updated record to the client
    return updated_doc


# -----------------------------------------------------------------------------
# Background Task for Document Classification
# -----------------------------------------------------------------------------
async def classify_document_background(file_path: str, case_id: UUID, document_id: UUID):
    """
    Background task to classify a document and update its type based on content.
    
    Args:
        file_path: Path to the uploaded file
        case_id: UUID of the case
        document_id: UUID of the document to update
    """
    logger = logging.getLogger("document_classification")
    
    # Configure the logger with timestamp and detailed formatting
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    if not logger.handlers:
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)
        logger.setLevel(logging.INFO)
    
    try:
        logger.info(f"======= STARTING DOCUMENT CLASSIFICATION =======")
        logger.info(f"Case ID: {case_id}")
        logger.info(f"Document ID: {document_id}")
        logger.info(f"File path: {file_path}")
        
        # Print for console visibility
        print(f"\n======= STARTING DOCUMENT CLASSIFICATION =======")
        print(f"File path: {file_path}")
        
        if not os.path.exists(file_path):
            logger.error(f"File does not exist: {file_path}")
            print(f"\n❌ ERROR: File does not exist: {file_path}\n")
            return
            
        file_size = os.path.getsize(file_path)
        logger.info(f"File size: {file_size} bytes ({file_size/1024/1024:.2f} MB)")
        print(f"File size: {file_size} bytes ({file_size/1024/1024:.2f} MB)")
        
        # Try to open the file for manual review
        try:
            logger.info(f"Opening file for manual review from background task")
            os.system(f'open "{file_path}"')
            print(f"\n📂 Opening file for review from background task: {file_path}\n")
        except Exception as e:
            logger.warning(f"Failed to open file for review: {e}")
        
        # Get all the available labels for classification
        logger.info(f"Fetching available document labels for classification")
        labels = await get_labels()
        
        if not labels:
            logger.warning("No labels available for document classification")
            return
            
        logger.info(f"Found {len(labels)} document type labels")
        
        # Classify the document
        logger.info(f"Starting classification for document at {file_path}")
        print(f"\nStarting classification for document: {os.path.basename(file_path)}\n")
        
        result = await classify_document(
            labels=labels,
            filepath=file_path
        )
        
        if not result or "predicted_label" not in result:
            logger.warning(f"Document classification failed or returned no prediction")
            return
            
        predicted_doc_type = result.get("predicted_label")
        confidence = result.get("confidence", 0)
        source_used = result.get("source", "unknown")
        
        logger.info(f"Classification results:")
        logger.info(f"  - Predicted document type: '{predicted_doc_type}'")
        logger.info(f"  - Confidence: {confidence:.4f}")
        logger.info(f"  - Text source: {source_used}")
        
        # Only update if confidence is high enough
        if confidence >= 0.7:  # 70% confidence threshold
            logger.info(f"Confidence {confidence:.4f} is above threshold (0.7), proceeding with document update")
            # Get document ID for the predicted type
            from server.database.documents_databse import get_document_by_name
            
            logger.info(f"Looking up document type ID for '{predicted_doc_type}'")
            # Find the document type
            doc_type = await get_document_by_name(predicted_doc_type)
            
            if doc_type:
                logger.info(f"Found document type: {doc_type}")
                # Update the case document's type
                from server.database.cases_database import update_case_document
                
                # Create update payload
                update_payload = CaseDocumentUpdate(
                    processing_status=DocumentProcessingStatus.processed
                )
                
                logger.info(f"Updating case document status to 'processed'")
                # Update the case document
                updated = await update_case_document(case_id, document_id, update_payload)
                
                if updated:
                    logger.info(f"✅ Document successfully updated with type '{predicted_doc_type}'")
                else:
                    logger.error(f"❌ Failed to update document type in database")
            else:
                logger.warning(f"❌ Could not find document type for '{predicted_doc_type}' in the database")
        else:
            logger.info(f"Confidence {confidence:.4f} is below threshold (0.7), setting status to 'userActionRequired'")
            
            # Set processing status to userActionRequired
            update_payload = CaseDocumentUpdate(
                processing_status=DocumentProcessingStatus.userActionRequired
            )
            
            # Update the case document
            from server.database.cases_database import update_case_document
            logger.info(f"Updating document status to 'userActionRequired'")
            updated = await update_case_document(case_id, document_id, update_payload)
            
            if updated:
                logger.info(f"✅ Document status updated to 'userActionRequired'")
            else:
                logger.error(f"❌ Failed to update document status")
            
    except Exception as e:
        logger.error(f"❌ Error in document classification background task: {e}", exc_info=True)
    finally:
        logger.info(f"======= DOCUMENT CLASSIFICATION COMPLETE =======\n")
        
        try:
            # Set processing status to error
            from server.database.cases_database import update_case_document
            update_payload = CaseDocumentUpdate(
                processing_status=DocumentProcessingStatus.error
            )
            
            # Update the case document
            await update_case_document(case_id, document_id, update_payload)
        except Exception as nested_e:
            logger.error(f"Error updating document status after classification error: {nested_e}", exc_info=True)


# =============================================================================
# 5. Case Loans Endpoints
# =============================================================================

@router.get("/cases/{case_id}/loans", response_model=List[CaseLoanInDB])
async def read_case_loans(case_id: UUID) -> List[CaseLoanInDB]:
    """
    List all loans associated with a specific case.
    """
    existing = await get_case(case_id)
    if not existing:
        raise HTTPException(status_code=404, detail="Case not found")

    return await list_case_loans(case_id)


@router.post("/cases/{case_id}/loans", response_model=CaseLoanInDB, status_code=201)
async def create_loan_for_case(case_id: UUID, loan_in: CaseLoanCreate) -> CaseLoanInDB:
    """
    Create a new case loan record for a given case.
    """
    if loan_in.case_id != case_id:
        raise HTTPException(status_code=400, detail="case_id mismatch")

    existing = await get_case(case_id)
    if not existing:
        raise HTTPException(status_code=404, detail="Case not found")

    return await create_case_loan(loan_in)


@router.get("/loans/{loan_id}", response_model=CaseLoanInDB)
async def read_case_loan(loan_id: UUID) -> CaseLoanInDB:
    """
    Retrieve a single case loan by its ID.
    """
    loan = await get_case_loan(loan_id)
    if not loan:
        raise HTTPException(status_code=404, detail="Case loan not found")
    return loan


@router.put("/loans/{loan_id}", response_model=CaseLoanInDB)
async def update_case_loan_endpoint(
        loan_id: UUID,
        loan_update: CaseLoanUpdate
) -> CaseLoanInDB:
    """
    Update fields of an existing case loan.
    """
    updated = await update_case_loan(loan_id, loan_update)
    if not updated:
        raise HTTPException(status_code=404, detail="Case loan not found or not updated")
    return updated


@router.delete("/loans/{loan_id}", status_code=204)
async def remove_case_loan_endpoint(loan_id: UUID):
    """
    Delete a case loan by its ID.
    """
    success = await delete_case_loan(loan_id)
    if not success:
        raise HTTPException(status_code=404, detail="Case loan not found")
    return None

# =============================================================================
# 6. Case Person Documents Endpoints
# =============================================================================

@router.get("/cases/{case_id}/persons/{person_id}/documents", response_model=List[CasePersonDocumentInDB])
async def read_case_person_documents(case_id: UUID, person_id: UUID) -> List[CasePersonDocumentInDB]:
    """
    List all documents linked to a specific person within a case.
    """
    try:
        return await list_case_person_documents(case_id, person_id)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Error fetching documents for person {person_id} in case {case_id}: {str(e)}"
        )


@router.post("/cases/{case_id}/persons/{person_id}/documents", response_model=CasePersonDocumentInDB, status_code=201)
async def create_document_for_case_person(
    case_id: UUID,
    person_id: UUID,
    doc_in: CasePersonDocumentCreate
) -> CasePersonDocumentInDB:
    """
    Create a new document link for a specific person within a case.
    """
    # Ensure the provided case_id and person_id match with the ones in the path
    if doc_in.case_id != case_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Case ID in the request body does not match the path parameter"
        )
    
    if doc_in.person_id != person_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Person ID in the request body does not match the path parameter"
        )
    
    try:
        return await create_case_person_document(doc_in)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error creating document link: {str(e)}"
        )


@router.get(
    "/cases/{case_id}/persons/{person_id}/documents/{document_id}",
    response_model=CasePersonDocumentInDB
)
async def read_case_person_document(
    case_id: UUID,
    person_id: UUID,
    document_id: UUID
) -> CasePersonDocumentInDB:
    """
    Retrieve a single document linked to a specific person within a case.
    """
    try:
        return await get_case_person_document(case_id, person_id, document_id)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving document: {str(e)}"
        )


@router.patch(
    "/cases/{case_id}/persons/{person_id}/documents/{document_id}",
    response_model=CasePersonDocumentInDB
)
async def update_case_person_document_endpoint(
    case_id: UUID,
    person_id: UUID,
    document_id: UUID,
    doc_update: CasePersonDocumentUpdate
) -> CasePersonDocumentInDB:
    """
    Update a document link for a specific person within a case.
    """
    try:
        return await update_case_person_document(case_id, person_id, document_id, doc_update)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error updating document link: {str(e)}"
        )


@router.delete(
    "/cases/{case_id}/persons/{person_id}/documents/{document_id}",
    response_model=dict
)
async def delete_case_person_document_endpoint(
    case_id: UUID,
    person_id: UUID,
    document_id: UUID
) -> dict:
    """
    Delete a document link for a specific person within a case.
    """
    try:
        result = await delete_case_person_document(case_id, person_id, document_id)
        if not result:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Document link not found for person {person_id} in case {case_id} with document ID {document_id}"
            )
        return {"deleted": result}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error deleting document link: {str(e)}"
        )

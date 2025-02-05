# cases_router.py
from typing import List
from uuid import UUID
import os

from fastapi import (
    APIRouter,
    HTTPException,
    UploadFile,
    File,
    Depends
)
from starlette import status
from starlette.responses import JSONResponse

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
)


# ----------------------------------------------------------------
# Example placeholder function for determining current user ID.
# In a real application, you'd extract this from a JWT or session.
# ----------------------------------------------------------------
def get_current_user_id() -> UUID:
    """
    A placeholder dependency that would normally extract the user ID from auth.
    """
    # Replace with real authentication logic
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
async def create_document_for_case(case_id: UUID, doc_in: CaseDocumentCreate) -> CaseDocumentInDB:
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
        user_id: UUID = Depends(get_current_user_id),
):
    """
    Upload the actual file for a case document. The file will be stored on the
    filesystem in a path like:
        /home/mortgage_system/uploaded_files/{user_id}/{case_id}/{file.filename}

    We then update the case_documents table with a file_path (if such a column
    exists). For this example, we assume you have added a 'file_path' column
    in 'case_documents' to store the local path. If not, you'll need to
    modify your schema accordingly.
    """
    # 1. Check that the case_document link exists
    doc_link = await get_case_document(case_id, document_id)
    if not doc_link:
        raise HTTPException(status_code=404, detail="Case document link not found")

    # 2. Define a local upload path. Adjust the base directory to your preference.
    base_dir = "./mortgage_system/uploaded_files"
    upload_dir = os.path.join(base_dir, str(user_id), str(case_id))
    os.makedirs(upload_dir, exist_ok=True)  # Create directories if needed

    # 3. Save the file to disk
    file_path = os.path.join(upload_dir, file.filename)
    try:
        with open(file_path, "wb") as out_file:
            content = await file.read()
            out_file.write(content)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"File upload failed: {e}")

    return JSONResponse({"success": True}, status_code=201)


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

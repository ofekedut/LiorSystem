"""
Router for person loans management
"""
import uuid
import logging
from fastapi import APIRouter, HTTPException, status, Depends

from server.database.person_loans_database import (
    PersonLoanInCreate,
    PersonLoanInDB,
    PersonLoanInUpdate,
    create_person_loan,
    get_person_loan_by_id,
    get_person_loans_by_person,
    update_person_loan,
    delete_person_loan
)
from server.database.cases_database import get_case_person
from server.features.users.security import get_current_active_user, oauth2_scheme
from server.database.users_database import UserPublic

logger = logging.getLogger(__name__)

router = APIRouter(
    dependencies=[Depends(oauth2_scheme)]
)


@router.post(
    "/cases/{case_id}/persons/{person_id}/loans",
    response_model=PersonLoanInDB,
    status_code=status.HTTP_201_CREATED,
    tags=["loans"]
)
async def create_loan_endpoint(
        case_id: uuid.UUID,
        person_id: uuid.UUID,
        payload: PersonLoanInCreate,
        current_user: UserPublic = Depends(get_current_active_user)
):
    """
    Add a new loan for a person in a case
    """
    # Check if person ID in path matches payload
    if payload.person_id != person_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Person ID in path must match person ID in payload"
        )

    # Verify the person exists and belongs to the case
    person = await get_case_person(person_id)
    if not person:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Person with ID {person_id} not found"
        )

    if person.case_id != case_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Person with ID {person_id} does not belong to case with ID {case_id}"
        )

    try:
        return await create_person_loan(payload)
    except Exception as e:
        logger.error(f"Error creating loan: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error creating loan: {str(e)}"
        )


@router.get(
    "/cases/{case_id}/persons/{person_id}/loans",
    response_model=list[PersonLoanInDB],
    tags=["loans"]
)
async def get_loans_endpoint(
        case_id: uuid.UUID,
        person_id: uuid.UUID,
        current_user: UserPublic = Depends(get_current_active_user)
):
    """
    Get all loans for a person in a case
    """
    # Verify the person exists and belongs to the case
    person = await get_case_person(person_id)
    if not person:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Person with ID {person_id} not found"
        )

    if person.case_id != case_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Person with ID {person_id} does not belong to case with ID {case_id}"
        )

    try:
        return await get_person_loans_by_person(person_id)
    except Exception as e:
        logger.error(f"Error retrieving loans: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving loans: {str(e)}"
        )


@router.get(
    "/cases/{case_id}/persons/{person_id}/loans/{loan_id}",
    response_model=PersonLoanInDB,
    tags=["loans"]
)
async def get_loan_endpoint(
        case_id: uuid.UUID,
        person_id: uuid.UUID,
        loan_id: uuid.UUID,
        current_user: UserPublic = Depends(get_current_active_user)
):
    """
    Get a specific loan for a person in a case
    """
    # Verify the person exists and belongs to the case
    person = await get_case_person(person_id)
    if not person:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Person with ID {person_id} not found"
        )

    if person.case_id != case_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Person with ID {person_id} does not belong to case with ID {case_id}"
        )

    # Get the loan
    loan = await get_person_loan_by_id(loan_id)
    if not loan:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Loan with ID {loan_id} not found"
        )

    # Verify the loan belongs to the person
    if loan.person_id != person_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Loan with ID {loan_id} does not belong to person with ID {person_id}"
        )

    return loan


@router.put(
    "/cases/{case_id}/persons/{person_id}/loans/{loan_id}",
    response_model=PersonLoanInDB,
    tags=["loans"]
)
async def update_loan_endpoint(
        case_id: uuid.UUID,
        person_id: uuid.UUID,
        loan_id: uuid.UUID,
        payload: PersonLoanInUpdate,
        current_user: UserPublic = Depends(get_current_active_user)
):
    """
    Update a specific loan for a person in a case
    """
    # Verify the person exists and belongs to the case
    person = await get_case_person(person_id)
    if not person:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Person with ID {person_id} not found"
        )

    if person.case_id != case_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Person with ID {person_id} does not belong to case with ID {case_id}"
        )

    # Get the loan
    loan = await get_person_loan_by_id(loan_id)
    if not loan:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Loan with ID {loan_id} not found"
        )

    # Verify the loan belongs to the person
    if loan.person_id != person_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Loan with ID {loan_id} does not belong to person with ID {person_id}"
        )

    try:
        updated = await update_person_loan(loan_id, payload)
        if not updated:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to update loan with ID {loan_id}"
            )

        return updated
    except Exception as e:
        logger.error(f"Error updating loan: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error updating loan: {str(e)}"
        )


@router.delete(
    "/cases/{case_id}/persons/{person_id}/loans/{loan_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    tags=["loans"]
)
async def delete_loan_endpoint(
        case_id: uuid.UUID,
        person_id: uuid.UUID,
        loan_id: uuid.UUID,
        current_user: UserPublic = Depends(get_current_active_user)
):
    """
    Delete a specific loan for a person in a case
    """
    # Verify the person exists and belongs to the case
    person = await get_case_person(person_id)
    if not person:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Person with ID {person_id} not found"
        )

    if person.case_id != case_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Person with ID {person_id} does not belong to case with ID {case_id}"
        )

    # Get the loan
    loan = await get_person_loan_by_id(loan_id)
    if not loan:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Loan with ID {loan_id} not found"
        )

    # Verify the loan belongs to the person
    if loan.person_id != person_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Loan with ID {loan_id} does not belong to person with ID {person_id}"
        )

    try:
        success = await delete_person_loan(loan_id)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to delete loan with ID {loan_id}"
            )

        return None  # 204 No Content
    except Exception as e:
        logger.error(f"Error deleting loan: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error deleting loan: {str(e)}"
        )
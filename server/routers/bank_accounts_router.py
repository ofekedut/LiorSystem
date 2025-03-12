"""
Router for bank accounts management
"""
import uuid
import logging
from fastapi import APIRouter, HTTPException, status, Depends

from server.database.bank_accounts_database import (
    BankAccountInCreate,
    BankAccountInDB,
    BankAccountInUpdate,
    create_bank_account,
    get_bank_account_by_id,
    get_bank_accounts_by_person,
    update_bank_account,
    delete_bank_account
)
from server.database.cases_database import get_case_person
from server.features.users.security import get_current_active_user, oauth2_scheme
from server.database.users_database import UserPublic

logger = logging.getLogger(__name__)

router = APIRouter(
    dependencies=[Depends(oauth2_scheme)]
)


@router.post(
    "/cases/{case_id}/persons/{person_id}/bank-accounts",
    response_model=BankAccountInDB,
    status_code=status.HTTP_201_CREATED,
    tags=["bank-accounts"]
)
async def create_bank_account_endpoint(
        case_id: uuid.UUID,
        person_id: uuid.UUID,
        payload: BankAccountInCreate,
        current_user: UserPublic = Depends(get_current_active_user)
):
    """
    Add a new bank account for a person in a case
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
        return await create_bank_account(payload)
    except Exception as e:
        logger.error(f"Error creating bank account: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error creating bank account: {str(e)}"
        )


@router.get(
    "/cases/{case_id}/persons/{person_id}/bank-accounts",
    response_model=list[BankAccountInDB],
    tags=["bank-accounts"]
)
async def get_bank_accounts_endpoint(
        case_id: uuid.UUID,
        person_id: uuid.UUID,
        current_user: UserPublic = Depends(get_current_active_user)
):
    """
    Get all bank accounts for a person in a case
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
        return await get_bank_accounts_by_person(person_id)
    except Exception as e:
        logger.error(f"Error retrieving bank accounts: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving bank accounts: {str(e)}"
        )


@router.get(
    "/cases/{case_id}/persons/{person_id}/bank-accounts/{account_id}",
    response_model=BankAccountInDB,
    tags=["bank-accounts"]
)
async def get_bank_account_endpoint(
        case_id: uuid.UUID,
        person_id: uuid.UUID,
        account_id: uuid.UUID,
        current_user: UserPublic = Depends(get_current_active_user)
):
    """
    Get a specific bank account for a person in a case
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

    # Get the bank account
    bank_account = await get_bank_account_by_id(account_id)
    if not bank_account:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Bank account with ID {account_id} not found"
        )

    # Verify the bank account belongs to the person
    if bank_account.person_id != person_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Bank account with ID {account_id} does not belong to person with ID {person_id}"
        )

    return bank_account


@router.put(
    "/cases/{case_id}/persons/{person_id}/bank-accounts/{account_id}",
    response_model=BankAccountInDB,
    tags=["bank-accounts"]
)
async def update_bank_account_endpoint(
        case_id: uuid.UUID,
        person_id: uuid.UUID,
        account_id: uuid.UUID,
        payload: BankAccountInUpdate,
        current_user: UserPublic = Depends(get_current_active_user)
):
    """
    Update a specific bank account for a person in a case
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

    # Get the bank account
    bank_account = await get_bank_account_by_id(account_id)
    if not bank_account:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Bank account with ID {account_id} not found"
        )

    # Verify the bank account belongs to the person
    if bank_account.person_id != person_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Bank account with ID {account_id} does not belong to person with ID {person_id}"
        )

    try:
        updated = await update_bank_account(account_id, payload)
        if not updated:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to update bank account with ID {account_id}"
            )

        return updated
    except Exception as e:
        logger.error(f"Error updating bank account: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error updating bank account: {str(e)}"
        )


@router.delete(
    "/cases/{case_id}/persons/{person_id}/bank-accounts/{account_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    tags=["bank-accounts"]
)
async def delete_bank_account_endpoint(
        case_id: uuid.UUID,
        person_id: uuid.UUID,
        account_id: uuid.UUID,
        current_user: UserPublic = Depends(get_current_active_user)
):
    """
    Delete a specific bank account for a person in a case
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

    # Get the bank account
    bank_account = await get_bank_account_by_id(account_id)
    if not bank_account:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Bank account with ID {account_id} not found"
        )

    # Verify the bank account belongs to the person
    if bank_account.person_id != person_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Bank account with ID {account_id} does not belong to person with ID {person_id}"
        )

    try:
        success = await delete_bank_account(account_id)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to delete bank account with ID {account_id}"
            )

        return None  # 204 No Content
    except Exception as e:
        logger.error(f"Error deleting bank account: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error deleting bank account: {str(e)}"
        )
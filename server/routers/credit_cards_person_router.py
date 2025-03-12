"""
Router for credit cards management
"""
import uuid
import logging
from fastapi import APIRouter, HTTPException, status, Depends

from server.database.credit_cards_database import (
    CreditCardInCreate,
    CreditCardInDB,
    CreditCardInUpdate,
    create_credit_card,
    get_credit_card_by_id,
    get_credit_cards_by_person,
    update_credit_card,
    delete_credit_card
)
from server.database.cases_database import get_case_person
from server.features.users.security import get_current_active_user, oauth2_scheme
from server.database.users_database import UserPublic

logger = logging.getLogger(__name__)

router = APIRouter(
    dependencies=[Depends(oauth2_scheme)]
)


@router.post(
    "/cases/{case_id}/persons/{person_id}/credit-cards",
    response_model=CreditCardInDB,
    status_code=status.HTTP_201_CREATED,
    tags=["credit-cards"]
)
async def create_credit_card_endpoint(
        case_id: uuid.UUID,
        person_id: uuid.UUID,
        payload: CreditCardInCreate,
        current_user: UserPublic = Depends(get_current_active_user)
):
    """
    Add a new credit card for a person in a case
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
        return await create_credit_card(payload)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error creating credit card: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error creating credit card: {str(e)}"
        )


@router.get(
    "/cases/{case_id}/persons/{person_id}/credit-cards",
    response_model=list[CreditCardInDB],
    tags=["credit-cards"]
)
async def get_credit_cards_endpoint(
        case_id: uuid.UUID,
        person_id: uuid.UUID,
        current_user: UserPublic = Depends(get_current_active_user)
):
    """
    Get all credit cards for a person in a case
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
        return await get_credit_cards_by_person(person_id)
    except Exception as e:
        logger.error(f"Error retrieving credit cards: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving credit cards: {str(e)}"
        )


@router.get(
    "/cases/{case_id}/persons/{person_id}/credit-cards/{card_id}",
    response_model=CreditCardInDB,
    tags=["credit-cards"]
)
async def get_credit_card_endpoint(
        case_id: uuid.UUID,
        person_id: uuid.UUID,
        card_id: uuid.UUID,
        current_user: UserPublic = Depends(get_current_active_user)
):
    """
    Get a specific credit card for a person in a case
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

    # Get the credit card
    credit_card = await get_credit_card_by_id(card_id)
    if not credit_card:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Credit card with ID {card_id} not found"
        )

    # Verify the credit card belongs to the person
    if credit_card.person_id != person_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Credit card with ID {card_id} does not belong to person with ID {person_id}"
        )

    return credit_card


@router.put(
    "/cases/{case_id}/persons/{person_id}/credit-cards/{card_id}",
    response_model=CreditCardInDB,
    tags=["credit-cards"]
)
async def update_credit_card_endpoint(
        case_id: uuid.UUID,
        person_id: uuid.UUID,
        card_id: uuid.UUID,
        payload: CreditCardInUpdate,
        current_user: UserPublic = Depends(get_current_active_user)
):
    """
    Update a specific credit card for a person in a case
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

    # Get the credit card
    credit_card = await get_credit_card_by_id(card_id)
    if not credit_card:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Credit card with ID {card_id} not found"
        )

    # Verify the credit card belongs to the person
    if credit_card.person_id != person_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Credit card with ID {card_id} does not belong to person with ID {person_id}"
        )

    try:
        updated = await update_credit_card(card_id, payload)
        if not updated:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to update credit card with ID {card_id}"
            )

        return updated
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error updating credit card: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error updating credit card: {str(e)}"
        )


@router.delete(
    "/cases/{case_id}/persons/{person_id}/credit-cards/{card_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    tags=["credit-cards"]
)
async def delete_credit_card_endpoint(
        case_id: uuid.UUID,
        person_id: uuid.UUID,
        card_id: uuid.UUID,
        current_user: UserPublic = Depends(get_current_active_user)
):
    """
    Delete a specific credit card for a person in a case
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

    # Get the credit card
    credit_card = await get_credit_card_by_id(card_id)
    if not credit_card:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Credit card with ID {card_id} not found"
        )

    # Verify the credit card belongs to the person
    if credit_card.person_id != person_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Credit card with ID {card_id} does not belong to person with ID {person_id}"
        )

    try:
        success = await delete_credit_card(card_id)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to delete credit card with ID {card_id}"
            )

        return None  # 204 No Content
    except Exception as e:
        logger.error(f"Error deleting credit card: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error deleting credit card: {str(e)}"
        )
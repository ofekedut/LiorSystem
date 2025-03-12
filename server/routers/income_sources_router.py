"""
Router for income sources management
"""
import uuid
import logging
from fastapi import APIRouter, HTTPException, status, Depends

from server.database.income_sources_database import (
    IncomeSourceInCreate,
    IncomeSourceInDB,
    IncomeSourceInUpdate,
    create_income_source,
    get_income_source_by_id,
    get_income_sources_by_person,
    update_income_source,
    delete_income_source
)
from server.database.cases_database import get_case_person
from server.features.users.security import get_current_active_user, oauth2_scheme
from server.database.users_database import UserPublic

logger = logging.getLogger(__name__)

router = APIRouter(
    dependencies=[Depends(oauth2_scheme)]
)


@router.post(
    "/cases/{case_id}/persons/{person_id}/income",
    response_model=IncomeSourceInDB,
    status_code=status.HTTP_201_CREATED,
    tags=["income"]
)
async def create_income_source_endpoint(
        case_id: uuid.UUID,
        person_id: uuid.UUID,
        payload: IncomeSourceInCreate,
        current_user: UserPublic = Depends(get_current_active_user)
):
    """
    Add a new income source for a person in a case
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
        return await create_income_source(payload)
    except Exception as e:
        logger.error(f"Error creating income source: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error creating income source: {str(e)}"
        )


@router.get(
    "/cases/{case_id}/persons/{person_id}/income",
    response_model=list[IncomeSourceInDB],
    tags=["income"]
)
async def get_income_sources_endpoint(
        case_id: uuid.UUID,
        person_id: uuid.UUID,
        current_user: UserPublic = Depends(get_current_active_user)
):
    """
    Get all income sources for a person in a case
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
        return await get_income_sources_by_person(person_id)
    except Exception as e:
        logger.error(f"Error retrieving income sources: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving income sources: {str(e)}"
        )


@router.get(
    "/cases/{case_id}/persons/{person_id}/income/{income_id}",
    response_model=IncomeSourceInDB,
    tags=["income"]
)
async def get_income_source_endpoint(
        case_id: uuid.UUID,
        person_id: uuid.UUID,
        income_id: uuid.UUID,
        current_user: UserPublic = Depends(get_current_active_user)
):
    """
    Get a specific income source for a person in a case
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

    # Get the income source
    income_source = await get_income_source_by_id(income_id)
    if not income_source:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Income source with ID {income_id} not found"
        )

    # Verify the income source belongs to the person
    if income_source.person_id != person_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Income source with ID {income_id} does not belong to person with ID {person_id}"
        )

    return income_source


@router.put(
    "/cases/{case_id}/persons/{person_id}/income/{income_id}",
    response_model=IncomeSourceInDB,
    tags=["income"]
)
async def update_income_source_endpoint(
        case_id: uuid.UUID,
        person_id: uuid.UUID,
        income_id: uuid.UUID,
        payload: IncomeSourceInUpdate,
        current_user: UserPublic = Depends(get_current_active_user)
):
    """
    Update a specific income source for a person in a case
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

    # Get the income source
    income_source = await get_income_source_by_id(income_id)
    if not income_source:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Income source with ID {income_id} not found"
        )

    # Verify the income source belongs to the person
    if income_source.person_id != person_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Income source with ID {income_id} does not belong to person with ID {person_id}"
        )

    try:
        updated = await update_income_source(income_id, payload)
        if not updated:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to update income source with ID {income_id}"
            )

        return updated
    except Exception as e:
        logger.error(f"Error updating income source: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error updating income source: {str(e)}"
        )


@router.delete(
    "/cases/{case_id}/persons/{person_id}/income/{income_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    tags=["income"]
)
async def delete_income_source_endpoint(
        case_id: uuid.UUID,
        person_id: uuid.UUID,
        income_id: uuid.UUID,
        current_user: UserPublic = Depends(get_current_active_user)
):
    """
    Delete a specific income source for a person in a case
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

    # Get the income source
    income_source = await get_income_source_by_id(income_id)
    if not income_source:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Income source with ID {income_id} not found"
        )

    # Verify the income source belongs to the person
    if income_source.person_id != person_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Income source with ID {income_id} does not belong to person with ID {person_id}"
        )

    try:
        success = await delete_income_source(income_id)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to delete income source with ID {income_id}"
            )

        return None  # 204 No Content
    except Exception as e:
        logger.error(f"Error deleting income source: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error deleting income source: {str(e)}"
        )
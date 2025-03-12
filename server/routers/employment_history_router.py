"""
Router for employment history management
"""
import uuid
import logging
from fastapi import APIRouter, HTTPException, status, Depends

from server.database.employment_history_database import (
    EmploymentHistoryInCreate,
    EmploymentHistoryInDB,
    EmploymentHistoryInUpdate,
    create_employment_history,
    get_employment_history_by_id,
    get_employment_history_by_person,
    update_employment_history,
    delete_employment_history
)
from server.database.cases_database import get_case_person
from server.features.users.security import get_current_active_user, oauth2_scheme
from server.database.users_database import UserPublic
from server.database.database import get_connection

logger = logging.getLogger(__name__)

router = APIRouter(
    dependencies=[Depends(oauth2_scheme)]
)


@router.post(
    "/cases/{case_id}/persons/{person_id}/employment",
    response_model=EmploymentHistoryInDB,
    status_code=status.HTTP_201_CREATED,
    tags=["employment"]
)
async def create_employment_record(
        case_id: uuid.UUID,
        person_id: uuid.UUID,
        payload: EmploymentHistoryInCreate,
        current_user: UserPublic = Depends(get_current_active_user)
):
    """
    Add a new employment record for a person in a case
    """
    # Check if person ID in path matches payload
    if payload.person_id != person_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Person ID in path must match person ID in payload"
        )


@router.delete(
    "/cases/{case_id}/persons/{person_id}/employment/{employment_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    tags=["employment"]
)
async def delete_employment_record(
        case_id: uuid.UUID,
        person_id: uuid.UUID,
        employment_id: uuid.UUID,
        current_user: UserPublic = Depends(get_current_active_user)
):
    """
    Delete a specific employment record for a person in a case
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

    # Get the employment record
    employment = await get_employment_history_by_id(employment_id)
    if not employment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Employment record with ID {employment_id} not found"
        )

    # Verify the employment record belongs to the person
    if employment.person_id != person_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Employment record with ID {employment_id} does not belong to person with ID {person_id}"
        )

    try:
        success = await delete_employment_history(employment_id)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to delete employment record with ID {employment_id}"
            )

        return None  # 204 No Content
    except Exception as e:
        logger.error(f"Error deleting employment record: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error deleting employment record: {str(e)}"
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
        # If this is set as current employer, first un-set any existing current employer
        if payload.current_employer:
            # First get all employment records for the person
            existing_records = await get_employment_history_by_person(person_id)

            # For each record marked as current employer, update it
            conn = await get_connection()
            try:
                async with conn.transaction():
                    for record in existing_records:
                        if record.current_employer:
                            await conn.execute(
                                """
                                UPDATE person_employment_history
                                SET current_employer = false, updated_at = NOW()
                                WHERE id = $1
                                """,
                                record.id
                            )
            finally:
                await conn.close()

        # Create the new employment record
        return await create_employment_history(payload)
    except Exception as e:
        logger.error(f"Error creating employment record: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error creating employment record: {str(e)}"
        )


@router.get(
    "/cases/{case_id}/persons/{person_id}/employment",
    response_model=list[EmploymentHistoryInDB],
    tags=["employment"]
)
async def get_employment_records(
        case_id: uuid.UUID,
        person_id: uuid.UUID,
        current_user: UserPublic = Depends(get_current_active_user)
):
    """
    Get all employment records for a person in a case
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
        return await get_employment_history_by_person(person_id)
    except Exception as e:
        logger.error(f"Error retrieving employment records: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving employment records: {str(e)}"
        )


@router.get(
    "/cases/{case_id}/persons/{person_id}/employment/{employment_id}",
    response_model=EmploymentHistoryInDB,
    tags=["employment"]
)
async def get_employment_record(
        case_id: uuid.UUID,
        person_id: uuid.UUID,
        employment_id: uuid.UUID,
        current_user: UserPublic = Depends(get_current_active_user)
):
    """
    Get a specific employment record for a person in a case
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

    # Get the employment record
    employment = await get_employment_history_by_id(employment_id)
    if not employment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Employment record with ID {employment_id} not found"
        )

    # Verify the employment record belongs to the person
    if employment.person_id != person_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Employment record with ID {employment_id} does not belong to person with ID {person_id}"
        )

    return employment


@router.put(
    "/cases/{case_id}/persons/{person_id}/employment/{employment_id}",
    response_model=EmploymentHistoryInDB,
    tags=["employment"]
)
async def update_employment_record(
        case_id: uuid.UUID,
        person_id: uuid.UUID,
        employment_id: uuid.UUID,
        payload: EmploymentHistoryInUpdate,
        current_user: UserPublic = Depends(get_current_active_user)
):
    """
    Update a specific employment record for a person in a case
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

    # Get the employment record
    employment = await get_employment_history_by_id(employment_id)
    if not employment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Employment record with ID {employment_id} not found"
        )

    # Verify the employment record belongs to the person
    if employment.person_id != person_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Employment record with ID {employment_id} does not belong to person with ID {person_id}"
        )

    try:
        # If setting as current employer, unset any existing current employer
        if payload.current_employer:
            # First get all employment records for the person
            existing_records = await get_employment_history_by_person(person_id)

            # For each record marked as current employer (excluding this one), update it
            conn = await get_connection()
            try:
                async with conn.transaction():
                    for record in existing_records:
                        if record.current_employer and record.id != employment_id:
                            await conn.execute(
                                """
                                UPDATE person_employment_history
                                SET current_employer = false, updated_at = NOW()
                                WHERE id = $1
                                """,
                                record.id
                            )
            finally:
                await conn.close()

        # Update the employment record
        updated = await update_employment_history(employment_id, payload)
        if not updated:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to update employment record with ID {employment_id}"
            )

        return updated
    except Exception as e:
        logger.error(f"Error updating employment record: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error updating employment record: {str(e)}"
        )
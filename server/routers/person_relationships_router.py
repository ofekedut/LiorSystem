"""
Router for person relationships management
"""
import uuid
import logging
from fastapi import APIRouter, HTTPException, status, Depends

from server.database.person_relationships_database import (
    RelationshipInCreate,
    RelationshipInDB,
    RelationshipInUpdate,
    RelationshipExtended,
    create_relationship,
    get_relationship,
    get_relationships_for_person,
    update_relationship,
    delete_relationship,
    check_persons_in_same_case
)
from server.database.cases_database import get_case_person
from server.features.users.security import get_current_active_user, oauth2_scheme
from server.database.users_database import UserPublic

logger = logging.getLogger(__name__)

router = APIRouter(
    dependencies=[Depends(oauth2_scheme)]
)


@router.post(
    "/cases/{case_id}/persons/{person_id}/relationships",
    response_model=RelationshipInDB,
    status_code=status.HTTP_201_CREATED,
    tags=["relationships"]
)
async def create_relationship_endpoint(
    case_id: uuid.UUID,
    person_id: uuid.UUID,
    payload: RelationshipInCreate,
    current_user: UserPublic = Depends(get_current_active_user)
):
    """
    Add a new relationship between two persons in a case
    """
    # Check if from_person_id in path matches payload
    if payload.from_person_id != person_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Person ID in path must match from_person_id in payload"
        )

    # Verify both persons exist and belong to the same case
    case_id_match = await check_persons_in_same_case(payload.from_person_id, payload.to_person_id)
    if not case_id_match:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Both persons must belong to the same case"
        )

    if case_id_match != case_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Persons belong to case {case_id_match}, not case {case_id}"
        )

    # Check if relationship already exists
    existing = await get_relationship(payload.from_person_id, payload.to_person_id)
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Relationship already exists between these persons"
        )

    try:
        return await create_relationship(payload)
    except Exception as e:
        logger.error(f"Error creating relationship: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error creating relationship: {str(e)}"
        )


@router.get(
    "/cases/{case_id}/persons/{person_id}/relationships",
    response_model=list[RelationshipExtended],
    tags=["relationships"]
)
async def get_relationships_endpoint(
    case_id: uuid.UUID,
    person_id: uuid.UUID,
    current_user: UserPublic = Depends(get_current_active_user)
):
    """
    Get all relationships for a person in a case
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
        return await get_relationships_for_person(person_id)
    except Exception as e:
        logger.error(f"Error retrieving relationships: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving relationships: {str(e)}"
        )


@router.get(
    "/cases/{case_id}/persons/{from_person_id}/relationships/{to_person_id}",
    response_model=RelationshipInDB,
    tags=["relationships"]
)
async def get_relationship_endpoint(
    case_id: uuid.UUID,
    from_person_id: uuid.UUID,
    to_person_id: uuid.UUID,
    current_user: UserPublic = Depends(get_current_active_user)
):
    """
    Get a specific relationship between two persons in a case
    """
    # Verify both persons exist and belong to the same case
    case_id_match = await check_persons_in_same_case(from_person_id, to_person_id)
    if not case_id_match:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Both persons must belong to the same case"
        )

    if case_id_match != case_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Persons belong to case {case_id_match}, not case {case_id}"
        )

    # Get the relationship
    relationship = await get_relationship(from_person_id, to_person_id)
    if not relationship:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Relationship between persons {from_person_id} and {to_person_id} not found"
        )

    return relationship


@router.put(
    "/cases/{case_id}/persons/{from_person_id}/relationships/{to_person_id}",
    response_model=RelationshipInDB,
    tags=["relationships"]
)
async def update_relationship_endpoint(
    case_id: uuid.UUID,
    from_person_id: uuid.UUID,
    to_person_id: uuid.UUID,
    payload: RelationshipInUpdate,
    current_user: UserPublic = Depends(get_current_active_user)
):
    """
    Update a specific relationship between two persons in a case
    """
    # Verify both persons exist and belong to the same case
    case_id_match = await check_persons_in_same_case(from_person_id, to_person_id)
    if not case_id_match:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Both persons must belong to the same case"
        )

    if case_id_match != case_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Persons belong to case {case_id_match}, not case {case_id}"
        )

    # Get the relationship
    relationship = await get_relationship(from_person_id, to_person_id)
    if not relationship:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Relationship between persons {from_person_id} and {to_person_id} not found"
        )

    try:
        updated = await update_relationship(from_person_id, to_person_id, payload)
        if not updated:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to update relationship between persons {from_person_id} and {to_person_id}"
            )

        return updated
    except Exception as e:
        logger.error(f"Error updating relationship: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error updating relationship: {str(e)}"
        )


@router.delete(
    "/cases/{case_id}/persons/{from_person_id}/relationships/{to_person_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    tags=["relationships"]
)
async def delete_relationship_endpoint(
    case_id: uuid.UUID,
    from_person_id: uuid.UUID,
    to_person_id: uuid.UUID,
    current_user: UserPublic = Depends(get_current_active_user)
):
    """
    Delete a specific relationship between two persons in a case
    """
    # Verify both persons exist and belong to the same case
    case_id_match = await check_persons_in_same_case(from_person_id, to_person_id)
    if not case_id_match:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Both persons must belong to the same case"
        )

    if case_id_match != case_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Persons belong to case {case_id_match}, not case {case_id}"
        )

    # Get the relationship
    relationship = await get_relationship(from_person_id, to_person_id)
    if not relationship:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Relationship between persons {from_person_id} and {to_person_id} not found"
        )

    try:
        success = await delete_relationship(from_person_id, to_person_id)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to delete relationship between persons {from_person_id} and {to_person_id}"
            )

        return None  # 204 No Content
    except Exception as e:
        logger.error(f"Error deleting relationship: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error deleting relationship: {str(e)}"
        )
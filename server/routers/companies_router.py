"""
Router for case companies management
"""
import uuid
import logging
from fastapi import APIRouter, HTTPException, status, Depends

from server.database.companies_database import (
    CompanyInCreate,
    CompanyInDB,
    CompanyInUpdate,
    create_company,
    get_company_by_id,
    get_companies_by_case,
    update_company,
    delete_company
)
from server.database.cases_database import get_case
from server.features.users.security import get_current_active_user, oauth2_scheme
from server.database.users_database import UserPublic

logger = logging.getLogger(__name__)

router = APIRouter(
    dependencies=[Depends(oauth2_scheme)]
)


@router.post(
    "/cases/{case_id}/companies",
    response_model=CompanyInDB,
    status_code=status.HTTP_201_CREATED,
    tags=["companies"]
)
async def create_company_endpoint(
        case_id: uuid.UUID,
        payload: CompanyInCreate,
        current_user: UserPublic = Depends(get_current_active_user)
):
    """
    Add a new company to a case
    """
    # Check if case ID in path matches payload
    if payload.case_id != case_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Case ID in path must match case ID in payload"
        )

    # Verify the case exists
    case = await get_case(case_id)
    if not case:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Case with ID {case_id} not found"
        )

    try:
        return await create_company(payload)
    except Exception as e:
        logger.error(f"Error creating company: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error creating company: {str(e)}"
        )


@router.get(
    "/cases/{case_id}/companies",
    response_model=list[CompanyInDB],
    tags=["companies"]
)
async def get_companies_endpoint(
        case_id: uuid.UUID,
        current_user: UserPublic = Depends(get_current_active_user)
):
    """
    Get all companies in a case
    """
    # Verify the case exists
    case = await get_case(case_id)
    if not case:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Case with ID {case_id} not found"
        )

    try:
        return await get_companies_by_case(case_id)
    except Exception as e:
        logger.error(f"Error retrieving companies: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving companies: {str(e)}"
        )


@router.get(
    "/cases/{case_id}/companies/{company_id}",
    response_model=CompanyInDB,
    tags=["companies"]
)
async def get_company_endpoint(
        case_id: uuid.UUID,
        company_id: uuid.UUID,
        current_user: UserPublic = Depends(get_current_active_user)
):
    """
    Get a specific company in a case
    """
    # Verify the case exists
    case = await get_case(case_id)
    if not case:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Case with ID {case_id} not found"
        )

    # Get the company
    company = await get_company_by_id(company_id)
    if not company:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Company with ID {company_id} not found"
        )

    # Verify the company belongs to the case
    if company.case_id != case_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Company with ID {company_id} does not belong to case with ID {case_id}"
        )

    return company


@router.put(
    "/cases/{case_id}/companies/{company_id}",
    response_model=CompanyInDB,
    tags=["companies"]
)
async def update_company_endpoint(
        case_id: uuid.UUID,
        company_id: uuid.UUID,
        payload: CompanyInUpdate,
        current_user: UserPublic = Depends(get_current_active_user)
):
    """
    Update a specific company in a case
    """
    # Verify the case exists
    case = await get_case(case_id)
    if not case:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Case with ID {case_id} not found"
        )

    # Get the company
    company = await get_company_by_id(company_id)
    if not company:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Company with ID {company_id} not found"
        )

    # Verify the company belongs to the case
    if company.case_id != case_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Company with ID {company_id} does not belong to case with ID {case_id}"
        )

    try:
        updated = await update_company(company_id, payload)
        if not updated:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to update company with ID {company_id}"
            )

        return updated
    except Exception as e:
        logger.error(f"Error updating company: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error updating company: {str(e)}"
        )


@router.delete(
    "/cases/{case_id}/companies/{company_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    tags=["companies"]
)
async def delete_company_endpoint(
        case_id: uuid.UUID,
        company_id: uuid.UUID,
        current_user: UserPublic = Depends(get_current_active_user)
):
    """
    Delete a specific company in a case
    """
    # Verify the case exists
    case = await get_case(case_id)
    if not case:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Case with ID {case_id} not found"
        )

    # Get the company
    company = await get_company_by_id(company_id)
    if not company:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Company with ID {company_id} not found"
        )

    # Verify the company belongs to the case
    if company.case_id != case_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Company with ID {company_id} does not belong to case with ID {case_id}"
        )

    try:
        success = await delete_company(company_id)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to delete company with ID {company_id}"
            )

        return None  # 204 No Content
    except Exception as e:
        logger.error(f"Error deleting company: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error deleting company: {str(e)}"
        )
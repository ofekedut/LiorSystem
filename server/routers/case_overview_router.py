"""
Router for case overview functionality.
This implements the case composition overview mentioned in the PRD.
"""
import uuid
import logging
from fastapi import APIRouter, Depends, HTTPException, status

from server.database.case_overview_database import (
    CaseOverview,
    DetailedCaseOverview,
    get_case_overview,
    get_detailed_case_overview
)
from server.features.users.security import get_current_active_user, oauth2_scheme
from server.database.users_database import UserPublic
from server.database.cases_database import get_case

# Setup logging
logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/case-overview",
    tags=["case_overview"],
    dependencies=[Depends(oauth2_scheme)]
)


@router.get(
    "/{case_id}",
    response_model=CaseOverview
)
async def get_case_overview_endpoint(
    case_id: uuid.UUID,
    current_user: UserPublic = Depends(get_current_active_user)
) -> CaseOverview:
    """
    Get a high-level overview of a case's composition.
    
    This provides a summary of entity counts, primary contact, 
    and documents needing attention.
    """
    try:
        # Check if the case exists
        case = await get_case(case_id)
        if not case:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Case with ID {case_id} not found"
            )
            
        overview = await get_case_overview(case_id)
        if not overview:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Case overview not available for case with ID {case_id}"
            )
            
        return overview
        
    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    except Exception as e:
        logger.error(f"Error getting case overview: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An unexpected error occurred: {str(e)}"
        )


@router.get(
    "/{case_id}/detailed",
    response_model=DetailedCaseOverview
)
async def get_detailed_case_overview_endpoint(
    case_id: uuid.UUID,
    current_user: UserPublic = Depends(get_current_active_user)
) -> DetailedCaseOverview:
    """
    Get a detailed overview of a case's composition including entity-level details.
    
    This provides comprehensive information about all entities in the case,
    their documents, and document status.
    """
    try:
        # Check if the case exists
        case = await get_case(case_id)
        if not case:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Case with ID {case_id} not found"
            )
            
        detailed_overview = await get_detailed_case_overview(case_id)
        if not detailed_overview:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Detailed case overview not available for case with ID {case_id}"
            )
            
        return detailed_overview
        
    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    except Exception as e:
        logger.error(f"Error getting detailed case overview: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An unexpected error occurred: {str(e)}"
        )

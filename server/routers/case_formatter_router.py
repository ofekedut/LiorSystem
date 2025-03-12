"""
Router for formatted case data
"""
import uuid
import logging
from fastapi import APIRouter, HTTPException, status, Depends
from typing import Dict, Any

from server.database.case_formatter_database import get_formatted_case
from server.database.cases_database import get_case
from server.features.users.security import get_current_active_user, oauth2_scheme
from server.database.users_database import UserPublic

logger = logging.getLogger(__name__)

router = APIRouter(
    dependencies=[Depends(oauth2_scheme)]
)


@router.get(
    "/api/v1/cases/{case_id}/complete",
    response_model=Dict[str, Any],
    tags=["case-formatter"]
)
async def get_complete_case(
        case_id: uuid.UUID,
        current_user: UserPublic = Depends(get_current_active_user)
):
    """
    Get a complete case with all related data formatted to match the sample JSON structure
    """
    # Verify the case exists
    case = await get_case(case_id)
    if not case:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Case with ID {case_id} not found"
        )

    try:
        formatted_case = await get_formatted_case(case_id)
        return formatted_case
    except Exception as e:
        logger.error(f"Error retrieving formatted case: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving formatted case: {str(e)}"
        )
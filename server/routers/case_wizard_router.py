"""
Router for New Case Wizard functionality.
This implements the guided workflow for new case creation as specified in the PRD.
"""
import logging
from fastapi import APIRouter, HTTPException, status, Depends
from typing import Dict, Any

from server.database.case_wizard_database import (
    CaseDeclarationSurvey,
    WizardResult,
    create_case_with_wizard
)
from server.features.users.security import get_current_active_user, oauth2_scheme
from server.database.users_database import UserPublic

# Setup logging
logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/case-wizard",
    tags=["case_wizard"],
    dependencies=[Depends(oauth2_scheme)]
)

@router.post(
    "/new",
    response_model=WizardResult,
    status_code=status.HTTP_201_CREATED
)
async def create_case_using_wizard(
    survey: CaseDeclarationSurvey,
    current_user: UserPublic = Depends(get_current_active_user)
) -> WizardResult:
    """
    Create a new case using the guided wizard workflow.
    
    The wizard takes a declaration survey that establishes the basic case structure
    with all relevant entities (persons, companies, financial entities, etc.).
    """
    try:
        logger.info(f"Starting New Case Wizard process for case: {survey.case_name}")
        
        # Validate the survey has at least one person
        if not survey.persons or len(survey.persons) == 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="At least one person must be included in the case declaration"
            )
        
        # Create the case with all related entities
        result = await create_case_with_wizard(survey)
        
        # Check if there were any errors
        if not result.success:
            # If we have critical errors (where case is None), raise exception
            if not result.case:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=f"Failed to create case: {'; '.join(result.errors)}"
                )
            
            # Otherwise log warnings about non-critical errors
            for error in result.errors:
                logger.warning(f"Non-critical error in wizard process: {error}")
        
        logger.info(f"Case wizard completed successfully for case ID: {result.case.id}")
        return result
        
    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    except Exception as e:
        logger.error(f"Error in Case Wizard: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An unexpected error occurred: {str(e)}"
        )


@router.get(
    "/dropdown-options",
    response_model=Dict[str, list]
)
async def get_wizard_dropdown_options(
    current_user: UserPublic = Depends(get_current_active_user)
) -> Dict[str, Any]:
    """
    Get all dropdown options needed for the case wizard form.
    
    This includes:
    - Person roles
    - Relationship types 
    - Marital statuses
    - Company types
    - Account types
    - Card types
    - Loan types
    - Asset types
    - Income source types
    """
    try:
        from server.database.lior_dropdown_options_database import get_dropdown_options_by_category
        
        # Get all required dropdown options
        categories = [
            "person_roles",
            "relationship_types",
            "marital_statuses",
            "company_types",
            "account_types",
            "card_types",
            "loan_types",
            "asset_types",
            "income_source_types"
        ]
        
        result = {}
        
        for category in categories:
            options = await get_dropdown_options_by_category(category)
            result[category] = [
                {
                    "id": str(option.id),
                    "name": option.name,
                    "value": option.value
                }
                for option in options
            ]
        
        return result
        
    except Exception as e:
        logger.error(f"Error fetching dropdown options: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error fetching dropdown options: {str(e)}"
        )

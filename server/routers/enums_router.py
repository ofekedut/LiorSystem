"""
Router for unified enum management
"""
from fastapi import APIRouter, HTTPException, Depends, status
from typing import List, Dict, Any

from server.database.enums_database import (
    get_enum_values,
    manage_enum_value,
    get_all_enums,
    EnumRequest,
    EnumValueInDB,
    ENUM_TABLE_MAP
)
from server.features.users.security import get_current_active_user, oauth2_scheme
from server.database.users_database import UserPublic, UserRole

router = APIRouter(
    prefix="/api/v1/enums",
    tags=["enums"],
    dependencies=[Depends(oauth2_scheme)]
)


@router.get("", response_model=Dict[str, List[Dict[str, Any]]])
async def list_all_enums(current_user: UserPublic = Depends(get_current_active_user)):
    """
    Get all enums with their values.

    Returns a dictionary with enum names as keys and lists of enum values as values.
    """
    try:
        enums = await get_all_enums()
        # Convert to dict format for each enum value for consistency
        return {
            enum_name: [
                {"id": str(val.id), "name": val.name, "value": val.value}
                for val in values
            ]
            for enum_name, values in enums.items()
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving enums: {str(e)}"
        )


@router.get("/available", response_model=List[str])
async def list_available_enums(current_user: UserPublic = Depends(get_current_active_user)):
    """
    Get a list of all available enum types.
    """
    return list(ENUM_TABLE_MAP.keys())


@router.get("/{enum_name}", response_model=List[Dict[str, Any]])
async def get_enum(enum_name: str, current_user: UserPublic = Depends(get_current_active_user)):
    """
    Get all values for a specific enum type.
    """
    try:
        values = await get_enum_values(enum_name)
        return [{"id": str(val.id), "name": val.name, "value": val.value} for val in values]
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving enum values: {str(e)}"
        )


@router.post("", response_model=Dict[str, Any])
async def manage_enum(
        request: EnumRequest,
        current_user: UserPublic = Depends(get_current_active_user)
):
    """
    Add, update, or delete an enum value.

    Requires admin role.
    """
    # Verify the user has admin rights for enum management
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only administrators can manage enum values"
        )

    try:
        result = await manage_enum_value(request)
        return result
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error managing enum value: {str(e)}"
        )
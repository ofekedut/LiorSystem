"""
Router for dropdown options management with enum service compatibility
"""
import uuid
import logging
from fastapi import APIRouter, HTTPException, status, Depends, Query, Body
from typing import Dict, List, Any, Optional
from pydantic import BaseModel

from server.database.lior_dropdown_options_database import (
    DropdownOptionCreate,
    DropdownOptionInDB,
    DropdownOptionUpdate,
    create_dropdown_option,
    get_dropdown_option_by_id,
    get_dropdown_option_by_value,
    get_dropdown_options_by_category,
    get_all_dropdown_options,
    get_all_categories,
    update_dropdown_option,
    delete_dropdown_option,
    check_option_in_use
)
from server.features.users.security import get_current_active_user, oauth2_scheme
from server.database.users_database import UserPublic, UserRole

logger = logging.getLogger(__name__)

router = APIRouter(
    tags=["dropdown-options"],
    dependencies=[Depends(oauth2_scheme)]
)


# ===============================================================================
# Original Dropdown Options Endpoints
# ===============================================================================

@router.get("/api/v1/dropdown-options", response_model=Dict[str, List[Dict[str, Any]]])
async def get_all_options(current_user: UserPublic = Depends(get_current_active_user)):
    """
    Get all dropdown options organized by category
    """
    try:
        options = await get_all_dropdown_options()
        # Convert to dict format for each option for consistency
        return {
            category: [
                {"id": str(opt.id), "name": opt.name, "value": opt.value}
                for opt in opts
            ]
            for category, opts in options.items()
        }
    except Exception as e:
        logger.error(f"Error retrieving dropdown options: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving dropdown options: {str(e)}"
        )


@router.get("/api/v1/dropdown-options/categories", response_model=List[str])
async def get_categories(current_user: UserPublic = Depends(get_current_active_user)):
    """
    Get a list of all available dropdown categories
    """
    try:
        return await get_all_categories()
    except Exception as e:
        logger.error(f"Error retrieving categories: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving categories: {str(e)}"
        )


@router.get("/api/v1/dropdown-options/{category}", response_model=List[Dict[str, Any]])
async def get_options_by_category(
        category: str,
        current_user: UserPublic = Depends(get_current_active_user)
):
    """
    Get all dropdown options for a specific category
    """
    try:
        options = await get_dropdown_options_by_category(category)
        return [{"id": str(opt.id), "name": opt.name, "value": opt.value} for opt in options]
    except Exception as e:
        logger.error(f"Error retrieving options for category {category}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving options for category {category}: {str(e)}"
        )


@router.post("/api/v1/dropdown-options", response_model=Dict[str, Any], status_code=status.HTTP_201_CREATED)
async def create_option(
        payload: DropdownOptionCreate,
        current_user: UserPublic = Depends(get_current_active_user)
):
    """
    Create a new dropdown option

    Requires admin role
    """
    # Verify the user has admin rights
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only administrators can manage dropdown options"
        )

    try:
        # Check if option with same category and value already exists
        existing = await get_dropdown_option_by_value(payload.category, payload.value)
        if existing:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Option with category '{payload.category}' and value '{payload.value}' already exists"
            )

        # Create the new option
        option = await create_dropdown_option(payload)
        return {
            "id": str(option.id),
            "category": option.category,
            "name": option.name,
            "value": option.value,
            "created_at": option.created_at.isoformat(),
            "updated_at": option.updated_at.isoformat()
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating dropdown option: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error creating dropdown option: {str(e)}"
        )


@router.put("/api/v1/dropdown-options/{option_id}", response_model=Dict[str, Any])
async def update_option(
        option_id: uuid.UUID,
        payload: DropdownOptionUpdate,
        current_user: UserPublic = Depends(get_current_active_user)
):
    """
    Update an existing dropdown option

    Requires admin role
    """
    # Verify the user has admin rights
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only administrators can manage dropdown options"
        )

    try:
        # Get the existing option
        existing = await get_dropdown_option_by_id(option_id)
        if not existing:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Dropdown option with ID {option_id} not found"
            )

        # Check if option is in use before allowing value changes
        if payload.value is not None and payload.value != existing.value:
            in_use = await check_option_in_use(option_id)
            if in_use:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail=f"Cannot change value of option '{existing.value}' because it is in use"
                )

            # Check if new value would conflict with existing value in same category
            conflict = await get_dropdown_option_by_value(existing.category, payload.value)
            if conflict and conflict.id != option_id:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail=f"Option with category '{existing.category}' and value '{payload.value}' already exists"
                )

        # Update the option
        updated = await update_dropdown_option(option_id, payload)
        if not updated:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to update dropdown option with ID {option_id}"
            )

        return {
            "id": str(updated.id),
            "category": updated.category,
            "name": updated.name,
            "value": updated.value,
            "created_at": updated.created_at.isoformat(),
            "updated_at": updated.updated_at.isoformat()
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating dropdown option: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error updating dropdown option: {str(e)}"
        )


@router.delete("/api/v1/dropdown-options/{option_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_option(
        option_id: uuid.UUID,
        force: bool = Query(False, description="Force deletion even if option is in use"),
        current_user: UserPublic = Depends(get_current_active_user)
):
    """
    Delete a dropdown option

    Requires admin role

    By default, will not delete options that are in use unless force=true
    """
    # Verify the user has admin rights
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only administrators can manage dropdown options"
        )

    try:
        # Get the existing option
        existing = await get_dropdown_option_by_id(option_id)
        if not existing:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Dropdown option with ID {option_id} not found"
            )

        # Check if option is in use
        if not force:
            in_use = await check_option_in_use(option_id)
            if in_use:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail=f"Cannot delete option '{existing.value}' because it is in use. Use force=true to override."
                )

        # Delete the option
        success = await delete_dropdown_option(option_id)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to delete dropdown option with ID {option_id}"
            )

        return None  # 204 No Content
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting dropdown option: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error deleting dropdown option: {str(e)}"
        )


# ===============================================================================
# New Enum Service Compatible Endpoints
# ===============================================================================

@router.get(
    "/api/v1/enums/{enum_name}",
    response_model=List[Dict[str, Any]],
    tags=["enums"]
)
async def get_enum_values(
    enum_name: str,
    current_user: UserPublic = Depends(get_current_active_user)
):
    """
    Get all enum values for a specific enum name (maps to dropdown category)
    Compatible with Angular EnumsService
    """
    try:
        options = await get_dropdown_options_by_category(enum_name)
        return [
            {"id": str(opt.id), "name": opt.name, "value": opt.value}
            for opt in options
        ]
    except Exception as e:
        logger.error(f"Error retrieving enum values for {enum_name}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving enum values: {str(e)}"
        )


class EnumRequest(BaseModel):
    enum_name: str
    operation: str
    id: Optional[str] = None
    name: Optional[str] = None
    value: Optional[str] = None


@router.post(
    "/api/v1/enums",
    status_code=status.HTTP_200_OK,
    tags=["enums"]
)
async def manage_enum(
    request: Dict[str, Any] = Body(...),
    current_user: UserPublic = Depends(get_current_active_user)
):
    """
    Unified endpoint for adding, updating, or deleting enum values
    Compatible with Angular EnumsService

    Expected request body format:
    {
        "enum_name": "category_name",
        "operation": "add" | "update" | "delete",
        "id": "uuid_string", // required for update and delete
        "name": "display_name", // required for add, optional for update
        "value": "value_string" // required for add, optional for update
    }
    """
    # Verify the user has admin rights
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only administrators can manage enum values"
        )

    # Extract operation and enum name
    operation = request.get("operation")
    enum_name = request.get("enum_name")

    if not operation or not enum_name:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Missing required fields: operation and enum_name"
        )

    try:
        # ADD operation
        if operation == "add":
            value = request.get("value")
            name = request.get("name")

            if not value or not name:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Missing required fields for add operation: name and value"
                )

            # Check if option with same category and value already exists
            existing = await get_dropdown_option_by_value(enum_name, value)
            if existing:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail=f"Option with category '{enum_name}' and value '{value}' already exists"
                )

            option = await create_dropdown_option(
                DropdownOptionCreate(
                    category=enum_name,
                    name=name,
                    value=value
                )
            )
            return {"success": True, "id": str(option.id)}

        # UPDATE operation
        elif operation == "update":
            option_id = request.get("id")
            value = request.get("value")
            name = request.get("name")

            if not option_id:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Missing required field for update operation: id"
                )

            # Get the existing option
            existing = await get_dropdown_option_by_id(uuid.UUID(option_id))
            if not existing:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Enum value with ID {option_id} not found"
                )

            # Prepare update data
            update_data = DropdownOptionUpdate()
            if name is not None:
                update_data.name = name
            if value is not None:
                update_data.value = value

                # Check if option is in use before allowing value changes
                if value != existing.value:
                    in_use = await check_option_in_use(uuid.UUID(option_id))
                    if in_use:
                        raise HTTPException(
                            status_code=status.HTTP_409_CONFLICT,
                            detail=f"Cannot change value of option '{existing.value}' because it is in use"
                        )

                    # Check if new value would conflict with existing value in same category
                    conflict = await get_dropdown_option_by_value(existing.category, value)
                    if conflict and str(conflict.id) != option_id:
                        raise HTTPException(
                            status_code=status.HTTP_409_CONFLICT,
                            detail=f"Option with category '{existing.category}' and value '{value}' already exists"
                        )

            # Update the option
            updated = await update_dropdown_option(uuid.UUID(option_id), update_data)
            if not updated:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=f"Failed to update enum value with ID {option_id}"
                )

            return {"success": True}

        # DELETE operation
        elif operation == "delete":
            option_id = request.get("id")

            if not option_id:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Missing required field for delete operation: id"
                )

            # Get the existing option
            existing = await get_dropdown_option_by_id(uuid.UUID(option_id))
            if not existing:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Enum value with ID {option_id} not found"
                )

            # Check if option is in use
            in_use = await check_option_in_use(uuid.UUID(option_id))
            if in_use:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail=f"Cannot delete option '{existing.value}' because it is in use."
                )

            # Delete the option
            success = await delete_dropdown_option(uuid.UUID(option_id))
            if not success:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=f"Failed to delete enum value with ID {option_id}"
                )

            return {"success": True}

        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid operation: {operation}. Must be one of: add, update, delete"
            )

    except HTTPException:
        raise
    except ValueError as e:
        logger.error(f"Value error in manage_enum operation={operation}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid value: {str(e)}"
        )
    except Exception as e:
        logger.error(f"Error in manage_enum operation={operation}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error managing enum: {str(e)}"
        )
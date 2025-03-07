import uuid
from typing import List
from fastapi import APIRouter, HTTPException, status

from server.database.asset_types_database import (
    AssetType,
    AssetTypeInCreate,
    AssetTypeInUpdate,
    create_asset_type,
    get_asset_types,
    get_asset_type_by_id,
    get_asset_type_by_value,
    update_asset_type,
    delete_asset_type
)

router = APIRouter(
    prefix='/asset-types',
    tags=['Asset Types']
)


@router.post('', response_model=AssetType, status_code=status.HTTP_201_CREATED)
async def create_asset_type_endpoint(payload: AssetTypeInCreate):
    """Create a new asset type"""
    existing_asset_type = await get_asset_type_by_value(payload.value)
    if existing_asset_type:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Asset type with value '{payload.value}' already exists"
        )

    return await create_asset_type(payload)


@router.get('', response_model=List[AssetType])
async def get_asset_types_endpoint():
    """Get all asset types"""
    return await get_asset_types()


@router.get('/{asset_type_id}', response_model=AssetType)
async def get_asset_type_endpoint(asset_type_id: uuid.UUID):
    """Get an asset type by ID"""
    asset_type = await get_asset_type_by_id(asset_type_id)
    if not asset_type:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Asset type with id '{asset_type_id}' not found"
        )

    return asset_type


@router.put('/{asset_type_id}', response_model=AssetType)
async def update_asset_type_endpoint(asset_type_id: uuid.UUID, payload: AssetTypeInUpdate):
    """Update an asset type"""
    # Check if the asset type exists
    asset_type = await get_asset_type_by_id(asset_type_id)
    if not asset_type:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Asset type with id '{asset_type_id}' not found"
        )

    # Check if the value is being updated and if it conflicts with an existing value
    if payload.value and payload.value != asset_type.value:
        existing_asset_type = await get_asset_type_by_value(payload.value)
        if existing_asset_type:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Asset type with value '{payload.value}' already exists"
            )

    updated_asset_type = await update_asset_type(asset_type_id, payload)
    if not updated_asset_type:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update asset type"
        )

    return updated_asset_type


import logging

logger = logging.getLogger(__name__)

@router.delete('/{asset_type_id}', status_code=status.HTTP_204_NO_CONTENT)
async def delete_asset_type_endpoint(asset_type_id: uuid.UUID):
    try:
        """Delete an asset type"""
        logger.info(f"Attempting to delete asset type with ID: {asset_type_id}")
        
        # Check if the asset type exists
        asset_type = await get_asset_type_by_id(asset_type_id)
        if not asset_type:
            logger.warning(f"Asset type with id '{asset_type_id}' not found")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Asset type with id '{asset_type_id}' not found"
            )

        success = await delete_asset_type(asset_type_id)
        logger.info(f"Delete operation result: {success}")
        # Return with no content for successful deletion
        return None
    except HTTPException:
        # Re-raise HTTP exceptions directly
        raise
    except Exception as e:
        logger.error(f"Error deleting asset type: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error deleting asset type: {str(e)}"
        )

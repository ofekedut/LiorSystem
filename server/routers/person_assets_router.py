import uuid
import logging
from typing import List
from fastapi import APIRouter, HTTPException, status
from uuid import UUID

from server.database.person_assets_database import (
    PersonAsset,
    PersonAssetInCreate,
    PersonAssetInUpdate,
    create_person_asset,
    get_person_assets_by_person_id,
    get_person_asset_by_id,
    update_person_asset,
    delete_person_asset
)

router = APIRouter(
    tags=['Person Assets']
)

logger = logging.getLogger(__name__)


@router.post(
    "/persons/{person_id}/assets",
    response_model=PersonAsset,
    status_code=status.HTTP_201_CREATED
)
async def create_person_asset_endpoint(
    person_id: UUID,
    payload: PersonAssetInCreate
):
    """
    Create a new asset for a person
    """
    # Ensure the person_id in the path matches the one in the payload
    if person_id != payload.person_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Person ID in path must match Person ID in payload"
        )
    
    try:
        result = await create_person_asset(payload)
        if not result:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to create person asset"
            )
        return result
    except Exception as e:
        logger.error(f"Error creating person asset: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error creating person asset: {str(e)}"
        )


@router.get(
    "/persons/{person_id}/assets",
    response_model=List[PersonAsset]
)
async def get_person_assets_endpoint(person_id: UUID):
    """
    Get all assets for a specific person
    """
    try:
        assets = await get_person_assets_by_person_id(person_id)
        if assets is None:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to fetch person assets"
            )
        return assets
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching person assets: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error fetching person assets: {str(e)}"
        )


@router.get(
    "/persons/{person_id}/assets/{asset_id}",
    response_model=PersonAsset
)
async def get_person_asset_endpoint(person_id: UUID, asset_id: UUID):
    """
    Get a specific asset for a person
    """
    try:
        asset = await get_person_asset_by_id(asset_id)
        if not asset:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Person asset with ID {asset_id} not found"
            )
        
        # Verify that the asset belongs to the specified person
        if asset.person_id != person_id:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Asset with ID {asset_id} does not belong to person with ID {person_id}"
            )
            
        return asset
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching person asset: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error fetching person asset: {str(e)}"
        )


@router.put(
    "/persons/{person_id}/assets/{asset_id}",
    response_model=PersonAsset
)
async def update_person_asset_endpoint(
    person_id: UUID,
    asset_id: UUID,
    payload: PersonAssetInUpdate
):
    """
    Update a specific asset for a person
    """
    try:
        # First verify that the asset exists and belongs to the person
        existing_asset = await get_person_asset_by_id(asset_id)
        if not existing_asset:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Person asset with ID {asset_id} not found"
            )
        
        if existing_asset.person_id != person_id:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Asset with ID {asset_id} does not belong to person with ID {person_id}"
            )
        
        # Update the asset
        updated_asset = await update_person_asset(asset_id, payload)
        if not updated_asset:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to update asset with ID {asset_id}"
            )
            
        return updated_asset
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating person asset: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error updating person asset: {str(e)}"
        )


@router.delete(
    "/persons/{person_id}/assets/{asset_id}",
    response_model=dict
)
async def delete_person_asset_endpoint(person_id: UUID, asset_id: UUID):
    """
    Delete a specific asset for a person
    """
    try:
        # First verify that the asset exists and belongs to the person
        existing_asset = await get_person_asset_by_id(asset_id)
        if not existing_asset:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Person asset with ID {asset_id} not found"
            )
        
        if existing_asset.person_id != person_id:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Asset with ID {asset_id} does not belong to person with ID {person_id}"
            )
        
        # Delete the asset
        result = await delete_person_asset(asset_id)
        if not result:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to delete asset with ID {asset_id}"
            )
            
        return {"message": f"Asset with ID {asset_id} successfully deleted"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting person asset: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error deleting person asset: {str(e)}"
        )

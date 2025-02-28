from fastapi import APIRouter, Depends, UploadFile, File, status
from typing import Optional, List
import uuid
from server.database.users_database import (
    UserCreate, UserPublic, UserUpdate, UserProfileUpdate,
    PasswordChange, NotificationPreferences, UserPreferences,
    update_user_profile, get_user,
    change_password,
    UserRole, UserStatus, list_users_paginated, delete_user, update_user_preferences, update_user_role, UserLanguage, NotificationTypes, PaginatedUsers
)
from server.features.users.security import get_current_active_user, oauth2_scheme
from server.features.users.image_service import ImageService

router = APIRouter(
    prefix="/api/v1/users",
    tags=["users"],
    dependencies=[Depends(oauth2_scheme)]
)

AVATAR_DIR = "../features/users/uploads/avatars"
MAX_FILE_SIZE = 2 * 1024 * 1024  # 2MB
ALLOWED_CONTENT_TYPES = ["image/jpeg", "image/png"]

image_service = ImageService(AVATAR_DIR)


@router.get("", response_model=PaginatedUsers)
async def list_users(
        search: Optional[str] = None,
        role: Optional[UserRole] = None,
        status: Optional[UserStatus] = None,
        page: int = 1,
        limit: int = 10,
        current_user: UserPublic = Depends(get_current_active_user)
):
    """List users with pagination and filtering (Admin only)"""
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(status_code=403, detail="Insufficient permissions")
    data = await list_users_paginated(search, role, status, page, limit)
    return data


@router.post("", response_model=UserPublic, status_code=status.HTTP_201_CREATED)
async def create_new_user(
        user_data: UserCreate,
        current_user: UserPublic = Depends(get_current_active_user)
):
    """Create a new user (Admin only)"""
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(status_code=403, detail="Insufficient permissions")
    created_user = await create_user(user_data)
    return UserPublic(**created_user.dict(exclude={"password_hash"}))


@router.get("/{user_id}", response_model=UserPublic)
async def get_user_profile(
        user_id: uuid.UUID,
        current_user: UserPublic = Depends(get_current_active_user)
):
    """Get user profile by ID (Self or Admin)"""
    if current_user.id != user_id and current_user.role != UserRole.ADMIN:
        raise HTTPException(status_code=403, detail="Insufficient permissions")

    user = await get_user(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user


@router.put("/{user_id}", response_model=UserPublic)
async def update_user(
        user_id: uuid.UUID,
        user_data: UserUpdate,
        current_user: UserPublic = Depends(get_current_active_user)
):
    """Update user profile (Self or Admin)"""
    if current_user.id != user_id and current_user.role != UserRole.ADMIN:
        raise HTTPException(status_code=403, detail="Insufficient permissions")
    return await update_user_profile(user_id, user_data)


@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user_account(
        user_id: uuid.UUID,
        current_user: UserPublic = Depends(get_current_active_user)
):
    """Delete user account (Admin only)"""
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(status_code=403, detail="Insufficient permissions")

    await delete_user(user_id)
    return None


@router.put("/{user_id}/profile", response_model=UserPublic)
async def update_user_profile_details(
        user_id: uuid.UUID,
        profile_data: UserProfileUpdate,
        current_user: UserPublic = Depends(get_current_active_user)
):
    """Update user profile details (Self only)"""
    if current_user.id != user_id:
        raise HTTPException(status_code=403, detail="Can only update your own profile")
    return await update_user_profile(user_id, profile_data)


@router.post("/{user_id}/password", status_code=status.HTTP_200_OK)
async def change_user_password(
        user_id: uuid.UUID,
        password_data: PasswordChange,
        current_user: UserPublic = Depends(get_current_active_user)
):
    """Change user password (Self only)"""
    if current_user.id != user_id:
        raise HTTPException(status_code=403, detail="Can only change your own password")
    await change_password(user_id, password_data)
    return {"message": "Password updated successfully"}


@router.put("/{user_id}/notifications", response_model=UserPublic)
async def update_notification_preferences(
        user_id: uuid.UUID,
        preferences: NotificationPreferences,
        current_user: UserPublic = Depends(get_current_active_user)
):
    """Update notification preferences (Self only)"""
    if current_user.id != user_id:
        raise HTTPException(status_code=403, detail="Can only update your own preferences")
    return await update_user_preferences(user_id, {"notifications": preferences.dict()})


@router.put("/{user_id}/preferences", response_model=UserPublic)
async def update_user_preferences_endpoint(
        user_id: uuid.UUID,
        preferences: UserPreferences,
        current_user: UserPublic = Depends(get_current_active_user)
):
    """Update user preferences including language and timezone (Self only)"""
    if current_user.id != user_id:
        raise HTTPException(status_code=403, detail="Can only update your own preferences")
    return await update_user_preferences(user_id, preferences.dict())


@router.put("/{user_id}/avatar", response_model=UserPublic)
async def update_avatar(
        user_id: uuid.UUID,
        file: UploadFile = File(...),
        current_user: UserPublic = Depends(get_current_active_user)
):
    """Update user avatar (Self only)"""
    if current_user.id != user_id:
        raise HTTPException(status_code=403, detail="Can only update your own avatar")

    if file.content_type not in ALLOWED_CONTENT_TYPES:
        raise HTTPException(status_code=400, detail="Invalid file type. Only JPEG/PNG allowed")

    if image_service.get_image_size(file) > MAX_FILE_SIZE:
        raise HTTPException(status_code=413, detail="File too large. Max 2MB allowed")

    try:
        # Generate unique filename
        file_ext = file.filename.split(".")[-1]
        filename = f"{uuid.uuid4()}.{file_ext}"

        # Process and save new avatar
        file_path = await image_service.process_avatar(file, filename)

        # Delete old avatar if exists
        old_user = await get_user(user_id)
        if old_user and old_user.avatar:
            await image_service.delete_avatar(old_user.avatar)

        # Update user profile with new avatar path
        return await update_user_profile(
            user_id,
            UserProfileUpdate(avatar=file_path)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error processing avatar: {str(e)}"
        )


import uuid
from server.database.users_database import create_user, UserCreate, UserRole

import asyncio
from fastapi import HTTPException


async def main():
    # Collect admin details
    password = "123456789qQ!"

    # Create UserCreate instance
    admin_user = UserCreate(
        email="ofekedut86@gmail.com",
        password=password,
        first_name="Ofek",
        last_name="Meleh"
    )

    try:
        # Create the admin user
        created_user = await create_user(admin_user)

        # Update role to admin
        updated_user = await update_user_role(created_user.id, UserRole.ADMIN)

        # Update additional profile information
        profile_update = UserProfileUpdate(
            phone="+1234567890",  # Add admin contact number
            department="IT Administration",  # Set admin department
            position="System Administrator",  # Set admin position
            avatar="default_admin_avatar.png"  # Set admin avatar
        )

        # Update preferences with admin-specific settings
        preferences_update = UserPreferences(
            language=UserLanguage.HE,  # Set preferred language
            timezone="Asia/Jerusalem",  # Set appropriate timezone
            notifications=NotificationPreferences(
                email=True,  # Enable email notifications
                system=True,  # Enable system notifications
                types=NotificationTypes(
                    cases=True,  # Enable all notification types for admin
                    documents=True,
                    system=True
                )
            )
        )

        # Update the user's status to active (if not already)
        await update_user_profile(updated_user.id, UserUpdate(
            email=updated_user.email,  # Maintain existing email
            first_name=updated_user.first_name,  # Maintain existing first name
            last_name=updated_user.last_name  # Maintain existing last name
        ))

        # Update user preferences
        await update_user_preferences(updated_user.id, preferences_update)

        print("Admin user created and configured successfully!")
        print(f"User ID: {updated_user.id}")
        print(f"Email: {updated_user.email}")
        print(f"Role: {updated_user.role}")
        print(f"Status: {updated_user.status}")
        print(f"Department: {profile_update.department}")
        print(f"Position: {profile_update.position}")
        print(f"Timezone: {preferences_update.timezone}")
        print(f"Notifications Enabled: Email={preferences_update.notifications.email}, System={preferences_update.notifications.system}")

    except HTTPException as e:
        print(f"HTTP Error: {e.detail}")
    except Exception as e:
        print(f"Error creating admin user: {e}")


if __name__ == "__main__":
    asyncio.run(main())

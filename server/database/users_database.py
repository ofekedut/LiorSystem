import asyncpg
from datetime import datetime
from pydantic import BaseModel, Field, validator, constr
from typing import Optional, Dict, List, Tuple, Literal
import pytz
import re
import uuid
from passlib.context import CryptContext
from fastapi import HTTPException, status
import json

from server.database.database import get_connection

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Using string literals instead of enums
# This provides flexibility while still having some type safety
UserRole = Literal["admin", "user"]
UserStatus = Literal["active", "inactive", "suspended"]
UserLanguage = Literal["en", "he"]


class UserBase(BaseModel):
    email: str
    first_name: str = Field(..., min_length=2)
    last_name: str = Field(..., min_length=2)


class UserCreate(UserBase):
    password: str

    @validator('password')
    def validate_password(cls, v):
        if len(v) < 8:
            raise ValueError('Password must be at least 8 characters')
        if not re.search(r'[A-Z]', v):
            raise ValueError('Password must contain an uppercase letter')
        if not re.search(r'[0-9]', v):
            raise ValueError('Password must contain a number')
        if not re.search(r'[!@#$%^&*(),.?":{}|<>]', v):
            raise ValueError('Password must contain a special character')
        return v


class UserUpdate(BaseModel):
    email: Optional[str] = None
    first_name: Optional[str] = Field(None)
    last_name: Optional[str] = Field(None)


class UserProfileUpdate(BaseModel):
    phone: Optional[str] = None
    department: Optional[str] = None
    position: Optional[str] = None
    avatar: Optional[str] = None


class PasswordChange(BaseModel):
    current_password: str
    new_password: str

    @validator('new_password')
    def validate_new_password(cls, v):
        if len(v) < 8:
            raise ValueError('Password must be at least 8 characters')
        if not re.search(r'[A-Z]', v):
            raise ValueError('Password must contain an uppercase letter')
        if not re.search(r'[0-9]', v):
            raise ValueError('Password must contain a number')
        if not re.search(r'[!@#$%^&*(),.?":{}|<>]', v):
            raise ValueError('Password must contain a special character')
        return v


class NotificationTypes(BaseModel):
    cases: bool = True
    documents: bool = True
    system: bool = True


class NotificationPreferences(BaseModel):
    email: bool = True
    system: bool = True
    types: NotificationTypes = Field(default_factory=NotificationTypes)


class UserPreferences(BaseModel):
    language: UserLanguage = "he"
    timezone: str = "UTC"
    notifications: NotificationPreferences = Field(default_factory=NotificationPreferences)

    @validator('timezone')
    def validate_timezone(cls, v):
        if v not in pytz.all_timezones:
            raise ValueError('Invalid timezone')
        return v


class UserInDB(UserBase):
    id: uuid.UUID
    role: str  # Changed from UserRole enum to string
    status: str  # Changed from UserStatus enum to string
    password_hash: str
    last_login: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime
    phone: Optional[str] = None
    department: Optional[str] = None
    position: Optional[str] = None
    avatar: Optional[str] = None
    preferences: UserPreferences
    deleted_at: Optional[datetime] = None

    class Config:
        from_attributes = True

    @classmethod
    def from_database(cls, item: dict) -> "UserInDB":
        item['preferences'] = UserPreferences.model_validate_json(item['preferences'])
        return UserInDB(**item)


class UserPublic(UserBase):
    id: uuid.UUID
    role: str  # Changed from UserRole enum to string
    status: str  # Changed from UserStatus enum to string
    last_login: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime
    phone: Optional[str] = None
    department: Optional[str] = None
    position: Optional[str] = None
    avatar: Optional[str] = None
    preferences: UserPreferences

    class Config:
        from_attributes = True

    @classmethod
    def from_database(cls, item: dict) -> "UserPublic":
        item['preferences'] = UserPreferences.model_validate_json(item['preferences'])
        return UserPublic(**item)


class PaginatedUsers(BaseModel):
    items: list[UserPublic]
    total: int
    page: int
    pages: int


async def create_user(user: UserCreate) -> UserInDB:
    hashed_password = pwd_context.hash(user.password)
    conn = await get_connection()
    async with conn.transaction():
        try:
            row = await conn.fetchrow("""
                    INSERT INTO users (email, first_name, last_name, password_hash)
                    VALUES ($1, $2, $3, $4)
                    RETURNING *
                    """,
                                      user.email.lower(),
                                      user.first_name,
                                      user.last_name,
                                      hashed_password
                                      )
            row = dict(row)
            return UserInDB.from_database(row)
        except asyncpg.UniqueViolationError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered"
            )


async def get_user(user_id: uuid.UUID) -> Optional[UserInDB]:
    conn = await get_connection()
    async with conn.transaction():
        row = await conn.fetchrow(
            "SELECT * FROM users WHERE id = $1 AND deleted_at IS NULL",
            user_id
        )
        return UserInDB.from_database(dict(row)) if row else None


async def get_user_by_email(email: str) -> Optional[UserInDB]:
    conn = await get_connection()
    row = await conn.fetchrow(
        "SELECT * FROM users WHERE email = $1 AND deleted_at IS NULL",
        email.lower()
    )
    return UserInDB.from_database(dict(row)) if row else None


async def update_user_profile(user_id: uuid.UUID, update_data: UserUpdate) -> UserPublic:
    updates = []
    params = []

    for field, value in update_data.dict(exclude_unset=True).items():
        if field == "email" and value is not None:
            updates.append("email = $%d" % (len(updates) + 1))
            params.append(value.lower())
        elif value is not None:
            updates.append(f"{field} = ${len(updates) + 1}")
            params.append(value)

    if not updates:
        user = await get_user(user_id)
        return UserPublic(**user.dict())

    query = f"""
        UPDATE users 
        SET {', '.join(updates)}, updated_at = NOW()
        WHERE id = ${len(updates) + 1} AND deleted_at IS NULL
        RETURNING *
    """
    params.append(user_id)

    conn = await get_connection()
    async with conn.transaction():
        try:
            row = await conn.fetchrow(query, *params)
            if not row:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="User not found"
                )
            return UserPublic.from_database(dict(row))
        except asyncpg.UniqueViolationError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already in use"
            )


async def update_failed_login(user_id: uuid.UUID, reset: bool = False):
    conn = await get_connection()
    async with conn.transaction():
        if reset:
            await conn.execute("""
                    UPDATE users
                    SET failed_login_attempts = 0,
                        lockout_until = NULL
                    WHERE id = $1 AND deleted_at IS NULL
                """, user_id)
        else:
            await conn.execute("""
                    UPDATE users
                    SET failed_login_attempts = failed_login_attempts + 1,
                        last_failed_login = NOW(),
                        lockout_until = CASE 
                            WHEN failed_login_attempts >= 4 THEN NOW() + interval '15 minutes'
                            ELSE lockout_until
                        END
                    WHERE id = $1 AND deleted_at IS NULL
                """, user_id)


async def update_last_login(user_id: uuid.UUID):
    conn = await get_connection()
    async with conn.transaction():
        await conn.execute(
            "UPDATE users SET last_login = NOW() WHERE id = $1 AND deleted_at IS NULL",
            user_id
        )


async def is_account_locked(user_id: uuid.UUID) -> bool:
    conn = await get_connection()
    async with conn.transaction():
        lockout = await conn.fetchval("""
            SELECT lockout_until > NOW()
            FROM users
            WHERE id = $1 AND deleted_at IS NULL
        """, user_id)
        return bool(lockout)


async def change_password(user_id: uuid.UUID, password_change: PasswordChange) -> None:
    conn = await get_connection()
    async with conn.transaction():
        async with conn.transaction():
            user = await get_user(user_id)
            if not user:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="User not found"
                )

            if not pwd_context.verify(password_change.current_password, user.password_hash):
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Incorrect current password"
                )

            if password_change.current_password == password_change.new_password:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="New password must be different from current password"
                )

            new_hash = pwd_context.hash(password_change.new_password)
            await conn.execute(
                "UPDATE users SET password_hash = $1, updated_at = NOW() WHERE id = $2 AND deleted_at IS NULL",
                new_hash,
                user_id
            )


async def list_users_paginated(
        search: Optional[str] = None,
        role: Optional[str] = None,  # Changed from UserRole enum to string
        status: Optional[str] = None,  # Changed from UserStatus enum to string
        page: int = 1,
        limit: int = 10
) -> PaginatedUsers:
    base_query = "FROM users WHERE deleted_at IS NULL"
    conditions = []
    params = []

    if search:
        conditions.append("(email ILIKE $1 OR first_name ILIKE $1 OR last_name ILIKE $1)")
        params.append(f"%{search}%")

    if role:
        conditions.append(f"role = ${len(params) + 1}")
        params.append(role)  # No need to access .value anymore

    if status:
        conditions.append(f"status = ${len(params) + 1}")
        params.append(status)  # No need to access .value anymore

    if conditions:
        base_query += " AND " + " AND ".join(conditions)

    conn = await get_connection()
    async with conn.transaction():
        total = await conn.fetchval(f"SELECT COUNT(*) {base_query}", *params)

        query = f"SELECT * {base_query} ORDER BY created_at DESC "
        query += f"OFFSET ${len(params) + 1} LIMIT ${len(params) + 2}"

        rows = await conn.fetch(query, *params, (page - 1) * limit, limit)
        return PaginatedUsers(
            items=[UserPublic.from_database(dict(row)) for row in rows],
            total=total,
            page=page,
            pages=(total + limit - 1) // limit
        )


async def cleanup_expired_lockouts():
    conn = await get_connection()
    async with conn.transaction():
        await conn.execute("""
                UPDATE users 
                SET lockout_until = NULL,
                    failed_login_attempts = 0
                WHERE lockout_until < NOW() AND deleted_at IS NULL
            """)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


async def authenticate_user(email: str, password: str) -> UserInDB:
    user = await get_user_by_email(email)
    if not user:
        pwd_context.dummy_verify()
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials"
        )

    if await is_account_locked(user.id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is locked"
        )

    if not verify_password(password, user.password_hash):
        await update_failed_login(user.id)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials"
        )

    await update_failed_login(user.id, reset=True)
    await update_last_login(user.id)
    return user


async def delete_user(user_id: uuid.UUID) -> None:
    conn = await get_connection()
    try:
        async with conn.transaction():
            result = await conn.execute("""
                   delete from users where id =$1
                   """, user_id)

            if result == "UPDATE 0":
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="User not found or already deleted"
                )
    finally:
        await conn.close()


async def update_user_preferences(user_id: uuid.UUID, preferences_update: UserPreferences) -> UserPublic:
    conn = await get_connection()
    async with conn.transaction():
        row = await conn.fetchrow(
            "SELECT preferences FROM users WHERE id = $1 AND deleted_at IS NULL",
            user_id
        )
        if not row:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )

        current_preferences = row['preferences'] or {}
        update_data = preferences_update.dict(exclude_unset=True)
        updated_preferences = _merge_preferences(current_preferences, update_data)

        try:
            validated_preferences = UserPreferences(**updated_preferences).dict()
        except ValueError as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=str(e)
            )

        result = await conn.fetchrow("""
               UPDATE users 
               SET preferences = $1, 
                   updated_at = NOW() 
               WHERE id = $2 AND deleted_at IS NULL
               RETURNING *
               """,
                                     json.dumps(validated_preferences),
                                     user_id
                                     )

        if not result:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found or deleted"
            )

        return UserPublic(**result)


async def update_user_role(user_id: uuid.UUID, new_role: str) -> UserPublic:
    """
    Update a user's role in the system.

    Args:
        user_id (uuid.UUID): The ID of the user to update
        new_role (str): The new role to assign to the user

    Returns:
        UserPublic: The updated user object

    Raises:
        HTTPException: If user is not found or other database errors occur
    """
    conn = await get_connection()
    async with conn.transaction():
        row = await conn.fetchrow("""
                UPDATE users 
                SET role = $1,
                    updated_at = NOW()
                WHERE id = $2 
                    AND deleted_at IS NULL
                RETURNING *
                """,
                                  new_role,  # No longer need to access .value
                                  user_id
                                  )

        if not row:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )

        return UserPublic.from_database(dict(row))


def _merge_preferences(original: Dict, updates: Dict) -> Dict:
    merged = original.copy()
    for key, value in updates.items():
        if isinstance(value, dict) and key in merged and isinstance(merged[key], dict):
            merged[key] = _merge_preferences(merged[key], value)
        else:
            merged[key] = value
    return merged
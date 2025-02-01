from fastapi import APIRouter, Depends, HTTPException, status, Body
from fastapi.security import OAuth2PasswordRequestForm
import uuid
from datetime import datetime
from jose import jwt, JWTError
from starlette.requests import Request
from pydantic import BaseModel

from server.features.users.security import (
    create_access_token, create_refresh_token,
    SECRET_KEY, ALGORITHM, verify_token_type
)
from server.database.auth_database import LoginAttempts, TokenBlacklist
from server.database.users_database import UserPublic, authenticate_user, get_user, UserStatus

router = APIRouter(prefix="/api/v1/auth", tags=["auth"])

login_attempts = LoginAttempts()
token_blacklist = TokenBlacklist()


@router.post("/token")
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
    if await login_attempts.is_locked(form_data.username):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account temporarily locked"
        )

    try:
        user = await authenticate_user(form_data.username, form_data.password)
        if not user.status == UserStatus.ACTIVE:
            raise HTTPException(status_code=403, detail="Account disabled")

        await login_attempts.reset_attempts(form_data.username)

        access_token = create_access_token(user.id)
        refresh_token, refresh_jti = create_refresh_token(user.id)

        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer",
            "user": UserPublic(**user.dict())
        }
    except HTTPException:
        is_locked = await login_attempts.record_attempt(form_data.username)
        if is_locked:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Account temporarily locked"
            )
        raise


class RefreshTokenRequest(BaseModel):
    refresh_token: str
@router.post("/refresh")
async def refresh(req : RefreshTokenRequest):
    try:
        payload = jwt.decode(req.refresh_token, SECRET_KEY, algorithms=[ALGORITHM])
        verify_token_type(payload, "refresh")

        if await token_blacklist.is_blacklisted(uuid.UUID(payload["jti"])):
            raise HTTPException(status_code=401, detail="Token has been revoked")

        exp = datetime.fromtimestamp(payload["exp"])
        if exp < datetime.utcnow():
            raise HTTPException(status_code=401, detail="Token has expired")

        user_id = uuid.UUID(payload["sub"])
        user = await get_user(user_id)

        if not user or not user.status == UserStatus.ACTIVE:
            raise HTTPException(status_code=404, detail="User not found or inactive")

        new_access_token = create_access_token(user.id)
        return {"access_token": new_access_token, "token_type": "bearer"}

    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid refresh token")


@router.post("/logout")
async def logout(req: RefreshTokenRequest):
    try:
        payload = jwt.decode(req.refresh_token, SECRET_KEY, algorithms=[ALGORITHM])
        verify_token_type(payload, "refresh")
        await token_blacklist.add_to_blacklist(
            uuid.UUID(payload["jti"]),
            uuid.UUID(payload["sub"]),
            datetime.fromtimestamp(payload["exp"])
        )
        return {"message": "Successfully logged out"}
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")

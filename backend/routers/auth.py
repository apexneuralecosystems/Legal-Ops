"""
Authentication router using Apex SaaS Framework.
Provides signup, login, token management, and password reset endpoints.

Version: Uses apex-saas-framework 0.3.24 (local module)
"""
from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel, EmailStr
from typing import Optional
from database import get_db, get_apex_client
from dependencies import get_current_user
import logging

# Import from local apex module
from apex.auth import (
    signup as apex_signup,
    login as apex_login,
    verify_token as apex_verify_token,
    refresh_token as apex_refresh_token,
    forgot_password as apex_forgot_password,
    reset_password as apex_reset_password,
    change_password as apex_change_password
)
from apex import Client as ApexClient

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/auth", tags=["Authentication"])

# Log apex module status
logger.info("Apex SaaS Framework loaded (local module v0.3.24)")


# Pydantic schemas for request/response
class SignupRequest(BaseModel):
    email: EmailStr
    password: str
    full_name: Optional[str] = None
    username: Optional[str] = None


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class RefreshRequest(BaseModel):
    refresh_token: str


class ForgotPasswordRequest(BaseModel):
    email: EmailStr


class ResetPasswordRequest(BaseModel):
    token: str
    new_password: str


class ChangePasswordRequest(BaseModel):
    current_password: str
    new_password: str


class MessageResponse(BaseModel):
    message: str


class UserResponse(BaseModel):
    id: str
    email: str
    full_name: Optional[str] = None
    username: Optional[str] = None
    is_active: bool = True


# Endpoints
@router.post("/signup", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def signup(request: SignupRequest, db: AsyncSession = Depends(get_db)):
    """
    Create a new user account.
    
    - **email**: User's email address (must be unique)
    - **password**: User's password (min 8 characters recommended)
    - **full_name**: Optional full name
    - **username**: Optional username (must be unique)
    """
    try:
        # Parse name into first_name/last_name
        first_name = ""
        last_name = ""
        
        if request.full_name:
            name_parts = request.full_name.split(' ', 1)
            first_name = name_parts[0]
            last_name = name_parts[1] if len(name_parts) > 1 else ""
        elif request.username:
            first_name = request.username
        
        # Get Apex client
        apex_client = get_apex_client()
        if not apex_client:
            raise ValueError("Apex client not initialized")
        
        user = await apex_signup(
            email=request.email,
            password=request.password,
            first_name=first_name,
            last_name=last_name,
            client=apex_client
        )
        
        return UserResponse(
            id=str(user["id"]),
            email=user["email"],
            full_name=user.get("full_name") or request.full_name or request.username,
            username=request.username,
            is_active=user.get("is_active", True)
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.post("/login", response_model=TokenResponse)
async def login(request: LoginRequest, db: AsyncSession = Depends(get_db)):
    """
    Authenticate user and get JWT tokens.
    
    - **email**: User's email address
    - **password**: User's password
    
    Returns access_token and refresh_token.
    """
    try:
        apex_client = get_apex_client()
        if not apex_client:
            raise ValueError("Apex client not initialized")
        
        tokens = await apex_login(
            email=request.email,
            password=request.password,
            client=apex_client
        )
        
        return TokenResponse(**tokens)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e),
            headers={"WWW-Authenticate": "Bearer"},
        )


@router.post("/refresh", response_model=TokenResponse)
async def refresh(request: RefreshRequest, db: AsyncSession = Depends(get_db)):
    """
    Refresh access token using refresh token.
    """
    try:
        apex_client = get_apex_client()
        if not apex_client:
            raise ValueError("Apex client not initialized")
        
        tokens = await apex_refresh_token(
            refresh_token_str=request.refresh_token,
            client=apex_client
        )
        
        return TokenResponse(**tokens)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e),
            headers={"WWW-Authenticate": "Bearer"},
        )


@router.post("/forgot-password", response_model=MessageResponse)
async def forgot_password(request: ForgotPasswordRequest, background_tasks: BackgroundTasks):
    """
    Request password reset. Sends email with reset link.
    """
    try:
        apex_client = get_apex_client()
        if not apex_client:
            raise ValueError("Apex client not initialized")
        
        result = await apex_forgot_password(
            email=request.email,
            client=apex_client
        )
        
        # Send password reset email
        if "reset_token" in result:
            from apex.email import get_email_client
            from config import settings
            
            email_client = get_email_client()
            reset_url = settings.frontend_reset_url
            
            if email_client:
                # Send email in background
                background_tasks.add_task(
                    email_client.send_password_reset_email,
                    to_email=request.email,
                    reset_token=result["reset_token"],
                    reset_url_base=reset_url
                )
                logger.info(f"Password reset email queued for {request.email}")
            else:
                # No email client - log token for development
                logger.warning(f"No email client - reset token for {request.email}: {result['reset_token'][:20]}...")
        
        return MessageResponse(
            message="If the email exists, a password reset link will be sent."
        )
    except Exception as e:
        logger.error(f"Forgot password error: {e}")
        # Don't reveal if email exists
        return MessageResponse(
            message="If the email exists, a password reset link will be sent."
        )


@router.post("/reset-password", response_model=MessageResponse)
async def reset_password(request: ResetPasswordRequest):
    """
    Reset password using reset token from email.
    """
    try:
        apex_client = get_apex_client()
        if not apex_client:
            raise ValueError("Apex client not initialized")
        
        result = await apex_reset_password(
            token=request.token,
            new_password=request.new_password,
            client=apex_client
        )
        
        return MessageResponse(message=result.get("message", "Password reset successful"))
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.post("/verify")
async def verify_token(token: str):
    """
    Verify a JWT token.
    """
    try:
        apex_client = get_apex_client()
        if not apex_client:
            raise ValueError("Apex client not initialized")
        
        payload = await apex_verify_token(token=token, client=apex_client)
        
        return {
            "valid": True,
            "user_id": payload.get("user_id"),
            "email": payload.get("email")
        }
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e)
        )


@router.get("/me")
async def get_current_user_info(
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    Get current user information.
    Requires Authorization header with Bearer token.
    
    Returns user profile based on the JWT token.
    """
    from apex.models import User
    from sqlalchemy import select
    
    # Get user from database using user_id from token
    user_id = current_user.get("user_id")
    
    apex_client = get_apex_client()
    if apex_client:
        async with apex_client.async_session() as session:
            result = await session.execute(
                select(User).where(User.id == user_id)
            )
            user = result.scalar_one_or_none()
            
            if user:
                return {
                    "id": user.id,
                    "email": user.email,
                    "full_name": user.full_name,
                    "username": user.username,
                    "is_active": user.is_active,
                    "is_superuser": user.is_superuser
                }
    
    # Fallback to token data if user not found in DB
    return {
        "id": current_user.get("user_id"),
        "email": current_user.get("email"),
        "full_name": None,
        "username": None,
        "is_active": True,
        "is_superuser": False
    }

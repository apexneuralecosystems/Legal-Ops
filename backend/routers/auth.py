"""
Authentication router using Apex SaaS Framework.
Provides signup, login, token management, and password reset endpoints.
"""
from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel, EmailStr
from typing import Optional
from database import get_db
import logging

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/auth", tags=["Authentication"])


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


# Try to import Apex auth functions
try:
    from apex.auth import (
        signup as apex_signup,
        login as apex_login,
        verify_token as apex_verify_token,
        refresh_token as apex_refresh_token,
        forgot_password as apex_forgot_password,
        reset_password as apex_reset_password,
        change_password as apex_change_password
    )
    APEX_AVAILABLE = True
except ImportError:
    APEX_AVAILABLE = False
    logger.warning("Apex not installed, using fallback authentication")


# Fallback authentication functions
async def fallback_signup(email: str, password: str, full_name: str, username: str, db: AsyncSession):
    """Fallback signup when Apex not available."""
    from passlib.context import CryptContext
    from models.auth import User
    from sqlalchemy import select
    import uuid
    
    pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto", bcrypt__rounds=12)
    
    # Check if user exists
    result = await db.execute(select(User).where(User.email == email))
    if result.scalar_one_or_none():
        raise ValueError("Email already registered")
    
    if username:
        result = await db.execute(select(User).where(User.username == username))
        if result.scalar_one_or_none():
            raise ValueError("Username already taken")
    
    # Truncate password to 72 bytes for bcrypt compatibility
    password_bytes = password.encode('utf-8')[:72]
    password_truncated = password_bytes.decode('utf-8', errors='ignore')
    
    # Create user
    user = User(
        id=str(uuid.uuid4()),
        email=email,
        password_hash=pwd_context.hash(password_truncated),
        full_name=full_name,
        username=username,
        is_active=True,
        is_superuser=False
    )
    
    db.add(user)
    await db.flush()
    
    return user


async def fallback_login(email: str, password: str, db: AsyncSession):
    """Fallback login when Apex not available."""
    from passlib.context import CryptContext
    from jose import jwt
    from datetime import datetime, timedelta
    from models.auth import User
    from sqlalchemy import select
    from config import settings
    
    pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto", bcrypt__rounds=12)
    
    # Get user
    result = await db.execute(select(User).where(User.email == email))
    user = result.scalar_one_or_none()
    
    # Truncate password for bcrypt compatibility
    password_bytes = password.encode('utf-8')[:72]
    password_truncated = password_bytes.decode('utf-8', errors='ignore')
    
    if not user or not pwd_context.verify(password_truncated, user.password_hash):
        raise ValueError("Invalid email or password")
    
    if not user.is_active:
        raise ValueError("User account is disabled")
    
    # Create tokens
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    refresh_token_expires = timedelta(days=7)
    
    access_token = jwt.encode(
        {
            "sub": user.id,
            "email": user.email,
            "exp": datetime.utcnow() + access_token_expires
        },
        settings.SECRET_KEY,
        algorithm=settings.ALGORITHM
    )
    
    refresh_token = jwt.encode(
        {
            "sub": user.id,
            "type": "refresh",
            "exp": datetime.utcnow() + refresh_token_expires
        },
        settings.SECRET_KEY,
        algorithm=settings.ALGORITHM
    )
    
    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer"
    }


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
        if APEX_AVAILABLE:
            user = await apex_signup(
                email=request.email,
                password=request.password,
                full_name=request.full_name,
                username=request.username,
                db=db
            )
        else:
            user = await fallback_signup(
                email=request.email,
                password=request.password,
                full_name=request.full_name,
                username=request.username,
                db=db
            )
        
        return UserResponse(
            id=str(user.id),
            email=user.email,
            full_name=user.full_name,
            username=user.username,
            is_active=user.is_active
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
        if APEX_AVAILABLE:
            tokens = await apex_login(
                email=request.email,
                password=request.password,
                db=db
            )
        else:
            tokens = await fallback_login(
                email=request.email,
                password=request.password,
                db=db
            )
        
        return TokenResponse(**tokens)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e),
            headers={"WWW-Authenticate": "Bearer"}
        )


@router.post("/verify", response_model=MessageResponse)
async def verify_token(token: str, db: AsyncSession = Depends(get_db)):
    """
    Verify if a JWT token is valid.
    
    - **token**: JWT access token to verify
    """
    try:
        if APEX_AVAILABLE:
            apex_verify_token(token=token, db=db)
        else:
            from jose import jwt, JWTError
            from config import settings
            jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        
        return MessageResponse(message="Token is valid")
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"}
        )


@router.post("/refresh", response_model=TokenResponse)
async def refresh_access_token(request: RefreshRequest, db: AsyncSession = Depends(get_db)):
    """
    Get new access token using refresh token.
    
    - **refresh_token**: Valid refresh token
    """
    try:
        if APEX_AVAILABLE:
            tokens = await apex_refresh_token(token=request.refresh_token, db=db)
        else:
            from jose import jwt, JWTError
            from datetime import datetime, timedelta
            from config import settings
            
            payload = jwt.decode(request.refresh_token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
            
            if payload.get("type") != "refresh":
                raise ValueError("Invalid token type")
            
            new_access_token = jwt.encode(
                {
                    "sub": payload.get("sub"),
                    "email": payload.get("email", ""),
                    "exp": datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
                },
                settings.SECRET_KEY,
                algorithm=settings.ALGORITHM
            )
            
            tokens = {
                "access_token": new_access_token,
                "refresh_token": request.refresh_token,
                "token_type": "bearer"
            }
        
        return TokenResponse(**tokens)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired refresh token",
            headers={"WWW-Authenticate": "Bearer"}
        )


@router.post("/forgot-password", response_model=MessageResponse)
async def forgot_password(
    request: ForgotPasswordRequest,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db)
):
    """
    Request password reset email.
    
    - **email**: Email address associated with account
    
    Note: Always returns success to prevent email enumeration.
    """
    try:
        if APEX_AVAILABLE:
            await apex_forgot_password(email=request.email, db=db)
        else:
            # Fallback: just log the request
            logger.info(f"Password reset requested for: {request.email}")
    except Exception:
        pass  # Don't reveal if email exists
    
    return MessageResponse(message="If the email exists, a reset link has been sent")


@router.post("/reset-password", response_model=MessageResponse)
async def reset_password(request: ResetPasswordRequest, db: AsyncSession = Depends(get_db)):
    """
    Reset password using token from email.
    
    - **token**: Password reset token from email
    - **new_password**: New password to set
    """
    try:
        if APEX_AVAILABLE:
            await apex_reset_password(token=request.token, new_password=request.new_password, db=db)
        else:
            raise HTTPException(
                status_code=status.HTTP_501_NOT_IMPLEMENTED,
                detail="Password reset requires Apex framework"
            )
        
        return MessageResponse(message="Password reset successfully")
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.post("/change-password", response_model=MessageResponse)
async def change_password(
    request: ChangePasswordRequest,
    db: AsyncSession = Depends(get_db),
):
    """
    Change password for authenticated user.
    
    - **current_password**: Current password
    - **new_password**: New password to set
    
    Requires authentication.
    """
    from dependencies import get_current_user
    from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
    
    # This endpoint needs the token from header
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="Use authenticated endpoint with Bearer token"
    )


@router.get("/me", response_model=UserResponse)
async def get_current_user_info(db: AsyncSession = Depends(get_db)):
    """
    Get current authenticated user's information.
    
    Requires authentication via Bearer token.
    """
    from dependencies import get_current_user
    from models.auth import User
    from sqlalchemy import select
    from fastapi.security import HTTPBearer
    
    # For now, this requires the dependency to be injected
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="Use /api/auth/me with Bearer token header"
    )

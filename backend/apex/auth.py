"""
Apex Auth Module - Authentication and token management.
"""
from typing import Optional, Dict, Any, Tuple
from datetime import datetime, timedelta
from jose import JWTError, jwt
from passlib.context import CryptContext
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from apex.client import Client, get_default_client
from apex.models import User
import uuid
import logging

logger = logging.getLogger(__name__)

# Password hashing context
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto", bcrypt__rounds=12)


def _get_client() -> Client:
    """Get the Apex client, raising error if not initialized."""
    client = get_default_client()
    if not client:
        raise RuntimeError("Apex client not initialized. Call Client() first.")
    return client


def hash_password(password: str) -> str:
    """Hash a password using bcrypt."""
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against its hash."""
    return pwd_context.verify(plain_password, hashed_password)


def create_access_token(
    data: Dict[str, Any],
    client: Optional[Client] = None,
    expires_delta: Optional[timedelta] = None
) -> str:
    """Create a JWT access token."""
    client = client or _get_client()
    
    to_encode = data.copy()
    expire = datetime.utcnow() + (
        expires_delta or timedelta(minutes=client.access_token_expire_minutes)
    )
    to_encode.update({"exp": expire, "type": "access"})
    
    return jwt.encode(to_encode, client.secret_key, algorithm=client.algorithm)


def create_refresh_token(
    data: Dict[str, Any],
    client: Optional[Client] = None,
    expires_delta: Optional[timedelta] = None
) -> str:
    """Create a JWT refresh token."""
    client = client or _get_client()
    
    to_encode = data.copy()
    expire = datetime.utcnow() + (
        expires_delta or timedelta(days=client.refresh_token_expire_days)
    )
    to_encode.update({"exp": expire, "type": "refresh"})
    
    return jwt.encode(to_encode, client.secret_key, algorithm=client.algorithm)


async def signup(
    email: str,
    password: str,
    first_name: str = "",
    last_name: str = "",
    client: Optional[Client] = None
) -> Dict[str, Any]:
    """
    Register a new user.
    
    Returns:
        Dict with user info (id, email, full_name, is_active)
    """
    client = client or _get_client()
    
    # Combine first_name and last_name into full_name
    full_name = f"{first_name} {last_name}".strip()
    
    async with client.async_session() as session:
        # Check if user exists
        result = await session.execute(
            select(User).where(User.email == email)
        )
        existing = result.scalar_one_or_none()
        
        if existing:
            raise ValueError("User with this email already exists")
        
        # Create new user
        user = User(
            id=str(uuid.uuid4()),
            email=email,
            password_hash=hash_password(password),
            full_name=full_name,
            is_active=True,
            created_at=datetime.utcnow()
        )
        
        session.add(user)
        await session.commit()
        await session.refresh(user)
        
        logger.info(f"New user registered: {email}")
        
        return {
            "id": user.id,
            "email": user.email,
            "full_name": user.full_name,
            "is_active": user.is_active
        }


async def login(
    email: str,
    password: str,
    client: Optional[Client] = None
) -> Dict[str, str]:
    """
    Authenticate user and return tokens.
    
    Returns:
        Dict with access_token, refresh_token, token_type
    """
    client = client or _get_client()
    
    async with client.async_session() as session:
        result = await session.execute(
            select(User).where(User.email == email)
        )
        user = result.scalar_one_or_none()
        
        if not user or not verify_password(password, user.password_hash):
            raise ValueError("Invalid email or password")
        
        if not user.is_active:
            raise ValueError("User account is disabled")
        
        # Update updated_at
        user.updated_at = datetime.utcnow()
        await session.commit()
        
        # Create tokens
        token_data = {"sub": user.id, "email": user.email}
        access_token = create_access_token(token_data, client)
        refresh_token = create_refresh_token(token_data, client)
        
        logger.info(f"User logged in: {email}")
        
        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer"
        }


async def verify_token(
    token: str,
    client: Optional[Client] = None
) -> Dict[str, Any]:
    """
    Verify a JWT token and return the payload.
    
    Returns:
        Dict with user_id, email, and token metadata
    """
    client = client or _get_client()
    
    try:
        payload = jwt.decode(
            token,
            client.secret_key,
            algorithms=[client.algorithm]
        )
        
        user_id = payload.get("sub")
        email = payload.get("email")
        token_type = payload.get("type", "access")
        
        if not user_id:
            raise ValueError("Invalid token: missing user ID")
        
        return {
            "user_id": user_id,
            "email": email,
            "token_type": token_type,
            "exp": payload.get("exp")
        }
        
    except JWTError as e:
        raise ValueError(f"Invalid token: {str(e)}")


async def refresh_token(
    refresh_token_str: str,
    client: Optional[Client] = None
) -> Dict[str, str]:
    """
    Refresh an access token using a refresh token.
    
    Returns:
        Dict with new access_token, refresh_token, token_type
    """
    client = client or _get_client()
    
    # Verify the refresh token
    payload = await verify_token(refresh_token_str, client)
    
    if payload.get("token_type") != "refresh":
        raise ValueError("Invalid token type: expected refresh token")
    
    # Create new tokens
    token_data = {"sub": payload["user_id"], "email": payload["email"]}
    new_access = create_access_token(token_data, client)
    new_refresh = create_refresh_token(token_data, client)
    
    return {
        "access_token": new_access,
        "refresh_token": new_refresh,
        "token_type": "bearer"
    }


async def forgot_password(
    email: str,
    client: Optional[Client] = None
) -> Dict[str, str]:
    """
    Initiate password reset flow.
    
    Returns:
        Dict with reset_token and message
    """
    client = client or _get_client()
    
    async with client.async_session() as session:
        result = await session.execute(
            select(User).where(User.email == email)
        )
        user = result.scalar_one_or_none()
        
        if not user:
            # Don't reveal if user exists
            return {"message": "If the email exists, a reset link will be sent"}
        
        # Create reset token (expires in 1 hour)
        reset_data = {"sub": user.id, "email": email, "purpose": "password_reset"}
        reset_token = jwt.encode(
            {**reset_data, "exp": datetime.utcnow() + timedelta(hours=1)},
            client.secret_key,
            algorithm=client.algorithm
        )
        
        logger.info(f"Password reset requested for: {email}")
        
        return {
            "reset_token": reset_token,
            "message": "Password reset token generated"
        }


async def reset_password(
    token: str,
    new_password: str,
    client: Optional[Client] = None
) -> Dict[str, str]:
    """
    Reset password using reset token.
    
    Returns:
        Dict with success message
    """
    client = client or _get_client()
    
    try:
        payload = jwt.decode(token, client.secret_key, algorithms=[client.algorithm])
        
        if payload.get("purpose") != "password_reset":
            raise ValueError("Invalid reset token")
        
        user_id = payload.get("sub")
        
        async with client.async_session() as session:
            result = await session.execute(
                select(User).where(User.id == user_id)
            )
            user = result.scalar_one_or_none()
            
            if not user:
                raise ValueError("User not found")
            
            user.password_hash = hash_password(new_password)
            await session.commit()
            
            logger.info(f"Password reset completed for user: {user_id}")
            
            return {"message": "Password reset successful"}
            
    except JWTError:
        raise ValueError("Invalid or expired reset token")


async def change_password(
    user_id: str,
    current_password: str,
    new_password: str,
    client: Optional[Client] = None
) -> Dict[str, str]:
    """
    Change password for authenticated user.
    
    Returns:
        Dict with success message
    """
    client = client or _get_client()
    
    async with client.async_session() as session:
        result = await session.execute(
            select(User).where(User.id == user_id)
        )
        user = result.scalar_one_or_none()
        
        if not user:
            raise ValueError("User not found")
        
        if not verify_password(current_password, user.password_hash):
            raise ValueError("Current password is incorrect")
        
        user.password_hash = hash_password(new_password)
        await session.commit()
        
        logger.info(f"Password changed for user: {user_id}")
        
        return {"message": "Password changed successfully"}

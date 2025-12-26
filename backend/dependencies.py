"""
Authentication dependencies for protected routes.
"""
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession
from database import get_db, get_apex_client
from typing import Dict, Any

security = HTTPBearer()


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncSession = Depends(get_db)
) -> Dict[str, Any]:
    """
    Dependency to get the current authenticated user from JWT token.
    
    Args:
        credentials: HTTP Bearer token from Authorization header
        db: Database session
        
    Returns:
        Dict with user_id and email
        
    Raises:
        HTTPException: 401 if token is invalid or expired
    """
    try:
        from apex.auth import verify_token
        
        token = credentials.credentials
        
        # Get Apex client
        apex_client = get_apex_client()
        
        # Apex verify_token requires client if not default
        if apex_client:
            payload = await verify_token(token=token, client=apex_client)
        else:
            payload = await verify_token(token=token)
        
        return {
            "user_id": payload.get('user_id') or payload.get('sub'),  # apex returns user_id, fallback to sub
            "email": payload.get('email')
        }
    except ImportError:
        # Apex not installed - use fallback JWT verification
        from jose import JWTError, jwt
        from config import settings
        
        token = credentials.credentials
        
        try:
            payload = jwt.decode(
                token,
                settings.SECRET_KEY,
                algorithms=[settings.ALGORITHM]
            )
            user_id = payload.get("sub")
            email = payload.get("email")
            
            if user_id is None:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid authentication credentials",
                    headers={"WWW-Authenticate": "Bearer"},
                )
            
            return {"user_id": user_id, "email": email}
            
        except JWTError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authentication credentials",
                headers={"WWW-Authenticate": "Bearer"},
            )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e),
            headers={"WWW-Authenticate": "Bearer"},
        )


async def get_current_active_user(
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> Dict[str, Any]:
    """
    Dependency to get current user and verify they are active.
    
    Args:
        current_user: Current user from token
        db: Database session
        
    Returns:
        Dict with user info
        
    Raises:
        HTTPException: 403 if user is disabled
    """
    # Could add is_active check here by querying database
    return current_user


async def get_current_superuser(
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> Dict[str, Any]:
    """
    Dependency to verify current user is a superuser.
    
    Args:
        current_user: Current user from token
        db: Database session
        
    Returns:
        Dict with user info
        
    Raises:
        HTTPException: 403 if not superuser
    """
    from sqlalchemy import select
    from models.auth import User
    
    result = await db.execute(
        select(User).where(User.id == current_user["user_id"])
    )
    user = result.scalar_one_or_none()
    
    if not user or not user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Superuser privileges required"
        )
    
    return current_user

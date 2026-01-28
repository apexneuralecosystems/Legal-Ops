"""
FastAPI dependencies for authentication.
Wrapper around Apex authentication.
"""

from typing import Any, Dict
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession
from database import get_db, get_apex_client
import logging

logger = logging.getLogger(__name__)

# HTTP Bearer scheme for token extraction
oauth2_scheme = HTTPBearer()


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(oauth2_scheme),
) -> Dict[str, Any]:
    """
    Dependency to get current authenticated user from JWT token.
    
    Returns:
        User payload with user_id and email
    
    Raises:
        HTTPException: If token is invalid
    """
    from apex.auth import verify_token as apex_verify_token
    
    token = credentials.credentials
    
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        apex_client = get_apex_client()
        if not apex_client:
            raise credentials_exception
        
        # Verify token using apex
        payload = await apex_verify_token(token=token, client=apex_client)
        
        user_id = payload.get("user_id") or payload.get("sub")
        if user_id is None:
            raise credentials_exception
        
        return {
            "user_id": user_id,
            "email": payload.get("email"),
            "is_active": payload.get("is_active", True),
            "is_superuser": payload.get("is_superuser", False),
        }

    except Exception as e:
        logger.warning(f"Token validation failed: {e}")
        raise credentials_exception


async def get_current_superuser(
    current_user: Dict[str, Any] = Depends(get_current_user),
) -> Dict[str, Any]:
    """
    Dependency to ensure current user is a superuser.
    
    Returns:
        Current user payload if superuser
    
    Raises:
        HTTPException: If user is not a superuser
    """
    is_superuser = current_user.get("is_superuser", False)
    if not is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Superuser access required",
        )
    return current_user


# Synchronous version for routers that don't use async
def get_current_user_sync(
    credentials: HTTPAuthorizationCredentials = Depends(oauth2_scheme),
) -> Dict[str, Any]:
    """
    Synchronous dependency to get current user from JWT token.
    For use in non-async endpoints.
    """
    import asyncio
    
    async def _verify():
        from apex.auth import verify_token as apex_verify_token
        
        token = credentials.credentials
        apex_client = get_apex_client()
        
        if not apex_client:
            return None
        
        try:
            payload = await apex_verify_token(token=token, client=apex_client)
            user_id = payload.get("user_id") or payload.get("sub")
            return {
                "user_id": user_id,
                "email": payload.get("email"),
                "is_active": payload.get("is_active", True),
                "is_superuser": payload.get("is_superuser", False),
            }
        except Exception:
            return None
    
    # Try to get existing event loop or create new one
    try:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            # We're in an async context, use run_coroutine_threadsafe or nest
            import concurrent.futures
            with concurrent.futures.ThreadPoolExecutor() as pool:
                result = pool.submit(asyncio.run, _verify()).result()
        else:
            result = loop.run_until_complete(_verify())
    except RuntimeError:
        result = asyncio.run(_verify())
    
    if not result:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    return result

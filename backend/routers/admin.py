"""
Admin API router - User management and statistics.
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from pydantic import BaseModel, EmailStr
from typing import List, Optional
from database import get_db
from models.auth import User
from dependencies import get_current_superuser
import logging

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/admin", tags=["Admin"])


class UserResponse(BaseModel):
    id: str
    email: str
    full_name: Optional[str] = None
    username: Optional[str] = None
    is_active: bool
    is_superuser: bool


class CreateUserRequest(BaseModel):
    email: EmailStr
    password: str
    full_name: Optional[str] = None
    username: Optional[str] = None
    is_superuser: bool = False


class PaginatedUsersResponse(BaseModel):
    users: List[UserResponse]
    total: int
    page: int
    per_page: int


@router.get("/users", response_model=PaginatedUsersResponse)
async def list_users(
    page: int = 1,
    per_page: int = 20,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_superuser)
):
    """
    List all users (admin only).
    """
    offset = (page - 1) * per_page
    
    # Get total count
    count_result = await db.execute(select(func.count(User.id)))
    total = count_result.scalar() or 0
    
    # Get paginated users
    result = await db.execute(
        select(User)
        .offset(offset)
        .limit(per_page)
        .order_by(User.created_at.desc())
    )
    users = result.scalars().all()
    
    return PaginatedUsersResponse(
        users=[
            UserResponse(
                id=str(user.id),
                email=user.email,
                full_name=user.full_name,
                username=user.username,
                is_active=user.is_active,
                is_superuser=user.is_superuser
            ) for user in users
        ],
        total=total,
        page=page,
        per_page=per_page
    )


@router.post("/users", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def create_admin_user(
    request: CreateUserRequest,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_superuser)
):
    """
    Create a new user (admin only).
    """
    from passlib.context import CryptContext
    import uuid
    
    pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
    
    # Check if user exists
    result = await db.execute(select(User).where(User.email == request.email))
    if result.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Email already registered")
    
    # Create user
    user = User(
        id=str(uuid.uuid4()),
        email=request.email,
        password_hash=pwd_context.hash(request.password),
        full_name=request.full_name,
        username=request.username,
        is_active=True,
        is_superuser=request.is_superuser
    )
    
    db.add(user)
    await db.flush()
    
    return UserResponse(
        id=str(user.id),
        email=user.email,
        full_name=user.full_name,
        username=user.username,
        is_active=user.is_active,
        is_superuser=user.is_superuser
    )


@router.get("/statistics", response_model=dict)
async def get_statistics(
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_superuser)
):
    """
    Get user statistics (admin only).
    """
    # Total users
    total_result = await db.execute(select(func.count(User.id)))
    total_users = total_result.scalar() or 0
    
    # Active users
    active_result = await db.execute(
        select(func.count(User.id)).where(User.is_active == True)
    )
    active_users = active_result.scalar() or 0
    
    # Superusers
    super_result = await db.execute(
        select(func.count(User.id)).where(User.is_superuser == True)
    )
    superusers = super_result.scalar() or 0
    
    return {
        "total_users": total_users,
        "active_users": active_users,
        "inactive_users": total_users - active_users,
        "superusers": superusers
    }

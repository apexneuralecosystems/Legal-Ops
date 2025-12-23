"""
User model using Apex SaaS Framework.
"""
from sqlalchemy import Column, String, Boolean

try:
    from apex import quick_user
    
    # Create User model using Apex's quick_user helper
    # Built-in fields: id (UUID), email, password_hash, created_at, updated_at, deleted_at
    User = quick_user(
        full_name=Column(String(255), nullable=True),
        username=Column(String(100), unique=True, index=True, nullable=True),
        is_active=Column(Boolean, default=True, nullable=False),
        is_superuser=Column(Boolean, default=False, nullable=False),
    )
except ImportError:
    # Fallback User model if apex not installed
    from database import Base
    from sqlalchemy import Column, String, Boolean, DateTime
    from datetime import datetime
    import uuid
    
    class User(Base):
        """Fallback User model mimicking Apex structure."""
        __tablename__ = "users"
        
        id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
        email = Column(String(255), unique=True, index=True, nullable=False)
        password_hash = Column(String(255), nullable=False)
        full_name = Column(String(255), nullable=True)
        username = Column(String(100), unique=True, index=True, nullable=True)
        is_active = Column(Boolean, default=True, nullable=False)
        is_superuser = Column(Boolean, default=False, nullable=False)
        created_at = Column(DateTime, default=datetime.utcnow)
        updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
        deleted_at = Column(DateTime, nullable=True)

__all__ = ["User"]

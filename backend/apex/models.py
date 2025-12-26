"""
Apex Models - Base models for database entities.
"""
from sqlalchemy import Column, String, Boolean, DateTime, Text, ForeignKey
from sqlalchemy.orm import declarative_base, relationship
from datetime import datetime
from typing import Optional, Dict, Any
import uuid

# SQLAlchemy declarative base
Base = declarative_base()


class User(Base):
    """User model for authentication - matches existing database schema."""
    
    __tablename__ = "users"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    email = Column(String(255), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)  # Matches existing column
    full_name = Column(String(255), default="")  # Matches existing column
    username = Column(String(100), unique=True, nullable=True)
    is_active = Column(Boolean, default=True)
    is_superuser = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    deleted_at = Column(DateTime, nullable=True)
    
    # Relationships
    subscriptions = relationship("Subscription", back_populates="user", lazy="dynamic")
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "id": self.id,
            "email": self.email,
            "full_name": self.full_name,
            "username": self.username,
            "is_active": self.is_active,
            "created_at": self.created_at.isoformat() if self.created_at else None
        }


class Subscription(Base):
    """Subscription model for payment tracking."""
    
    __tablename__ = "subscriptions"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String(36), ForeignKey("users.id"), nullable=False)
    plan_id = Column(String(100), nullable=False)
    status = Column(String(50), default="active")  # active, cancelled, expired
    payment_provider = Column(String(50), default="paypal")  # paypal, stripe
    external_subscription_id = Column(String(255), nullable=True)
    amount = Column(String(20), nullable=True)
    currency = Column(String(10), default="USD")
    created_at = Column(DateTime, default=datetime.utcnow)
    expires_at = Column(DateTime, nullable=True)
    cancelled_at = Column(DateTime, nullable=True)
    
    # Relationships
    user = relationship("User", back_populates="subscriptions")
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "id": self.id,
            "user_id": self.user_id,
            "plan_id": self.plan_id,
            "status": self.status,
            "payment_provider": self.payment_provider,
            "amount": self.amount,
            "currency": self.currency,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "expires_at": self.expires_at.isoformat() if self.expires_at else None
        }


class PaymentOrder(Base):
    """Payment order tracking."""
    
    __tablename__ = "payment_orders"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String(36), ForeignKey("users.id"), nullable=False)
    external_order_id = Column(String(255), nullable=True)  # PayPal order ID
    amount = Column(String(20), nullable=False)
    currency = Column(String(10), default="USD")
    status = Column(String(50), default="pending")  # pending, approved, completed, failed
    payment_provider = Column(String(50), default="paypal")
    description = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "id": self.id,
            "user_id": self.user_id,
            "external_order_id": self.external_order_id,
            "amount": self.amount,
            "currency": self.currency,
            "status": self.status,
            "created_at": self.created_at.isoformat() if self.created_at else None
        }


def quick_user(
    email: str,
    password: str = None,
    first_name: str = "",
    last_name: str = ""
) -> User:
    """
    Quick helper to create a User object.
    Note: This creates an in-memory object, not saved to DB.
    """
    from apex.auth import hash_password
    
    return User(
        id=str(uuid.uuid4()),
        email=email,
        hashed_password=hash_password(password) if password else "",
        first_name=first_name,
        last_name=last_name,
        is_active=True
    )

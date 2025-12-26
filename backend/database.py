"""
Database connection management with Apex SaaS Framework.
Uses async SQLAlchemy with Apex Base for all models.
"""
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from typing import AsyncGenerator
from config import settings
import logging

# Import Apex Base for all models (avoid importing apex Settings to prevent conflict)
try:
    # Import only Base, not the whole apex package which loads Settings
    from apex.domain.models.base import Base as ApexBase
    Base = ApexBase
    logging.info("Using Apex Base for models")
except ImportError:
    try:
        # Fallback: try getting Base from apex directly
        from apex import Base
        logging.info("Using Apex Base (direct import)")
    except (ImportError, Exception):
        # Final fallback if apex not installed or has issues
        from sqlalchemy.orm import declarative_base
        Base = declarative_base()
        logging.warning("Apex not available, using standard SQLAlchemy Base")

logger = logging.getLogger(__name__)

# Convert sync database URL to async
def get_async_db_url(sync_url: str) -> str:
    """Convert sync database URL to async format."""
    if sync_url.startswith("postgresql://"):
        return sync_url.replace("postgresql://", "postgresql+asyncpg://", 1)
    elif sync_url.startswith("sqlite:///"):
        return sync_url.replace("sqlite:///", "sqlite+aiosqlite:///", 1)
    return sync_url

# Create async database engine
async_db_url = get_async_db_url(settings.DATABASE_URL)

engine = create_async_engine(
    async_db_url,
    echo=settings.LOG_LEVEL == "DEBUG",
    future=True,
    pool_pre_ping=True,
)

# Async session factory
AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    Async dependency for FastAPI routes to get database session.
    
    Yields:
        AsyncSession: Async SQLAlchemy database session
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


async def init_db():
    """
    Initialize database by creating all tables.
    Called on application startup.
    """
    async with engine.begin() as conn:
        # Import all models to register them with Base
        from models import matter, document, segment, pleading, research, audit
        try:
            from models import auth, usage
        except ImportError:
            pass
        
        await conn.run_sync(Base.metadata.create_all)
        logger.info("Database tables created successfully")


# Keep sync versions for backward compatibility during migration
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session

sync_engine = create_engine(
    settings.DATABASE_URL,
    pool_pre_ping=True,
    pool_size=10,
    max_overflow=20,
    echo=settings.LOG_LEVEL == "DEBUG"
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=sync_engine)


def get_sync_db():
    """
    Sync dependency for routes not yet migrated to async.
    
    Yields:
        Session: SQLAlchemy database session
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()



# Global Apex client instance
_apex_client = None


def set_apex_client(client):
    """Set the global Apex client instance."""
    global _apex_client
    _apex_client = client
    logger.info("Global Apex client set")


def get_apex_client():
    """
    Get Apex client - try global instance first, fallback to creating new one.
    Centralized helper for use in routers and dependencies.
    """
    global _apex_client
    if _apex_client:
        return _apex_client
        
    try:
        from apex import Client as ApexClient
            
        # Fallback: create client inline
        # This is expensive so we should rely on set_apex_client being called in main.py
        from models.auth import User
        from config import settings
        
        # Check if settings has DATABASE_URL
        db_url = getattr(settings, "DATABASE_URL", None)
        if not db_url:
            return None
            
        # Convert to async URL
        async_db_url = get_async_db_url(db_url)
            
        client = ApexClient(
            database_url=async_db_url,
            user_model=User,
            async_mode=True
        )
        return client
    except Exception as e:
        logger.warning(f"Could not get/create Apex client: {e}")
        return None

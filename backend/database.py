"""
Database connection management with Apex SaaS Framework.
Uses async SQLAlchemy with Apex Base for all models.
"""
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from typing import AsyncGenerator
from config import settings
import logging

# Import Apex Base for all models
try:
    from apex import Base
except ImportError:
    # Fallback if apex not installed yet
    from sqlalchemy.orm import declarative_base
    Base = declarative_base()
    logging.warning("Apex not installed, using standard SQLAlchemy Base")

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
            from models import auth
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

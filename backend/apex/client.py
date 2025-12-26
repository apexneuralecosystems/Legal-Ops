"""
Apex Client - Central configuration and database management.
"""
from typing import Optional, Dict, Any
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine
import logging

logger = logging.getLogger(__name__)


class Client:
    """
    Apex SaaS Framework Client.
    
    Manages database connections, configuration, and provides
    access to auth and payment services.
    
    Usage:
        client = Client(
            database_url="postgresql+asyncpg://...",
            secret_key="your-secret-key",
            async_mode=True
        )
    """
    
    _instance: Optional["Client"] = None
    
    def __init__(
        self,
        database_url: str,
        secret_key: str,
        async_mode: bool = True,
        algorithm: str = "HS256",
        access_token_expire_minutes: int = 30,
        refresh_token_expire_days: int = 7,
        **kwargs
    ):
        self.database_url = database_url
        self.secret_key = secret_key
        self.algorithm = algorithm
        self.async_mode = async_mode
        self.access_token_expire_minutes = access_token_expire_minutes
        self.refresh_token_expire_days = refresh_token_expire_days
        self.extra_config = kwargs
        
        # Initialize database engine
        if async_mode:
            self._init_async_db()
        else:
            self._init_sync_db()
        
        # Store as singleton
        Client._instance = self
        logger.info(f"Apex Client initialized (async_mode={async_mode})")
    
    def _init_async_db(self):
        """Initialize async database engine."""
        self.engine = create_async_engine(
            self.database_url,
            echo=False,
            pool_pre_ping=True
        )
        self.async_session = async_sessionmaker(
            self.engine,
            class_=AsyncSession,
            expire_on_commit=False
        )
    
    def _init_sync_db(self):
        """Initialize sync database engine."""
        # Convert async URL to sync if needed
        sync_url = self.database_url.replace("+asyncpg", "").replace("+aiosqlite", "")
        self.engine = create_engine(sync_url, echo=False, pool_pre_ping=True)
        self.Session = sessionmaker(bind=self.engine)
    
    async def get_session(self) -> AsyncSession:
        """Get async database session."""
        if not self.async_mode:
            raise RuntimeError("Client not in async mode")
        return self.async_session()
    
    def get_sync_session(self):
        """Get sync database session."""
        if self.async_mode:
            raise RuntimeError("Client in async mode, use get_session()")
        return self.Session()
    
    @classmethod
    def get_instance(cls) -> Optional["Client"]:
        """Get the singleton client instance."""
        return cls._instance
    
    @classmethod
    def set_as_default(cls, client: "Client"):
        """Set a client as the default instance."""
        cls._instance = client
    
    def to_dict(self) -> Dict[str, Any]:
        """Return client configuration as dict."""
        return {
            "database_url": self.database_url[:50] + "...",  # Truncate for security
            "async_mode": self.async_mode,
            "algorithm": self.algorithm,
            "access_token_expire_minutes": self.access_token_expire_minutes,
            "refresh_token_expire_days": self.refresh_token_expire_days
        }


def get_default_client() -> Optional[Client]:
    """Get the default Apex client instance."""
    return Client.get_instance()

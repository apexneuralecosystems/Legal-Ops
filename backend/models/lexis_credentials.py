"""
Lexis cookie credentials storage model.
"""
from sqlalchemy import Column, String, Text, DateTime, ForeignKey, text
from sqlalchemy.dialects.postgresql import UUID
from database import Base
from datetime import datetime
from typing import Optional, List
import json
import logging

logger = logging.getLogger(__name__)


class LexisCredentials(Base):
    """
    Stores encrypted Lexis Advance cookies per user.
    Separate table to avoid conflicts with Apex User model.
    """
    __tablename__ = "lexis_credentials"
    
    id = Column(UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()"))
    user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, unique=True)
    auth_method = Column(String, default="um_library")  # "um_library" | "cookies"
    cookies_encrypted = Column(Text, nullable=True)  # Encrypted JSON
    cookies_expires_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def set_cookies(self, cookies: List[dict], expiry: datetime):
        """Encrypt and store Lexis cookies"""
        try:
            from config import settings
            from cryptography.fernet import Fernet
            
            # Get or generate Fernet key
            if hasattr(settings, 'FERNET_KEY') and settings.FERNET_KEY:
                cipher = Fernet(settings.FERNET_KEY.encode() if isinstance(settings.FERNET_KEY, str) else settings.FERNET_KEY)
            else:
                # Generate a key for this session (not recommended for production)
                logger.warning("FERNET_KEY not set, generating temporary key")
                key = Fernet.generate_key()
                cipher = Fernet(key)
            
            cookies_json = json.dumps(cookies)
            encrypted = cipher.encrypt(cookies_json.encode())
            self.cookies_encrypted = encrypted.decode()
            self.cookies_expires_at = expiry
            self.auth_method = "cookies"
            self.updated_at = datetime.utcnow()
            logger.info(f"✅ Encrypted and saved {len(cookies)} cookies for user {self.user_id}")
        except Exception as e:
            logger.error(f"Failed to encrypt cookies: {e}")
            raise
    
    def get_cookies(self) -> Optional[List[dict]]:
        """Decrypt and return Lexis cookies if valid"""
        if not self.cookies_encrypted:
            return None
        if self.cookies_expires_at and datetime.utcnow() > self.cookies_expires_at:
            logger.info(f"Cookies expired for user {self.user_id}")
            return None  # Expired
        
        try:
            from config import settings
            from cryptography.fernet import Fernet
            
            if hasattr(settings, 'FERNET_KEY') and settings.FERNET_KEY:
                cipher = Fernet(settings.FERNET_KEY.encode() if isinstance(settings.FERNET_KEY, str) else settings.FERNET_KEY)
            else:
                logger.warning("FERNET_KEY not set, cannot decrypt")
                return None
            
            decrypted = cipher.decrypt(self.cookies_encrypted.encode())
            cookies = json.loads(decrypted.decode())
            logger.info(f"✅ Decrypted {len(cookies)} cookies for user {self.user_id}")
            return cookies
        except Exception as e:
            logger.error(f"Failed to decrypt cookies: {e}")
            return None
    
    def clear_cookies(self):
        """Revoke cookie authentication"""
        self.cookies_encrypted = None
        self.cookies_expires_at = None
        self.auth_method = "um_library"
        self.updated_at = datetime.utcnow()

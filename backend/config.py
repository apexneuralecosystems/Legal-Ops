"""
Centralized configuration management using Pydantic Settings.
"""
from pydantic_settings import BaseSettings
from typing import List
import os
import platform


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    # Database
    DATABASE_URL: str
    DB_HOST: str = "localhost"
    DB_PORT: int = 5432
    DB_NAME: str = "law_agent_db"
    DB_USER: str = "postgres"
    DB_PASSWORD: str = "password"
    
    # Google Gemini API
    GEMINI_API_KEY: str
    GEMINI_MODEL: str = "gemini-1.5-flash"
    
    # Google Cloud
    GOOGLE_CLIENT_ID: str = ""
    GOOGLE_CLIENT_SECRET: str = ""
    GOOGLE_REDIRECT_URI: str = ""  # Set via env: GOOGLE_REDIRECT_URI=https://api.yourdomain.com/auth/google/callback
    
    # Translation
    TRANSLATION_SERVICE: str = "google"  # google, azure, or deepl
    GOOGLE_TRANSLATE_API_KEY: str = ""
    
    # File Storage
    STORAGE_TYPE: str = "local"  # local or s3
    UPLOAD_DIR: str = "./uploads"
    MAX_UPLOAD_SIZE: int = 52428800  # 50MB
    
    # Redis
    REDIS_URL: str = "redis://localhost:6379/0"  # Set via env for production
    
    # Backend Server Configuration
    BACKEND_PORT: int = 8005  # Set via env: BACKEND_PORT=8005
    
    # Security
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    
    # JWT Configuration (for Apex Auth)
    JWT_SECRET_KEY: str = ""
    JWT_ALGORITHM: str = "HS256"
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    JWT_REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    
    # Feature Flags
    ENABLE_LIVE_TRANSCRIPTION: bool = False
    ENABLE_FULL_TEXT_LOGGING: bool = False
    ENABLE_PII_REDACTION: bool = True
    
    # PayPal Configuration
    PAYPAL_CLIENT_ID: str = ""
    PAYPAL_CLIENT_SECRET: str = ""
    PAYPAL_MODE: str = "sandbox"  # sandbox or live
    
    # SendGrid Configuration
    SENDGRID_API_KEY: str = ""
    FROM_EMAIL: str = "noreply@example.com"
    
    # Frontend Configuration
    FRONTEND_URL: str = "http://localhost:3000"  # Set via env: FRONTEND_URL=https://yourdomain.com
    FRONTEND_RESET_URL: str = ""  # Optional: Set via env, falls back to FRONTEND_URL/reset-password
    
    @property
    def frontend_reset_url(self) -> str:
        """Return explicit FRONTEND_RESET_URL if set, otherwise build from FRONTEND_URL."""
        if self.FRONTEND_RESET_URL:
            return self.FRONTEND_RESET_URL
        return f"{self.FRONTEND_URL.rstrip('/')}/reset-password"
    
    # OCR Configuration
    OCR_ENGINE: str = "auto"  # auto, tesseract, pymupdf, or google_vision
    TESSERACT_CMD: str = ""  # Auto-detect if empty
    OCR_LANGUAGES: str = "eng+msa"  # English + Malay
    GOOGLE_VISION_API_KEY: str = ""  # For cloud OCR fallback
    
    # Legal Database
    CASELAW_DB_TYPE: str = "mock"
    USE_COMMONLII: bool = False
    CASELAW_API_URL: str = ""
    CASELAW_API_KEY: str = ""
    
    # CORS - Set via env variable for your deployment
    # Example: CORS_ORIGINS=https://yourdomain.com,https://api.yourdomain.com
    CORS_ORIGINS: str | List[str] = "http://localhost:3000,http://127.0.0.1:3000"
    CORS_ALLOW_ALL: bool = False  # Set True for development only, False for production
    
    # Logging
    LOG_LEVEL: str = "INFO"
    LOG_FILE: str = "./logs/app.log"
    
    class Config:
        env_file = ".env"
        case_sensitive = True
        extra = "ignore"  # Ignore unknown env vars to prevent deployment failures
    
    @property
    def cors_origins_list(self) -> List[str]:
        """Parse CORS origins - handles both JSON array and comma-separated string."""
        if isinstance(self.CORS_ORIGINS, list):
            return self.CORS_ORIGINS
        return [origin.strip() for origin in self.CORS_ORIGINS.split(",")]
    
    def ensure_directories(self):
        """Create necessary directories if they don't exist."""
        os.makedirs(self.UPLOAD_DIR, exist_ok=True)
        os.makedirs(os.path.dirname(self.LOG_FILE), exist_ok=True)


# Global settings instance
settings = Settings()
settings.ensure_directories()

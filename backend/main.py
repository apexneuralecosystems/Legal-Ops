"""
FastAPI main application entry point with Apex SaaS Framework integration.
"""
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from config import settings
from database import init_db, Base
import logging

# Configure logging
logging.basicConfig(
    level=getattr(logging, settings.LOG_LEVEL),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(settings.LOG_FILE),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan context manager for startup and shutdown events."""
    # Startup
    logger.info("Starting Malaysian Legal AI Agent API...")
    try:
        from database import init_db, set_apex_client, get_async_db_url
        await init_db()
        logger.info("Database initialized successfully (async)")
        
        # Initialize Apex authentication client
        try:
            from apex import Client
            from apex.models import Base as ApexBase
            
            logger.info("Initializing Apex SaaS Framework (v0.3.24)...")
            
            # Convert sync URL to async URL for Apex
            async_url = get_async_db_url(settings.DATABASE_URL)
            
            apex_client = Client(
                database_url=async_url,
                secret_key=settings.SECRET_KEY,
                algorithm=settings.ALGORITHM,
                access_token_expire_minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES,
                async_mode=True
            )
            
            # Create apex tables (users, subscriptions, etc.)
            from sqlalchemy import inspect
            async with apex_client.engine.begin() as conn:
                # Create tables if they don't exist
                await conn.run_sync(ApexBase.metadata.create_all)
            
            # Set as global client for the application
            set_apex_client(apex_client)
            logger.info("✓ Apex SaaS Framework initialized successfully")
            
            # Initialize email client (SendGrid)
            try:
                from apex.email import init_email
                sendgrid_key = getattr(settings, 'SENDGRID_API_KEY', '')
                from_email = getattr(settings, 'FROM_EMAIL', '')
                if sendgrid_key and from_email:
                    init_email(sendgrid_key, from_email)
                    logger.info("✓ Email client (SendGrid) initialized")
                else:
                    logger.warning("SendGrid not configured - emails will be logged only")
            except Exception as e:
                logger.warning(f"Email client init failed: {e}")
            
        except ImportError as e:
            logger.error(f"Apex module import failed: {e}")
            raise RuntimeError("Apex module required but not available")
        except Exception as e:
            logger.error(f"Failed to initialize Apex client: {e}")
            raise RuntimeError(f"Apex initialization failed: {e}")
            
    except Exception as e:
        logger.error(f"Failed to initialize database: {e}")
        raise
    
    yield  # Application runs here
    
    # Shutdown (cleanup if needed)
    logger.info("Shutting down Malaysian Legal AI Agent API...")


# Create FastAPI app with lifespan
app = FastAPI(
    title="Malaysian Legal AI Agent API",
    description="Multi-agent system for legal document processing with bilingual support (Malay/English)",
    version="1.0.0",
    lifespan=lifespan
)

# Configure CORS - environment-aware
cors_origins = ["*"] if settings.CORS_ALLOW_ALL else settings.cors_origins_list
app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=not settings.CORS_ALLOW_ALL,  # Can't use credentials with wildcard
    allow_methods=["*"],
    allow_headers=["*"],
)

# Rate limiting configuration with user-awareness
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

def get_rate_limit_key(request):
    """Get rate limit key - prefer user ID over IP for authenticated requests."""
    auth_header = request.headers.get("Authorization", "")
    if auth_header.startswith("Bearer "):
        token = auth_header[7:]
        try:
            from jose import jwt
            payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
            user_id = payload.get("sub")
            if user_id:
                return f"user:{user_id}"
        except Exception:
            pass
    return get_remote_address(request)

limiter = Limiter(key_func=get_rate_limit_key)
# app.state.limiter = limiter
# app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# Global exception handler
@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    logger.error(f"Global exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={
            "status": "error",
            "message": "Internal server error",
            "detail": str(exc) if settings.LOG_LEVEL == "DEBUG" else None
        }
    )

# Health check endpoint
@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "service": "Malaysian Legal AI Agent",
        "version": "1.0.0"
    }

# Root endpoint
@app.get("/")
async def root():
    """Root endpoint with API information."""
    return {
        "message": "Malaysian Legal AI Agent API",
        "version": "1.0.0",
        "docs": "/docs",
        "health": "/health"
    }

# Import and include routers
from routers import matters, documents, research, ai_tasks, auth, admin, payments, evidence, subscription, webhooks

# Auth router (Apex SaaS Framework)
app.include_router(auth.router, prefix="/api", tags=["Authentication"])

# Admin router (requires superuser)
app.include_router(admin.router, prefix="/api", tags=["Admin"])

# Payment router (PayPal integration)
app.include_router(payments.router, prefix="/api", tags=["Payments"])

# Subscription router (usage tracking and subscription management)
app.include_router(subscription.router, prefix="/api", tags=["Subscription"])

# Existing routers (use sync database for backward compatibility)
app.include_router(matters.router, prefix="/api/matters", tags=["Matters"])
app.include_router(documents.router, prefix="/api/documents", tags=["Documents"])
app.include_router(research.router, prefix="/api/research", tags=["Research"])
app.include_router(ai_tasks.router, prefix="/api/ai-tasks", tags=["AI Tasks"])
app.include_router(evidence.router, prefix="/api/evidence", tags=["Evidence"])

# Webhooks router (PayPal events)
app.include_router(webhooks.router, prefix="/api", tags=["Webhooks"])


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=settings.BACKEND_PORT,
        reload=True,
        log_level=settings.LOG_LEVEL.lower()
    )

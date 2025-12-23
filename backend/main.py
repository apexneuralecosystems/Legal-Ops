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
        await init_db()
        logger.info("Database initialized successfully (async)")
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

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Rate limiting configuration
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

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
from routers import matters, documents, research, ai_tasks, auth, admin, payments, evidence

# Auth router (Apex SaaS Framework)
app.include_router(auth.router, prefix="/api", tags=["Authentication"])

# Admin router (requires superuser)
app.include_router(admin.router, prefix="/api", tags=["Admin"])

# Payment router (PayPal integration)
app.include_router(payments.router, prefix="/api", tags=["Payments"])

# Existing routers (use sync database for backward compatibility)
app.include_router(matters.router, prefix="/api/matters", tags=["Matters"])
app.include_router(documents.router, prefix="/api/documents", tags=["Documents"])
app.include_router(research.router, prefix="/api/research", tags=["Research"])
app.include_router(ai_tasks.router, prefix="/api/ai-tasks", tags=["AI Tasks"])
app.include_router(evidence.router, prefix="/api/evidence", tags=["Evidence"])


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8005,
        reload=True,
        log_level=settings.LOG_LEVEL.lower()
    )

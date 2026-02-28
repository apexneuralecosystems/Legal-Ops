"""
FastAPI main application entry point with Apex SaaS Framework integration.
Production-hardened for Dokploy deployment.
"""
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from config import settings
from database import init_db, Base, set_apex_client, get_async_db_url
import logging
import sys
import asyncio
import os
import uuid
import time
import certifi

# Force use of valid certifi bundle, overriding any system-wide PostgreSQL/Conda paths
os.environ["REQUESTS_CA_BUNDLE"] = certifi.where()
os.environ["SSL_CERT_FILE"] = certifi.where()

# Fix for Playwright on Windows (Asyncio Loop Policy)
if sys.platform == 'win32':
    asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())

# Configure structured logging
logging.basicConfig(
    level=getattr(logging, settings.LOG_LEVEL),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(settings.LOG_FILE),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

# Application readiness flag — set True when startup is fully complete
_app_ready = False


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan context manager for startup and shutdown events."""
    # Startup
    logger.info("Starting Malaysian Legal AI Agent API...")
    try:
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
    
    global _app_ready
    _app_ready = True
    logger.info("✓ Application is READY — accepting traffic")
    
    yield  # Application runs here
    
    # Shutdown — graceful cleanup
    _app_ready = False
    logger.info("Shutting down Malaysian Legal AI Agent API...")
    
    # 1. Cleanup browser pool
    try:
        from services.browser_pool import cleanup_browser_pool
        await cleanup_browser_pool()
        logger.info("✓ Browser pool cleaned up")
    except Exception as e:
        logger.warning(f"Browser pool cleanup failed: {e}")
    
    # 2. Close async DB engine
    try:
        from database import engine as async_engine
        await async_engine.dispose()
        logger.info("✓ Async DB engine disposed")
    except Exception as e:
        logger.warning(f"Async DB engine cleanup failed: {e}")
    
    # 3. Close sync DB engine
    try:
        from database import sync_engine
        sync_engine.dispose()
        logger.info("✓ Sync DB engine disposed")
    except Exception as e:
        logger.warning(f"Sync DB engine cleanup failed: {e}")
    
    logger.info("Shutdown complete.")



# Determine if docs should be accessible (only in DEBUG mode)
_docs_url = "/docs" if settings.LOG_LEVEL == "DEBUG" else None
_redoc_url = "/redoc" if settings.LOG_LEVEL == "DEBUG" else None

# Create FastAPI app with lifespan
app = FastAPI(
    title="Legal-Ops Backend Agent",
    description="Backend agent for legal research and drafting",
    version=settings.VERSION,
    lifespan=lifespan,
    docs_url=_docs_url,
    redoc_url=_redoc_url,
)

# Combined CORS and Request ID middleware — handles both tracing and CORS
@app.middleware("http")
async def cors_and_request_id_middleware(request: Request, call_next):
    """Combined middleware for CORS handling and request ID tracing."""
    request_id = request.headers.get("X-Request-ID", str(uuid.uuid4())[:8])
    start_time = time.time()
    
    try:
        # Log API requests for debugging
        if request.url.path.startswith("/api"):
            logger.info(f"[CORS-DEBUG] [{request_id}] {request.method} {request.url.path} from {request.headers.get('origin', 'no-origin')}")
        
        # Handle OPTIONS requests explicitly for all API endpoints
        if request.method == "OPTIONS":
            logger.info(f"[CORS-DEBUG] [{request_id}] Handling OPTIONS request for {request.url.path}")
            
            origin = settings.FRONTEND_URL or "https://legalops.apexneural.cloud"
            allow_headers_value = "Content-Type, content-type, Authorization, authorization, Accept, X-Requested-With"

            # Return proper CORS response for OPTIONS preflight
            cors_response = JSONResponse(
                status_code=200,
                content={"message": "OK"},
                headers={
                    "Access-Control-Allow-Origin": origin,
                    "Access-Control-Allow-Methods": "GET, POST, PUT, DELETE, OPTIONS, PATCH",
                    "Access-Control-Allow-Headers": allow_headers_value,
                    "Access-Control-Max-Age": "3600",
                    "Access-Control-Allow-Credentials": "true",
                    "X-Request-ID": request_id,
                }
            )
            
            # Add request ID to response time logging
            duration_ms = round((time.time() - start_time) * 1000)
            logger.info(f"[CORS-DEBUG] [{request_id}] OPTIONS {request.url.path} → 200 ({duration_ms}ms)")
            
            return cors_response
        
        # For non-OPTIONS requests, continue with normal processing
        response = await call_next(request)
        
        # Add request ID to response
        response.headers["X-Request-ID"] = request_id
        
        # Add CORS headers for all API endpoints
        origin = settings.FRONTEND_URL or "https://legalops.apexneural.cloud"
        response.headers["Access-Control-Allow-Origin"] = origin
        response.headers["Access-Control-Allow-Methods"] = "GET, POST, PUT, DELETE, OPTIONS, PATCH"
        response.headers["Access-Control-Allow-Headers"] = "Content-Type, content-type, Authorization, authorization, Accept, X-Requested-With"
        response.headers["Access-Control-Allow-Credentials"] = "true"
        if request.url.path.startswith("/api"):
            logger.info(f"[CORS-DEBUG] [{request_id}] Added CORS headers for origin: {origin}")
        
        # Log response for all API endpoints
        if request.url.path.startswith("/api"):
            duration_ms = round((time.time() - start_time) * 1000)
            logger.info(f"[CORS-DEBUG] [{request_id}] {request.method} {request.url.path} → {response.status_code} ({duration_ms}ms)")
        
        return response
        
    except Exception as e:
        logger.error(f"[CORS-DEBUG] [{request_id}] Error in middleware: {str(e)}", exc_info=True)
        # Return error response with CORS headers if it's an API endpoint
        if request.method == "OPTIONS":
            allow_headers_value = "Content-Type, content-type, Authorization, authorization, Accept, X-Requested-With"
            return JSONResponse(
                status_code=500,
                content={"error": "Internal server error"},
                headers={
                    "Access-Control-Allow-Origin": settings.FRONTEND_URL or "https://legalops.apexneural.cloud",
                    "Access-Control-Allow-Methods": "GET, POST, PUT, DELETE, OPTIONS, PATCH",
                    "Access-Control-Allow-Headers": allow_headers_value,
                    "Access-Control-Allow-Credentials": "true",
                    "X-Request-ID": request_id,
                }
            )
        else:
            raise

# Configure CORS - environment-aware
cors_origins = ["*"] if settings.CORS_ALLOW_ALL else settings.cors_origins_list

# Enhanced CORS configuration for production
if not settings.CORS_ALLOW_ALL:
    # Explicitly add the production domains
    production_origins = [
        "https://legalops.apexneural.cloud",
        "https://www.legalops.apexneural.cloud",
        "https://legalops-api.apexneural.cloud",
        "https://www.legalops-api.apexneural.cloud"
    ]
    
    # Add production origins if not already present
    for origin in production_origins:
        if origin not in cors_origins:
            cors_origins.append(origin)

# Allow all subdomains of the production domain via regex
# This catches www.legalops... vs legalops... vs other variations
allow_origin_regex = r"https://.*\.apexneural\.cloud" if not settings.CORS_ALLOW_ALL else None

app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_origin_regex=allow_origin_regex,
    allow_credentials=True, # Always allow credentials for specific origins/regex
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS", "PATCH"],
    allow_headers=["Content-Type", "content-type", "Authorization", "authorization", "Accept", "X-Requested-With"],
    expose_headers=["X-Request-ID"],
    max_age=3600,
)

# Rate limiting — shared limiter instance
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from rate_limit import limiter

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# Global exception handler — standardized error response
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc):
    request_id = request.headers.get("X-Request-ID", "unknown")
    if isinstance(exc, (ImportError, ModuleNotFoundError)):
        logger.warning(f"[{request_id}] Dependency missing: {exc}")
    else:
        logger.error(f"[{request_id}] Unhandled exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={
            "error": {
                "code": "INTERNAL_SERVER_ERROR",
                "message": "Internal server error",
                "detail": str(exc) if settings.LOG_LEVEL == "DEBUG" else None,
                "request_id": request_id,
            }
        }
    )

# ── Health / Liveness / Readiness ──────────────────────────────────────
@app.get("/health")
@app.get("/healthz")
async def health_check():
    """Liveness probe — returns 200 if process is alive."""
    return {
        "status": "healthy",
        "service": "Legal-Ops Backend Agent",
        "version": settings.VERSION,
    }

@app.get("/readyz")
async def readiness_check():
    """Readiness probe — checks DB and Redis connectivity."""
    checks = {}
    ready = True
    
    # Check database
    try:
        from database import sync_engine
        from sqlalchemy import text
        with sync_engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        checks["database"] = "ok"
    except Exception as e:
        checks["database"] = f"error: {str(e)[:100]}"
        ready = False
    
    # Check Redis
    try:
        import redis as redis_lib
        r = redis_lib.from_url(settings.REDIS_URL, socket_connect_timeout=2)
        r.ping()
        checks["redis"] = "ok"
    except Exception as e:
        checks["redis"] = f"error: {str(e)[:100]}"
        ready = False
    
    # Check app readiness flag
    checks["app_ready"] = _app_ready
    if not _app_ready:
        ready = False
    
    status_code = 200 if ready else 503
    return JSONResponse(
        status_code=status_code,
        content={"ready": ready, "checks": checks, "version": settings.VERSION}
    )

@app.get("/version-debug")
async def version_debug():
    """Version debug — only available when LOG_LEVEL is DEBUG."""
    if settings.LOG_LEVEL != "DEBUG":
        raise HTTPException(status_code=404, detail="Not found")
    return {"version": settings.VERSION, "status": "verified"}

# Root endpoint
@app.get("/")
async def root():
    """Root endpoint with API information."""
    return {
        "message": "Malaysian Legal AI Agent API",
        "version": settings.VERSION,
        "docs": "/docs",
        "health": "/health",
        "readyz": "/readyz",
    }

# Import and include routers
from routers import matters, documents, research, ai_tasks, auth, admin, payments, evidence, subscription, webhooks, paralegal, user_settings

# Auth router (Apex SaaS Framework)
app.include_router(auth.router, prefix="/api", tags=["Authentication"])

# User Settings router (cookie management)
app.include_router(user_settings.router, prefix="/api/user", tags=["User Settings"])

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
app.include_router(paralegal.router, prefix="/api/paralegal", tags=["Paralegal"])

# Chat feedback router
from routers import chat_feedback
app.include_router(chat_feedback.router, prefix="/api/feedback", tags=["Chat Feedback"])

# Case intelligence router (knowledge graph)
from routers import case_intelligence
app.include_router(case_intelligence.router, prefix="/api/case-intelligence", tags=["Case Intelligence"])

# Case insights router (automated analysis)
from routers import case_insights
app.include_router(case_insights.router, prefix="/api/insights", tags=["Case Insights"])

# Cross-case learning router (Phase 5)
from routers import cross_case_learning
app.include_router(cross_case_learning.router, tags=["Cross-Case Learning"])

# Webhooks router (PayPal events)
app.include_router(webhooks.router, prefix="/api", tags=["Webhooks"])


if __name__ == "__main__":
    import uvicorn
    # Disable reload to prevent loop policy issues on Windows
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=settings.BACKEND_PORT,
        reload=False, 
        loop="asyncio",
        log_level=settings.LOG_LEVEL.lower()
    )

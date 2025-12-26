"""
Centralized Logging Configuration for Legal-Ops
================================================
Provides structured JSON logging for log aggregation systems
(ELK Stack, CloudWatch, Datadog, etc.)
"""
import logging
import json
import sys
from datetime import datetime
from typing import Optional
from config import settings


class JSONFormatter(logging.Formatter):
    """
    JSON formatter for structured logging.
    Compatible with ELK Stack, CloudWatch, and other log aggregation tools.
    """
    
    def format(self, record: logging.LogRecord) -> str:
        log_record = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }
        
        # Add exception info if present
        if record.exc_info:
            log_record["exception"] = self.formatException(record.exc_info)
            log_record["exception_type"] = record.exc_info[0].__name__ if record.exc_info[0] else None
        
        # Add extra fields if present
        if hasattr(record, 'request_id'):
            log_record["request_id"] = record.request_id
        if hasattr(record, 'user_id'):
            log_record["user_id"] = record.user_id
        if hasattr(record, 'matter_id'):
            log_record["matter_id"] = record.matter_id
        if hasattr(record, 'duration_ms'):
            log_record["duration_ms"] = record.duration_ms
        
        return json.dumps(log_record, default=str)


class HumanReadableFormatter(logging.Formatter):
    """
    Human-readable formatter for console output.
    Adds colors for different log levels.
    """
    
    COLORS = {
        "DEBUG": "\033[36m",      # Cyan
        "INFO": "\033[32m",       # Green
        "WARNING": "\033[33m",    # Yellow
        "ERROR": "\033[31m",      # Red
        "CRITICAL": "\033[35m",   # Magenta
    }
    RESET = "\033[0m"
    
    def format(self, record: logging.LogRecord) -> str:
        # Add color for terminal
        color = self.COLORS.get(record.levelname, "")
        reset = self.RESET if color else ""
        
        # Format timestamp
        timestamp = datetime.fromtimestamp(record.created).strftime("%Y-%m-%d %H:%M:%S")
        
        # Build message
        base_msg = f"{timestamp} | {color}{record.levelname:8}{reset} | {record.name} | {record.getMessage()}"
        
        # Add exception if present
        if record.exc_info:
            base_msg += f"\n{self.formatException(record.exc_info)}"
        
        return base_msg


class RequestContextFilter(logging.Filter):
    """
    Filter that adds request context to log records.
    Used to track request_id, user_id across log entries.
    """
    
    def __init__(self, name: str = ""):
        super().__init__(name)
        self._context = {}
    
    def set_context(self, **kwargs):
        """Set context values for current request."""
        self._context.update(kwargs)
    
    def clear_context(self):
        """Clear context after request completes."""
        self._context.clear()
    
    def filter(self, record: logging.LogRecord) -> bool:
        # Add context to record
        for key, value in self._context.items():
            setattr(record, key, value)
        return True


# Global context filter for request tracking
request_context = RequestContextFilter()


def setup_logging(
    level: Optional[str] = None,
    log_file: Optional[str] = None,
    json_logs: bool = True,
    console_output: bool = True,
) -> logging.Logger:
    """
    Configure application-wide logging.
    
    Args:
        level: Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_file: Path to log file (uses settings.LOG_FILE if not provided)
        json_logs: Whether to use JSON format for file logging
        console_output: Whether to output to console
    
    Returns:
        The root logger
    """
    level = level or settings.LOG_LEVEL
    log_file = log_file or settings.LOG_FILE
    
    # Get root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, level.upper()))
    
    # Remove existing handlers
    root_logger.handlers.clear()
    
    # Add context filter
    root_logger.addFilter(request_context)
    
    # Console handler (human readable)
    if console_output:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(HumanReadableFormatter())
        console_handler.setLevel(getattr(logging, level.upper()))
        root_logger.addHandler(console_handler)
    
    # File handler (JSON for aggregation)
    if log_file:
        import os
        os.makedirs(os.path.dirname(log_file), exist_ok=True)
        
        file_handler = logging.FileHandler(log_file, encoding='utf-8')
        if json_logs:
            file_handler.setFormatter(JSONFormatter())
        else:
            file_handler.setFormatter(logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            ))
        file_handler.setLevel(getattr(logging, level.upper()))
        root_logger.addHandler(file_handler)
    
    # Log startup message
    root_logger.info(f"Logging configured: level={level}, file={log_file}, json={json_logs}")
    
    return root_logger


def get_logger(name: str) -> logging.Logger:
    """
    Get a logger for a specific module.
    
    Args:
        name: Logger name (usually __name__)
    
    Returns:
        Logger instance
    """
    return logging.getLogger(name)


class LogContext:
    """
    Context manager for adding request-specific logging context.
    
    Usage:
        with LogContext(request_id="abc123", user_id="user1"):
            logger.info("Processing request")
    """
    
    def __init__(self, **kwargs):
        self.context = kwargs
    
    def __enter__(self):
        request_context.set_context(**self.context)
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        request_context.clear_context()
        return False


# FastAPI middleware for request logging
async def logging_middleware(request, call_next):
    """
    FastAPI middleware that adds request context to logs.
    
    Usage in main.py:
        from services.logging_service import logging_middleware
        app.middleware("http")(logging_middleware)
    """
    import time
    import uuid
    
    request_id = str(uuid.uuid4())[:8]
    start_time = time.time()
    
    # Set logging context
    request_context.set_context(
        request_id=request_id,
        method=request.method,
        path=request.url.path,
    )
    
    # Add user_id if authenticated
    auth_header = request.headers.get("Authorization", "")
    if auth_header.startswith("Bearer "):
        try:
            from jose import jwt
            token = auth_header[7:]
            payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
            request_context.set_context(user_id=payload.get("sub"))
        except Exception:
            pass
    
    try:
        response = await call_next(request)
        
        # Log request completion
        duration_ms = (time.time() - start_time) * 1000
        request_context.set_context(duration_ms=duration_ms)
        
        logger = get_logger("request")
        logger.info(
            f"{request.method} {request.url.path} -> {response.status_code} ({duration_ms:.2f}ms)"
        )
        
        return response
    except Exception as e:
        logger = get_logger("request")
        logger.error(f"{request.method} {request.url.path} -> ERROR: {e}")
        raise
    finally:
        request_context.clear_context()

# ============================================
# Legal-Ops Backend Dockerfile
# ============================================
# Optimized for faster builds on Dokploy

FROM python:3.11-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app \
    PIP_NO_CACHE_DIR=0 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /app

# Install system dependencies in one layer
RUN apt-get update && apt-get install -y --no-install-recommends \
    # Build dependencies
    build-essential \
    libpq-dev \
    gcc \
    # OCR dependencies
    tesseract-ocr \
    tesseract-ocr-eng \
    # PDF processing
    poppler-utils \
    libmagic1 \
    # Runtime utilities
    curl \
    wget \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# Copy requirements first (for better layer caching)
COPY requirements.txt .

# Install Python dependencies with parallel processing
RUN pip install --upgrade pip && \
    pip install -r requirements.txt

# Copy application code
COPY . .

# Create necessary directories
RUN mkdir -p /app/uploads /app/logs && \
    chmod -R 755 /app

# Expose port
EXPOSE 8091

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD curl -f http://localhost:8091/health || exit 1

# Run with uvicorn directly (simpler than gunicorn for debugging)
CMD ["python", "-m", "uvicorn", "main:app", \
    "--host", "0.0.0.0", \
    "--port", "8091", \
    "--workers", "1", \
    "--timeout-keep-alive", "300"]

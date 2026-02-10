# ============================================
# Legal-Ops Backend Dockerfile
# ============================================
# Multi-stage production build optimized for Dokploy

# Stage 1: Builder
FROM python:3.12-slim as builder

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /build

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Install dependencies into a virtualenv
COPY requirements.txt .
RUN python -m venv /opt/venv
# Make sure we use the venv's pip
ENV PATH="/opt/venv/bin:$PATH"
# Use --no-cache-dir to save space
RUN pip install --upgrade pip --no-cache-dir && \
    pip install -r requirements.txt --no-cache-dir

# Stage 2: Runtime
# Use official Playwright image which includes all browsers and dependencies
FROM mcr.microsoft.com/playwright/python:v1.49.1-jammy

WORKDIR /app

# Copy virtualenv from builder
COPY --from=builder /opt/venv /opt/venv

# Set environment variables
ENV PATH="/opt/venv/bin:$PATH" \
    PYTHONPATH="/app" \
    PORT=8000 \
    PLAYWRIGHT_BROWSERS_PATH=/ms-playwright

# Install runtime system dependencies (Postgres, OCR)
# Note: Playwright image is Ubuntu-based (jammy), so we use apt-get
# Clean up apt lists in the same layer to save space
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq-dev \
    tesseract-ocr \
    tesseract-ocr-eng \
    tesseract-ocr-msa \
    poppler-utils \
    libmagic1 \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Download Spacy model (safe to run here as venv is copied)
RUN python -m spacy download en_core_web_sm || true

# Copy application code
COPY . .

# Create necessary directories
RUN mkdir -p /app/uploads /app/logs && \
    chmod -R 755 /app

# Expose port
EXPOSE ${PORT:-8091}

# Health check (use 127.0.0.1 for stability)
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD curl -f http://127.0.0.1:${PORT:-8091}/health || exit 1

# Non-root user for security
RUN useradd -m -u 1000 appuser && \
    chown -R appuser:appuser /app && \
    chown -R appuser:appuser /opt/venv

USER appuser

# Run with startup script (migrations + server)
CMD ["/app/scripts/start.sh"]

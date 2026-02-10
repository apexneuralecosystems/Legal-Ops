# ============================================
# Legal-Ops Backend Dockerfile
# ============================================
# Single-stage production build optimized for extreme space efficiency

# Use official Playwright image which includes all browsers and dependencies
FROM mcr.microsoft.com/playwright/python:v1.49.1-jammy

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH="/app" \
    PORT=8000 \
    PLAYWRIGHT_BROWSERS_PATH=/ms-playwright \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

# Combine everything into ONE layer to minimize disk footprint
# 1. Install build tools + libraries
# 2. Install python deps
# 3. Remove build tools to reclaim space
# 4. Clean up apt caches
COPY requirements.txt .

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    gcc \
    tesseract-ocr \
    tesseract-ocr-eng \
    tesseract-ocr-msa \
    poppler-utils \
    libmagic1 \
    curl \
    && pip install --upgrade pip --no-cache-dir \
    && pip install -r requirements.txt --no-cache-dir \
    && python -m spacy download en_core_web_sm || true \
    && apt-get purge -y --auto-remove build-essential gcc \
    && rm -rf /var/lib/apt/lists/* \
    && rm -rf /root/.cache

# Copy application code
COPY . .

# Create necessary directories and set permissions
# Playwright image already has 'pwuser' (UID 1000)
RUN mkdir -p /app/uploads /app/logs && \
    chown -R pwuser:pwuser /app

# Switch to the existing non-root user
USER pwuser

# Expose port
EXPOSE ${PORT:-8091}

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD curl -f http://127.0.0.1:${PORT:-8091}/health || exit 1

# Run with startup script (migrations + server)
CMD ["/app/scripts/start.sh"]



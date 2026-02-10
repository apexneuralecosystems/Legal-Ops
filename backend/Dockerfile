# ============================================
# Legal-Ops Backend Dockerfile
# ============================================
# Production build — Playwright base for browser automation (Lexis scraping)
# Optimized for Dokploy deployment with Traefik reverse proxy

# Use official Playwright image which includes all browsers and dependencies
FROM mcr.microsoft.com/playwright/python:v1.49.1-jammy

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH="/app" \
    PLAYWRIGHT_BROWSERS_PATH=/app/pw-browsers \
    PIP_NO_CACHE_DIR=1

# PORT is the single source of truth — set via Dokploy env, default 8091
ENV PORT=8091

WORKDIR /app

# Install system deps + python deps in ONE layer, then clean up
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
    tini \
    && pip install --upgrade pip --no-cache-dir \
    && pip install -r requirements.txt --no-cache-dir \
    && python -m spacy download en_core_web_sm || true \
    && playwright install --with-deps chromium \
    && apt-get purge -y --auto-remove build-essential gcc \
    && rm -rf /var/lib/apt/lists/* \
    && rm -rf /root/.cache

# Copy application code
COPY . .

# Create non-root user, directories, and set permissions
RUN groupadd -g 1001 appuser && \
    useradd -r -u 1001 -g appuser -m appuser && \
    mkdir -p /app/uploads /app/logs /app/pw-browsers && \
    chmod +x /app/scripts/start.sh && \
    chown -R appuser:appuser /app

# Switch to non-root user
USER appuser

# Expose the PORT (Dokploy maps host→container via this)
EXPOSE ${PORT}

# Health check — deterministic, uses $PORT
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD curl -sf http://127.0.0.1:${PORT}/health || exit 1

# Use tini as PID 1 for proper signal forwarding (SIGTERM to gunicorn)
STOPSIGNAL SIGTERM
ENTRYPOINT ["tini", "--"]

# Run with startup script (migrations + gunicorn)
CMD ["/app/scripts/start.sh"]



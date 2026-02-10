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

# Copy and install Python dependencies
COPY requirements.txt .
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"
RUN pip install --upgrade pip && \
    pip install -r requirements.txt

# Stage 2: Runtime
FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app \
    PATH="/opt/venv/bin:$PATH"

WORKDIR /app

# Install runtime dependencies only
RUN apt-get update && apt-get install -y --no-install-recommends \
    tesseract-ocr \
    tesseract-ocr-eng \
    tesseract-ocr-msa \
    poppler-utils \
    libmagic1 \
    curl \
    libpq5 \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# Copy Python dependencies from builder
COPY --from=builder /opt/venv /opt/venv

# Copy application code
COPY . .

# Install dos2unix to fix line endings in scripts
RUN apt-get update && apt-get install -y dos2unix && \
    dos2unix scripts/start.sh && \
    chmod +x scripts/start.sh && \
    rm -rf /var/lib/apt/lists/*

# Install Playwright Browsers (Chromium only to save space)
RUN pip install playwright && \
    playwright install --with-deps chromium && \
    (python -m spacy download en_core_web_sm || true)

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

#!/bin/bash
set -e

echo "🚀 Starting Legal Ops Backend..."

# Run database migrations
echo "Runnning Database Migrations..."
alembic upgrade head

# Start application
echo "Starting Gunicorn Server on port ${PORT:-8091}..."
exec gunicorn main:app \
    --workers 4 \
    --worker-class uvicorn.workers.UvicornWorker \
    --bind 0.0.0.0:${PORT:-8091} \
    --timeout 300 \
    --max-requests 1000 \
    --max-requests-jitter 50 \
    --access-logfile - \
    --error-logfile -

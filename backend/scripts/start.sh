#!/bin/bash
set -e

echo "🚀 Starting Legal Ops Backend..."

# Run database migrations
echo "Running Database Migrations..."

# Check if alembic_version table exists (i.e., has Alembic ever run on this DB?)
# If the DB has tables but no alembic_version, stamp it at head first
if ! python -c "
from config import settings
from sqlalchemy import create_engine, inspect
engine = create_engine(settings.DATABASE_URL)
inspector = inspect(engine)
tables = inspector.get_table_names()
has_alembic = 'alembic_version' in tables
has_tables = len(tables) > 0
if has_tables and not has_alembic:
    print('STAMP_NEEDED')
    exit(1)
else:
    print('OK')
    exit(0)
" 2>/dev/null; then
    echo "⚠️  Existing database detected without migration history. Stamping at head..."
    alembic stamp head
    echo "✅ Database stamped at head"
fi

# Now run any pending migrations
alembic upgrade head
echo "✅ Migrations complete"

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

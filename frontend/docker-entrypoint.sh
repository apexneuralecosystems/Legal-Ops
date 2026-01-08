#!/bin/sh
# ============================================
# Docker Entrypoint for Next.js + Nginx
# ============================================

set -e

echo "Starting Legal-Ops Frontend..."

# Start Next.js server in background
echo "Starting Next.js server on port 3000 (binding to 0.0.0.0)..."
cd /app
export PORT=3000
HOSTNAME=0.0.0.0 node server.js &

# Wait for Next.js to be ready
echo "Waiting for Next.js to start..."
sleep 3

for i in $(seq 1 30); do
    if wget -q -O /dev/null http://127.0.0.1:3000/ 2>/dev/null; then
        echo "Next.js is ready!"
        break
    fi
    echo "Waiting... ($i/30)"
    sleep 1
done

# Verify Next.js is running
if ! wget -q -O /dev/null http://127.0.0.1:3000/ 2>/dev/null; then
    echo "ERROR: Next.js failed to start!"
    exit 1
fi

# Start Nginx on port 3001
echo "Starting Nginx on port 3001..."
exec nginx -g "daemon off;"

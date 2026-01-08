#!/bin/sh
# ============================================
# Docker Entrypoint for Next.js + Nginx
# ============================================

set -e

echo "Starting Legal-Ops Frontend..."

# Set hostname for Next.js to bind to all interfaces
export HOSTNAME="0.0.0.0"
export PORT=3000

# Start Next.js server in background on port 3000
echo "Starting Next.js server on port 3000 (binding to 0.0.0.0)..."
cd /app
node server.js &

# Wait for Next.js to be ready with health check
echo "Waiting for Next.js to start..."
for i in $(seq 1 30); do
    if wget -q --spider http://127.0.0.1:3000/ 2>/dev/null; then
        echo "Next.js is ready!"
        break
    fi
    echo "Waiting... ($i/30)"
    sleep 1
done

# Start Nginx on port 3001
echo "Starting Nginx on port 3001..."
nginx -g "daemon off;"

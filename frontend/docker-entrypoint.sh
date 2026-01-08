#!/bin/sh
# ============================================
# Docker Entrypoint for Next.js + Nginx
# ============================================

set -e

echo "Starting Legal-Ops Frontend..."

# Start Next.js server in background on port 3000
echo "Starting Next.js server on port 3000..."
cd /app
node server.js &

# Wait for Next.js to be ready
echo "Waiting for Next.js to start..."
sleep 5

# Start Nginx on port 3001
echo "Starting Nginx on port 3001..."
nginx -g "daemon off;"

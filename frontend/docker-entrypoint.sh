#!/bin/sh
# ============================================
# Docker Entrypoint for Next.js + Nginx
# ============================================
# tini (PID 1) forwards SIGTERM to this script.
# We trap it and shut down both processes cleanly.

set -e

NEXTJS_PID=""

# Graceful shutdown: kill Next.js, let nginx finish
cleanup() {
    echo "Received shutdown signal — stopping services..."
    if [ -n "$NEXTJS_PID" ] && kill -0 "$NEXTJS_PID" 2>/dev/null; then
        kill -TERM "$NEXTJS_PID" 2>/dev/null || true
        wait "$NEXTJS_PID" 2>/dev/null || true
    fi
    # nginx PID 1 replacement via exec will receive SIGTERM from tini directly
    echo "Shutdown complete."
    exit 0
}

trap cleanup TERM INT QUIT

echo "Starting Legal-Ops Frontend..."

# Start Next.js server in background (internal port 3000)
echo "Starting Next.js server on port 3000 (binding to 0.0.0.0)..."
cd /app
export PORT=3000
HOSTNAME=0.0.0.0 node server.js &
NEXTJS_PID=$!

# Wait for Next.js to be ready (max 30 attempts)
echo "Waiting for Next.js to start..."
sleep 3

for i in $(seq 1 30); do
    if wget -q -O /dev/null http://127.0.0.1:3000/ 2>/dev/null; then
        echo "Next.js is ready! (PID: $NEXTJS_PID)"
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

# Start Nginx on port 8006 (replaces this shell — tini will forward signals)
echo "Starting Nginx on port 8006..."
exec nginx -g "daemon off;"

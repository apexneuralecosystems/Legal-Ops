# ============================================
# Legal-Ops Frontend Dockerfile
# ============================================
# Multi-stage build for Next.js production - Optimized for Disk Space

# Stage 1: Build the application
FROM node:20-alpine AS builder

# Install system dependencies in one layer
RUN apk add --no-cache libc6-compat && \
    rm -rf /var/cache/apk/*

WORKDIR /app

# Copy dependency files first for caching
COPY package.json package-lock.json* ./

# Install ALL dependencies (including devDeps needed for build)
# and clean cache in the SAME layer to minimize disk usage
RUN npm ci --prefer-offline --no-audit && \
    npm cache clean --force

# Copy source code
COPY . .

# Build arguments
ARG NEXT_PUBLIC_API_URL
ARG NEXT_PUBLIC_APP_URL

ENV NEXT_PUBLIC_API_URL=${NEXT_PUBLIC_API_URL:-https://legalops-api.apexneural.cloud}
ENV NEXT_PUBLIC_APP_URL=${NEXT_PUBLIC_APP_URL:-https://legalops.apexneural.cloud}
ENV NEXT_TELEMETRY_DISABLED=1
ENV NODE_ENV=production

# Build the app and clean up everything NOT needed for production immediately
# This drastically reduces the size of the builder stage
RUN npm run build && \
    rm -rf src/ components/ pages/ app/ node_modules/.cache node_modules/.cache/terser-webpack-plugin

# Stage 3: Production runtime
FROM node:20-alpine AS runner

# Install nginx and cleanup in one layer
RUN apk add --no-cache nginx dos2unix && \
    rm -rf /var/cache/apk/*

WORKDIR /app

ENV NODE_ENV=production
ENV NEXT_TELEMETRY_DISABLED=1

# Create non-root user
RUN addgroup -g 1001 -S nodejs && \
    adduser -S nextjs -u 1001

# Copy built app and dependencies
COPY --from=builder /app/public ./public
COPY --from=builder /app/.next/standalone ./
COPY --from=builder /app/.next/static ./.next/static

# Copy Nginx configuration and entrypoint
COPY nginx.conf /etc/nginx/nginx.conf
COPY docker-entrypoint.sh /app/docker-entrypoint.sh

# Fix Windows line endings and set permissions
RUN dos2unix /app/docker-entrypoint.sh && \
    chmod +x /app/docker-entrypoint.sh && \
    chown -R nextjs:nodejs /app && \
    mkdir -p /var/log/nginx /var/lib/nginx /tmp/client_temp /tmp/proxy_temp && \
    chown -R nextjs:nodejs /var/log/nginx /var/lib/nginx /tmp && \
    touch /tmp/nginx.pid && \
    chown nextjs:nodejs /tmp/nginx.pid

USER nextjs

ENV PORT=8006
EXPOSE 8006

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=30s --retries=3 \
    CMD wget -q --spider http://localhost:8006/health || exit 1

# Use entrypoint script to start both Next.js and Nginx
ENTRYPOINT ["/app/docker-entrypoint.sh"]


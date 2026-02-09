# ============================================
# Legal-Ops Frontend Dockerfile
# ============================================
# Multi-stage build for Next.js production

# Stage 1: Dependencies
FROM node:20-alpine AS deps
RUN apk add --no-cache libc6-compat

WORKDIR /app
COPY package.json package-lock.json* ./
RUN npm ci --prefer-offline --no-audit

# Stage 2: Builder
FROM node:20-alpine AS builder

WORKDIR /app

# Copy dependencies
COPY --from=deps /app/node_modules ./node_modules
COPY . .

# Build arguments
ARG NEXT_PUBLIC_API_URL
ARG NEXT_PUBLIC_APP_URL

ENV NEXT_PUBLIC_API_URL=${NEXT_PUBLIC_API_URL:-http://localhost:8091}
ENV NEXT_PUBLIC_APP_URL=${NEXT_PUBLIC_APP_URL:-http://localhost:8006}
ENV NEXT_TELEMETRY_DISABLED=1
ENV NODE_ENV=production

# Build the app
RUN npm run build

# Stage 3: Production runtime
FROM node:20-alpine AS runner

# Install nginx
RUN apk add --no-cache nginx

WORKDIR /app

ENV NODE_ENV=production
ENV NEXT_TELEMETRY_DISABLED=1

# Create non-root user
RUN addgroup -g 1001 -S nodejs
RUN adduser -S nextjs -u 1001

# Copy built app and dependencies
COPY --from=builder /app/public ./public
COPY --from=builder /app/.next/standalone ./
COPY --from=builder /app/.next/static ./.next/static

# Copy Nginx configuration and entrypoint
COPY nginx.conf /etc/nginx/nginx.conf
COPY docker-entrypoint.sh /app/docker-entrypoint.sh

# Install dos2unix to fix Windows line endings and set permissions
RUN apk add --no-cache dos2unix && \
    dos2unix /app/docker-entrypoint.sh && \
    chmod +x /app/docker-entrypoint.sh

# Change ownership
RUN chown -R nextjs:nodejs /app && \
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

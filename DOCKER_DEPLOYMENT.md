# Docker Deployment Guide for Dokploy

This guide explains how to deploy the Legal-Ops application using Docker on Dokploy.

## Files Created

| File | Purpose |
|------|---------|
| `backend/Dockerfile` | FastAPI backend with OCR dependencies |
| `frontend/Dockerfile` | Next.js frontend with standalone output |
| `docker-compose.yml` | Full-stack orchestration |
| `.env.docker.example` | Environment variables template |
| `backend/.dockerignore` | Exclude files from backend build |
| `frontend/.dockerignore` | Exclude files from frontend build |

## Quick Start (Local Testing)

```bash
# 1. Copy and configure environment
cp .env.docker.example .env

# 2. Edit .env with your values
# - Set your GEMINI_API_KEY or OPENROUTER_API_KEY
# - Set a secure SECRET_KEY
# - Configure database credentials

# 3. Build and start all services
docker-compose up --build -d

# 4. Check status
docker-compose ps

# 5. View logs
docker-compose logs -f
```

## Dokploy Deployment

### Option 1: Using Docker Compose (Recommended)

1. **Push to Git**: Ensure all Docker files are committed and pushed
2. **Create Application**: In Dokploy, create a new application from your repository
3. **Configure Environment**: Add environment variables in Dokploy:
   - `GEMINI_API_KEY` (or `OPENROUTER_API_KEY`)
   - `SECRET_KEY` (generate a secure key)
   - `DB_PASSWORD`
   - `NEXT_PUBLIC_API_URL` (your backend URL)
   - `NEXT_PUBLIC_APP_URL` (your frontend URL)
4. **Deploy**: Dokploy will build and run using docker-compose.yml

### Option 2: Separate Services

Deploy backend and frontend as separate applications:

#### Backend Service
- **Context**: `./backend`
- **Dockerfile**: `Dockerfile`
- **Port**: `8091`
- **Environment Variables**:
  ```
  DATABASE_URL=postgresql://user:pass@host:5432/db
  GEMINI_API_KEY=your_key
  SECRET_KEY=your_secret
  CORS_ORIGINS=https://your-frontend.com
  ```

#### Frontend Service
- **Context**: `./frontend`
- **Dockerfile**: `Dockerfile`
- **Port**: `8006`
- **Build Args**:
  ```
  NEXT_PUBLIC_API_URL=https://your-backend.com
  NEXT_PUBLIC_APP_URL=https://your-frontend.com
  ```

## Environment Variables Reference

### Required

| Variable | Description |
|----------|-------------|
| `DATABASE_URL` | PostgreSQL connection string |
| `SECRET_KEY` | JWT signing secret (generate with `python -c "import secrets; print(secrets.token_hex(32))"`) |
| `GEMINI_API_KEY` | Google Gemini API key (if using Gemini) |
| `NEXT_PUBLIC_API_URL` | Backend URL for frontend |

### Optional

| Variable | Default | Description |
|----------|---------|-------------|
| `LLM_PROVIDER` | `gemini` | LLM provider (`gemini` or `openrouter`) |
| `OPENROUTER_API_KEY` | - | OpenRouter API key |
| `CORS_ORIGINS` | * | Allowed CORS origins |
| `PAYPAL_CLIENT_ID` | - | PayPal integration |
| `SENDGRID_API_KEY` | - | Email service |

## Health Checks

Both services include health check endpoints:

- **Backend**: `GET /health`
- **Frontend**: `GET /`

## Volumes

The docker-compose configuration includes persistent volumes:

- `postgres_data` - Database storage
- `redis_data` - Cache storage
- `uploads_data` - Uploaded files
- `logs_data` - Application logs

## Troubleshooting

### Backend not starting
```bash
docker-compose logs backend
```

### Database connection issues
Ensure PostgreSQL is healthy:
```bash
docker-compose exec postgres pg_isready
```

### Frontend build fails
Check build args are set correctly:
```bash
docker-compose build --no-cache frontend
```

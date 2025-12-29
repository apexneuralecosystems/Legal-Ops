# Legal-Ops Deployment Report
## Cloud Panel Server Deployment Guide

**Generated:** December 26, 2024  
**Version:** 1.0.0  
**Apex Module:** v0.3.24

---

## 🟢 Working Features

| Feature | Status | Endpoint/Notes |
|---------|--------|----------------|
| **Authentication** | ✅ | |
| ├─ User Signup | ✅ | `POST /api/auth/signup` |
| ├─ User Login | ✅ | `POST /api/auth/login` |
| ├─ Get Current User | ✅ | `GET /api/auth/me` |
| ├─ Token Refresh | ✅ | `POST /api/auth/refresh` |
| ├─ Forgot Password | ✅ | `POST /api/auth/forgot-password` (SendGrid) |
| └─ Reset Password | ✅ | `POST /api/auth/reset-password` |
| **Subscriptions** | ✅ | |
| ├─ Usage Status | ✅ | `GET /api/subscription/usage/status` |
| ├─ Check Access | ✅ | `GET /api/subscription/check/{workflow}` |
| ├─ Activate | ✅ | `POST /api/subscription/activate` |
| └─ Cancel | ✅ | `POST /api/subscription/cancel` |
| **Payments (PayPal)** | ✅ | |
| ├─ Create Order | ✅ | `POST /api/payments/orders/create` |
| ├─ Capture Order | ✅ | `POST /api/payments/orders/{id}/capture` |
| ├─ Create Subscription | ✅ | `POST /api/payments/subscriptions/create` |
| └─ Webhooks | ✅ | `POST /api/webhooks/paypal` |
| **Workflows** | ✅ | |
| ├─ Intake | ✅ | `POST /api/matters/intake` |
| ├─ Drafting | ✅ | `POST /api/matters/{id}/draft` |
| ├─ Research | ✅ | `POST /api/research/build-argument` |
| └─ Evidence | ✅ | `POST /api/evidence/build` |
| **Payment Gate** | ✅ | |
| ├─ Free Trial (1 use) | ✅ | First use passes |
| └─ Blocks After Limit | ✅ | Returns 402 |
| **Frontend Pages** | ✅ | |
| ├─ Login | ✅ | `/login` |
| ├─ Signup | ✅ | `/signup` |
| ├─ Dashboard | ✅ | `/dashboard` |
| ├─ Forgot Password | ✅ | `/forgot-password` |
| ├─ Reset Password | ✅ | `/reset-password` |
| └─ Pricing | ✅ | `/pricing` |

---

## 🟡 Optional/Partial Features

| Feature | Status | Notes |
|---------|--------|-------|
| OCR (Tesseract) | ⚠️ | Falls back to PyMuPDF text extraction |
| Redis Caching | ⚠️ | Requires Redis server for production |
| Rate Limiting | ⚠️ | Uses in-memory by default; Redis recommended |
| File Storage | ⚠️ | Local storage only; S3 not configured |

---

## Environment Variables Required

```env
# Database (Required)
DATABASE_URL=postgresql://user:password@host:5432/database

# Security (Required)
SECRET_KEY=your-secret-key-min-32-chars
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# AI (Required)
GEMINI_API_KEY=your-gemini-api-key

# PayPal (Required for payments)
PAYPAL_CLIENT_ID=your-paypal-client-id
PAYPAL_CLIENT_SECRET=your-paypal-client-secret
PAYPAL_MODE=sandbox  # Change to 'live' for production

# SendGrid (Required for emails)
SENDGRID_API_KEY=your-sendgrid-api-key
FROM_EMAIL=noreply@yourdomain.com
FRONTEND_RESET_URL=https://yourdomain.com/reset-password

# CORS (Production)
CORS_ALLOW_ALL=false
CORS_ORIGINS=https://yourdomain.com

# Redis (Optional)
REDIS_URL=redis://localhost:6379/0
```

---

## Server Requirements

| Requirement | Minimum | Recommended |
|-------------|---------|-------------|
| Python | 3.10+ | 3.12 |
| Node.js | 18+ | 20 |
| PostgreSQL | 14+ | 16 |
| RAM | 2GB | 4GB |
| Storage | 10GB | 20GB |

---

## Deployment Commands

### Backend

```bash
# Navigate to backend
# Navigate to backend directory first
cd backend

# Start server (production)
gunicorn main:app -w 4 -k uvicorn.workers.UvicornWorker -b 0.0.0.0:8091
```

### Frontend

```bash
# Navigate to frontend
cd frontend

# Install dependencies
npm install

# Build for production
npm run build

# Start server
npm start
# Or use PM2:
pm2 start npm --name "legal-ops-frontend" -- start
```

---

## Nginx Configuration

```nginx
server {
    listen 80;
    server_name yourdomain.com;
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name yourdomain.com;

    ssl_certificate /path/to/cert.pem;
    ssl_certificate_key /path/to/key.pem;

    # Frontend
    location / {
        proxy_pass http://127.0.0.1:3000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_cache_bypass $http_upgrade;
    }

    # Backend API
    location /api {
        proxy_pass http://127.0.0.1:8091;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # PayPal Webhooks
    location /api/webhooks {
        proxy_pass http://127.0.0.1:8091;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

---

## PayPal Webhook Setup

1. Go to [PayPal Developer Dashboard](https://developer.paypal.com/dashboard/applications)
2. Select your application
3. Click "Add Webhook"
4. Set URL: `https://yourdomain.com/api/webhooks/paypal`
5. Subscribe to events:
   - `PAYMENT.CAPTURE.COMPLETED`
   - `BILLING.SUBSCRIPTION.ACTIVATED`
   - `BILLING.SUBSCRIPTION.CANCELLED`
   - `BILLING.SUBSCRIPTION.EXPIRED`

---

## Health Check

After deployment, verify:

```bash
# Backend health
curl https://yourdomain.com/api/health

# Expected response:
# {"status": "healthy", "service": "Malaysian Legal AI Agent", "version": "1.0.0"}
```

---

## Feature Testing Checklist

- [ ] User can sign up
- [ ] User can log in
- [ ] User can reset password (email received)
- [ ] First workflow use works (free trial)
- [ ] Second workflow use shows payment gate (402)
- [ ] PayPal payment flow works
- [ ] After payment, unlimited access granted
- [ ] Webhook updates subscription status

---

## Support

For issues, check:
1. Backend logs: `journalctl -u legal-ops-backend -f`
2. Frontend logs: `pm2 logs legal-ops-frontend`
3. Database: Verify migrations with `alembic current`

# Malaysian Legal AI Agent System

> **LegalOps Hub** - Automated legal document processing with 15 specialized AI agents for Malaysian law firms

A comprehensive multi-agent system for processing legal documents with bilingual support (Malay/English), automated OCR, risk assessment, and legal drafting powered by Google Gemini.

[![Backend](https://img.shields.io/badge/backend-FastAPI-009688)]()
[![Frontend](https://img.shields.io/badge/frontend-Next.js%2014-black)]()
[![Database](https://img.shields.io/badge/database-PostgreSQL-336791)]()
[![Auth](https://img.shields.io/badge/auth-Apex%20v0.3.24-purple)]()
[![Payments](https://img.shields.io/badge/payments-PayPal-003087)]()

---

## 🚀 Quick Start

### Development

```bash
# 1. Clone and setup backend
cd backend
python -m venv venv
venv\Scripts\activate        # Windows
source venv/bin/activate     # Linux/Mac
pip install -r requirements.txt

# 2. Configure environment
cp .env.example .env
# Edit .env with your credentials

# 3. Run database migrations
alembic upgrade head

# 4. Start backend
python main.py               # Runs on http://localhost:8091

# 5. Start frontend (new terminal)
cd frontend
npm install
npm run dev                  # Runs on http://localhost:8006
```

**Access the app**: http://localhost:8006  
**API Docs**: http://localhost:8091/docs

---

## 📋 Environment Variables

Create a `.env` file in the `backend/` directory:

```env
# Database (Required)
DATABASE_URL=postgresql://user:password@localhost:5432/legal_ops_db

# Security (Required)
SECRET_KEY=your-secret-key-minimum-32-characters
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# AI (Required)
GEMINI_API_KEY=your-google-gemini-api-key

# PayPal Payments (Required for subscriptions)
PAYPAL_CLIENT_ID=your-paypal-client-id
PAYPAL_CLIENT_SECRET=your-paypal-client-secret
PAYPAL_MODE=sandbox    # Use 'live' for production

# SendGrid Email (Required for password reset)
SENDGRID_API_KEY=your-sendgrid-api-key
FROM_EMAIL=noreply@yourdomain.com
FRONTEND_RESET_URL=http://localhost:8006/reset-password

# CORS
CORS_ALLOW_ALL=true    # Set to 'false' in production
CORS_ORIGINS=http://localhost:8006
```

---

## 🛠️ Commands Reference

### Backend Commands

```bash
# Navigate to backend
cd backend

# Activate virtual environment
venv\Scripts\activate        # Windows
source venv/bin/activate     # Linux/Mac

# Install dependencies
pip install -r requirements.txt

# Run database migrations
alembic upgrade head

# Create new migration (after model changes)
alembic revision --autogenerate -m "description"

# Check current migration
alembic current

# Start development server
python main.py

# Start production server (with gunicorn)
gunicorn main:app -w 4 -k uvicorn.workers.UvicornWorker -b 0.0.0.0:8091
```

### Frontend Commands

```bash
# Navigate to frontend
cd frontend

# Install dependencies
npm install

# Start development server
npm run dev

# Build for production
npm run build

# Start production server
npm start

# Lint code
npm run lint
```

### Database Commands

```bash
# Create PostgreSQL database
psql -U postgres -c "CREATE DATABASE legal_ops_db;"

# Run migrations
cd backend
alembic upgrade head

# Rollback last migration
alembic downgrade -1

# Reset database (dangerous!)
alembic downgrade base
alembic upgrade head
```

---

## 🚢 Production Deployment

### Using PM2

```bash
# Backend
cd backend
source venv/bin/activate
pm2 start "gunicorn main:app -w 4 -k uvicorn.workers.UvicornWorker -b 0.0.0.0:8091" --name legal-ops-backend

# Frontend
cd frontend
npm run build
pm2 start npm --name legal-ops-frontend -- start
```

### Using Systemd

Create `/etc/systemd/system/legal-ops-backend.service`:

```ini
[Unit]
Description=Legal-Ops Backend
After=network.target

[Service]
User=www-data
WorkingDirectory=/path/to/Legal-Ops/backend
Environment="PATH=/path/to/Legal-Ops/backend/venv/bin"
ExecStart=/path/to/Legal-Ops/backend/venv/bin/gunicorn main:app -w 4 -k uvicorn.workers.UvicornWorker -b 0.0.0.0:8091
Restart=always

[Install]
WantedBy=multi-user.target
```

```bash
sudo systemctl enable legal-ops-backend
sudo systemctl start legal-ops-backend
```

---

## ✨ Features

### 🤖 15 Specialized AI Agents

| Workflow | Agents | Description |
|----------|--------|-------------|
| **Intake** | 5 | Document upload, OCR, translation, structuring, risk scoring |
| **Drafting** | 5 | Issue planning, templates, Malay drafting, English companion, QA |
| **Research** | 2 | Case law search, argument building |
| **Evidence** | 3 | Evidence packets, translation cert, hearing prep |

### 💳 Payment System

- **Freemium Model**: 1 free use per workflow
- **PayPal Integration**: One-time payments and subscriptions
- **Payment Gate**: Automatic 402 response when limit reached
- **Webhooks**: Automatic subscription status updates

### 🔐 Authentication

- **Apex Framework v0.3.24**: Custom auth module
- **JWT Tokens**: Access and refresh tokens
- **Password Reset**: SendGrid email integration
- **User Management**: Full CRUD operations

---

## 📁 Project Structure

```
Legal-Ops/
├── backend/
│   ├── apex/               # Custom auth/payments module
│   │   ├── auth.py         # Authentication functions
│   │   ├── email.py        # SendGrid integration
│   │   ├── models.py       # User, Subscription models
│   │   └── payments.py     # PayPal integration
│   ├── agents/             # 15 AI agents
│   ├── orchestrator/       # LangGraph workflows
│   ├── routers/            # API endpoints
│   ├── models/             # Database models
│   ├── alembic/            # Database migrations
│   └── main.py             # FastAPI app
├── frontend/
│   ├── app/                # Next.js pages
│   │   ├── login/          # Login page
│   │   ├── signup/         # Signup page
│   │   ├── forgot-password/# Password reset request
│   │   ├── reset-password/ # Password reset form
│   │   ├── dashboard/      # Main dashboard
│   │   ├── pricing/        # Subscription plans
│   │   └── ...
│   ├── components/         # Reusable UI components
│   └── lib/                # API clients, stores
└── DEPLOYMENT_REPORT.md    # Full deployment guide
```

---

## 🔗 API Endpoints

| Category | Endpoint | Method |
|----------|----------|--------|
| **Auth** | `/api/auth/signup` | POST |
| | `/api/auth/login` | POST |
| | `/api/auth/me` | GET |
| | `/api/auth/forgot-password` | POST |
| | `/api/auth/reset-password` | POST |
| **Subscription** | `/api/subscription/usage/status` | GET |
| | `/api/subscription/check/{workflow}` | GET |
| | `/api/subscription/activate` | POST |
| **Payments** | `/api/payments/orders/create` | POST |
| | `/api/payments/orders/{id}/capture` | POST |
| **Webhooks** | `/api/webhooks/paypal` | POST |
| **Workflows** | `/api/matters/intake` | POST |
| | `/api/matters/{id}/draft` | POST |
| | `/api/research/build-argument` | POST |
| | `/api/evidence/build` | POST |

---

## 📖 Documentation

- **API Docs**: http://localhost:8091/docs
- **Deployment Guide**: [DEPLOYMENT_REPORT.md](./DEPLOYMENT_REPORT.md)

---

**Built with ❤️ for Malaysian legal professionals**  
*Last updated: 2024-12-26*

# Port Configuration Updated

## New Ports

- **Backend**: Port 8005 (changed from 8000)
- **Frontend**: Port 8006 (changed from 3000)

## Updated Files

1. **Backend**:
   - `backend/main.py` - Changed uvicorn port to 8005
   - `backend/.env` - Updated CORS_ORIGINS to http://localhost:8006

2. **Frontend**:
   - `frontend/package.json` - Updated dev and start scripts to use port 8006
   - `frontend/.env.local` - Updated NEXT_PUBLIC_API_URL to http://localhost:8005

## How to Run

**Backend**:
```bash
cd backend
python main.py
```
Server will start on: http://localhost:8005

**Frontend**:
```bash
cd frontend
npm run dev
```
Server will start on: http://localhost:8006

## Access Points

- **Frontend**: http://localhost:8006
- **Backend API**: http://localhost:8005
- **API Documentation**: http://localhost:8005/docs
- **Health Check**: http://localhost:8005/health

All configurations have been updated to use the new ports!

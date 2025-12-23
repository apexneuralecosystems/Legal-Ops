# ============================================
# SIMPLIFIED API SETUP - ONLY 1 API KEY NEEDED!
# ============================================

## ⭐ ONLY REQUIRED API KEY

### Google Gemini API (FREE)
**Purpose**: Powers EVERYTHING - LLM agents AND translation!
- Entity extraction, legal drafting, issue planning
- Malay ↔ English translation (no separate translation API needed!)

**How to Get**:
1. Visit: https://makersuite.google.com/app/apikey
2. Sign in with Google account
3. Click "Create API Key"
4. Copy the key

**Add to `backend/.env`**:
```bash
GEMINI_API_KEY=your_gemini_api_key_here
GEMINI_MODEL=gemini-2.0-flash-exp
TRANSLATION_SERVICE=gemini
```

**Cost**: FREE (60 requests/min)

---

## Required Software (Free)

### 1. PostgreSQL Database
**Already configured!** Just create the database:
```bash
createdb law_agent_db
```

Your credentials are already in `.env.example`:
```bash
DATABASE_URL=postgresql://postgres:Rahul@123@127.0.0.1:5432/law_agent_db
```

### 2. Tesseract OCR
**Download**: https://github.com/UB-Mannheim/tesseract/wiki

**Windows Installation**:
1. Download installer
2. Install to: `C:\Program Files\Tesseract-OCR`
3. Add to `.env`:
```bash
TESSERACT_CMD=C:\\Program Files\\Tesseract-OCR\\tesseract.exe
```

---

## Complete .env Configuration

Copy `backend/.env.example` to `backend/.env` and update:

```bash
# ============================================
# DATABASE (Already configured)
# ============================================
DATABASE_URL=postgresql://postgres:Rahul@123@127.0.0.1:5432/law_agent_db
DB_HOST=127.0.0.1
DB_PORT=5432
DB_NAME=law_agent_db
DB_USER=postgres
DB_PASSWORD=Rahul@123

# ============================================
# GOOGLE GEMINI (ONLY API KEY NEEDED!)
# ============================================
GEMINI_API_KEY=your_gemini_api_key_here
GEMINI_MODEL=gemini-2.0-flash-exp

# ============================================
# TRANSLATION (Uses Gemini - No extra key!)
# ============================================
TRANSLATION_SERVICE=gemini

# ============================================
# OCR CONFIGURATION
# ============================================
TESSERACT_CMD=C:\\Program Files\\Tesseract-OCR\\tesseract.exe
OCR_LANGUAGES=eng+msa

# ============================================
# STORAGE
# ============================================
STORAGE_TYPE=local
UPLOAD_DIR=./uploads
MAX_UPLOAD_SIZE=52428800

# ============================================
# SECURITY
# ============================================
SECRET_KEY=your-secret-key-change-in-production
CORS_ORIGINS=http://localhost:3000

# ============================================
# FEATURES
# ============================================
ENABLE_PII_REDACTION=true
LOG_LEVEL=INFO
LOG_FILE=./logs/app.log
```

---

## Setup Checklist (5 Minutes!)

- [ ] **Get Gemini API Key** (2 min)
  - Visit: https://makersuite.google.com/app/apikey
  - Add to `backend/.env`

- [ ] **Install Tesseract** (2 min)
  - Download: https://github.com/UB-Mannheim/tesseract/wiki
  - Add path to `backend/.env`

- [ ] **Create Database** (1 min)
  ```bash
  createdb law_agent_db
  ```

- [ ] **Initialize & Run** (1 min)
  ```bash
  cd backend
  pip install -r requirements.txt
  python -c "from database import init_db; init_db()"
  python main.py
  ```

---

## Cost: $0/month (100% FREE!)

✅ Google Gemini: FREE (60 requests/min)
✅ PostgreSQL: FREE (self-hosted)
✅ Tesseract OCR: FREE (open-source)
✅ Translation: FREE (uses Gemini)

**Total: $0/month** 🎉

---

## What Changed?

**Before**: Needed 2 API keys (Gemini + Google Translate)
**Now**: Only 1 API key (Gemini does both!)

The Translation Agent now uses Gemini's multilingual capabilities for high-quality Malay ↔ English translation, eliminating the need for a separate Google Translate API subscription.

---

## Testing Your Setup

```bash
# Test configuration
cd backend
python -c "from config import settings; print('✅ Config loaded')"

# Test database
python -c "from database import init_db; init_db(); print('✅ Database ready')"

# Start server
python main.py
```

Visit http://localhost:8000/docs to see API documentation.

---

## Troubleshooting

### "GEMINI_API_KEY not found"
- Ensure `.env` file exists in `backend/` directory
- Copy from `.env.example`: `copy .env.example .env`
- Add your Gemini API key

### "Tesseract not found"
- Install from: https://github.com/UB-Mannheim/tesseract/wiki
- Update `TESSERACT_CMD` path in `.env`

### "Database connection failed"
- Ensure PostgreSQL is running
- Run: `createdb law_agent_db`
- Verify credentials in `.env`

---

## Next Steps

1. Get Gemini API key (only API key needed!)
2. Install Tesseract OCR
3. Create PostgreSQL database
4. Copy `.env.example` to `.env` and add your Gemini key
5. Run `python main.py`

You're ready! 🚀

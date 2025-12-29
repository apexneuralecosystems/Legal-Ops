# CommonLII Integration - Quick Start Guide

## Overview

Your Research Agent now connects to **live Malaysian legal cases** from CommonLII! 🎉

---

## Quick Start

### 1. Run the Test

```bash
python test_commonlii_simple.py
```

**Expected Output**: ✅ ALL TESTS PASSED

---

### 2. Start the Backend

```bash
cd backend
uvicorn app:app --reload --port 8091
```

---

### 3. Test the API

**Windows PowerShell**:
```powershell
Invoke-WebRequest -Uri "http://localhost:8091/research/search" `
  -Method POST `
  -Headers @{"Content-Type"="application/json"} `
  -Body '{"query":"breach of contract","filters":{}}'
```

**cURL**:
```bash
curl -X POST http://localhost:8091/research/search \
  -H "Content-Type: application/json" \
  -d '{"query":"breach of contract","filters":{}}'
```

---

## Features

✅ **Live Data** - Real Malaysian cases from CommonLII  
✅ **Multiple Courts** - Federal, Appeal, High Courts  
✅ **Smart Fallback** - Uses mock data if CommonLII unavailable  
✅ **Rate Limited** - Respectful 1 request/second  
✅ **Error Handling** - Automatic retries and graceful degradation

---

## Configuration

**Enable/Disable CommonLII** (optional):

Create/edit `.env` file in `backend/`:
```
USE_COMMONLII=true   # Use live CommonLII data (default)
# USE_COMMONLII=false  # Use mock data only
```

---

## Search Examples

```json
// Simple search
{
  "query": "breach of contract",
  "filters": {}
}

// Filter by court
{
  "query": "negligence",
  "filters": {
    "court": "federal"
  }
}

// Limit results
{
  "query": "employment",
  "filters": {
    "court": "appeal",
    "limit": 5
  }
}
```

---

## Response Format

```json
{
  "status": "success",
  "cases": [
    {
      "citation": "[2020] 1 MLJ 456",
      "title": "ABC Corp v XYZ Sdn Bhd",
      "court": "Federal Court",
      "year": 2020,
      "binding": true,
      "headnote_en": "Contract - Breach ...",
      "url": "http://www.commonlii.org/my/cases/..."
    }
  ],
  "total_results": 5,
  "data_source": "commonlii",  // or "mock"
  "live_data": true  // true if from CommonLII
}
```

---

## Troubleshooting

### "CommonLII search failed, falling back to mock data"

This is **normal** - the system automatically uses mock data when:
- CommonLII is down or slow
- Network connection issues
- Rate limit exceeded

### "No results found"

Try:
- Broader search terms ("contract" instead of "specific performance of contracts")
- Different court filters
- Check CommonLII is accessible: http://www.commonlii.org

---

## Files

- **Scraper**: `backend/services/commonlii_scraper.py`
- **Agent**: `backend/agents/research.py`
- **Test**: `test_commonlii_simple.py`
- **Docs**: See `implementation_plan.md` and `walkthrough.md`

---

## Support

For detailed documentation, see:
1. [`implementation_plan.md`](file:///C:/Users/rahul/.gemini/antigravity/brain/ff7a055a-a5e0-43ae-8094-3d274bade253/implementation_plan.md) - Technical implementation details
2. [`walkthrough.md`](file:///C:/Users/rahul/.gemini/antigravity/brain/ff7a055a-a5e0-43ae-8094-3d274bade253/walkthrough.md) - Complete implementation walkthrough
3. [`task.md`](file:///C:/Users/rahul/.gemini/antigravity/brain/ff7a055a-a5e0-43ae-8094-3d274bade253/task.md) - Implementation checklist

---

**Status**: ✅ Ready for Production  
**Last Updated**: 2025-12-03

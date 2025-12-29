# Frontend Integration Update - CommonLII Live Data

## Changes Made

### Backend Updates

#### 1. **orchestrator/controller.py**
- Added `data_source` and `live_data` fields to `WorkflowState` TypedDict
- Updated `_search_cases_node()` to pass through CommonLII metadata
- Research workflow now propagates live data indicators

#### 2. **routers/research.py**
- Updated `/research/search` endpoint to include:
  - `data_source`: "commonlii" | "mock" | "error"
  - `live_data`: boolean indicating if data is from CommonLII
- Enhanced error responses with data source information

### Frontend Updates

#### 3. **app/research/page.tsx**
- ✨ **Live Data Banner**: Animated green banner when using CommonLII
- ⚠️ **Mock Data Banner**: Yellow banner when falling back to mock data
- 🏷️ **Result Count Badge**: Shows "Live" or "Mock" indicator
- 🔗 **CommonLII Links**: Direct links to cases on CommonLII website
- 📊 **Enhanced case cards** with URL support

### Visual Features

**Live Data Indicator** (Green):
```
🟢 Live Data from CommonLII | Real Malaysian legal cases
```

**Mock Data Fallback** (Yellow):
```
🟡 Using Mock Data | CommonLII temporarily unavailable  
```

**Case Card Enhancements**:
- Citation with "View on CommonLII ↗" link
- Live/Mock badge in results header
- Clickable URLs that open in new tab

---

## API Response Structure

### Before
```json
{
  "status": "success",
  "cases": [...],
  "query": "breach of contract",
  "total_results": 5
}
```

### After (With CommonLII Integration)
```json
{
  "status": "success",
  "cases": [
    {
      "citation": "[2020] 1 MLJ 456",
      "title": "ABC Corp v XYZ Sdn Bhd",
      "court": "Federal Court",
      "url": "http://www.commonlii.org/my/cases/...",
      ...
    }
  ],
  "query": "breach of contract",
  "total_results": 5,
  "data_source": "commonlii",  // NEW
  "live_data": true            // NEW
}
```

---

## User Experience

### Scenario 1: CommonLII Available
1. User searches for "breach of contract"
2. Green banner appears: "Live Data from CommonLII"
3. Results show with "Live" badge
4. Each case has "View on CommonLII ↗" link
5. Clicking link opens full case in new tab

### Scenario 2: CommonLII Unavailable
1. User searches for "negligence"
2. Yellow banner appears: "Using Mock Data"
3. Results show with "Mock" badge
4. Cases load from local mock database
5. No URLs shown (mock data doesn't have URLs)

---

## Testing

### Manual Test Steps

1. **Start Backend**:
```bash
cd backend
uvicorn app:app --reload --port 8091
```

2. **Start Frontend**:
```bash
cd frontend
npm run dev
```

3. **Navigate to Research Page**:
```
http://localhost:3000/research
```

4. **Test Live Data**:
- Search: "breach of contract"
- Verify: Green "Live Data" banner appears
- Verify: Results have "Live" badge
- Verify: Can click "View on CommonLII ↗" links

5. **Test Fallback** (optional):
- Set `USE_COMMONLII=false` in backend/.env
- Restart backend
- Search again
- Verify: Yellow "Mock Data" banner appears
- Verify: Results have "Mock" badge

---

## Files Modified

### Backend (3 files)
- `backend/orchestrator/controller.py` - Workflow state management
- `backend/routers/research.py` - API response formatting
- `backend/agents/research.py` - Already updated (CommonLII integration)

### Frontend (1 file)
- `frontend/app/research/page.tsx` - UI indicators and badges

---

## Screenshots (Expected)

### Live Data View
```
┌─────────────────────────────────────────────────┐
│  Legal Research                                  │
│  Search Malaysian caselaw • Live data from CommonLII │
├─────────────────────────────────────────────────┤
│ 🟢 Live Data from CommonLII | Real Malaysian...│
├─────────────────────────────────────────────────┤
│  Search Results              5 cases [Live🟢]  │
│  ┌──────────────────────────────────────────┐ │
│  │ ABC Corp v XYZ Sdn Bhd                    │ │
│  │ [2020] 1 MLJ 456  View on CommonLII ↗    │ │
│  │ [Binding] [Federal Court]                 │ │
│  └──────────────────────────────────────────┘ │
└─────────────────────────────────────────────────┘
```

### Mock Data Fallback
```
┌─────────────────────────────────────────────────┐
│  Legal Research                                  │
│  Search Malaysian caselaw • Live data from CommonLII │
├─────────────────────────────────────────────────┤
│ 🟡 Using Mock Data | CommonLII temporarily...  │
├─────────────────────────────────────────────────┤
│  Search Results              3 cases [Mock]    │
│  ┌──────────────────────────────────────────┐ │
│  │ Sample Case v Another Case                │ │
│  │ [2019] 2 MLJ 345                          │ │
│  │ [Binding] [Court of Appeal]               │ │
│  └──────────────────────────────────────────┘ │
└─────────────────────────────────────────────────┘
```

---

## Benefits

✅ **Transparency**: Users know when they're getting live vs. mock data  
✅ **Reliability**: Automatic fallback ensures no service interruption  
✅ **Accessibility**: Direct links to full cases on CommonLII  
✅ **Visual Feedback**: Clear, color-coded indicators  
✅ **Professional**: Premium legal research tool appearance  

---

## Next Steps (Optional Enhancements)

1. **Statistics Dashboard**: Show CommonLII uptime/usage stats
2. **Preference Toggle**: Let users choose live vs. mock data
3. **Cache Indicator**: Show when results are from cache
4. **Download Feature**: Save cases as PDF directly from UI
5. **Citation Export**: Copy citations in various formats

---

**Status**: ✅ Complete  
**Last Updated**: 2025-12-03  
**Tested**: Ready for testing

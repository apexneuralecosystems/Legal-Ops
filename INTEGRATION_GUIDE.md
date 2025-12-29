# 🔗 Frontend-Backend Integration Guide

## System Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     USER INTERFACE                           │
│                  (Next.js - Port 8006)                       │
└──────────────────────┬──────────────────────────────────────┘
                       │ HTTP/REST API
                       │
┌──────────────────────▼──────────────────────────────────────┐
│                  FASTAPI BACKEND                             │
│                   (Port 8091)                                │
│  ┌────────────────────────────────────────────────────────┐ │
│  │              API Layer (Routers)                       │ │
│  │  - /api/matters/*    - /api/documents/*               │ │
│  └────────────┬───────────────────────────────────────────┘ │
│               │                                              │
│  ┌────────────▼───────────────────────────────────────────┐ │
│  │         Orchestration Controller                       │ │
│  │           (LangGraph Workflows)                        │ │
│  └────────────┬───────────────────────────────────────────┘ │
│               │                                              │
│  ┌────────────▼───────────────────────────────────────────┐ │
│  │              15 Specialized Agents                     │ │
│  │  - Document Collector  - OCR & Language                │ │
│  │  - Translation         - Case Structuring              │ │
│  │  - Risk Scoring        - Issue Planner                 │ │
│  │  - Template Compliance - Malay Drafting                │ │
│  │  - English Companion   - Consistency QA                │ │
│  │  - Research            - Argument Builder              │ │
│  │  - Translation Cert    - Evidence Builder              │ │
│  │  - Hearing Prep                                        │ │
│  └────────────┬───────────────────────────────────────────┘ │
│               │                                              │
│  ┌────────────▼───────────────────────────────────────────┐ │
│  │           Database Layer (PostgreSQL)                  │ │
│  │  - matters  - documents  - segments                    │ │
│  │  - pleadings  - research_cases  - audit_logs           │ │
│  └────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────┘
```

## Configuration

### Backend (.env)
```bash
# Server
PORT=8091
HOST=0.0.0.0

# Database
DATABASE_URL=postgresql://postgres:Rahul%40123@127.0.0.1:5432/law_agent_db

# Gemini API (for LLM and Translation)
GEMINI_API_KEY=AIzaSyAjhw0TWciHBnbUDLFNkB1tBRF37Bw4Xsg
GEMINI_MODEL=gemini-2.0-flash-exp
TRANSLATION_SERVICE=gemini

# CORS (allow frontend)
CORS_ORIGINS=http://localhost:8006,http://127.0.0.1:8006

# OCR
TESSERACT_CMD=C:\\Program Files\\Tesseract-OCR\\tesseract.exe
```

### Frontend (.env.local)
```bash
# Backend API URL
NEXT_PUBLIC_API_URL=http://localhost:8091
```

## API Endpoints

### Health & Info
- `GET /health` - Health check
- `GET /` - API information
- `GET /docs` - Swagger documentation

### Matters
- `GET /api/matters/` - List all matters
- `GET /api/matters/{id}` - Get matter details
- `POST /api/matters/intake` - Start intake workflow
- `POST /api/matters/{id}/draft` - Start drafting workflow
- `GET /api/matters/{id}/documents` - Get matter documents
- `GET /api/matters/{id}/parallel-view` - Get parallel text view

### Documents
- `POST /api/documents/upload` - Upload document
- `GET /api/documents/{id}` - Get document metadata
- `GET /api/documents/{id}/download` - Download document
- `GET /api/documents/{id}/preview` - Get OCR preview

## Frontend Pages

### 1. Dashboard (`/dashboard`)
**Component**: `app/dashboard/page.tsx`
**Features**:
- Lists all matters with filters
- Shows matter cards with risk scores
- Quick actions (view, draft, research)

**API Calls**:
```typescript
const { data: matters } = useQuery({
  queryKey: ['matters', status],
  queryFn: () => api.getMatters(status)
})
```

### 2. Upload Page (`/upload`)
**Component**: `app/upload/page.tsx`
**Features**:
- Drag-and-drop file upload
- Multiple file support
- Connector type selection
- Intake workflow trigger

**API Calls**:
```typescript
const mutation = useMutation({
  mutationFn: (formData: FormData) => api.startIntakeWorkflow(formData),
  onSuccess: (data) => {
    router.push(`/matters/${data.matter_id}`)
  }
})
```

### 3. Matter Details (`/matters/[id]`)
**Features**:
- Matter snapshot display
- Document list
- Risk scores visualization
- Action buttons (draft, research)

**API Calls**:
```typescript
const { data: matter } = useQuery({
  queryKey: ['matter', matterId],
  queryFn: () => api.getMatter(matterId)
})
```

### 4. Parallel Viewer (`/matters/[id]/parallel`)
**Component**: `components/ParallelViewer.tsx`
**Features**:
- Sentence-level Malay ↔ English alignment
- Confidence filtering
- Expandable details
- Flag/comment functionality

**API Calls**:
```typescript
const { data: segments } = useQuery({
  queryKey: ['parallel-view', matterId],
  queryFn: () => api.getParallelView(matterId)
})
```

### 5. Drafting Flow (`/matters/[id]/draft`)
**Component**: `components/DraftingFlow.tsx`
**Features**:
- 3-step wizard:
  1. Select issues & prayers
  2. Choose template
  3. Review dual-pane draft
- Malay/English side-by-side
- QA report display

**API Calls**:
```typescript
const mutation = useMutation({
  mutationFn: () => api.startDraftingWorkflow(matterId, {
    template_id,
    issues_selected,
    prayers_selected
  })
})
```

## Data Flow Examples

### Example 1: Upload Document → Matter Card

**Frontend**:
```typescript
// User uploads file
const formData = new FormData()
formData.append('files', file)
formData.append('connector_type', 'upload')

// Trigger intake workflow
const response = await api.startIntakeWorkflow(formData)
// Response: { matter_id: "MAT-xxx", workflow_result: {...} }

// Navigate to matter page
router.push(`/matters/${response.matter_id}`)
```

**Backend Workflow**:
1. Document Collector: Saves file → DOC-xxx
2. OCR Agent: Extracts text → segments
3. Translation: Creates parallel texts
4. Case Structuring: Extracts parties, court, issues
5. Risk Scoring: Calculates scores
6. Returns: Matter Card with MAT-xxx

### Example 2: Draft Pleading

**Frontend**:
```typescript
// User selects issues and prayers
const draftData = {
  template_id: "TPL-HighCourt-MS-v2",
  issues_selected: [{ id: "ISS-01", title: "Breach of contract" }],
  prayers_selected: [{ text_ms: "Penghakiman RM 500,000" }]
}

// Start drafting
const response = await api.startDraftingWorkflow(matterId, draftData)
// Response: { pleading_ms: {...}, pleading_en: {...}, qa_report: {...} }
```

**Backend Workflow**:
1. Issue Planner: Validates issues
2. Template Compliance: Selects template
3. Malay Drafting: Generates pleading
4. English Companion: Creates aligned English
5. Consistency QA: Verifies alignment
6. Returns: Bilingual pleading + QA report

## State Management

### React Query
```typescript
// Caching and automatic refetching
const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 5 * 60 * 1000, // 5 minutes
      cacheTime: 10 * 60 * 1000, // 10 minutes
    }
  }
})
```

### Zustand (Optional)
```typescript
// Global state for UI
const useStore = create((set) => ({
  currentMatter: null,
  setCurrentMatter: (matter) => set({ currentMatter: matter })
}))
```

## Error Handling

### Backend
```python
@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    return JSONResponse(
        status_code=500,
        content={
            "status": "error",
            "message": "Internal server error",
            "detail": str(exc)
        }
    )
```

### Frontend
```typescript
const mutation = useMutation({
  mutationFn: api.startIntakeWorkflow,
  onError: (error) => {
    toast.error(`Upload failed: ${error.message}`)
  },
  onSuccess: (data) => {
    toast.success(`Matter ${data.matter_id} created!`)
  }
})
```

## Testing Integration

### Test Backend API
```bash
cd backend
python test_apis.py
```

### Test Frontend (Manual)
1. Start backend: `cd backend && python main.py`
2. Start frontend: `cd frontend && npm run dev`
3. Open: http://localhost:8006
4. Upload test_case_demo.txt
5. Verify matter card created
6. Test drafting workflow

## Current Status

### ✅ Working
- Backend API (all 11 endpoints)
- Database schema
- All 15 agents
- Intake workflow
- Drafting workflow
- Risk scoring
- API testing script

### ⚠️ Pending
- Frontend npm install (package registry issues)
- WebSocket real-time updates
- Authentication
- Production deployment

## Troubleshooting

### Frontend won't start
```bash
# Clear npm cache
npm cache clean --force

# Install core packages only
npm install next@14.0.4 react@18.2.0 react-dom@18.2.0

# Start dev server
npm run dev
```

### Backend connection refused
```bash
# Check if running
netstat -ano | findstr :8091

# Restart backend
cd backend
python main.py
```

### CORS errors
- Verify `CORS_ORIGINS` in backend/.env includes frontend URL
- Check frontend is on port 8006
- Restart backend after .env changes

## Next Steps

1. **Fix Frontend Dependencies**: Resolve npm install issues
2. **Test Integration**: Upload → Matter Card → Draft flow
3. **Add WebSocket**: Real-time workflow progress
4. **Implement Auth**: User login/signup
5. **Deploy**: Docker containers + production config

---

**Integration Status**: Backend ✅ | Frontend ⚠️ (dependency issues)
**API Documentation**: http://localhost:8091/docs
**Test Results**: See API_TEST_RESULTS.md
**Workflow Details**: See AGENT_WORKFLOW.md

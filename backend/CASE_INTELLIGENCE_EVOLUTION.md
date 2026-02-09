# Case Intelligence Evolution System - Design

## Vision
Make doc chat **progressively smarter** about each case by:
1. Learning from every question asked
2. Building a knowledge graph of the case
3. Extracting insights automatically
4. Improving answer quality over time

---

## Phase 1: Conversation Memory (Quick Win) 🚀

### Database Schema Addition
```sql
-- Store chat history per matter
CREATE TABLE chat_messages (
    id VARCHAR(36) PRIMARY KEY,
    matter_id VARCHAR(36) REFERENCES matters(id),
    user_id VARCHAR(36),
    role VARCHAR(20), -- 'user' or 'assistant'
    message TEXT,
    context_used TEXT, -- Which documents were referenced
    confidence VARCHAR(20),
    helpful BOOLEAN, -- User feedback: thumbs up/down
    created_at TIMESTAMP DEFAULT NOW()
);

-- Index for fast retrieval
CREATE INDEX idx_chat_matter_time ON chat_messages(matter_id, created_at DESC);
```

### Implementation
**services/rag_service.py** - Add conversation memory:
```python
async def query(self, query_text: str, matter_id: Optional[str] = None, 
                conversation_id: Optional[str] = None, k: int = 5):
    # LOAD RECENT CONVERSATION HISTORY
    recent_context = ""
    if matter_id and conversation_id:
        from database import SessionLocal
        db = SessionLocal()
        
        # Get last 5 exchanges
        recent_msgs = db.query(ChatMessage).filter(
            ChatMessage.matter_id == matter_id,
            ChatMessage.conversation_id == conversation_id
        ).order_by(ChatMessage.created_at.desc()).limit(10).all()
        
        if recent_msgs:
            recent_context = "\n\n=== CONVERSATION HISTORY ===\n"
            for msg in reversed(recent_msgs):
                recent_context += f"{msg.role.upper()}: {msg.message}\n"
            recent_context += "=== END HISTORY ===\n\n"
        
        db.close()
    
    # Prepend conversation context to full_context_accumulated
    if recent_context:
        context_text = recent_context + context_text
```

**Benefits:**
- ✅ Follow-up questions work naturally ("What about the other defendant?")
- ✅ No need to re-explain context
- ✅ 2 hours implementation time

---

## Phase 2: Case Knowledge Graph (1 Week) 📊

### Auto-Extract Case Entities
After each chat session, extract structured data:

```python
# services/case_intelligence_service.py

class CaseIntelligenceService:
    async def extract_case_entities(self, matter_id: str):
        """Extract entities from all documents in matter"""
        
        prompt = f"""Analyze the case documents and extract:
        
        1. PARTIES:
           - Plaintiff(s) with roles
           - Defendant(s) with roles
           - Third parties
           
        2. KEY CLAIMS:
           - Amount claimed
           - Type of claim
           - Legal basis
           
        3. DEFENSES:
           - Each defense raised
           - Legal basis
           
        4. CRITICAL DATES:
           - Filing date
           - Incident date
           - Deadlines
           
        5. KEY DOCUMENTS:
           - Document type
           - Significance
           
        6. LEGAL ISSUES:
           - Primary issues
           - Applicable laws
           
        Return as JSON structure.
        
        Documents:
        {full_document_text}
        """
        
        # Extract structured data
        result = await llm.generate(prompt)
        
        # Store in case_entities table
        # ...
```

### Database Schema
```sql
CREATE TABLE case_entities (
    id VARCHAR(36) PRIMARY KEY,
    matter_id VARCHAR(36) REFERENCES matters(id),
    entity_type VARCHAR(50), -- 'party', 'claim', 'defense', 'date', 'issue'
    entity_name VARCHAR(500),
    entity_value TEXT, -- JSON with details
    confidence FLOAT,
    source_document VARCHAR(100),
    extracted_at TIMESTAMP,
    verified_by_user BOOLEAN DEFAULT false
);

CREATE TABLE case_relationships (
    id VARCHAR(36) PRIMARY KEY,
    matter_id VARCHAR(36),
    entity_1_id VARCHAR(36) REFERENCES case_entities(id),
    entity_2_id VARCHAR(36) REFERENCES case_entities(id),
    relationship_type VARCHAR(100), -- 'claims_against', 'defended_by', 'relies_on'
    confidence FLOAT,
    created_at TIMESTAMP
);
```

### Enhanced RAG Query
```python
async def query(self, query_text: str, matter_id: str):
    # STEP 1: Load case knowledge graph
    case_entities = self._load_case_entities(matter_id)
    
    # STEP 2: Identify query intent
    intent = await self._classify_query_intent(query_text)
    # e.g., "amount_query", "party_query", "timeline_query", "defense_query"
    
    # STEP 3: Retrieve relevant entities first
    relevant_entities = self._filter_entities_by_intent(case_entities, intent)
    
    # STEP 4: Build enhanced context
    enhanced_context = f"""
CASE KNOWLEDGE GRAPH:
{self._format_entities(relevant_entities)}

RELEVANT DOCUMENT EXCERPTS:
{full_context_accumulated}
"""
    
    # STEP 5: Generate answer with structured knowledge
    answer = await llm.generate(prompt_with_enhanced_context)
```

**Benefits:**
- ✅ Instant answers for structured queries ("What's the claim amount?")
- ✅ Better understanding of case relationships
- ✅ Progressive refinement as user corrects extractions

---

## Phase 3: Learning from Feedback (3 Days) 👍👎

### Capture User Feedback
```python
# routers/paralegal.py

@router.post("/chat/feedback")
async def chat_feedback(
    message_id: str,
    helpful: bool,
    correction: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """User rates answer quality"""
    
    msg = db.query(ChatMessage).filter(ChatMessage.id == message_id).first()
    msg.helpful = helpful
    msg.user_correction = correction
    
    # If user provided correction, extract learnings
    if correction and not helpful:
        await case_intel.learn_from_correction(
            matter_id=msg.matter_id,
            original_answer=msg.message,
            correction=correction,
            query=msg.parent_query
        )
    
    db.commit()
```

### Store Corrections as Case Notes
```sql
CREATE TABLE case_learnings (
    id VARCHAR(36) PRIMARY KEY,
    matter_id VARCHAR(36),
    learning_type VARCHAR(50), -- 'correction', 'clarification', 'new_fact'
    original_text TEXT,
    corrected_text TEXT,
    importance INT, -- 1-5 scale
    created_at TIMESTAMP
);
```

### Apply Learnings in Future Queries
```python
async def query(self, query_text: str, matter_id: str):
    # Load user corrections/clarifications
    learnings = db.query(CaseLearning).filter(
        CaseLearning.matter_id == matter_id,
        CaseLearning.importance >= 3
    ).all()
    
    if learnings:
        corrections_context = "\n\n=== IMPORTANT CLARIFICATIONS ===\n"
        for learning in learnings:
            corrections_context += f"- {learning.corrected_text}\n"
        corrections_context += "=== END CLARIFICATIONS ===\n\n"
        
        context_text = corrections_context + context_text
```

**Benefits:**
- ✅ System learns from mistakes
- ✅ User corrections become permanent knowledge
- ✅ Answer accuracy improves over time

---

## Phase 4: Insight Generation (2 Weeks) 🧠

### Automated Case Analysis
Run periodically or on-demand:

```python
class CaseInsightEngine:
    async def generate_case_insights(self, matter_id: str):
        """Generate strategic insights from case data"""
        
        insights = []
        
        # 1. Strength/Weakness Analysis
        swot = await self._analyze_case_swot(matter_id)
        insights.append({
            'type': 'swot_analysis',
            'data': swot,
            'confidence': 0.85
        })
        
        # 2. Risk Assessment
        risks = await self._assess_case_risks(matter_id)
        insights.append({
            'type': 'risk_assessment',
            'data': risks,
            'confidence': 0.78
        })
        
        # 3. Timeline Gap Detection
        timeline = await self._build_case_timeline(matter_id)
        gaps = self._detect_timeline_gaps(timeline)
        insights.append({
            'type': 'timeline_gaps',
            'data': gaps,
            'confidence': 0.92
        })
        
        # 4. Missing Evidence Detection
        required_evidence = await self._identify_required_evidence(matter_id)
        available_evidence = self._list_available_evidence(matter_id)
        missing = set(required_evidence) - set(available_evidence)
        
        insights.append({
            'type': 'evidence_gaps',
            'data': missing,
            'confidence': 0.80
        })
        
        # Store in database
        await self._store_insights(matter_id, insights)
        
        return insights
```

### Display Insights in UI
```typescript
// frontend/components/CaseInsights.tsx

export function CaseInsights({ matterId }: { matterId: string }) {
  const { data: insights } = useQuery(['case-insights', matterId], 
    () => fetchCaseInsights(matterId)
  )
  
  return (
    <div className="case-insights-panel">
      <h3>Case Intelligence</h3>
      
      <InsightCard type="strength_analysis" data={insights.swot} />
      <InsightCard type="risks" data={insights.risks} />
      <InsightCard type="evidence_gaps" data={insights.gaps} />
      <InsightCard type="suggested_actions" data={insights.actions} />
    </div>
  )
}
```

**Benefits:**
- ✅ Proactive case analysis
- ✅ Identifies weak points automatically
- ✅ Suggests strategic actions

---

## Phase 5: Collaborative Learning (Advanced) 🤝

### Cross-Case Learning
```python
class CrossCaseLearning:
    async def learn_from_similar_cases(self, matter_id: str):
        """Learn patterns from similar past cases"""
        
        # 1. Find similar cases (by type, jurisdiction, legal issues)
        similar_cases = await self._find_similar_cases(matter_id, limit=5)
        
        # 2. Extract common patterns
        patterns = []
        for case in similar_cases:
            if case.outcome:
                pattern = await self._extract_success_pattern(case)
                patterns.append(pattern)
        
        # 3. Apply insights to current case
        recommendations = await self._generate_recommendations(
            current_case=matter_id,
            learned_patterns=patterns
        )
        
        return recommendations
```

### Database Schema
```sql
CREATE TABLE case_patterns (
    id VARCHAR(36) PRIMARY KEY,
    pattern_type VARCHAR(100), -- 'successful_defense', 'winning_argument', 'settlement_trigger'
    description TEXT,
    frequency INT, -- How many cases this appeared in
    success_rate FLOAT, -- 0.0 to 1.0
    applicable_to JSON, -- Case types where this applies
    created_at TIMESTAMP
);
```

**Benefits:**
- ✅ Learn from historical cases
- ✅ Suggest strategies that worked before
- ✅ Predict likely outcomes

---

## Implementation Priority

### Week 1 (Quick Wins)
1. ✅ Conversation memory (2 hours)
2. ✅ User feedback system (1 day)
3. ✅ Basic entity extraction (2 days)

### Week 2-3 (Knowledge Graph)
4. Complete entity/relationship extraction
5. Build query intent classifier
6. Implement enhanced context building

### Week 4-5 (Intelligence)
7. Automated insight generation
8. Risk assessment
9. Evidence gap detection

### Month 2+ (Advanced)
10. Cross-case learning
11. Predictive analytics
12. Strategy recommendations

---

## Measurement Metrics

Track improvement over time:
```sql
CREATE TABLE case_intelligence_metrics (
    matter_id VARCHAR(36),
    metric_date DATE,
    
    -- Accuracy metrics
    answer_helpful_rate FLOAT, -- % of thumbs up
    correction_rate FLOAT, -- % requiring corrections
    
    -- Knowledge metrics
    entities_extracted INT,
    entities_verified INT,
    relationships_mapped INT,
    
    -- Usage metrics
    questions_answered INT,
    avg_confidence FLOAT,
    unique_insights INT,
    
    PRIMARY KEY (matter_id, metric_date)
);
```

---

## Example: Before vs After

### BEFORE (Current)
```
User: "What defenses do we have?"
AI: [Searches all 127 chunks every time]
AI: "The defendants raise 6 defenses: coercion, pressure..."
```

### AFTER (Evolved)
```
User: "What defenses do we have?"
AI: [Loads case knowledge graph instantly]
AI: "Based on our case knowledge graph, defendants raise 6 defenses:

STRONG DEFENSES (High likelihood of success):
• Additional Agreement defense (83% confidence based on evidence)
• Commercial conspiracy claim (67% confidence, similar to Case XYZ)

MODERATE DEFENSES:
• Pressure/coercion defense (45% confidence, lacks corroboration)

WEAK DEFENSES:
• Misunderstanding guarantee (22% confidence, contradicted by evidence)

STRATEGIC RECOMMENDATION:
Focus on strengthening the Additional Agreement defense by obtaining:
- Bank statements from Kempas Project period
- Email correspondence with ITMAX
- Project timeline documentation

Similar cases: ABC v XYZ (2024) - Settlement after Additional Agreement evidence
```

---

## Technical Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                      USER QUERY                              │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────┐
│              QUERY ORCHESTRATOR                              │
│  • Load conversation history                                 │
│  • Load case knowledge graph                                 │
│  • Load user corrections/learnings                           │
│  • Classify query intent                                     │
└──────────────────────┬──────────────────────────────────────┘
                       │
        ┌──────────────┼──────────────┬──────────────┐
        ▼              ▼              ▼              ▼
┌──────────────┐ ┌──────────┐ ┌──────────────┐ ┌──────────┐
│ Knowledge    │ │ Document │ │ Conversation │ │ Case     │
│ Graph        │ │ Chunks   │ │ History      │ │ Insights │
│ (Entities &  │ │ (OCR)    │ │ (Past Q&A)   │ │ (Auto-   │
│ Relations)   │ │          │ │              │ │ generated)│
└──────┬───────┘ └────┬─────┘ └──────┬───────┘ └─────┬────┘
       │              │               │               │
       └──────────────┴───────────────┴───────────────┘
                       │
                       ▼
         ┌────────────────────────────┐
         │    CONTEXT BUILDER         │
         │  Merge all sources into    │
         │  optimal context for LLM   │
         └──────────┬─────────────────┘
                    │
                    ▼
         ┌────────────────────────────┐
         │    LLM (Gemini 1.5 Pro)    │
         │  Generate answer with      │
         │  full case intelligence    │
         └──────────┬─────────────────┘
                    │
                    ▼
         ┌────────────────────────────┐
         │    POST-PROCESSING         │
         │  • Store in chat history   │
         │  • Update entity confidence│
         │  • Extract new learnings   │
         │  • Generate follow-up Qs   │
         └────────────────────────────┘
```

---

## Get Started Now

1. **Create database migrations** for new tables
2. **Add conversation_id** to chat API
3. **Implement basic memory** (Phase 1)
4. **Add thumbs up/down UI** (Phase 3)
5. **Schedule entity extraction** nightly (Phase 2)

Would you like me to implement Phase 1 (Conversation Memory) right now?

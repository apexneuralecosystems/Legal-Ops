# Complete System Architecture: Agents & Folder Structure

## 📁 FOLDER STRUCTURE EXPLAINED

### 🔷 `/backend` - Main Application Root
The core of the Malaysian Legal AI system. Contains all server-side logic, APIs, and processing pipelines.

---

### 🤖 `/backend/agents` - Specialized AI Agents (19 Agents)

**Purpose:** Each agent is a specialized AI module that performs one specific legal task. They can work independently or in orchestrated workflows.

#### **1. base_agent.py** - Foundation Class
- **What it does:** Parent class for all agents
- **Key features:**
  - Metadata generation (agent_id, timestamp, version)
  - Source reference tracking
  - Confidence scoring framework
  - Human review flag logic
  - Standard input/output validation
- **Used by:** All other agents inherit from this

#### **2. legal_research_agent.py** - Legal Research with Tool Calling (505 lines)
- **What it does:** Orchestrates multi-source legal research using LangChain tools
- **Tools it uses:**
  - `search_uploaded_docs`: Query RAG vector store
  - `search_lexis`: Search Lexis Advance Malaysia for case law
  - `search_legislation`: Query Malaysian legislation database
  - `search_clj`: Search CLJ database (planned)
- **Use cases:**
  - "Find cases about breach of contract with specific performance"
  - "What does the Contracts Act say about consideration?"
- **LLM:** OpenAI GPT-4 with function calling

#### **3. devils_advocate_agent.py** - Cross-Examination Analysis (197 lines)
- **What it does:** **Automatically challenges** your legal position like opposing counsel would
- **Outputs 5 components:**
  1. **Contractual Defenses Table** - What the other side will argue
  2. **Evidentiary Gaps** - Missing documents/testimony you need
  3. **Cross-Examination Questions** - Questions opposing counsel will ask
  4. **Strategic Recommendations** - How to fix vulnerabilities
  5. **Opposing Strategy Prediction** - What motions/defenses they'll file
- **Use case:** "I want to sue for RM 5M. What are my weaknesses?"
- **LLM:** GPT-4 (simulates senior litigation partner)

#### **4. case_strength.py** - AI Win Probability Predictor (210 lines)
- **What it does:** Predicts your chances of winning
- **Outputs:**
  - Win probability (0-100%)
  - Risks (weaknesses in your case)
  - Strengths (advantages you have)
  - Suggestions (how to improve your position)
  - Overall assessment
- **Use case:** "What are my chances in this contract dispute?"
- **LLM:** Gemini 1.5 Pro (analyzes all case data)

#### **5. ocr_language.py** - OCR & Language Detection (486 lines)
- **What it does:** Converts PDFs/images to searchable text + detects language
- **Process:**
  1. Extract text using Tesseract OCR or Google Vision API
  2. Segment text into paragraphs
  3. Detect language per segment (Malay/English/mixed)
  4. Calculate confidence scores
- **Outputs:** Segments with `{text, language, confidence, page, position}`
- **Use case:** Uploaded scanned court document → searchable text
- **Technologies:** Tesseract, Google Vision API, langdetect

#### **6. translation.py** - Legal Translation (206 lines)
- **What it does:** Translates Malay ↔ English preserving legal terminology
- **Modes:**
  - **Literal:** Word-for-word translation
  - **Idiomatic:** Natural legal phrasing
  - **Both:** Provides both versions
- **Features:**
  - Preserves legal terms (plaintif, defendan, mahkamah)
  - Alignment scoring
  - Parallel text output
- **Use case:** Translate Malay contract into English for analysis
- **LLM:** Gemini 1.5 Pro (legal translation specialist)

#### **7. translation_certification.py** - Sworn Translator Affidavit Generator
- **What it does:** Creates translator's affidavit for court submission
- **Outputs:**
  - Affidavit text (English + Malay)
  - Declaration of accuracy
  - Translator credentials
  - Document mapping
- **Use case:** Need certified translation for court filing
- **Complies with:** Malaysian court requirements

#### **8. case_structuring.py** - Entity Extraction (279 lines)
- **What it does:** Extracts structured data from unstructured legal documents
- **Extracts:**
  - Parties (plaintiffs, defendants, witnesses)
  - Court (name, location, level)
  - Dates (filing, hearing, deadlines)
  - Issues (legal questions to be decided)
  - Remedies (what plaintiff wants)
  - Amounts (claim amounts, damages)
- **Output:** JSON "matter_snapshot" with all entities
- **Use case:** Upload contract → automatically extract parties and amounts
- **LLM:** Gemini 1.5 Pro (entity recognition)

#### **9. risk_scoring.py** - Risk & Complexity Analyzer (341 lines)
- **What it does:** Scores case on 4 risk dimensions (1-5 scale)
- **Scores:**
  1. **Jurisdictional Complexity** (High Court = 4, Federal Court = 5)
  2. **Language Complexity** (Mixed Malay/English = higher risk)
  3. **Volume Risk** (More documents = more work)
  4. **Time Pressure** (Deadline approaching = higher urgency)
- **Output:** Composite risk score + rationale
- **Use case:** "How complex is this case?" → Score: 3.8/5 (High complexity)

#### **10. issue_planner.py** - Legal Issue Planner
- **What it does:** Structures legal arguments into formal issues
- **Process:**
  1. Identifies all legal questions
  2. Orders by importance
  3. Maps to legal principles
  4. Suggests prayers (relief sought)
- **Output:** Structured issue list with citations
- **Use case:** "I have a breach of contract. What issues should I plead?"

#### **11. template_compliance.py** - Court Template Validator
- **What it does:** Ensures pleadings comply with court templates
- **Checks:**
  - Required sections present
  - Correct numbering
  - Mandatory statements included
  - Format compliance
- **Templates:** High Court, Sessions Court, Magistrates' Court
- **Use case:** Validate draft pleading before filing

#### **12. malay_drafting.py** - Malay Legal Drafting (271 lines)
- **What it does:** Generates formal Malay pleadings (Pernyataan Tuntutan, Pembelaan)
- **Features:**
  - Uses court templates
  - Formal Malay legal language
  - Auto-numbering paragraphs
  - Maps paragraphs to source segments
- **Output:** Full Malay pleading ready for filing
- **LLM:** Gemini 1.5 Pro (trained on Malaysian legal Malay)

#### **13. english_companion.py** - English Legal Drafting
- **What it does:** Generates English pleadings or translates Malay pleadings
- **Modes:**
  - Draft from scratch (for Federal Court)
  - Translate Malay pleading to English
- **Output:** Professional English legal document
- **Use case:** High Court requires Malay, but lawyer needs English notes

#### **14. argument_builder.py** - Bilingual Issue Memo (253 lines)
- **What it does:** Drafts legal arguments with case citations
- **Process:**
  1. Takes legal issues
  2. Finds relevant cases
  3. Drafts analysis in English
  4. Translates to Malay
  5. Suggests wording for submissions
- **Output:** Issue memo (EN + MS) with citations
- **Use case:** "Draft argument for breach of contract issue"

#### **15. evidence_builder.py** - Evidence Bundle Creator (224 lines)
- **What it does:** Creates court evidence bundle with index
- **Components:**
  - Document index
  - Version history
  - Translator affidavits
  - PDF assembly plan
- **Output:** Tabbed evidence bundle ready for filing
- **Use case:** "Prepare all evidence for trial"

#### **16. hearing_prep.py** - Hearing Preparation (385 lines)
- **What it does:** Prepares everything needed for court hearing
- **Outputs:**
  - **Hearing bundle** (tabbed structure)
  - **Oral submission script** (Malay with English notes)
  - **"If Judge Asks" FAQs** (anticipated questions + answers)
  - **Case citations** (quick reference)
- **Use case:** "Hearing tomorrow, need oral submission script"
- **LLM:** Gemini 1.5 Pro (generates contextual scripts)

#### **17. document_collector.py** - File Ingestion
- **What it does:** Collects documents from various sources
- **Sources:**
  - User uploads
  - Email attachments
  - Cloud storage
  - Case management systems
- **Output:** Document manifest with metadata

#### **18. consistency_qa.py** - Quality Assurance
- **What it does:** Checks pleading for inconsistencies
- **Checks:**
  - Party names consistent
  - Dates don't conflict
  - Amounts match
  - Citations valid
  - Malay/English versions aligned
- **Output:** QA report with issues flagged

#### **19. english_companion.py** - English Companion Drafter
- **What it does:** Creates English version of Malay pleadings
- **Features:**
  - Preserves legal structure
  - Maintains paragraph numbering
  - Adds explanatory notes
- **Use case:** Malay is official, but client/foreign counsel needs English

---

### 🎭 `/backend/orchestrator` - Workflow Controller

**Purpose:** Coordinates multiple agents in sequential/parallel workflows using LangGraph.

#### **controller.py** (845 lines) - Main Orchestrator
**What it does:** Routes work through agent chains based on workflow type

**5 Main Workflows:**

1. **INTAKE WORKFLOW** (Document Processing)
   ```
   DocumentCollector → OCRLanguage → Translation → 
   CaseStructuring → RiskScoring
   ```
   - **Input:** Uploaded PDF/image
   - **Output:** Structured case data + risk scores
   - **Use case:** Client sends contract → extract parties, dates, amounts

2. **DRAFTING WORKFLOW** (Pleading Generation)
   ```
   IssuePlanner → TemplateCompliance → MalayDrafting → 
   EnglishCompanion → ConsistencyQA
   ```
   - **Input:** Case facts + template type
   - **Output:** Court-ready Malay + English pleadings
   - **Use case:** "Draft Statement of Claim for breach of contract"

3. **RESEARCH WORKFLOW** (Legal Research)
   ```
   LegalResearchAgent → ArgumentBuilder
   ```
   - **Input:** Legal question
   - **Output:** Cases + analysis + suggested wording
   - **Use case:** "Find cases about specific performance remedies"

4. **EVIDENCE WORKFLOW** (Trial Preparation)
   ```
   TranslationCertification → EvidenceBuilder → HearingPrep
   ```
   - **Input:** Documents + pleadings
   - **Output:** Evidence bundle + hearing materials
   - **Use case:** "Prepare for trial next week"

5. **ANALYSIS WORKFLOW** (Case Assessment)
   ```
   CaseStrength → DevilsAdvocate
   ```
   - **Input:** Case data
   - **Output:** Win probability + vulnerabilities + recommendations
   - **Use case:** "Should I take this case to trial?"

---

### 🔧 `/backend/services` - Core Services (17 Services)

**Purpose:** Reusable business logic and integrations. Used by agents and routers.

#### **1. llm_service.py** - AI Language Model Interface
- **What it does:** Unified interface to Gemini 1.5 Pro
- **Features:**
  - Streaming responses
  - Context window management (2M tokens)
  - Error handling & retries
  - Token counting
- **Used by:** All agents that need LLM

#### **2. rag_service.py** - Retrieval Augmented Generation
- **What it does:** "Long Context Strategy" - loads ALL case documents
- **Process:**
  1. User asks question
  2. Load conversation history (Phase 1)
  3. Load case learnings (Phase 1)
  4. Load knowledge graph entities (Phase 2)
  5. Load ALL document chunks
  6. Send everything to Gemini (2M context window)
- **Why not vector search?** Gemini's 2M context can hold entire case (~700k chars)
- **Phases integrated:** 1 (Memory) + 2 (Knowledge Graph) + 3 (Feedback)

#### **3. ocr_service.py** - OCR Processing
- **What it does:** Extracts text from PDFs/images
- **Technologies:**
  - Tesseract (local, fast, free)
  - Google Vision API (cloud, better accuracy)
- **Features:**
  - Page-by-page processing
  - Confidence scoring
  - Language detection per segment

#### **4. vision_ocr_service.py** - Google Vision Integration
- **What it does:** Enhanced OCR using Google Cloud Vision
- **Best for:** Scanned documents, handwriting, poor quality images
- **Features:**
  - Batch processing
  - Layout detection
  - Multi-language support

#### **5. enhanced_ocr_pipeline.py** - Advanced OCR Pipeline
- **What it does:** Full OCR workflow with post-processing
- **Steps:**
  1. Convert PDF to images
  2. OCR each page
  3. Segment into paragraphs
  4. Detect language
  5. Post-process (fix spacing, merge lines)
  6. Save to database
- **Output:** Searchable document chunks

#### **6. ocr_post_processor.py** - OCR Text Cleanup
- **What it does:** Fixes common OCR errors
- **Fixes:**
  - Broken words ("con tract" → "contract")
  - Missing spaces ("theparty" → "the party")
  - Wrong characters ("0" → "O", "1" → "I")
  - Legal term corrections

#### **7. ocr_embedding_service.py** - Vector Embeddings (Currently Bypassed)
- **What it does:** Creates semantic embeddings for vector search
- **Status:** Not used (Long Context Strategy instead)
- **Technology:** Would use ChromaDB + sentence transformers

#### **8. case_intelligence_service.py** - Knowledge Graph Extraction (Phase 2)
- **What it does:** Extracts entities and relationships from case documents
- **Extracts:**
  - **Entities:** Parties, claims, defenses, dates, issues, documents
  - **Relationships:** "claims_against", "defended_by", "relies_on"
- **Process:** LLM analyzes all document chunks → structured JSON
- **Storage:** `case_entities` and `case_relationships` tables

#### **9. case_insight_service.py** - Automated Insights (Phase 4)
- **What it does:** Generates 5 types of proactive insights
- **Insights:**
  1. **SWOT Analysis** (Strengths, Weaknesses, Opportunities, Threats)
  2. **Risk Assessment** (Critical/High/Medium/Low risks)
  3. **Evidence Gaps** (Missing contracts, witnesses, expert reports)
  4. **Timeline Analysis** (Deadline warnings, statute limitations)
  5. **Strategic Recommendations** (Priority-based action items)
- **Process:** LLM analyzes case + knowledge graph → 28 insights
- **Storage:** `case_insights` table

#### **10. cross_case_learning_service.py** - Pattern Recognition (Phase 5)
- **What it does:** Learns from historical similar cases
- **Features:**
  - **Similarity Matching** (finds similar past cases)
  - **Pattern Extraction** (identifies winning strategies)
  - **Outcome Prediction** (estimates success probability)
  - **Strategic Recommendations** (based on proven patterns)
- **Similarity Algorithm:**
  - Case type (40% weight)
  - Jurisdiction (20% weight)
  - Entities (30% weight)
  - Issues (10% weight)
- **Example:** "Strong documentary evidence = 100% success in similar cases"

#### **11. lexis_scraper.py** - Lexis Advance Malaysia Integration
- **What it does:** Searches Lexis database for case law
- **Features:**
  - Web scraping with Playwright
  - Session management
  - Case extraction
  - Citation parsing
- **Status:** Authentication challenges (Lexis blocks bots)

#### **12. commonlii_scraper.py** - CommonLII Scraper
- **What it does:** Scrapes free Malaysian case law from CommonLII
- **Features:**
  - No authentication needed
  - Full case text
  - Citation parsing
- **Use case:** Free alternative to Lexis

#### **13. agc_legislation_scraper.py** - AGC Legislation Scraper
- **What it does:** Scrapes Malaysian legislation from AGC website
- **Sources:**
  - Acts of Parliament
  - Subsidiary legislation
  - Rules of Court
- **Features:**
  - Section-by-section extraction
  - Amendment tracking

#### **14. browser_pool.py** - Playwright Browser Management
- **What it does:** Manages headless browsers for web scraping
- **Features:**
  - Connection pooling
  - Session persistence
  - Error handling
  - Cleanup on shutdown

#### **15. email_service.py** - Email Notifications
- **What it does:** Sends emails via SendGrid
- **Use cases:**
  - Account verification
  - Password reset
  - Case updates
  - Deadline reminders

#### **16. logging_service.py** - Centralized Logging
- **What it does:** Structured logging with rotation
- **Logs:**
  - API requests
  - Agent execution
  - Errors
  - Performance metrics

#### **17. usage_tracker.py** - Subscription Usage Tracking
- **What it does:** Tracks API usage per user
- **Tracks:**
  - Chat queries
  - Document uploads
  - Pages OCR'd
  - AI tasks executed
- **Enforces:** Plan limits (Starter/Professional/Enterprise)

---

### 🌐 `/backend/routers` - API Endpoints (15 Routers)

**Purpose:** FastAPI routers that expose functionality via HTTP endpoints.

#### **1. auth.py** - Authentication (Apex SaaS)
- `POST /api/register` - Create account
- `POST /api/login` - Get JWT token
- `POST /api/verify-email` - Verify email
- `POST /api/reset-password` - Password reset

#### **2. admin.py** - Admin Panel (Superuser Only)
- `GET /api/admin/users` - List all users
- `POST /api/admin/users/{user_id}/suspend` - Suspend user
- `GET /api/admin/stats` - System statistics

#### **3. matters.py** - Case Management
- `POST /api/matters` - Create new case
- `GET /api/matters` - List all cases
- `GET /api/matters/{id}` - Get case details
- `PUT /api/matters/{id}` - Update case
- `DELETE /api/matters/{id}` - Delete case

#### **4. documents.py** - Document Management
- `POST /api/documents/upload` - Upload PDF/image
- `GET /api/documents` - List documents
- `GET /api/documents/{id}` - Get document
- `DELETE /api/documents/{id}` - Delete document

#### **5. paralegal.py** - AI Chat (Main Interface)
- `POST /api/paralegal/query` - Ask question about case
- `GET /api/paralegal/history` - Get chat history
- Uses: RAG service + all 5 phases

#### **6. research.py** - Legal Research
- `POST /api/research/search` - Search case law
- `POST /api/research/legislation` - Search legislation
- `POST /api/research/analyze` - Analyze cases

#### **7. ai_tasks.py** - AI Task Orchestration
- `POST /api/ai-tasks/intake` - Run intake workflow
- `POST /api/ai-tasks/draft` - Run drafting workflow
- `POST /api/ai-tasks/evidence` - Run evidence workflow
- `GET /api/ai-tasks/{id}/status` - Check task status

#### **8. evidence.py** - Evidence Management
- `POST /api/evidence/generate-bundle` - Create evidence bundle
- `POST /api/evidence/generate-hearing-prep` - Create hearing materials

#### **9. chat_feedback.py** - Feedback (Phase 3)
- `POST /api/feedback/thumbs-up` - Mark response helpful
- `POST /api/feedback/thumbs-down` - Mark unhelpful
- `POST /api/feedback/correction` - Submit user correction

#### **10. case_intelligence.py** - Knowledge Graph (Phase 2)
- `POST /api/case-intelligence/extract/{matter_id}` - Extract entities
- `GET /api/case-intelligence/entities/{matter_id}` - Get entities
- `GET /api/case-intelligence/relationships/{matter_id}` - Get relationships
- `GET /api/case-intelligence/graph/{matter_id}` - Get full graph

#### **11. case_insights.py** - Automated Insights (Phase 4)
- `POST /api/insights/generate/{matter_id}` - Generate all insights
- `GET /api/insights/{matter_id}` - Get insights by type
- `POST /api/insights/{insight_id}/resolve` - Mark insight resolved

#### **12. cross_case_learning.py** - Cross-Case Learning (Phase 5)
- `POST /api/learning/analyze/{matter_id}` - Analyze similar cases
- `POST /api/learning/outcome/{matter_id}` - Record case outcome
- `GET /api/learning/outcomes` - List historical outcomes

#### **13. payments.py** - PayPal Integration
- `POST /api/payments/create-order` - Create PayPal order
- `POST /api/payments/capture-order` - Capture payment
- `GET /api/payments/history` - Payment history

#### **14. subscription.py** - Subscription Management
- `GET /api/subscription/status` - Get current plan
- `POST /api/subscription/upgrade` - Upgrade plan
- `GET /api/subscription/usage` - Get usage stats

#### **15. webhooks.py** - PayPal Webhooks
- `POST /api/webhooks/paypal` - Handle PayPal events

---

### 💾 `/backend/models` - Database Models (13 Models)

**Purpose:** SQLAlchemy ORM models for PostgreSQL database.

#### **1. matter.py** - Case/Matter Model
- **Fields:** id, title, matter_type, client_name, court, jurisdiction, status, issues, created_at
- **Relations:** Has many documents, pleadings, insights

#### **2. document.py** - Document Model
- **Fields:** id, matter_id, filename, file_path, mime_type, status, created_at
- **Relations:** Belongs to matter, has many OCR segments

#### **3. ocr_models.py** - OCR Data Models
- **OCRDocument:** OCR job metadata
- **OCRSegment:** Individual text chunks with language, confidence, position
- **Relations:** Links documents to searchable text

#### **4. chat.py** - Conversation Models (Phase 1)
- **ChatMessage:** Chat history (user/assistant messages)
- **CaseLearning:** User corrections and learnings
- **Fields:** message, role, helpful (feedback), importance (1-5), applied_count

#### **5. case_intelligence.py** - Knowledge Graph (Phase 2)
- **CaseEntity:** Extracted entities (parties, claims, dates, issues)
- **CaseRelationship:** Relationships between entities
- **Fields:** entity_type, entity_value (JSON), relationship_type

#### **6. case_insights.py** - Automated Insights (Phase 4)
- **CaseInsight:** Generated insights (SWOT, risks, gaps, timeline, recommendations)
- **CaseMetric:** Accuracy tracking
- **Fields:** insight_type, title, description, severity, actionable, resolved

#### **7. cross_case_learning.py** - Cross-Case Learning (Phase 5)
- **CasePattern:** Learned patterns (success rates, frequencies)
- **CaseOutcome:** Historical case outcomes (settlements, judgments)
- **CaseSimilarity:** Pre-computed similarity scores
- **Fields:** pattern_type, success_rate, outcome_type, settlement_amount

#### **8. pleading.py** - Legal Pleadings
- **Fields:** id, matter_id, pleading_type, language, content, version, status

#### **9. research.py** - Research Results
- **Fields:** id, query, source, results (JSON), created_at

#### **10. segment.py** - Text Segments
- **Fields:** id, doc_id, page, position, text, language, confidence

#### **11. usage.py** - Usage Tracking
- **Fields:** user_id, date, queries_count, pages_ocr, ai_tasks

#### **12. audit.py** - Audit Log
- **Fields:** id, user_id, action, resource, timestamp

#### **13. auth.py** - User Authentication (Apex)
- Managed by Apex SaaS Framework
- **Tables:** users, subscriptions, payments

---

### 🗄️ `/backend/alembic` - Database Migrations

**Purpose:** Version control for database schema changes.

**Key migrations:**
- `add_conversation_memory` - Phase 1 tables
- `add_knowledge_graph` - Phase 2 tables
- `add_case_insights` - Phase 4 tables
- `add_cross_case_learning` - Phase 5 tables

**Commands:**
```bash
alembic upgrade head  # Apply all migrations
alembic current       # Check current version
alembic revision --autogenerate -m "description"  # Create new migration
```

---

### 🔐 `/backend/apex` - Apex SaaS Framework

**Purpose:** Authentication, subscriptions, payments (3rd-party framework).

**Features:**
- User registration/login (JWT tokens)
- Email verification
- Password reset
- Subscription management (Starter/Pro/Enterprise)
- Payment processing (PayPal)
- Usage tracking & limits

---

### 📊 `/backend/data` - Static Data

**Purpose:** Templates, legal terms, court forms.

**Contents:**
- Pleading templates (Malay + English)
- Legal term dictionaries
- Court rules
- Citation formats

---

### 📝 `/backend/logs` - Application Logs

**Purpose:** Rotating log files.

**Logs:**
- `server.log` - General application logs
- `error.log` - Error tracking
- `ocr.log` - OCR processing logs
- `agent.log` - Agent execution logs

---

### 📤 `/backend/uploads` - Uploaded Files

**Purpose:** Temporary storage for user-uploaded documents.

**Structure:**
- `/uploads/{matter_id}/` - Files organized by case
- Cleaned up after OCR processing

---

### 🧪 `/backend/scripts` - Utility Scripts

**Purpose:** Maintenance and testing scripts.

**Scripts:**
- `delete_all_matters.py` - Clean database
- `reset_usage.py` - Reset usage counters
- `e2e_workflow_test.py` - End-to-end testing
- `verify_segmentation_fix.py` - Verify OCR fixes

---

### 🛠️ `/backend/utils` - Helper Functions

**Purpose:** Shared utility functions.

**Utilities:**
- `usage_tracker.py` - Track API usage
- `sync_usage_tracker.py` - Sync usage across instances

---

### 🧪 Test Files (Root Level)

**Purpose:** Comprehensive testing of all features.

**Key tests:**
- `test_all_phases_comprehensive.py` - Tests all 5 phases together
- `test_case_insights.py` - Tests Phase 4 (insights)
- `test_cross_case_learning.py` - Tests Phase 5 (cross-case learning)
- `test_knowledge_graph.py` - Tests Phase 2 (knowledge graph)
- `test_conversation_memory.py` - Tests Phase 1 (memory)
- `test_drafting_orchestrator.py` - Tests drafting workflow
- `test_evidence_orchestrator.py` - Tests evidence workflow
- `test_e2e_ocr_chat.py` - Tests OCR → Chat flow

---

### 🐳 Docker Files

- **Dockerfile** - Backend container definition
- **docker-compose.yml** - Multi-container orchestration (backend + frontend + database)

---

### 📚 Configuration Files

- **config.py** - Application configuration (database URL, API keys, settings)
- **.env** - Environment variables (secrets)
- **requirements.txt** - Python dependencies
- **alembic.ini** - Alembic configuration
- **ecosystem.config.js** - PM2 process management

---

## 🔄 HOW IT ALL WORKS TOGETHER

### Example: User Asks "What are my risks in this case?"

**Flow:**

1. **Frontend** → `POST /api/paralegal/query`
   - Router: `paralegal.py`

2. **RAG Service** activated:
   - Loads conversation history (Phase 1 - `chat.py`)
   - Loads case learnings (Phase 1 - `chat.py`)
   - Loads knowledge graph entities (Phase 2 - `case_intelligence.py`)
   - Loads ALL document chunks from OCR (OCR service)

3. **Context Assembly:**
   - Conversation: Last 10 messages
   - Learnings: User corrections with importance ≥ 3
   - Knowledge Graph: Parties, claims, defenses, issues
   - Documents: All ~700k characters of case documents

4. **LLM Processing:**
   - Gemini 1.5 Pro receives full context
   - Generates response referencing:
     - Previous conversations
     - Applied learnings
     - Extracted entities
     - Document text

5. **Optionally Reference Insights (Phase 4):**
   - Response can cite generated insights
   - "As noted in Risk Assessment, you have 3 HIGH risks..."

6. **Optionally Compare Similar Cases (Phase 5):**
   - Response can reference historical patterns
   - "In similar cases, strong documentary evidence led to 100% success"

7. **Save & Feedback:**
   - Message saved to `chat_messages`
   - User can thumbs up/down (Phase 3)
   - User can submit corrections (Phase 3 → Phase 1 learnings)

8. **Continuous Learning:**
   - Feedback updates `helpful` flag
   - Corrections saved to `case_learnings`
   - Applied learnings increment `applied_count`
   - System gets smarter with every interaction

---

## 📊 SYSTEM STATISTICS

- **Total Agents:** 19 specialized AI agents
- **Total Services:** 17 core services
- **Total Routers:** 15 API endpoints groups
- **Total Models:** 13 database models
- **Database Tables:** 25+ tables
- **Lines of Code:** ~15,000+ lines
- **AI Models Used:**
  - Gemini 1.5 Pro (2M context window)
  - GPT-4 (function calling)
- **Databases:**
  - PostgreSQL (main database)
  - ChromaDB (vector embeddings - currently bypassed)
- **Technologies:**
  - FastAPI (web framework)
  - SQLAlchemy (ORM)
  - LangChain (agent orchestration)
  - LangGraph (workflow management)
  - Playwright (web scraping)
  - Tesseract/Google Vision (OCR)
  - Apex (SaaS framework)

---

## 🎯 KEY WORKFLOWS

1. **Document Upload → Chat:**
   - Upload PDF → OCR → Segment → Store → Query

2. **Draft Pleading:**
   - Facts → Issues → Template → Draft → QA → Output

3. **Legal Research:**
   - Question → Search → Analyze → Argument Memo

4. **Case Assessment:**
   - Documents → Extract Entities → Risk Scoring → Strength Analysis → Devil's Advocate

5. **Trial Preparation:**
   - Evidence → Bundle → Hearing Prep → Oral Script

---

This is the complete architecture of the Malaysian Legal AI system! Every folder and agent serves a specific purpose in the intelligent legal workflow.

# Malaysian Legal AI Agent System

> **LegalOps Hub** - Automated legal document processing with 15 specialized AI agents for Malaysian law firms

A comprehensive multi-agent system for processing legal documents with bilingual support (Malay/English), automated OCR, risk assessment, and legal drafting powered by Google Gemini.

[![Tests](https://img.shields.io/badge/tests-15%2F15%20passing-brightgreen)]()
[![Backend](https://img.shields.io/badge/backend-FastAPI-009688)]()
[![Frontend](https://img.shields.io/badge/frontend-Next.js%2014-black)]()
[![Database](https://img.shields.io/badge/database-SQLite-003B57)]()

---

## 🚀 Quick Start

```bash
# 1. Start Backend
cd backend
python -m venv venv
venv\Scripts\activate  # Windows
pip install -r requirements.txt
python main.py  # Runs on http://localhost:8005

# 2. Start Frontend (new terminal)
cd frontend
npm install
npm run dev  # Runs on http://localhost:8006
```

**Access the app**: http://localhost:8006

---

## ✨ Features

### 🤖 15 Specialized AI Agents

**Intake Workflow (5 agents)**
- 📄 **Document Collection** - Upload PDF, images, text files
- 🔍 **OCR & Language Detection** - Extract text with 86% confidence
- 🌐 **Translation** - Malay ↔ English automatic translation
- 📋 **Case Structuring** - Extract parties, dates, issues
- ⚖️ **Risk Scoring** - Multi-factor complexity assessment

**Drafting Workflow (5 agents)**
- 💡 **Issue Planning** - Identify legal issues, find precedents
- 📑 **Template Compliance** - High Court templates with mandatory clauses
- 📝 **Malay Drafting** - Generate formal Malay pleadings
- 🔄 **English Companion** - Parallel English version
- ✅ **Consistency QA** - Quality assurance with fix suggestions

**Research Workflow (2 agents)**
- 🔎 **Research Agent** - Search Malaysian case law
- 📚 **Argument Builder** - Generate legal argument memos

**Evidence Workflow (3 agents)**
- 📦 **Evidence Builder** - Compile evidence packets
- 🔏 **Translation Certification** - Certified translations
- 🏛️ **Hearing Prep** - Hearing bundles and materials (Scripts, FAQs)

---

## 📊 Test Results

**Overall Success Rate: 100%** (All 15 agents functional)

| Workflow | Agents | Status | Success Rate |
|----------|--------|--------|--------------|
| **Intake** | 5 | ✅ PASSED | 100% |
| **Drafting** | 5 | ✅ PASSED | 100% |
| **Research** | 2 | ✅ PASSED | 100% |
| **Evidence** | 3 | ✅ PASSED | 100% |

---

## 📋 Prerequisites

- **Python 3.11+**
- **Node.js 18+**
- **Git**

---

## 🛠️ Installation

### 1. Backend Setup
```bash
cd backend
python -m venv venv
venv\Scripts\activate  # Windows
pip install -r requirements.txt
```

### 2. Frontend Setup
```bash
cd frontend
npm install
```

---

## 🚀 Running the Application

### Start Backend
```bash
cd backend
venv\Scripts\activate
python main.py
```
✅ Backend API: http://localhost:8005  
📚 API Docs: http://localhost:8005/docs

### Start Frontend
```bash
cd frontend
npm run dev
```
✅ Frontend: http://localhost:8006

---

## 📖 Usage Guide

1. **Intake**: Navigate to Dashboard, click "+ New Matter", and upload documents.
2. **Analysis**: View matter details for risk scores and extracted entities.
3. **Drafting**: Generate bilingual pleadings with high court templates.
4. **Research**: Search case law and build argument memos.
5. **Evidence**: Compile evidence packets and prepare for hearings.

---

## 🧪 Testing

```bash
# Test all workflows with PDF document
python test_workflows_comprehensive.py

# Test PDF intake specifically
python test_pdf_intake.py

# Test all agents step-by-step
python test_all_agents_stepbystep.py
```

---

## 📁 Project Structure

- `backend/agents/`: 15 specialized AI agents
- `backend/orchestrator/`: LangGraph workflow controllers
- `backend/routers/`: API endpoints
- `frontend/app/`: Next.js pages (Dashboard, Drafting, Evidence, Research)
- `frontend/components/`: Reusable UI components

---

**Built with ❤️ for Malaysian legal professionals**
*Last updated: 2025-12-23*

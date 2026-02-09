# RAG Embedding Installation Guide

## Current Issue
The RAG embedding feature requires `onnxruntime` which currently **does not support Python 3.14** on Windows (as of January 2026). Python 3.14 was just released in January 2026 and many packages haven't caught up yet.

## ✅ Workaround Options

### Option 1: Use Python 3.12 or 3.13 (Recommended)
1. Install Python 3.12 or 3.13 from python.org
2. Create a new virtual environment:
   ```powershell
   python3.12 -m venv venv_312
   .\venv_312\Scripts\Activate.ps1
   ```
3. Install all dependencies:
   ```powershell
   pip install -r requirements.txt
   pip install chromadb langchain-chroma langchain-openai
   ```

### Option 2: Wait for onnxruntime Python 3.14 Support
Monitor the onnxruntime GitHub releases: https://github.com/microsoft/onnxruntime
- The package maintainers typically add support for new Python versions within 2-3 months
- Expected availability: March-April 2026

### Option 3: Use Alternative Embedding Backend
You can modify the code to use a different vector database that doesn't require onnxruntime:

#### A. FAISS (Facebook AI Similarity Search)
```powershell
pip install faiss-cpu langchain-community
```

Then modify `services/rag_service.py`:
```python
from langchain_community.vectorstores import FAISS

# Replace Chroma with FAISS
self._vector_store = FAISS(
    embedding_function=self._embedding_function,
    index_name="legal_ops_rag"
)
```

#### B. Simple In-Memory Vector Store
```python
from langchain_community.vectorstores import DocArrayInMemorySearch

self._vector_store = DocArrayInMemorySearch(
    embedding_function=self._embedding_function
)
```

## 🚀 Quick Test (without RAG)
The system is already designed to work without RAG:
- OCR processing: ✅ Fully functional
- Document storage: ✅ Working
- Doc chat: ✅ Falls back to direct LLM when RAG unavailable

## Current Status
```
✅ Vision API - Working perfectly
✅ OCR Pipeline - 35 pages processed successfully  
✅ Segment Storage - 35 chunks in database
❌ RAG Embedding - Blocked by Python 3.14 / onnxruntime incompatibility
✅ Doc Chat - Working with LLM fallback
✅ Error Handling - All error logging functional
```

## Recommended Action
**Use Python 3.12 until onnxruntime releases Python 3.14 support.** This is a temporary limitation due to using a cutting-edge Python version.

## Installation Commands (Python 3.12/3.13)
```powershell
# After switching to Python 3.12 or 3.13
cd "c:\Users\rahul\Documents\GitHub\legal ops 01\Legal-Ops\backend"

pip install chromadb==0.4.24
pip install langchain-chroma==0.1.2  
pip install langchain-openai
pip install onnxruntime

# Test RAG embedding
python debug_ocr_workflow.py "uploads/02. SOC (Sena Traffic v AR-Rifqi)_ +@002.pdf"
```

Expected result with Python 3.12/3.13: **6/6 tests passing** ✅

"""
Test PDF extraction on the uploaded file.
"""
import os
import sys

file_path = "uploads/ctx_2 marks answer   .pdf"

print(f"Testing PDF extraction on: {file_path}")
print(f"File exists: {os.path.exists(file_path)}")

if not os.path.exists(file_path):
    print("File not found!")
    sys.exit(1)

# Method 1: PyPDFLoader
print("\n--- Method 1: PyPDFLoader ---")
try:
    from langchain_community.document_loaders import PyPDFLoader
    loader = PyPDFLoader(file_path)
    docs = loader.load()
    content = "\n".join([doc.page_content for doc in docs])
    print(f"Extracted {len(content)} chars")
    print(f"First 500 chars: {content[:500]}")
except Exception as e:
    print(f"Failed: {e}")

# Method 2: pdfplumber
print("\n--- Method 2: pdfplumber ---")
try:
    import pdfplumber
    with pdfplumber.open(file_path) as pdf:
        pages_text = []
        for page in pdf.pages:
            text = page.extract_text() or ""
            pages_text.append(text)
        content = "\n".join(pages_text)
    print(f"Extracted {len(content)} chars")
    print(f"First 500 chars: {content[:500]}")
except Exception as e:
    print(f"Failed: {e}")

# Method 3: PyMuPDF
print("\n--- Method 3: PyMuPDF (fitz) ---")
try:
    import fitz
    doc = fitz.open(file_path)
    pages_text = []
    for page in doc:
        pages_text.append(page.get_text())
    content = "\n".join(pages_text)
    doc.close()
    print(f"Extracted {len(content)} chars")
    print(f"First 500 chars: {content[:500]}")
except Exception as e:
    print(f"Failed: {e}")

"""
Simple OCR Test - Run from backend directory
Usage: python simple_ocr_test.py path/to/file.pdf
"""
import asyncio
import sys
import os

async def test_ocr(pdf_path):
    # Read the PDF
    with open(pdf_path, "rb") as f:
        pdf_bytes = f.read()
    
    print(f"\n📄 Testing OCR on: {os.path.basename(pdf_path)}")
    print(f"   Size: {len(pdf_bytes):,} bytes")
    
    # Test 1: Vision OCR
    print("\n[1] Testing Vision API OCR...")
    from services.vision_ocr_service import get_vision_ocr_service
    vision = get_vision_ocr_service()
    
    pages, page_count = await vision.extract_text_from_pdf(pdf_bytes, max_concurrent=2)
    print(f"   ✅ Extracted {page_count} pages")
    
    if pages:
        sample = pages[0].get("text", "")[:200]
        print(f"   Sample: {sample}...")
    
    # Test 2: Post-processing
    print("\n[2] Testing Post-Processor...")
    from services.ocr_post_processor import get_ocr_post_processor
    processor = get_ocr_post_processor()
    
    # Prepare pages for processing
    page_data = [{"page_number": p["page"], "raw_text": p.get("text", "")} for p in pages]
    
    result = processor.process_document_pages(page_data)
    
    print(f"   ✅ Created {len(result['chunks'])} chunks")
    print(f"   ✅ Detected patterns: {len(result['patterns_detected'].get('headers', []))} headers, {len(result['patterns_detected'].get('footers', []))} footers")
    
    if result.get("metadata"):
        print(f"   ✅ Metadata: {result['metadata']}")
    
    # Test 3: Token counts
    print("\n[3] Chunk Statistics...")
    tokens = [c["token_count"] for c in result["chunks"]]
    if tokens:
        print(f"   Min tokens: {min(tokens)}")
        print(f"   Max tokens: {max(tokens)}")
        print(f"   Avg tokens: {sum(tokens)//len(tokens)}")
    
    print("\n✅ All tests passed!")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python simple_ocr_test.py path/to/file.pdf")
        sys.exit(1)
    
    pdf_path = sys.argv[1]
    if not os.path.exists(pdf_path):
        print(f"File not found: {pdf_path}")
        sys.exit(1)
    
    asyncio.run(test_ocr(pdf_path))

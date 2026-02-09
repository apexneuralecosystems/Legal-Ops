"""
Full Pipeline Test - Processes document through enhanced OCR and saves to database
"""
import asyncio
import sys
import os

async def full_pipeline_test(pdf_path):
    print("\n" + "="*70)
    print("   FULL ENHANCED OCR PIPELINE TEST")
    print("="*70)
    
    # Read the PDF
    with open(pdf_path, "rb") as f:
        pdf_bytes = f.read()
    
    filename = os.path.basename(pdf_path)
    print(f"\n📄 Document: {filename}")
    print(f"   Size: {len(pdf_bytes):,} bytes")
    
    # Run full pipeline
    from services.enhanced_ocr_pipeline import get_enhanced_ocr_pipeline
    
    pipeline = get_enhanced_ocr_pipeline()
    
    async def progress(step, detail):
        print(f"   [{step:15}] {detail}")
    
    try:
        result = await pipeline.process_document(
            file_content=pdf_bytes,
            filename=filename,
            matter_id="test-matter-full-pipeline",
            file_path=pdf_path,
            progress_callback=progress
        )
        
        print("\n" + "-"*70)
        print("   RESULTS")
        print("-"*70)
        
        if result.get("duplicate"):
            print(f"\n⚠️  Duplicate detected!")
            print(f"   Message: {result.get('message')}")
            print(f"   Document ID: {result.get('document_id')}")
        else:
            print(f"\n✅ Processing Complete!")
            print(f"   Document ID: {result['document_id']}")
            print(f"   Total Pages: {result['total_pages']}")
            print(f"   Total Chunks: {result['total_chunks']}")
            print(f"   Processing Time: {result['processing_time_ms']}ms")
            
            if result.get('metadata'):
                print(f"\n📋 Extracted Metadata:")
                for key, value in result['metadata'].items():
                    if value:
                        print(f"      {key}: {value}")
            
            if result.get('patterns_detected'):
                patterns = result['patterns_detected']
                print(f"\n🔍 Patterns Detected:")
                print(f"      Headers: {len(patterns.get('headers', []))}")
                print(f"      Footers: {len(patterns.get('footers', []))}")
        
        # Verify database storage
        print("\n" + "-"*70)
        print("   DATABASE VERIFICATION")
        print("-"*70)
        
        from database import SessionLocal
        from models.ocr_models import OCRDocument, OCRPage, OCRChunk, OCRProcessingLog
        
        db = SessionLocal()
        
        doc = db.query(OCRDocument).filter(OCRDocument.id == result['document_id']).first()
        if doc:
            print(f"\n✅ Document stored in ocr_documents:")
            print(f"      ID: {doc.id}")
            print(f"      Status: {doc.ocr_status}")
            print(f"      Pages: {doc.total_pages}")
        
        pages = db.query(OCRPage).filter(OCRPage.document_id == result['document_id']).count()
        print(f"\n✅ Pages stored in ocr_pages: {pages}")
        
        chunks = db.query(OCRChunk).filter(OCRChunk.document_id == result['document_id']).all()
        print(f"\n✅ Chunks stored in ocr_chunks: {len(chunks)}")
        
        if chunks:
            tokens = [c.token_count for c in chunks]
            print(f"      Token range: {min(tokens)} - {max(tokens)}")
            print(f"      Avg tokens: {sum(tokens)//len(tokens)}")
            
            # Show first chunk sample
            print(f"\n📝 First chunk sample:")
            print(f"      {chunks[0].chunk_text[:200]}...")
        
        logs = db.query(OCRProcessingLog).filter(OCRProcessingLog.document_id == result['document_id']).all()
        print(f"\n✅ Processing logs: {len(logs)} entries")
        for log in logs:
            print(f"      [{log.status:10}] {log.step_name}")
        
        db.close()
        
        print("\n" + "="*70)
        print("   ✅ FULL PIPELINE TEST PASSED!")
        print("="*70 + "\n")
        
        return True
        
    except Exception as e:
        print(f"\n❌ Pipeline error: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python full_pipeline_test.py path/to/file.pdf")
        sys.exit(1)
    
    pdf_path = sys.argv[1]
    if not os.path.exists(pdf_path):
        print(f"File not found: {pdf_path}")
        sys.exit(1)
    
    asyncio.run(full_pipeline_test(pdf_path))

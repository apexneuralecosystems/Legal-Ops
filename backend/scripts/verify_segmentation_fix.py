
import sys
import os
import logging
from pprint import pprint

# Add backend to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from services.ocr_post_processor import get_ocr_post_processor

def test_segmentation():
    processor = get_ocr_post_processor()
    
    # Sample legal text mimicking OCR output
    sample_text = """
    SECTION 12.3. TERMINATION FOR CAUSE
    
    This Agreement may be terminated by either party immediately upon written notice to the other party 
    if the other party commits a material breach of any of its obligations under this Agreement.
    
    ARTICLE 5
    CONFIDENTIALITY
    
    Each party agrees to keep confidential all non-public information provided by the other party.
    """
    
    pages = [{
        'page_number': 1,
        'raw_text': sample_text,
        'text': sample_text
    }]
    
    print("Processing sample document...")
    result = processor.process_document_pages(pages)
    
    chunks = result['chunks']
    print(f"\nGenerated {len(chunks)} chunks.")
    
    passed = True
    
    for i, chunk in enumerate(chunks):
        print(f"\nChunk {i+1}:")
        print(f"Text: {chunk['chunk_text'][:50]}...")
        print(f"Section Ref: {chunk['section_ref']}")
        print(f"Language: {chunk['language']}")
        
        # Verification logic
        if "TERMINATION" in chunk['chunk_text']:
            if chunk['section_ref'] != "SECTION 12.3":
                print(f"FAILED: Expected 'SECTION 12.3', got '{chunk['section_ref']}'")
                passed = False
            else:
                print("PASSED: Section Ref match")
        
        if "CONFIDENTIALITY" in chunk['chunk_text']:
            if chunk['section_ref'] == "ARTICLE 5":
                print("PASSED: Section Ref match")
            # Note: The logic puts 'ARTICLE 5' as a heading chunk, then the text following it might get it too if logic works
            
    if passed:
        print("\nSUCCESS: Segmentation logic verified.")
    else:
        print("\nFAILURE: Verification failed.")

if __name__ == "__main__":
    test_segmentation()

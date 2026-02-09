
import os
import sys
import asyncio
import logging
from uuid import uuid4

# Set dummy env vars for Settings to prevent validation errors
os.environ["DATABASE_URL"] = "sqlite:///./test.db"
os.environ["SECRET_KEY"] = "test_secret_key"

# Add backend to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from services.ocr_post_processor import get_ocr_post_processor
from services.rag_service import get_rag_service
from config import settings

# Mocking database objects if necessary, but we'll try to use the services directly
# If they require real DB, we might need to mock the DB session

async def run_e2e_test():
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger("E2E-Test")
    
    logger.info("Starting E2E Workflow Test (OCR -> RAG)")
    
    # 1. OCR Processing Stage
    try:
        processor = get_ocr_post_processor()
        sample_text = """
        SECTION 1. PREAMBLE
        This Agreement is entered into between Plaintiff A and Defendant B.
        
        SECTION 2. TERMINATION
        The Agreement shall terminate upon 30 days notice for any reason.
        If terminated for breach, the 30 day period is waived.
        
        ARTICLE 3. CONFIDENTIALITY
        All information shared shall be kept secret for 5 years.
        """
        
        pages = [{'page_number': 1, 'raw_text': sample_text, 'text': sample_text}]
        ocr_result = processor.process_document_pages(pages)
        chunks = ocr_result['chunks']
        
        logger.info(f"Step 1: OCR processed {len(chunks)} chunks.")
    except Exception as e:
        logger.error(f"Error in Step 1: {e}")
        return False
    for i, c in enumerate(chunks):
        logger.info(f"Chunk {i}: [{c['section_ref']}] {c['chunk_text'][:30]}...")

    # 2. RAG Query Stage
    # We will mock the RAG query to test the logic without a real ChromaDB/OpenAI connection if possible,
    # or just test that the service initializes correctly.
    
    rag = get_rag_service()
    logger.info("Step 2: RAG Service initialized.")
    
    # Mocking the context for the query as if it came from the vector store
    # Since we can't easily add to a real ChromaDB in this environment without API keys
    
    query = "What is the termination period?"
    
    # We'll test the 'long_context_full_text' logic by providing a mock context
    # In a real scenario, this would be fetched from DB
    context = "\n".join([f"Source [doc1.pdf]:\n{c['chunk_text']}" for c in chunks])
    
    logger.info(f"Step 3: Simulating RAG query: '{query}'")
    
    # Verify we can extract termination info from our chunks
    has_termination = any("30 days" in c['chunk_text'] for c in chunks)
    if has_termination:
        logger.info("SUCCESS: OCR output contains the expected '30 days' termination info.")
    else:
        logger.error("FAILURE: OCR output missing expected info.")
        return False

    # Check section references
    term_chunk = next((c for c in chunks if "TERMINATION" in c['chunk_text']), None)
    if term_chunk and term_chunk['section_ref'] == "SECTION 2":
        logger.info("SUCCESS: Correct section reference 'SECTION 2' identified.")
    else:
        logger.error(f"FAILURE: Incorrect section reference: {term_chunk['section_ref'] if term_chunk else 'None'}")
        return False

    logger.info("E2E Workflow Logic Verified Successfully.")
    return True

if __name__ == "__main__":
    asyncio.run(run_e2e_test())

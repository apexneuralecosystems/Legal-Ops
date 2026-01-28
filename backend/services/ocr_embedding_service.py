"""
OCR Chunk Embedding Service
===========================
Embeds chunks from the ocr_chunks table into the vector store.
"""
import logging
from typing import Dict, Any, List, Optional

logger = logging.getLogger(__name__)


async def embed_pending_chunks(
    document_id: Optional[str] = None,
    batch_size: int = 50
) -> Dict[str, Any]:
    """
    Embed pending chunks from the ocr_chunks table into Chroma.
    
    Args:
        document_id: Optional filter by specific document
        batch_size: Number of chunks to process at once
    
    Returns:
        Dict with embedded_count, chunk_ids, and any errors
    """
    from services.rag_service import get_rag_service
    from services.enhanced_ocr_pipeline import get_enhanced_ocr_pipeline
    
    rag_service = get_rag_service()
    
    if not rag_service._vector_store:
        logger.error("Vector store not initialized.")
        return {"embedded_count": 0, "error": "Vector store not initialized"}
    
    try:
        from langchain.schema import Document as LCDocument
        
        pipeline = get_enhanced_ocr_pipeline()
        
        # Get chunks ready for embedding
        chunks = await pipeline.get_chunks_for_embedding(document_id, limit=batch_size)
        
        if not chunks:
            logger.info("No chunks pending embedding")
            return {"embedded_count": 0, "message": "No chunks to embed"}
        
        logger.info(f"Embedding {len(chunks)} chunks from ocr_chunks table")
        
        # Convert to LangChain documents
        lc_docs = []
        chunk_ids = []
        
        for chunk in chunks:
            lc_doc = LCDocument(
                page_content=chunk["text"],
                metadata={
                    "chunk_id": chunk["id"],
                    "chunk_id_str": chunk["chunk_id_str"],
                    "document_id": chunk["metadata"]["document_id"],
                    "matter_id": chunk["metadata"]["matter_id"],
                    "source": chunk["metadata"]["filename"],
                    "page_start": chunk["metadata"]["source_page_start"],
                    "page_end": chunk["metadata"]["source_page_end"],
                    "chunk_type": chunk["metadata"]["chunk_type"],
                }
            )
            lc_docs.append(lc_doc)
            chunk_ids.append(chunk["id"])
        
        # Add to vector store
        rag_service._vector_store.add_documents(documents=lc_docs)
        
        # Mark as embedded
        await pipeline.mark_chunks_embedded(chunk_ids)
        
        logger.info(f"Successfully embedded {len(chunks)} chunks")
        
        return {
            "embedded_count": len(chunks),
            "chunk_ids": chunk_ids
        }
        
    except Exception as e:
        logger.error(f"Chunk embedding failed: {e}", exc_info=True)
        return {"embedded_count": 0, "error": str(e)}


async def embed_all_pending(batch_size: int = 50, max_batches: int = 100) -> Dict[str, Any]:
    """
    Embed all pending chunks across all documents.
    
    Args:
        batch_size: Chunks per batch
        max_batches: Maximum number of batches to process
    
    Returns:
        Summary of embedding results
    """
    total_embedded = 0
    all_chunk_ids = []
    errors = []
    
    for i in range(max_batches):
        result = await embed_pending_chunks(batch_size=batch_size)
        
        if result.get("error"):
            errors.append(result["error"])
            break
        
        embedded = result.get("embedded_count", 0)
        if embedded == 0:
            break
        
        total_embedded += embedded
        all_chunk_ids.extend(result.get("chunk_ids", []))
        
        logger.info(f"Batch {i+1}: Embedded {embedded} chunks (total: {total_embedded})")
    
    return {
        "total_embedded": total_embedded,
        "batches_processed": i + 1 if 'i' in dir() else 0,
        "errors": errors if errors else None
    }

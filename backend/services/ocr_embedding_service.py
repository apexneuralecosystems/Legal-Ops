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
    
    if not getattr(rag_service, "_embedding_function", None):
        logger.error("Vector store not initialized.")
        return {"embedded_count": 0, "error": "Vector store not initialized"}
    
    try:
        from langchain_core.documents import Document as LCDocument
        
        pipeline = get_enhanced_ocr_pipeline()
        
        # Get chunks ready for embedding
        chunks = await pipeline.get_chunks_for_embedding(document_id, limit=batch_size)
        
        if not chunks:
            logger.info("No chunks pending embedding")
            return {"embedded_count": 0, "message": "No chunks to embed"}
        
        logger.info(f"Embedding {len(chunks)} chunks from ocr_chunks table")
        
        # Convert to LangChain documents
        matter_docs = {}
        matter_chunk_ids = {}
        
        for chunk in chunks:
            metadata = chunk["metadata"]
            matter_id = metadata["matter_id"]
            lc_doc = LCDocument(
                page_content=chunk["text"],
                metadata={
                    "chunk_id": chunk["id"],
                    "chunk_id_str": chunk["chunk_id_str"],
                    "document_id": metadata["document_id"],
                    "matter_id": matter_id,
                    "source": metadata["filename"],
                    "page_start": metadata["source_page_start"],
                    "page_end": metadata["source_page_end"],
                    "chunk_type": metadata["chunk_type"],
                }
            )
            if matter_id not in matter_docs:
                matter_docs[matter_id] = []
                matter_chunk_ids[matter_id] = []
            matter_docs[matter_id].append(lc_doc)
            matter_chunk_ids[matter_id].append(chunk["id"])
        
        total_embedded = 0
        all_chunk_ids = []
        
        for matter_id, docs in matter_docs.items():
            try:
                store = rag_service._get_vector_store(matter_id)
                if not store:
                    error_msg = f"Vector store not initialized for matter {matter_id}"
                    logger.error(error_msg)
                    continue
                
                logger.info(f"Embedding {len(docs)} chunks for matter {matter_id}")
                store.add_documents(documents=docs)
                total_embedded += len(docs)
                all_chunk_ids.extend(matter_chunk_ids[matter_id])
                logger.info(f"Successfully embedded {len(docs)} chunks for matter {matter_id}")
            except Exception as embed_err:
                logger.error(f"Failed to embed chunks for matter {matter_id}: {embed_err}", exc_info=True)
        
        if all_chunk_ids:
            await pipeline.mark_chunks_embedded(all_chunk_ids)
        
        logger.info(f"Successfully embedded {total_embedded} chunks into {len(matter_docs)} matter collections")
        
        return {
            "embedded_count": total_embedded,
            "chunk_ids": all_chunk_ids
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

"""
Enhanced OCR Pipeline Service
=============================
Integrates the full OCR pipeline with:
- Document registry and deduplication
- 300 DPI rendering  
- DOCUMENT_TEXT_DETECTION
- Post-processing (header/footer removal, noise filtering)
- Token-controlled chunking
- Database storage in new ocr_* tables
"""
import os
import hashlib
import logging
from datetime import datetime
from typing import Dict, Any, List, Optional, Tuple
from uuid import uuid4
import time

logger = logging.getLogger(__name__)


class EnhancedOCRPipeline:
    """
    Enhanced OCR pipeline that stores results in the new ocr_* tables
    and produces RAG-ready chunks.
    """
    
    def __init__(self):
        self._post_processor = None
        self._vision_service = None
    
    def _get_post_processor(self):
        """Lazy load post-processor."""
        if self._post_processor is None:
            from services.ocr_post_processor import get_ocr_post_processor
            self._post_processor = get_ocr_post_processor()
        return self._post_processor
    
    def _get_vision_service(self):
        """Lazy load vision OCR service."""
        if self._vision_service is None:
            from services.vision_ocr_service import get_vision_ocr_service
            self._vision_service = get_vision_ocr_service()
        return self._vision_service
    
    def _compute_file_hash(self, content: bytes) -> str:
        """Compute SHA-256 hash of file content."""
        return hashlib.sha256(content).hexdigest()
    
    async def process_document(
        self,
        file_content: bytes,
        filename: str,
        matter_id: Optional[str] = None,
        file_path: Optional[str] = None,
        created_by: Optional[str] = None,
        progress_callback: Optional[callable] = None
    ) -> Dict[str, Any]:
        """
        Process a document through the full enhanced OCR pipeline.
        
        Args:
            file_content: Raw bytes of the document
            filename: Original filename
            matter_id: Associated matter ID
            file_path: Path where file is stored
            created_by: User ID who uploaded
            progress_callback: async callback(step, detail) for progress updates
        
        Returns:
            Dict with document_id, pages, chunks, metadata
        """
        from database import SessionLocal
        from models.ocr_models import OCRDocument, OCRPage, OCRChunk, OCRProcessingLog
        
        db = SessionLocal()
        start_time = time.time()
        
        try:
            # Step 1: Check for duplicate via file hash
            file_hash = self._compute_file_hash(file_content)
            
            existing = db.query(OCRDocument).filter(OCRDocument.file_hash == file_hash).first()
            if existing:
                logger.info(f"Duplicate document found: {existing.id}")
                db.close()
                return {
                    "document_id": existing.id,
                    "duplicate": True,
                    "message": f"Document already processed as {existing.filename}"
                }
            
            # Step 2: Create document registry entry
            doc_id = str(uuid4())
            
            # Detect total pages
            import fitz
            pdf_doc = fitz.open(stream=file_content, filetype="pdf")
            total_pages = len(pdf_doc)
            pdf_doc.close()
            
            ocr_document = OCRDocument(
                id=doc_id,
                matter_id=matter_id,
                filename=filename,
                file_path=file_path,
                file_hash=file_hash,
                file_size_bytes=len(file_content),
                total_pages=total_pages,
                ocr_status='processing',
                ocr_started_at=datetime.utcnow(),
                created_by=created_by
            )
            db.add(ocr_document)
            db.commit()
            
            self._log_step(db, doc_id, None, "document_registered", "completed", 
                          input_summary=f"File: {filename}, Size: {len(file_content)} bytes",
                          output_summary=f"Doc ID: {doc_id}, Pages: {total_pages}")
            
            if progress_callback:
                await progress_callback("registered", f"Document registered: {total_pages} pages")
            
            # Step 3: Run OCR on all pages
            vision_service = self._get_vision_service()
            
            async def ocr_progress(page_done, total):
                if progress_callback:
                    await progress_callback("ocr", f"OCR page {page_done}/{total}")
            
            ocr_start = time.time()
            page_results, _ = await vision_service.extract_text_from_pdf(
                file_content,
                max_concurrent=8,
                progress_callback=ocr_progress
            )
            ocr_duration = int((time.time() - ocr_start) * 1000)
            
            self._log_step(db, doc_id, None, "vision_api_ocr", "completed",
                          duration_ms=ocr_duration,
                          output_summary=f"Processed {len(page_results)} pages")
            
            # Step 4: Store raw OCR results in ocr_pages
            pages_data = []
            for result in page_results:
                page_num = result["page"]
                raw_text = result.get("text", "")
                confidence = result.get("confidence", 0.0)
                
                pages_data.append({
                    "page_number": page_num,
                    "raw_text": raw_text,
                    "text": raw_text,  # For compatibility with post-processor
                    "confidence": confidence
                })
                
                # Create page record (will update cleaned_text after post-processing)
                ocr_page = OCRPage(
                    id=str(uuid4()),
                    document_id=doc_id,
                    page_number=page_num,
                    raw_text=raw_text,
                    ocr_confidence=confidence,
                    word_count=len(raw_text.split()),
                    char_count=len(raw_text),
                    is_blank=len(raw_text.strip()) < 50
                )
                db.add(ocr_page)
            
            db.commit()
            
            # Step 5: Run post-processing pipeline
            if progress_callback:
                await progress_callback("post_processing", "Cleaning and extracting metadata")
            
            post_start = time.time()
            post_processor = self._get_post_processor()
            processed = post_processor.process_document_pages(pages_data)
            post_duration = int((time.time() - post_start) * 1000)
            
            self._log_step(db, doc_id, None, "post_processing", "completed",
                          duration_ms=post_duration,
                          output_summary=f"Detected {len(processed['patterns_detected'].get('headers', []))} headers, extracted metadata")
            
            # Step 6: Update pages with cleaned text and patterns
            for page_data in processed['pages']:
                page_num = page_data['page_number']
                db.query(OCRPage).filter(
                    OCRPage.document_id == doc_id,
                    OCRPage.page_number == page_num
                ).update({
                    'cleaned_text': page_data['cleaned_text'],
                    'detected_headers': page_data.get('detected_headers', []),
                    'detected_footers': page_data.get('detected_footers', []),
                })
            
            # Step 7: Store chunks
            if progress_callback:
                await progress_callback("chunking", f"Creating {len(processed['chunks'])} chunks")
            
            for chunk_data in processed['chunks']:
                chunk_id = str(uuid4())
                chunk_id_str = f"doc-{doc_id[:8]}-p{chunk_data['source_page_start']}-c{chunk_data['chunk_sequence']}"
                
                ocr_chunk = OCRChunk(
                    id=chunk_id,
                    document_id=doc_id,
                    chunk_sequence=chunk_data['chunk_sequence'],
                    chunk_id_str=chunk_id_str,
                    chunk_text=chunk_data['chunk_text'],
                    token_count=chunk_data['token_count'],
                    source_page_start=chunk_data['source_page_start'],
                    source_page_end=chunk_data['source_page_end'],
                    chunk_type=chunk_data.get('chunk_type', 'paragraph'),
                    is_embeddable=chunk_data.get('is_embeddable', True)
                )
                db.add(ocr_chunk)
            
            # Step 8: Update document with metadata and status
            db.query(OCRDocument).filter(OCRDocument.id == doc_id).update({
                'ocr_status': 'completed',
                'ocr_completed_at': datetime.utcnow(),
                'extracted_metadata': processed['metadata'],
                'primary_language': 'en'  # Can be enhanced with actual detection
            })
            
            db.commit()
            
            total_duration = int((time.time() - start_time) * 1000)
            self._log_step(db, doc_id, None, "pipeline_complete", "completed",
                          duration_ms=total_duration,
                          output_summary=f"Total: {len(processed['pages'])} pages, {len(processed['chunks'])} chunks")
            
            db.close()
            
            if progress_callback:
                await progress_callback("complete", f"OCR complete: {len(processed['chunks'])} chunks ready for embedding")
            
            return {
                "document_id": doc_id,
                "duplicate": False,
                "total_pages": total_pages,
                "total_chunks": len(processed['chunks']),
                "metadata": processed['metadata'],
                "patterns_detected": processed['patterns_detected'],
                "processing_time_ms": total_duration
            }
            
        except Exception as e:
            logger.error(f"Enhanced OCR pipeline failed: {e}", exc_info=True)
            
            # Log error
            if 'doc_id' in dir():
                self._log_step(db, doc_id, None, "pipeline_error", "failed",
                              error_message=str(e))
                db.query(OCRDocument).filter(OCRDocument.id == doc_id).update({
                    'ocr_status': 'failed'
                })
                db.commit()
            
            db.close()
            raise
    
    def _log_step(
        self,
        db,
        document_id: str,
        page_number: Optional[int],
        step_name: str,
        status: str,
        duration_ms: Optional[int] = None,
        input_summary: Optional[str] = None,
        output_summary: Optional[str] = None,
        error_message: Optional[str] = None
    ):
        """Log a processing step to the audit table."""
        from models.ocr_models import OCRProcessingLog
        
        log_entry = OCRProcessingLog(
            id=str(uuid4()),
            document_id=document_id,
            page_number=page_number,
            step_name=step_name,
            status=status,
            duration_ms=duration_ms,
            input_summary=input_summary,
            output_summary=output_summary,
            error_message=error_message
        )
        db.add(log_entry)
        # Don't commit here - let caller handle transaction
    
    async def get_chunks_for_embedding(
        self,
        document_id: Optional[str] = None,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """
        Get chunks that are ready for embedding but haven't been embedded yet.
        
        Args:
            document_id: Optional filter by document
            limit: Maximum chunks to return
        
        Returns:
            List of chunk dicts with id, text, metadata
        """
        from database import SessionLocal
        from models.ocr_models import OCRChunk, OCRDocument
        
        db = SessionLocal()
        
        try:
            query = db.query(OCRChunk).filter(
                OCRChunk.is_embeddable == True,
                OCRChunk.embedded_at == None
            )
            
            if document_id:
                query = query.filter(OCRChunk.document_id == document_id)
            
            chunks = query.order_by(OCRChunk.created_at).limit(limit).all()
            
            result = []
            for chunk in chunks:
                # Get document metadata for context
                doc = db.query(OCRDocument).filter(OCRDocument.id == chunk.document_id).first()
                
                result.append({
                    "id": chunk.id,
                    "chunk_id_str": chunk.chunk_id_str,
                    "text": chunk.chunk_text,
                    "token_count": chunk.token_count,
                    "metadata": {
                        "document_id": chunk.document_id,
                        "matter_id": doc.matter_id if doc else None,
                        "filename": doc.filename if doc else None,
                        "source_page_start": chunk.source_page_start,
                        "source_page_end": chunk.source_page_end,
                        "chunk_type": chunk.chunk_type,
                    }
                })
            
            db.close()
            return result
            
        except Exception as e:
            db.close()
            raise
    
    async def mark_chunks_embedded(
        self,
        chunk_ids: List[str],
        embedding_model: str = "text-embedding-3-small"
    ):
        """Mark chunks as embedded after successful embedding."""
        from database import SessionLocal
        from models.ocr_models import OCRChunk
        
        db = SessionLocal()
        
        try:
            db.query(OCRChunk).filter(OCRChunk.id.in_(chunk_ids)).update({
                'embedded_at': datetime.utcnow(),
                'embedding_model': embedding_model
            }, synchronize_session=False)
            
            db.commit()
            db.close()
            
        except Exception as e:
            db.close()
            raise


# Global instance
_enhanced_ocr_pipeline = None


def get_enhanced_ocr_pipeline() -> EnhancedOCRPipeline:
    """Get the global enhanced OCR pipeline instance."""
    global _enhanced_ocr_pipeline
    if _enhanced_ocr_pipeline is None:
        _enhanced_ocr_pipeline = EnhancedOCRPipeline()
    return _enhanced_ocr_pipeline

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
import sys
from datetime import datetime
from typing import Dict, Any, List, Optional, Tuple
from uuid import uuid4
import time
from sqlalchemy import text

logger = logging.getLogger(__name__)


def console_log(msg: str):
    """Force immediate console output that bypasses uvicorn buffering."""
    sys.stdout.write(msg + "\n")
    sys.stdout.flush()
    sys.stderr.write(msg + "\n")
    sys.stderr.flush()
    # Also write to dedicated OCR progress file
    try:
        from datetime import datetime as dt
        log_path = os.path.join(os.path.dirname(__file__), "..", "logs", "ocr_progress.log")
        with open(log_path, "a", encoding="utf-8") as f:
            f.write(f"{dt.now().strftime('%Y-%m-%d %H:%M:%S')} - {msg}\n")
            f.flush()
    except Exception as e:
        sys.stderr.write(f"ERROR writing to log: {e}\n")
        sys.stderr.flush()


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
        progress_callback: Optional[callable] = None,
        document_id: Optional[str] = None
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
            document_id: Existing ID from the 'documents' table to link to
        
        Returns:
            Dict with document_id, pages, chunks, metadata
        """
        from database import SessionLocal
        from models.ocr_models import OCRDocument, OCRPage, OCRChunk, OCRProcessingLog
        from models.document import Document
        
        db = SessionLocal()
        start_time = time.time()
        
        # Normalize matter_id
        if matter_id == "" or matter_id == "general":
            matter_id = None
        
        try:
            # Step 1: Check for duplicate via file hash
            file_hash = self._compute_file_hash(file_content)
            
            # Use provided document_id or generate new one
            doc_id = document_id if document_id else str(uuid4())
            
            # Check if this specific document_id already has an OCR record
            existing_ocr = db.query(OCRDocument).filter(OCRDocument.id == doc_id).first()
            if existing_ocr:
                logger.info(f"OCR record already exists for document: {doc_id}")
                # Ensure hash matches (if not, we might have an ID collision or re-upload with different content)
                if existing_ocr.file_hash != file_hash:
                    logger.warning(f"ID collision or content change for {doc_id}. Updating hash.")
                    existing_ocr.file_hash = file_hash
                    existing_ocr.file_size_bytes = len(file_content)
                    existing_ocr.ocr_status = 're-processing'
                    db.add(existing_ocr)
                    db.commit()
                else:
                    db.close()
                    return {
                        "document_id": doc_id,
                        "existing": True,
                        "message": "OCR record already exists for this document ID"
                    }

            # Check for hash-based duplicates (regardless of ID)
            existing_hash = db.query(OCRDocument).filter(OCRDocument.file_hash == file_hash).first()
            
            if existing_hash:
                logger.info(f"Existing document found with same hash: {existing_hash.id}")
                
                # Case A: Same ID (already handled above, but for safety)
                if existing_hash.id == doc_id:
                    db.close()
                    return {"document_id": doc_id, "existing": True}
                
                # Case B: Different ID (Re-upload or Matter Link)
                logger.info(f"Hash collision detected. New ID: {doc_id}, Existing ID: {existing_hash.id}. Re-linking.")
                
                # Option: Update the existing record's ID if we really want to use the new one?
                # No, better to keep the existing one and just return its ID, 
                # OR update the existing one to the new matter.
                
                # If a new document_id was provided, we should ideally point the 'documents' table to THIS ocr_id,
                # but ocr_documents.id is usually 1:1 with Document.id.
                
                # The safest fix for UniqueViolation is to reuse the existing_hash.id 
                # and update the 'documents' table to match if possible.
                
                if document_id:
                    from models.document import Document
                    db_doc = db.query(Document).filter(Document.id == document_id).first()
                    if db_doc:
                        # We can't easily change db_doc.id as it's a primary key.
                        # Instead, we'll update existing_hash to point to this new matter if needed
                        if matter_id and existing_hash.matter_id != matter_id:
                            existing_hash.matter_id = matter_id
                            db.add(existing_hash)
                        
                        db_doc.ocr_completed = True
                        # Pipeline results are already there for existing_hash.id
                        # We might need to duplicate segments/chunks if we want them tied to the new ID,
                        # but that defeats the purpose of deduplication.
                        # For now, we'll just mark it as completed and return the EXISTING id.
                        db.commit()
                
                # Access the ID before closing the session to avoid DetachedInstanceError
                existing_doc_id = existing_hash.id
                db.close()
                return {
                    "document_id": existing_doc_id,
                    "duplicate": True,
                    "message": "Reuse existing OCR results for same content"
                }
            
            # Step 2: Create document registry entry
            # Detect total pages
            import io
            from pypdf import PdfReader
            pdf_reader = PdfReader(io.BytesIO(file_content))
            total_pages = len(pdf_reader.pages)
            
            with open("debug_pipeline.log", "a") as logf:
                logf.write(f"[{datetime.utcnow()}] Registering OCR record for {doc_id}\n")
            
            logger.info(f"Creating OCR document record: doc_id={doc_id}, matter_id={matter_id}, pages={total_pages}, hash={file_hash[:16]}...")
            
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
            
            with open("debug_pipeline.log", "a") as logf:
                logf.write(f"[{datetime.utcnow()}] Committing OCR record for {doc_id}\n")
            
            try:
                db.commit()
                logger.info(f"OCR document record committed successfully: {doc_id}")
            except Exception as commit_err:
                logger.error(f"Failed to commit OCR document record: {commit_err}", exc_info=True)
                db.rollback()
                raise
            
            with open("debug_pipeline.log", "a") as logf:
                logf.write(f"[{datetime.utcnow()}] Successfully committed OCR record for {doc_id}\n")
            
            self._log_step(db, doc_id, None, "document_registered", "completed", 
                          input_summary=f"File: {filename}, Size: {len(file_content)} bytes",
                          output_summary=f"Doc ID: {doc_id}, Pages: {total_pages}")
            
            # Commit the log step too
            db.commit()
            
            if progress_callback:
                await progress_callback("registered", f"Document registered: {total_pages} pages")
            
            # Step 3: Run OCR on all pages
            banner = f"{'='*80}\n📄 STARTING OCR WORKFLOW\n   Document ID: {doc_id}\n   Filename: {filename}\n   Total Pages: {total_pages}\n   Matter ID: {matter_id or 'N/A'}\n{'='*80}"
            logger.info(banner)
            console_log("\n" + banner)  # Force immediate console output
            
            vision_service = self._get_vision_service()
            
            async def ocr_progress(page_done, total):
                logger.info(f"✓ OCR Progress: Page {page_done}/{total} completed for {filename}")
                if progress_callback:
                    await progress_callback("ocr", f"OCR page {page_done}/{total}")
            
            ocr_start = time.time()
            try:
                page_results, _ = await vision_service.extract_text_from_pdf(
                    file_content,
                    max_concurrent=8,
                    progress_callback=ocr_progress
                )
                ocr_duration = int((time.time() - ocr_start) * 1000)
                logger.info(f"="*80)
                logger.info(f"✅ VISION OCR COMPLETED")
                logger.info(f"   Document: {filename}")
                logger.info(f"   Duration: {ocr_duration}ms ({ocr_duration/1000:.2f}s)")
                logger.info(f"   Page Results: {len(page_results)}/{total_pages}")
                logger.info(f"="*80)
            except Exception as ocr_err:
                ocr_duration = int((time.time() - ocr_start) * 1000)
                logger.error(f"❌ Vision OCR FAILED for {filename} after {ocr_duration}ms: {ocr_err}", exc_info=True)
                # Update status to failed
                ocr_document.ocr_status = 'failed'
                ocr_document.ocr_completed_at = datetime.utcnow()
                db.commit()
                raise
            
            self._log_step(db, doc_id, None, "vision_api_ocr", "completed",
                          duration_ms=ocr_duration,
                          output_summary=f"Processed {len(page_results)} pages")
            
            # Step 4: Store raw OCR results in ocr_pages
            logger.info(f"\n📊 STORING PAGE RESULTS FOR {filename}")
            pages_data = []
            total_conf = 0.0
            processed_pages = 0
            skipped_pages = []
            
            for result in page_results:
                page_num = result["page"]
                raw_text = result.get("text", "")
                confidence = result.get("confidence", 0.0)
                error = result.get("error")
                
                # Log page processing status
                if error:
                    msg = f"⚠️  Page {page_num}/{total_pages}: SKIPPED - {error}"
                    logger.warning(msg)
                    console_log(msg)
                    skipped_pages.append({"page": page_num, "reason": error})
                elif not raw_text or len(raw_text.strip()) < 10:
                    reason = "No text content" if not raw_text else f"Text too short ({len(raw_text)} chars)"
                    msg = f"⚠️  Page {page_num}/{total_pages}: EMPTY - {reason}"
                    logger.warning(msg)
                    console_log(msg)
                    skipped_pages.append({"page": page_num, "reason": reason})
                else:
                    msg = f"✓ Page {page_num}/{total_pages}: SUCCESS - {len(raw_text)} chars, confidence: {confidence:.2%}"
                    logger.info(msg)
                    console_log(msg)
                
                total_conf += confidence
                processed_pages += 1
                
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
                    section_ref=chunk_data.get('section_ref'),
                    language=chunk_data.get('language', 'en'),
                    is_embeddable=chunk_data.get('is_embeddable', True)
                )
                db.add(ocr_chunk)
            
            # Step 8: Update document with metadata and status
            avg_confidence = total_conf / processed_pages if processed_pages > 0 else 0.0
            
            db.query(OCRDocument).filter(OCRDocument.id == doc_id).update({
                'ocr_status': 'completed',
                'ocr_completed_at': datetime.utcnow(),
                'extracted_metadata': processed['metadata'],
                'primary_language': 'en'  # Can be enhanced with actual detection
            })
            
            # Update the main documents table
            db.query(Document).filter(Document.id == doc_id).update({
                'ocr_completed': True,
                'ocr_needed': False,
                'ocr_confidence': int(avg_confidence * 100),
                'processed_at': datetime.utcnow()
            })
            
            db.commit()
            
            # Log final summary
            summary = (
                f"\n{'='*80}\n"
                f"📋 OCR WORKFLOW SUMMARY FOR {filename}\n"
                f"   Document ID: {doc_id}\n"
                f"   Total Pages: {total_pages}\n"
                f"   Processed Successfully: {processed_pages}\n"
                f"   Skipped/Failed: {len(skipped_pages)}\n"
            )
            if skipped_pages:
                summary += "   Skipped Pages Details:\n"
                for skip_info in skipped_pages:
                    summary += f"      - Page {skip_info['page']}: {skip_info['reason']}\n"
            summary += (
                f"   Average Confidence: {avg_confidence:.2%}\n"
                f"   Total Chunks Created: {len(processed['chunks'])}\n"
                f"{'='*80}\n"
            )
            logger.info(summary)
            console_log(summary)  # Force immediate console output
            
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
            
            # Log error only if document record exists
            if 'doc_id' in dir():
                try:
                    existing_doc = db.query(OCRDocument).filter(OCRDocument.id == doc_id).first()
                    if existing_doc:
                        self._log_step(db, doc_id, None, "pipeline_error", "failed",
                                      error_message=str(e))
                        db.query(OCRDocument).filter(OCRDocument.id == doc_id).update({
                            'ocr_status': 'failed'
                        })
                        db.commit()
                except Exception as log_err:
                    logger.warning(f"Could not log error to database: {log_err}")
            
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
                        "section_ref": chunk.section_ref,
                        "language": chunk.language,
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

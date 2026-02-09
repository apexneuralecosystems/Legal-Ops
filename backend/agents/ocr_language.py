"""
OCR and Language Detection Agent.
"""
from agents.base_agent import BaseAgent
from typing import Dict, Any, List, Optional
import io
import os
import asyncio
from config import settings
import logging
import re

# Set seed for consistent language detection if langdetect is available
def _init_detector_factory():
    try:
        from langdetect import DetectorFactory
        DetectorFactory.seed = 0
    except ImportError:
        pass

_init_detector_factory()

logger = logging.getLogger(__name__)

class OCRLanguageAgent(BaseAgent):
    """
    Performs OCR on images/PDFs and detects language per segment.
    
    Inputs:
    - document: document object with file path/content
    - doc_id: document ID
    
    Outputs:
    - segments: array of {segment_id, doc_id, page, text, lang, confidence}
    - ocr_metadata: overall OCR statistics
    """
    
    def __init__(self):
        super().__init__(agent_id="OCRLanguage")
        # Tesseract configuration is checked lazily in process
    
    async def process(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process OCR and language detection.
        
        Args:
            inputs: {
                "doc_id": str,
                "file_content": bytes,
                "mime_type": str
            }
            
        Returns:
            {
                "segments": List[Dict],
                "ocr_metadata": Dict
            }
        """
        await self.validate_input(inputs, ["doc_id", "file_content", "mime_type"])
        
        doc_id = inputs["doc_id"]
        matter_id = inputs.get("matter_id")
        file_content = inputs["file_content"]
        mime_type = inputs["mime_type"]
        
        segments = []
        actual_page_count = 1  # Default for non-PDFs
        
        logger.info(f"DEBUG: Processing doc {doc_id}, matter={matter_id}, mime={mime_type}")
        
        if mime_type == "application/pdf":
            segments, actual_page_count = await self._process_pdf_with_page_count(doc_id, file_content, matter_id=matter_id)
        elif mime_type.startswith("image/"):
            segments = await self._process_image(doc_id, file_content, page=1)
        else:
            # Text file - no OCR needed
            text = file_content.decode('utf-8', errors='ignore')
            segments = await self._segment_text(doc_id, text, page=1)
        
        # Calculate overall confidence
        if segments:
            avg_ocr_conf = sum(s.get("ocr_confidence", 1.0) for s in segments) / len(segments)
            avg_lang_conf = sum(s.get("lang_confidence", 1.0) for s in segments) / len(segments)
        else:
            avg_ocr_conf = 0.0
            avg_lang_conf = 0.0
        
        ocr_metadata = {
            "total_segments": len(segments),
            "actual_page_count": actual_page_count,  # NEW: Actual PDF page count
            "avg_ocr_confidence": avg_ocr_conf,
            "avg_lang_confidence": avg_lang_conf,
            "languages_detected": list(set(s["lang"] for s in segments))
        }
        
        return self.format_output(
            data={
                "segments": segments,
                "ocr_metadata": ocr_metadata,
                "actual_page_count": actual_page_count  # Also at top level for easy access
            },
            confidence=avg_ocr_conf,
            human_review_required=avg_lang_conf < 0.7
        )
    
    async def _process_pdf_with_page_count(self, doc_id: str, pdf_content: bytes, matter_id: str = None) -> tuple:
        """Process PDF file page-by-page with Google Vision API. Returns (segments, page_count)."""
        segments = []
        actual_page_count = 1
        
        # PRIMARY METHOD: Google Vision API (fast, reliable OCR)
        try:
            from services.vision_ocr_service import get_vision_ocr_service
            from pypdf import PdfReader
            import io
            
            vision_service = get_vision_ocr_service()
            
            # Use pypdf to get page count (safe alternative to fitz)
            reader = PdfReader(io.BytesIO(pdf_content))
            actual_page_count = len(reader.pages)
            
            logger.info(f"Vision OCR: Processing {actual_page_count} pages for doc {doc_id}")
            
            # Progress callback for DB updates
            async def update_db_status(page_done, total):
                if not matter_id:
                    return
                try:
                    from database import SessionLocal
                    from models import Matter
                    from sqlalchemy import update
                    db = SessionLocal()
                    stmt = update(Matter).where(Matter.id == matter_id).values(
                        processing_status=f"OCR reading pages {page_done}/{total}..."
                    )
                    db.execute(stmt)
                    db.commit()
                    db.close()
                except Exception as e:
                    logger.warning(f"Failed to update progress: {e}")
            
            # Extract text from all pages using Vision API
            page_results, actual_page_count = await vision_service.extract_text_from_pdf(
                pdf_content,
                max_concurrent=8,
                progress_callback=update_db_status
            )
            
            # Convert page results to segments
            logger.info(f"\n🔍 PROCESSING PAGE RESULTS FOR {doc_id}")
            for page_result in page_results:
                page_num = page_result["page"]
                page_text = page_result.get("text", "")
                confidence = page_result.get("confidence", 0.95)
                error_msg = page_result.get("error")
                
                if error_msg:
                    logger.warning(f"❌ Page {page_num}/{actual_page_count}: SKIPPED - Error: {error_msg}")
                elif not page_text:
                    logger.warning(f"⚠️  Page {page_num}/{actual_page_count}: SKIPPED - No text extracted")
                elif len(page_text.strip()) < 10:
                    logger.warning(f"⚠️  Page {page_num}/{actual_page_count}: SKIPPED - Text too short ({len(page_text)} chars)")
                else:
                    logger.info(f"✓ Page {page_num}/{actual_page_count}: Processing {len(page_text)} chars (confidence: {confidence:.2%})")
                    page_segs = await self._segment_text(doc_id, page_text, page=page_num, ocr_confidence=confidence)
                    logger.info(f"  → Generated {len(page_segs)} segments from page {page_num}")
                    segments.extend(page_segs)
            
            if not segments:
                errors = [p.get('error') for p in page_results if p.get('error')]
                empty_pages = [p['page'] for p in page_results if not p.get('text')]
                logger.error(f"❌ Vision OCR returned 0 segments from {len(page_results)} page results")
                logger.error(f"   Pages with errors: {errors}")
                logger.error(f"   Empty pages: {empty_pages}")
                raise RuntimeError(f"Vision OCR returned 0 segments from {len(page_results)} pages. Check page_results for errors.")

            logger.info(f"\n✅ Vision OCR Complete: {len(segments)} segments from {actual_page_count} pages")
            return segments, actual_page_count

        except Exception as e:
            logger.error(f"Vision API OCR failed with error: {type(e).__name__}: {e}", exc_info=True)
            logger.warning(f"Falling back to pypdf due to: {e}")
            
            # FALLBACK 1: Try pypdf (pure python, good for text PDFs)
            try:
                import io
                from pypdf import PdfReader
                
                reader = PdfReader(io.BytesIO(pdf_content))
                full_segments = []
                for i, page in enumerate(reader.pages):
                     text = page.extract_text() or ""
                     if text.strip():
                         page_segments = await self._segment_text(doc_id, text, page=i+1)
                         full_segments.extend(page_segments)
                
                if full_segments:
                    logger.info(f"Recovered {len(full_segments)} segments using pypdf fallback.")
                    return full_segments, len(reader.pages)
                
                # If no text found in PDF (e.g. scanned image only), try Gemini via LLMService
                logger.warning(f"pypdf found {len(reader.pages)} pages but 0 text segments (likely scanned/image-only PDF). Attempting Gemini Vision fallback...")
                logger.info(f"This is NORMAL for scanned documents - Gemini can read them but pypdf cannot.")
                
                try:
                    from services.llm_service import get_llm_service
                    llm_service = get_llm_service()
                    
                    # This uses Gemini (or OpenRouter Vision) to read the PDF
                    full_text = await llm_service.extract_pdf_content_from_bytes(pdf_content, f"{doc_id}.pdf")
                    
                    if not full_text or full_text.startswith("["): # Error indicator
                         logger.error(f"Gemini fallback returned error/empty: {full_text[:200]}. PDF may be corrupted or unreadable.")
                         return [], len(reader.pages)
                    
                    logger.info(f"Gemini OCR returned {len(full_text)} chars from scanned PDF")
                    # The LLM prompt asks for "--- PAGE [NUMBER] ---"
                    # We can try to split by that, or just treat as one big page if parsing fails
                    import re
                    page_splits = re.split(r'--- PAGE \d+ ---', full_text)
                    
                    llm_segments = []
                    current_page = 1
                    
                    # If split didn't work effectively (just one chunk), treat as page 1
                    if len(page_splits) < 2:
                        page_splits = [full_text]
                    
                    for text_chunk in page_splits:
                        text_chunk = text_chunk.strip()
                        if text_chunk:
                            page_segs = await self._segment_text(doc_id, text_chunk, page=current_page)
                            llm_segments.extend(page_segs)
                            current_page += 1
                            
                    if llm_segments:
                        logger.info(f"Recovered {len(llm_segments)} segments using Gemini Vision fallback.")
                        return llm_segments, len(reader.pages)
                        
                except Exception as llm_err:
                     logger.error(f"Gemini OCR fallback failed: {llm_err}")

                return [], len(reader.pages)
                
            except Exception as pypdf_err:
                logger.warning(f"pypdf fallback failed: {pypdf_err}")
                return [], 0
    
    async def _process_image(
        self,
        doc_id: str,
        image_content: Any,
        page: int
    ) -> List[Dict[str, Any]]:
        """Process image with Google Vision API OCR."""
        # Ensure we have bytes
        if isinstance(image_content, bytes):
            image_bytes = image_content
        else:
            # Convert PIL Image to bytes
            try:
                from PIL import Image
                import io as _io
                buffer = _io.BytesIO()
                image_content.save(buffer, format='PNG')
                image_bytes = buffer.getvalue()
            except Exception as e:
                logger.error(f"Failed to convert image to bytes: {e}")
                return [{
                    "segment_id": f"SEG-{doc_id}-p{page}-error",
                    "doc_id": doc_id,
                    "page": page,
                    "text": f"[OCR ERROR: Failed to convert image: {e}]",
                    "lang": "unknown",
                    "lang_confidence": 0.0,
                    "ocr_confidence": 0.0,
                    "error": True
                }]
        
        try:
            # Use Google Vision API
            from services.vision_ocr_service import get_vision_ocr_service
            
            vision_service = get_vision_ocr_service()
            text, confidence = await vision_service.extract_text_from_image(image_bytes)
            
            if not text:
                logger.warning(f"Vision OCR returned empty text for image {doc_id}")
                return [{
                    "segment_id": f"SEG-{doc_id}-p{page}-empty",
                    "doc_id": doc_id,
                    "page": page,
                    "text": "[No text detected in image]",
                    "lang": "unknown",
                    "lang_confidence": 0.0,
                    "ocr_confidence": 0.0,
                    "error": False
                }]
            
            logger.info(f"Vision OCR extracted {len(text)} chars with {confidence:.2%} confidence")
            
            # Segment the text
            segments = await self._segment_text(
                doc_id,
                text,
                page,
                ocr_confidence=confidence
            )
            
            return segments
        
        except Exception as e:
            logger.error(f"Vision OCR error: {e}")
            return [{
                "segment_id": f"SEG-{doc_id}-p{page}-error",
                "doc_id": doc_id,
                "page": page,
                "text": f"[OCR ERROR: {str(e)}]",
                "lang": "unknown",
                "lang_confidence": 0.0,
                "ocr_confidence": 0.0,
                "error": True
            }]
    
    async def _segment_text(
        self,
        doc_id: str,
        text: str,
        page: int,
        ocr_confidence: float = 1.0
    ) -> List[Dict[str, Any]]:
        """
        Segment text into sentences and detect language for each.
        
        Args:
            doc_id: Document ID
            text: Full text content
            page: Page number
            ocr_confidence: OCR confidence score
            
        Returns:
            List of segment dictionaries
        """
        segments = []
        
        # Use legal-aware sentence splitting instead of naive period splitting
        # This preserves citations like "S.30", "No. 123", "[2024] 1 MLJ 456"
        sentences = []
        logger.info(f"DEBUG: Segmenting text of length {len(text)}")
        
        try:
            from services.ocr_post_processor import get_ocr_post_processor
            post_processor = get_ocr_post_processor()
            sentences = post_processor.split_sentences_legal(text)
            logger.info(f"DEBUG: Legal-aware split produced {len(sentences)} sentences")
        except ImportError:
            # Fallback to improved splitting if post-processor not available
            logger.warning("Post-processor not available, using improved fallback")
            for line in text.split('\n'):
                line = line.strip()
                if line:
                    # Improved: Don't split on abbreviations
                    # Protect common abbreviations
                    protected = line
                    protected = re.sub(r'\b(No|Dr|Mr|Mrs|Ms|vs|v|S|Art|Sdn|Bhd)\.', r'\1〈DOT〉', protected)
                    # Split on sentence-ending punctuation
                    parts = re.split(r'(?<=[.!?])\s+(?=[A-Z])', protected)
                    for part in parts:
                        part = part.replace('〈DOT〉', '.').strip()
                        if part:
                            sentences.append(part)
        
        logger.info(f"DEBUG: Found {len(sentences)} sentences")
        
        # Detect language for each sentence
        current_lang = None
        current_text = []
        sequence = 0
        current_section = None
        
        for sentence in sentences:
            if len(sentence.strip()) < 3:
                continue
            
            # Extract section reference (e.g., "Section 12.3", "Article 5")
            # Reuse similar logic as in ocr_post_processor
            section_match = re.match(r'^(?:Section|S\.|Article|Art\.|Rule|Regulation)\s*([0-9]+(?:\.[0-9]+)*)', sentence, re.IGNORECASE)
            if section_match:
                new_section = section_match.group(0)
                # Force break if section changes
                if current_text and new_section != current_section:
                    # Save current before switching
                    sequence += 1
                    segments.append({
                        "segment_id": f"SEG-{doc_id}-p{page}-s{sequence}",
                        "doc_id": doc_id,
                        "page": page,
                        "sequence": sequence,
                        "text": ' '.join(current_text),
                        "lang": current_lang,
                        "lang_confidence": lang_confidence,
                        "ocr_confidence": ocr_confidence,
                        "human_check_required": lang_confidence < 0.7,
                        "section_ref": current_section
                    })
                    current_text = []
                
                current_section = new_section

            
            # Detect language
            try:
                from langdetect import detect
                detected_lang = detect(sentence)
                logger.debug(f"Sentence lang={detected_lang}: '{sentence[:50]}...'")
                # Map to our language codes
                if detected_lang == 'ms':
                    lang = 'ms'
                elif detected_lang in ['en', 'id']:  # Indonesian often confused with Malay
                    lang = 'en' if 'the' in sentence.lower() or 'is' in sentence.lower() else 'ms'
                else:
                    lang = 'en'  # default to English
                
                lang_confidence = 0.85  # langdetect doesn't provide confidence
            except (ImportError, Exception) as e:
                msg = str(e)
                if "No features in text" in msg:
                    # Common expected error for numbers/symbols
                    logger.debug(f"Language detection skip for short/numeric text: {sentence[:30]}")
                elif "langdetect" in msg.lower():
                    logger.warning(f"langdetect library not installed - defaulting to English. Install with: pip install langdetect")
                else:
                    logger.warning(f"Language detection failed for '{sentence[:30]}...': {msg}")
                lang = 'en'  # Default to English if library missing or failure
                lang_confidence = 0.5
            
            # Merge adjacent sentences of same language ONLY if they are short fragments
            # This ensures granularity (sentence-level) while avoiding tiny noise segments
            should_merge = (
                lang == current_lang and 
                current_text and 
                (len(' '.join(current_text)) < 150 or len(sentence) < 50)
            )
            
            if should_merge:
                current_text.append(sentence)
            else:
                # Save previous segment
                if current_text:
                    sequence += 1
                    segments.append({
                        "segment_id": f"SEG-{doc_id}-p{page}-s{sequence}",
                        "doc_id": doc_id,
                        "page": page,
                        "sequence": sequence,
                        "text": ' '.join(current_text),
                        "lang": current_lang,
                        "lang_confidence": lang_confidence,
                        "ocr_confidence": ocr_confidence,
                        "human_check_required": lang_confidence < 0.7,
                        "section_ref": current_section
                    })
                
                # Start new segment
                current_lang = lang
                current_text = [sentence]
        
        # Add final segment
        if current_text:
            sequence += 1
            segments.append({
                "segment_id": f"SEG-{doc_id}-p{page}-s{sequence}",
                "doc_id": doc_id,
                "page": page,
                "sequence": sequence,
                "text": ' '.join(current_text),
                "lang": current_lang,
                "lang_confidence": lang_confidence,
                "ocr_confidence": ocr_confidence,
                "human_check_required": lang_confidence < 0.7,
                "section_ref": current_section
            })
        
        return segments

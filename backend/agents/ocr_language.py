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
            import fitz  # PyMuPDF
            
            vision_service = get_vision_ocr_service()
            
            # Open PDF with PyMuPDF to get page count
            doc = fitz.open(stream=pdf_content, filetype="pdf")
            actual_page_count = len(doc)
            doc.close()
            
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
            for page_result in page_results:
                page_num = page_result["page"]
                page_text = page_result.get("text", "")
                confidence = page_result.get("confidence", 0.95)
                
                if page_text and not page_result.get("error"):
                    logger.info(f"Page {page_num} extracted: {len(page_text)} chars")
                    page_segs = await self._segment_text(doc_id, page_text, page=page_num, ocr_confidence=confidence)
                    segments.extend(page_segs)
                else:
                    logger.warning(f"Page {page_num} failed or empty: {page_result.get('error', 'No text')}")
            
            logger.info(f"Vision OCR: Completed {len(segments)} segments from {actual_page_count} pages")
            return segments, actual_page_count

        except Exception as e:
            logger.warning(f"Vision API OCR failed: {e}. Falling back to pypdf.")
            
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
                    import re
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
        
        for sentence in sentences:
            if len(sentence.strip()) < 3:
                continue
            
            # Detect language
            try:
                from langdetect import detect
                detected_lang = detect(sentence)
                logger.info(f"DEBUG: Sentence '{sentence[:30]}...' detected as '{detected_lang}'")
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
                    logger.debug(f"Language detection skip for short text: {msg}")
                else:
                    logger.warning(f"Language detection failed: {msg}")
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
                        "human_check_required": lang_confidence < 0.7
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
                "human_check_required": lang_confidence < 0.7
            })
        
        return segments

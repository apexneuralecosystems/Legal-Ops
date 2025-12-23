"""
OCR and Language Detection Agent.
"""
from agents.base_agent import BaseAgent
from typing import Dict, Any, List, Optional
import pytesseract
from PIL import Image
import io
from pdf2image import convert_from_bytes
from langdetect import detect, DetectorFactory
from config import settings
import logging

# Set seed for consistent language detection
DetectorFactory.seed = 0

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
        # Configure Tesseract
        if settings.TESSERACT_CMD:
            pytesseract.pytesseract.tesseract_cmd = settings.TESSERACT_CMD
    
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
        file_content = inputs["file_content"]
        mime_type = inputs["mime_type"]
        
        segments = []
        actual_page_count = 1  # Default for non-PDFs
        
        logger.info(f"DEBUG: Processing doc {doc_id}, mime={mime_type}, size={len(file_content)}")
        
        if mime_type == "application/pdf":
            segments, actual_page_count = await self._process_pdf_with_page_count(doc_id, file_content)
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
    
    async def _process_pdf_with_page_count(self, doc_id: str, pdf_content: bytes) -> tuple:
        """Process PDF file with text extraction fallback to OCR. Returns (segments, page_count)."""
        segments = []
        actual_page_count = 1
        
        # Try text extraction first (faster and doesn't need Poppler)
        try:
            import PyPDF2
            pdf_reader = PyPDF2.PdfReader(io.BytesIO(pdf_content))
            actual_page_count = len(pdf_reader.pages)  # Get actual page count
            full_text = ""
            for page in pdf_reader.pages:
                full_text += page.extract_text() + "\n"
            
            if full_text.strip():
                logger.info(f"Successfully extracted text from PDF {doc_id} without OCR. Length: {len(full_text)}, Pages: {actual_page_count}")
                logger.info(f"Extracted Text Preview: {full_text[:200]}")
                segments = await self._segment_text(doc_id, full_text, page=1, ocr_confidence=1.0)
                return segments, actual_page_count
            else:
                logger.warning(f"PDF text extraction returned empty string for {doc_id}")
                
        except Exception as e:
            logger.warning(f"Text extraction failed, falling back to OCR: {e}")

        try:
            # Convert PDF to images
            images = convert_from_bytes(pdf_content)
            actual_page_count = len(images)  # Get page count from images
            
            for page_num, image in enumerate(images, start=1):
                page_segments = await self._process_image(doc_id, image, page=page_num)
                segments.extend(page_segments)
        
        except Exception as e:
            print(f"Error processing PDF: {e}")
            # Return empty segments with error flag
            segments.append({
                "segment_id": f"SEG-{doc_id}-error",
                "doc_id": doc_id,
                "page": 1,
                "text": f"[OCR ERROR: {str(e)}]",
                "lang": "unknown",
                "lang_confidence": 0.0,
                "ocr_confidence": 0.0,
                "error": True
            })
        
        return segments, actual_page_count
    
    async def _process_image(
        self,
        doc_id: str,
        image_content: Any,
        page: int
    ) -> List[Dict[str, Any]]:
        """Process image with OCR."""
        
        # If image_content is bytes, convert to PIL Image
        if isinstance(image_content, bytes):
            image = Image.open(io.BytesIO(image_content))
        else:
            image = image_content
        
        try:
            # Perform OCR with confidence data
            ocr_data = pytesseract.image_to_data(
                image,
                lang=settings.OCR_LANGUAGES,
                output_type=pytesseract.Output.DICT
            )
            
            # Extract text with confidence
            text_parts = []
            confidences = []
            
            for i, text in enumerate(ocr_data['text']):
                if text.strip():
                    text_parts.append(text)
                    confidences.append(int(ocr_data['conf'][i]))
            
            full_text = ' '.join(text_parts)
            avg_confidence = sum(confidences) / len(confidences) if confidences else 0.0
            
            # Segment the text
            segments = await self._segment_text(
                doc_id,
                full_text,
                page,
                ocr_confidence=avg_confidence / 100.0
            )
            
            return segments
        
        except Exception as e:
            print(f"Error in OCR: {e}")
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
        
        # Simple sentence segmentation (split by periods, newlines)
        sentences = []
        logger.info(f"DEBUG: Segmenting text of length {len(text)}")
        for line in text.split('\n'):
            line = line.strip()
            if line:
                # Split by period but keep the period
                parts = line.split('.')
                for part in parts:
                    if part.strip():
                        sentences.append(part.strip() + '.')
        
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
            except Exception as e:
                logger.error(f"DEBUG: Language detection failed for '{sentence[:30]}...': {e}")
                lang = 'unknown'
                lang_confidence = 0.0
            
            # Merge adjacent sentences of same language
            if lang == current_lang and current_text:
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

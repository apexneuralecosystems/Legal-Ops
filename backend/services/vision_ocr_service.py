"""
Google Vision API OCR Service
==============================
Uses Google Cloud Vision REST API for text extraction from images and PDFs.
Much faster than LLM-based OCR (~1-3 seconds per page vs 5-15 seconds).
"""
import aiohttp
import asyncio
import base64
import logging
from typing import List, Tuple, Optional
from config import settings

logger = logging.getLogger(__name__)

# Google Vision API endpoint
VISION_API_URL = "https://vision.googleapis.com/v1/images:annotate"


class VisionOCRService:
    """
    Google Vision API OCR service using REST API.
    
    Usage:
        from services.vision_ocr_service import vision_ocr_service
        text = await vision_ocr_service.extract_text_from_image(image_bytes)
    """
    
    def __init__(self, api_key: str = None):
        self.api_key = api_key or settings.GOOGLE_VISION_API_KEY
        self.language_hints = self._build_language_hints()
        if not self.api_key:
            logger.warning("GOOGLE_VISION_API_KEY not set. Vision OCR will fail.")

    def _build_language_hints(self) -> List[str]:
        raw = settings.OCR_LANGUAGES or ""
        parts = [p.strip() for p in raw.replace(",", "+").split("+") if p.strip()]
        mapping = {"eng": "en", "msa": "ms"}
        hints = []
        for p in parts:
            hints.append(mapping.get(p, p))
        if not hints:
            hints = ["en"]
        return hints
    
    async def extract_text_from_image(self, image_bytes: bytes) -> Tuple[str, float]:
        """
        Extract text from an image using Google Vision API.
        
        Args:
            image_bytes: Image content as bytes (PNG, JPG, etc.)
            
        Returns:
            Tuple of (extracted_text, confidence_score)
        """
        if not self.api_key:
            raise ValueError("GOOGLE_VISION_API_KEY is not configured")
        
        # Base64 encode the image
        image_b64 = base64.b64encode(image_bytes).decode('utf-8')
        
        # Prepare the request payload
        # Using DOCUMENT_TEXT_DETECTION for better layout understanding in legal docs
        payload = {
            "requests": [
                {
                    "image": {
                        "content": image_b64
                    },
                    "features": [
                        {
                            "type": "DOCUMENT_TEXT_DETECTION",
                            "maxResults": 1
                        }
                    ],
                    "imageContext": {
                        "languageHints": self.language_hints
                    }
                }
            ]
        }
        
        # Make the API request
        url = f"{VISION_API_URL}?key={self.api_key}"
        
        async with aiohttp.ClientSession() as session:
            async with session.post(
                url,
                json=payload,
                headers={"Content-Type": "application/json"},
                timeout=aiohttp.ClientTimeout(total=30)
            ) as response:
                if response.status != 200:
                    error_text = await response.text()
                    logger.error(f"Vision API HTTP {response.status}: {error_text}")
                    logger.error(f"Request URL: {url}")
                    logger.error(f"API Key Present: {bool(self.api_key)}, Length: {len(self.api_key) if self.api_key else 0}")
                    raise RuntimeError(f"Vision API HTTP {response.status}: {error_text[:500]}")
                
                result = await response.json()
        
        # Parse the response
        responses = result.get("responses", [])
        if not responses:
            return "", 0.0
        
        first_response = responses[0]
        
        # Check for errors
        if "error" in first_response:
            error = first_response["error"]
            logger.error(f"Vision API returned error in response: {error}")
            logger.error(f"Full error details: code={error.get('code')}, message={error.get('message')}, status={error.get('status')}")
            raise RuntimeError(f"Vision API error (code {error.get('code', 'unknown')}): {error.get('message', 'Unknown error')}")
        
        # Get full text annotation (best result)
        full_text = first_response.get("fullTextAnnotation", {})
        if full_text:
            text = full_text.get("text", "")
            # Calculate average confidence from pages
            pages = full_text.get("pages", [])
            if pages:
                confidences = []
                for page in pages:
                    for block in page.get("blocks", []):
                        conf = block.get("confidence", 0)
                        if conf > 0:
                            confidences.append(conf)
                avg_confidence = sum(confidences) / len(confidences) if confidences else 0.95
            else:
                avg_confidence = 0.95
            return text, avg_confidence
        
        # Fallback to text annotations
        text_annotations = first_response.get("textAnnotations", [])
        if text_annotations:
            # First annotation contains the full text
            text = text_annotations[0].get("description", "")
            return text, 0.9  # Default confidence for TEXT_DETECTION
        
        return "", 0.0
    
    async def extract_text_from_pdf(
        self, 
        pdf_bytes: bytes, 
        max_concurrent: int = 8,
        progress_callback=None
    ) -> Tuple[List[dict], int]:
        """
        Extract text from a PDF by converting pages to images and using Vision API.
        Supports multiple PDF processing backends: PyMuPDF, pdf2image, or pypdf.
        
        Args:
            pdf_bytes: PDF content as bytes
            max_concurrent: Maximum concurrent API calls (default: 8)
            progress_callback: Optional async callback(page_done, total) for progress updates
            
        Returns:
            Tuple of (list of page results, total page count)
            Each page result: {"page": int, "text": str, "confidence": float}
        """
        # Try different PDF processing backends
        page_images = []
        total_pages = 0
        
        # Option 1: Try PyMuPDF (fitz) - DISABLED due to persistent environment issues (fitz vs pymupdf)
        # try:
        #     import fitz
        #     # CRITICAL FIX: Check if this is actually PyMuPDF (has 'open') or the wrong 'fitz' package
        #     if not hasattr(fitz, "open"):
        #         logger.warning("Detected incorrectly installed 'fitz' package (missing 'open'). Triggering fallback.")
        #         raise ImportError("Authentication error: 'fitz' package is not PyMuPDF")
        #         
        #     doc = fitz.open(stream=pdf_bytes, filetype="pdf")
        #     total_pages = len(doc)
        #     logger.info(f"Vision OCR: Using PyMuPDF for {total_pages} pages")
        #     
        #     for i in range(total_pages):
        #         page = doc.load_page(i)
        #         # Use 300 DPI (4.17x scale) for better OCR accuracy on legal documents
        #         # PDF default is 72 DPI, so 300/72 ≈ 4.17
        #         pix = page.get_pixmap(matrix=fitz.Matrix(4.17, 4.17))
        #         page_images.append(pix.tobytes("png"))
        #     doc.close()
        # except ImportError:
        pass # Skip fitz
            
        if not page_images:
            # Option 2: Try DIRECT Google Vision PDF Upload (Preferred over local rendering)
            # This is much faster and more reliable than converting to images locally
            try:
                logger.info("Attempting DIRECT PDF submission to Google Vision (Priority Mode).")
                # Use pypdf to count pages if we haven't already
                if total_pages == 0:
                    from pypdf import PdfReader
                    import io
                    reader = PdfReader(io.BytesIO(pdf_bytes))
                    total_pages = len(reader.pages)
                    
                # We need to await this
                results = await self.extract_text_from_pdf_direct(pdf_bytes, total_pages)
                if results:
                    return results, total_pages
                logger.warning("Direct Vision API returned no results, falling back to local OCR")
            except Exception as e:
                 logger.warning(f"Direct Vision API failed ({e}), falling back to local OCR")

            logger.info("PyMuPDF disabled/failed and Direct Vision skipped/failed, trying pdf2image")
            
            # Option 2: Try pdf2image (requires Poppler)
            try:
                from pdf2image import convert_from_bytes
                import io
                
                images = convert_from_bytes(pdf_bytes, dpi=200)
                total_pages = len(images)
                logger.info(f"Vision OCR: Using pdf2image for {total_pages} pages")
                
                for img in images:
                    buffer = io.BytesIO()
                    img.save(buffer, format='PNG')
                    page_images.append(buffer.getvalue())
            except (ImportError, Exception) as e:
                logger.info(f"pdf2image not available ({e}), trying PyPDF2")
                
                # Option 3: Try PyPDF2 - extract text directly (not images, but usable)
                try:
                    from PyPDF2 import PdfReader
                    import io
                    
                    reader = PdfReader(io.BytesIO(pdf_bytes))
                    total_pages = len(reader.pages)
                    logger.info(f"Vision OCR: Using PyPDF2 text extraction for {total_pages} pages (no images)")
                    
                    # PyPDF2 extracts text directly, no need for Vision API
                    results = []
                    for i, page in enumerate(reader.pages):
                        text = page.extract_text() or ""
                        if progress_callback:
                            try:
                                await progress_callback(i + 1, total_pages)
                            except:
                                pass
                        results.append({
                            "page": i + 1,
                            "text": text,
                            "confidence": 0.85 if text else 0.0
                        })
                    return results, total_pages
                except ImportError:
                    raise ImportError("No PDF processing library available. Install one of: PyMuPDF, pdf2image+Poppler, or PyPDF2")
        
        # Old Direct PDF block removed (moved to top priority)
        
        logger.info(f"Vision OCR: Processing {total_pages} pages with max {max_concurrent} concurrent requests")
        
        # Semaphore for concurrency control
        semaphore = asyncio.Semaphore(max_concurrent)
        
        async def process_page(page_num: int, image_bytes: bytes):
            async with semaphore:
                try:
                    logger.debug(f"Vision OCR: Processing page {page_num + 1}/{total_pages}")
                    
                    # Extract text using Vision API
                    text, confidence = await self.extract_text_from_image(image_bytes)
                    
                    # Update progress
                    if progress_callback:
                        try:
                            await progress_callback(page_num + 1, total_pages)
                        except Exception as e:
                            logger.debug(f"Progress callback error (non-fatal): {e}")
                    
                    logger.debug(f"Vision OCR: Page {page_num + 1} completed - {len(text)} chars, confidence {confidence:.2f}")
                    
                    return {
                        "page": page_num + 1,
                        "text": text,
                        "confidence": confidence
                    }
                except Exception as e:
                    logger.error(f"Vision OCR: Page {page_num + 1} failed: {type(e).__name__}: {e}", exc_info=True)
                    return {
                        "page": page_num + 1,
                        "text": "",
                        "confidence": 0.0,
                        "error": str(e)
                    }
        
        # Process all pages concurrently
        tasks = [process_page(i, img) for i, img in enumerate(page_images)]
        results = await asyncio.gather(*tasks)
        
        # Sort by page number
        results = sorted(results, key=lambda x: x["page"])
        
        # Log summary
        successful = sum(1 for r in results if r.get("text"))
        logger.info(f"Vision OCR: Completed {successful}/{total_pages} pages successfully")
        
        return results, total_pages
    
    async def test_connection(self) -> dict:
        """Test the Vision API connection with a simple request."""
        if not self.api_key:
            return {"success": False, "error": "API key not configured"}
        
        # Create a tiny test image (1x1 white pixel PNG)
        # This is a minimal valid PNG
        test_png = bytes([
            0x89, 0x50, 0x4E, 0x47, 0x0D, 0x0A, 0x1A, 0x0A,  # PNG signature
            0x00, 0x00, 0x00, 0x0D, 0x49, 0x48, 0x44, 0x52,  # IHDR chunk
            0x00, 0x00, 0x00, 0x01, 0x00, 0x00, 0x00, 0x01,  # 1x1
            0x08, 0x02, 0x00, 0x00, 0x00, 0x90, 0x77, 0x53,
            0xDE, 0x00, 0x00, 0x00, 0x0C, 0x49, 0x44, 0x41,  # IDAT chunk
            0x54, 0x08, 0xD7, 0x63, 0xF8, 0xFF, 0xFF, 0xFF,
            0x00, 0x05, 0xFE, 0x02, 0xFE, 0xDC, 0xCC, 0x59,
            0xE7, 0x00, 0x00, 0x00, 0x00, 0x49, 0x45, 0x4E,  # IEND chunk
            0x44, 0xAE, 0x42, 0x60, 0x82
        ])
        
        try:
            text, confidence = await self.extract_text_from_image(test_png)
            return {
                "success": True,
                "message": "Vision API connection successful",
                "api_key_prefix": self.api_key[:10] + "..."
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }

    async def extract_text_from_pdf_direct(self, pdf_bytes: bytes, total_pages: int) -> List[dict]:
        """
        Directly send PDF to Google Vision API (files:annotate).
        This bypasses local image conversion issues.
        Limitations: Max 5 pages per request, max 10MB per request.
        """
        if not self.api_key:
             return []

        # Split PDF into chunks of 5 pages using pypdf
        import io
        from pypdf import PdfReader, PdfWriter
        
        logger.info("Vision OCR: Using DIRECT PDF mode (files:annotate)")
        
        chunks = []
        try:
            reader = PdfReader(io.BytesIO(pdf_bytes))
            current_writer = PdfWriter()
            current_page_count = 0
            start_page = 0
            
            for i, page in enumerate(reader.pages):
                current_writer.add_page(page)
                current_page_count += 1
                
                if current_page_count == 5 or i == len(reader.pages) - 1:
                    # Finalize chunk
                    out_buffer = io.BytesIO()
                    current_writer.write(out_buffer)
                    chunks.append({
                        "bytes": out_buffer.getvalue(),
                        "start": start_page,
                        "pages": current_page_count
                    })
                    # Reset
                    current_writer = PdfWriter()
                    start_page = i + 1
                    current_page_count = 0
                    
        except Exception as e:
            logger.error(f"Direct OCR split failed: {e}")
            return []

        # Process chunks
        all_results = []
        url = f"https://vision.googleapis.com/v1/files:annotate?key={self.api_key}"
        
        for chunk in chunks:
            chunk_b64 = base64.b64encode(chunk["bytes"]).decode('utf-8')
            
            payload = {
                "requests": [
                    {
                        "inputConfig": {
                            "content": chunk_b64,
                            "mimeType": "application/pdf"
                        },
                        "features": [{"type": "DOCUMENT_TEXT_DETECTION"}],
                        "pages": [i+1 for i in range(chunk["pages"])] # 1-based index relative to chunk
                    }
                ]
            }
            
            try:
                logger.info(f"Using Vision API URL: {url}")
                logger.info(f"Payload keys: {list(payload.keys())}")
                logger.info(f"Payload requests count: {len(payload['requests'])}")
                async with aiohttp.ClientSession() as session:
                    async with session.post(url, json=payload, headers={"Content-Type": "application/json"}) as response:
                        if response.status != 200:
                            logger.error(f"Direct Vision API failed: {await response.text()}")
                            continue
                        
                        data = await response.json()
                        # DEBUG: Log keys to debug structure
                        logger.info(f"DEBUG: Vision API Response Keys: {list(data.keys())}")
                        if "responses" in data and len(data["responses"]) > 0:
                             logger.info(f"DEBUG: Top-level responses count: {len(data['responses'])}")
                             if "responses" in data["responses"][0]:
                                  logger.info(f"DEBUG: Nested responses found! Count: {len(data['responses'][0]['responses'])}")
                             else:
                                  logger.info("DEBUG: NO nested responses found in first element.")
                                  # Only log full dump if structure looks wrong to avoid massive logs
                                  logger.info(f"DEBUG: First element keys: {list(data['responses'][0].keys())}")

                        # The API returns a list of AnnotateFileResponse objects (one per request)
                        # Each AnnotateFileResponse contains a list of 'responses' (one per page)
                        file_responses = data.get("responses", [])
                        
                        for file_resp in file_responses:
                            # Check for top-level error in file response
                            if "error" in file_resp:
                                logger.error(f"Vision API file error: {file_resp['error']}")
                                continue
                                
                            page_responses = file_resp.get("responses", [])
                            
                            for i, page_resp in enumerate(page_responses):
                                # Map back to global page number
                                # inner loop index 'i' maps to the page index in the chunk
                                global_page = chunk["start"] + i + 1
                                
                                full_text = page_resp.get("fullTextAnnotation", {}).get("text", "")
                                
                                # Calculate confidence (simplified)
                                conf = 0.95 
                                
                                if full_text:
                                    all_results.append({
                                        "page": global_page,
                                        "text": full_text,
                                        "confidence": conf
                                    })
                                else:
                                     # Log empty pages for debug
                                     error = page_resp.get("error", {})
                                     if error:
                                         logger.warning(f"Vision API page {global_page} error: {error}")
            except Exception as e:
                logger.error(f"Chunk processing failed: {e}")
        
        results = sorted(all_results, key=lambda x: x["page"])
        
        if not results and total_pages > 0:
            raise RuntimeError("Vision API returned no text for any page (Direct Mode)")
            
        return results


# Global instance
_vision_ocr_service = None


def get_vision_ocr_service() -> VisionOCRService:
    """Get the global Vision OCR service instance."""
    global _vision_ocr_service
    if _vision_ocr_service is None:
        _vision_ocr_service = VisionOCRService()
    return _vision_ocr_service





vision_ocr_service = get_vision_ocr_service()

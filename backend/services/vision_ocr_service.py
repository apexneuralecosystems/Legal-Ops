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
        if not self.api_key:
            logger.warning("GOOGLE_VISION_API_KEY not set. Vision OCR will fail.")
    
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
                        "languageHints": ["en", "ms"]  # English + Malay for legal docs
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
                    logger.error(f"Vision API error {response.status}: {error_text}")
                    raise RuntimeError(f"Vision API error: {error_text}")
                
                result = await response.json()
        
        # Parse the response
        responses = result.get("responses", [])
        if not responses:
            return "", 0.0
        
        first_response = responses[0]
        
        # Check for errors
        if "error" in first_response:
            error = first_response["error"]
            raise RuntimeError(f"Vision API error: {error.get('message', 'Unknown error')}")
        
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
        
        # Option 1: Try PyMuPDF (fitz)
        try:
            import fitz
            doc = fitz.open(stream=pdf_bytes, filetype="pdf")
            total_pages = len(doc)
            logger.info(f"Vision OCR: Using PyMuPDF for {total_pages} pages")
            
            for i in range(total_pages):
                page = doc.load_page(i)
                # Use 300 DPI (4.17x scale) for better OCR accuracy on legal documents
                # PDF default is 72 DPI, so 300/72 ≈ 4.17
                pix = page.get_pixmap(matrix=fitz.Matrix(4.17, 4.17))
                page_images.append(pix.tobytes("png"))
            doc.close()
        except ImportError:
            logger.info("PyMuPDF not available, trying pdf2image")
            
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
        
        if not page_images:
            return [], 0
        
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
                            logger.debug(f"Progress callback error: {e}")
                    
                    return {
                        "page": page_num + 1,
                        "text": text,
                        "confidence": confidence
                    }
                except Exception as e:
                    logger.error(f"Vision OCR: Page {page_num + 1} failed: {e}")
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


# Global instance
_vision_ocr_service = None


def get_vision_ocr_service() -> VisionOCRService:
    """Get the global Vision OCR service instance."""
    global _vision_ocr_service
    if _vision_ocr_service is None:
        _vision_ocr_service = VisionOCRService()
    return _vision_ocr_service


# Convenience alias
vision_ocr_service = get_vision_ocr_service()

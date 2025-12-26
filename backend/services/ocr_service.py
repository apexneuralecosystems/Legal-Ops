"""
Multi-backend OCR Service for Legal-Ops
=======================================
Supports multiple OCR backends with automatic fallback:
- Tesseract (primary, if installed)
- PyMuPDF (fallback for PDF text extraction)
- Google Cloud Vision (cloud fallback)
"""
import platform
import shutil
import logging
from pathlib import Path
from typing import Optional, Tuple
from config import settings

logger = logging.getLogger(__name__)


class OCRService:
    """
    Unified OCR service with multiple backend support.
    
    Usage:
        from services.ocr_service import ocr_service
        text = ocr_service.extract_text("/path/to/image.png")
    """
    
    def __init__(self):
        self.engine = None
        self._tesseract_path = None
        self._initialize()
    
    def _initialize(self):
        """Initialize and detect available OCR engine."""
        if settings.OCR_ENGINE != "auto":
            self.engine = settings.OCR_ENGINE
            logger.info(f"OCR engine set to: {self.engine}")
        else:
            self.engine = self._auto_detect_engine()
            logger.info(f"Auto-detected OCR engine: {self.engine}")
    
    def _auto_detect_engine(self) -> str:
        """Auto-detect the best available OCR engine."""
        # Try Tesseract first (best quality)
        tesseract_path = self._find_tesseract()
        if tesseract_path:
            self._tesseract_path = tesseract_path
            return "tesseract"
        
        # Try PyMuPDF (good for PDFs with embedded text)
        try:
            import fitz  # PyMuPDF
            return "pymupdf"
        except ImportError:
            logger.debug("PyMuPDF not available")
        
        # Try Google Cloud Vision (cloud fallback)
        if settings.GOOGLE_VISION_API_KEY:
            return "google_vision"
        
        # No OCR available
        logger.warning("No OCR engine available - text extraction will fail")
        return "none"
    
    def _find_tesseract(self) -> Optional[str]:
        """Find Tesseract executable path."""
        # Check configured path first
        if settings.TESSERACT_CMD and Path(settings.TESSERACT_CMD).exists():
            return settings.TESSERACT_CMD
        
        # Try system PATH
        system_tesseract = shutil.which("tesseract")
        if system_tesseract:
            return system_tesseract
        
        # Windows default paths
        if platform.system() == "Windows":
            default_paths = [
                r"C:\Program Files\Tesseract-OCR\tesseract.exe",
                r"C:\Program Files (x86)\Tesseract-OCR\tesseract.exe",
                r"C:\Tesseract-OCR\tesseract.exe",
            ]
            for path in default_paths:
                if Path(path).exists():
                    return path
        
        # Linux/Mac default paths
        else:
            default_paths = [
                "/usr/bin/tesseract",
                "/usr/local/bin/tesseract",
                "/opt/homebrew/bin/tesseract",
            ]
            for path in default_paths:
                if Path(path).exists():
                    return path
        
        return None
    
    @property
    def is_available(self) -> bool:
        """Check if any OCR engine is available."""
        return self.engine != "none"
    
    @property
    def engine_info(self) -> dict:
        """Get information about the current OCR engine."""
        return {
            "engine": self.engine,
            "available": self.is_available,
            "tesseract_path": self._tesseract_path,
            "languages": settings.OCR_LANGUAGES,
        }
    
    def extract_text(self, file_path: str) -> str:
        """
        Extract text from an image or PDF file.
        
        Args:
            file_path: Path to the image or PDF file
            
        Returns:
            Extracted text as string
        """
        if not self.is_available:
            raise RuntimeError("No OCR engine available. Install Tesseract or PyMuPDF.")
        
        file_path = Path(file_path)
        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")
        
        logger.info(f"Extracting text from {file_path} using {self.engine}")
        
        try:
            if self.engine == "tesseract":
                return self._ocr_tesseract(str(file_path))
            elif self.engine == "pymupdf":
                return self._ocr_pymupdf(str(file_path))
            elif self.engine == "google_vision":
                return self._ocr_google_vision(str(file_path))
            else:
                raise ValueError(f"Unknown OCR engine: {self.engine}")
        except Exception as e:
            logger.error(f"OCR failed with {self.engine}: {e}")
            # Try fallback
            return self._try_fallback(str(file_path), exclude=self.engine)
    
    def _try_fallback(self, file_path: str, exclude: str) -> str:
        """Try alternative OCR engines as fallback."""
        fallback_order = ["tesseract", "pymupdf", "google_vision"]
        
        for engine in fallback_order:
            if engine == exclude:
                continue
            
            try:
                if engine == "tesseract" and self._find_tesseract():
                    logger.info(f"Falling back to {engine}")
                    return self._ocr_tesseract(file_path)
                elif engine == "pymupdf":
                    try:
                        import fitz
                        logger.info(f"Falling back to {engine}")
                        return self._ocr_pymupdf(file_path)
                    except ImportError:
                        continue
                elif engine == "google_vision" and settings.GOOGLE_VISION_API_KEY:
                    logger.info(f"Falling back to {engine}")
                    return self._ocr_google_vision(file_path)
            except Exception as e:
                logger.warning(f"Fallback {engine} failed: {e}")
                continue
        
        raise RuntimeError("All OCR engines failed")
    
    def _ocr_tesseract(self, file_path: str) -> str:
        """Use Tesseract OCR for text extraction."""
        import pytesseract
        from PIL import Image
        
        # Set Tesseract path
        if self._tesseract_path:
            pytesseract.pytesseract.tesseract_cmd = self._tesseract_path
        
        # Handle PDFs by converting to images first
        if file_path.lower().endswith('.pdf'):
            from pdf2image import convert_from_path
            images = convert_from_path(file_path)
            text_parts = []
            for i, image in enumerate(images):
                text = pytesseract.image_to_string(image, lang=settings.OCR_LANGUAGES)
                text_parts.append(f"--- Page {i+1} ---\n{text}")
            return "\n\n".join(text_parts)
        else:
            image = Image.open(file_path)
            return pytesseract.image_to_string(image, lang=settings.OCR_LANGUAGES)
    
    def _ocr_pymupdf(self, file_path: str) -> str:
        """
        Use PyMuPDF for text extraction.
        Note: This extracts embedded text, not true OCR.
        Works great for PDFs with selectable text.
        """
        import fitz
        
        doc = fitz.open(file_path)
        text_parts = []
        
        for page_num, page in enumerate(doc):
            text = page.get_text()
            if text.strip():
                text_parts.append(f"--- Page {page_num + 1} ---\n{text}")
        
        doc.close()
        
        if not text_parts:
            raise ValueError("No text found in PDF - may need OCR")
        
        return "\n\n".join(text_parts)
    
    def _ocr_google_vision(self, file_path: str) -> str:
        """Use Google Cloud Vision API for OCR."""
        try:
            from google.cloud import vision
        except ImportError:
            raise ImportError("google-cloud-vision package required for Google Vision OCR")
        
        client = vision.ImageAnnotatorClient()
        
        with open(file_path, "rb") as f:
            content = f.read()
        
        image = vision.Image(content=content)
        response = client.text_detection(image=image)
        
        if response.error.message:
            raise RuntimeError(f"Google Vision API error: {response.error.message}")
        
        if response.text_annotations:
            return response.text_annotations[0].description
        
        return ""
    
    def get_confidence(self, file_path: str) -> Tuple[str, float]:
        """
        Extract text with confidence score (Tesseract only).
        
        Returns:
            Tuple of (text, confidence_score)
        """
        if self.engine != "tesseract":
            return self.extract_text(file_path), 0.0
        
        import pytesseract
        from PIL import Image
        
        if self._tesseract_path:
            pytesseract.pytesseract.tesseract_cmd = self._tesseract_path
        
        image = Image.open(file_path)
        data = pytesseract.image_to_data(image, lang=settings.OCR_LANGUAGES, output_type=pytesseract.Output.DICT)
        
        # Calculate average confidence
        confidences = [int(c) for c in data['conf'] if int(c) > 0]
        avg_confidence = sum(confidences) / len(confidences) if confidences else 0.0
        
        text = pytesseract.image_to_string(image, lang=settings.OCR_LANGUAGES)
        
        return text, avg_confidence / 100.0


# Global instance - lazy initialization
_ocr_service = None

def get_ocr_service() -> OCRService:
    """Get the global OCR service instance."""
    global _ocr_service
    if _ocr_service is None:
        _ocr_service = OCRService()
    return _ocr_service

# Convenience alias
ocr_service = property(lambda self: get_ocr_service())

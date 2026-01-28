"""
LLM Service - Unified interface for language model providers.
Supports Google Gemini and OpenRouter APIs with automatic fallback.
"""
import logging
from typing import Optional
from config import settings

logger = logging.getLogger(__name__)

# Global LLM service instance
_llm_service = None


class LLMService:
    """
    Unified LLM interface that supports both Gemini and OpenRouter.
    
    Usage:
        llm = get_llm_service()
        response = await llm.generate("Your prompt here")
    """
    
    def __init__(self):
        self.provider = settings.LLM_PROVIDER.lower()
        self._gemini_model = None
        self._openrouter_client = None
        
        if self.provider == "openrouter":
            self._init_openrouter()
        else:
            self._init_gemini()
    
    def _init_gemini(self):
        """Initialize Google Gemini client."""
        try:
            import google.generativeai as genai
            
            if not settings.GEMINI_API_KEY:
                raise ValueError("GEMINI_API_KEY is not set")
            
            genai.configure(api_key=settings.GEMINI_API_KEY)
            self._gemini_model = genai.GenerativeModel(settings.GEMINI_MODEL)
            logger.info(f"LLM Service initialized with Gemini ({settings.GEMINI_MODEL})")
        except Exception as e:
            logger.error(f"Failed to initialize Gemini: {e}")
            raise
    
    def _init_openrouter(self):
        """Initialize OpenRouter client (OpenAI-compatible)."""
        try:
            from openai import OpenAI
            
            if not settings.OPENROUTER_API_KEY:
                raise ValueError("OPENROUTER_API_KEY is not set")
            
            self._openrouter_client = OpenAI(
                base_url="https://openrouter.ai/api/v1",
                api_key=settings.OPENROUTER_API_KEY,
                timeout=120.0,  # 120 second timeout to prevent indefinite hangs
            )
            logger.info(f"LLM Service initialized with OpenRouter ({settings.OPENROUTER_MODEL})")
        except ImportError:
            logger.error("openai package not installed. Run: pip install openai")
            raise
        except Exception as e:
            logger.error(f"Failed to initialize OpenRouter: {e}")
            raise
    
    def generate_sync(self, prompt: str, max_tokens: int = 4096) -> str:
        """
        Generate text synchronously.
        
        Args:
            prompt: The prompt to send to the LLM
            max_tokens: Maximum tokens in response
            
        Returns:
            Generated text string
        """
        if self.provider == "openrouter":
            return self._generate_openrouter(prompt, max_tokens)
        else:
            return self._generate_gemini(prompt)
    
    async def generate(self, prompt: str, max_tokens: int = 4096) -> str:
        """
        Generate text asynchronously with retry logic.
        Handles rate limits (429) with exponential backoff.
        """
        import asyncio
        
        max_retries = 10
        base_delay = 4
        
        for attempt in range(max_retries):
            try:
                # Run sync generation in executor to avoid blocking event loop
                loop = asyncio.get_event_loop()
                # Use lambda or partial to pass arguments
                return await loop.run_in_executor(None, self.generate_sync, prompt, max_tokens)
            except Exception as e:
                error_str = str(e).lower()
                
                # Check for rate limits or temporary server errors
                is_retryable = (
                    "429" in error_str or 
                    "quota" in error_str or 
                    "rate limit" in error_str or
                    "503" in error_str or
                    "500" in error_str
                )
                
                if attempt < max_retries - 1 and is_retryable:
                    delay = base_delay * (2 ** attempt)
                    logger.warning(f"LLM request specific error: {e}")
                    logger.warning(f"Retrying in {delay}s... (Attempt {attempt+1}/{max_retries})")
                    await asyncio.sleep(delay)
                else:
                    # Reraise if not retryable or max retries exceeded
                    raise
    
    def _generate_gemini(self, prompt: str) -> str:
        """Generate using Gemini API."""
        try:
            response = self._gemini_model.generate_content(prompt)
            return response.text
        except Exception as e:
            logger.error(f"Gemini generation error: {e}")
            raise
    
    def _safe_api_call(self, func, *args, **kwargs):
        """Execute API call with exponential backoff for 429 errors."""
        import time
        import random
        retries = 3
        base_delay = 2
        
        for i in range(retries):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                error_str = str(e)
                # Check for 429 in error
                if ("429" in error_str or "rate limit" in error_str.lower()) and i < retries - 1:
                    delay = (base_delay * (2 ** i)) + random.uniform(0, 1)
                    logger.warning(f"Rate limited (429). Retrying in {delay:.2f}s... (Attempt {i+1}/{retries})")
                    time.sleep(delay)
                else:
                    raise e

    def _generate_openrouter(self, prompt: str, max_tokens: int = 4096) -> str:
        """Generate using OpenRouter API."""
        import time
        start_time = time.time()
        
        try:
            logger.info(f"OpenRouter: Starting generation with model {settings.OPENROUTER_MODEL}, prompt_len={len(prompt)}")
            
            response = self._safe_api_call(
                self._openrouter_client.chat.completions.create,
                model=settings.OPENROUTER_MODEL,
                messages=[
                    {"role": "user", "content": prompt}
                ],
                max_tokens=max_tokens,
                extra_headers={
                    "HTTP-Referer": settings.FRONTEND_URL or "https://legalops.apexneural.cloud",
                    "X-Title": "Legal-Ops AI"
                }
            )
            
            elapsed = time.time() - start_time
            result = response.choices[0].message.content
            logger.info(f"OpenRouter: Generation completed in {elapsed:.2f}s, response_len={len(result) if result else 0}")
            
            return result
        except Exception as e:
            elapsed = time.time() - start_time
            logger.error(f"OpenRouter generation error after {elapsed:.2f}s: {e}")
            raise

    async def extract_pdf_content(self, file_path: str) -> str:
        """
        Extract text from PDF using Vision API (OpenRouter).
        Works with both text-based and scanned/image PDFs.
        
        Args:
            file_path: Path to the PDF file
            
        Returns:
            Extracted text content
        """
        import base64
        import os
        
        if not os.path.exists(file_path):
            return "[File not found]"
        
        try:
            # Read PDF as binary
            with open(file_path, 'rb') as f:
                pdf_data = f.read()
            
            # Base64 encode the PDF
            pdf_b64 = base64.b64encode(pdf_data).decode('utf-8')
            
            # Use OpenRouter with vision-capable model
            if self._openrouter_client:
                logger.info(f"Extracting PDF via OpenRouter Vision API: {os.path.basename(file_path)}")
                
                # Use safe wrapper
                response = self._safe_api_call(
                    self._openrouter_client.chat.completions.create,
                    model=settings.OPENROUTER_MODEL,  # Use configured model (default: gpt-4o-mini)
                    messages=[
                        {
                            "role": "user", 
                            "content": [
                                {
                                    "type": "text",
                                    "text": """Extract ALL text content from this PDF document.
Include headings, paragraphs, lists, tables, and any other text.
If it's a scanned document, use OCR to read the text.
Return ONLY the extracted text, no explanations or formatting notes.
If you cannot read the document, explain why."""
                                },
                                {
                                    "type": "file",
                                    "file": {
                                        "filename": os.path.basename(file_path),
                                        "file_data": f"data:application/pdf;base64,{pdf_b64}"
                                    }
                                }
                            ]
                        }
                    ],
                    max_tokens=8000,
                    extra_headers={
                        "HTTP-Referer": settings.FRONTEND_URL or "https://legalops.apexneural.cloud",
                        "X-Title": "Legal-Ops PDF Extractor"
                    }
                )
                if not response.choices or len(response.choices) == 0:
                    logger.warning(f"OpenRouter returned no choices for PDF: {os.path.basename(file_path)}")
                    return "[Error: LLM returned empty response]"

                # Safe access
                choice = response.choices[0]
                if not choice.message or not choice.message.content:
                     logger.warning(f"OpenRouter returned empty content for PDF: {os.path.basename(file_path)}")
                     return "[Error: LLM returned no content]"

                return choice.message.content
            
            # Fallback to Gemini if OpenRouter not available
            elif self._gemini_model:
                import google.generativeai as genai
                
                uploaded_file = genai.upload_file(file_path, mime_type="application/pdf")
                
                prompt = """Extract ALL text content from this PDF document. 
Include headings, paragraphs, lists, tables, and any other text.
Return ONLY the extracted text, no explanations."""

                response = self._gemini_model.generate_content([prompt, uploaded_file])
                
                try:
                    genai.delete_file(uploaded_file.name)
                except:
                    pass
                
                return response.text
            
            return "[No vision-capable model available]"
            
        except Exception as e:
            logger.error(f"PDF vision extraction error: {e}")
            return f"[PDF extraction failed: {str(e)}]"

    async def extract_pdf_content_from_bytes(self, pdf_bytes: bytes, filename: str = "document.pdf") -> str:
        """
        Extract text from PDF bytes using Vision API (OpenRouter/Gemini).
        
        Args:
            pdf_bytes: PDF content as bytes
            filename: Original filename (for logging/mime type)
            
        Returns:
            Extracted text content with page markers if possible
        """
        import base64
        
        try:
            # Base64 encode the content
            content_b64 = base64.b64encode(pdf_bytes).decode('utf-8')
            
            # Determine mime type
            mime_type = "application/pdf"
            if filename.lower().endswith(".png"):
                mime_type = "image/png"
            elif filename.lower().endswith((".jpg", ".jpeg")):
                mime_type = "image/jpeg"
            
            # Prepare content parts
            content_parts = [
                {
                    "type": "text",
                    "text": """Extract ALL text content from this document/image.
Include headings, paragraphs, lists, tables, and any other text.
If it's a scanned document, use OCR to read the text.
Return ONLY the extracted text, no explanations or formatting notes.
If you cannot read the document, explain why."""
                }
            ]
            
            # Add image or file part
            if mime_type.startswith("image/"):
                content_parts.append({
                    "type": "image_url",
                    "image_url": {
                        "url": f"data:{mime_type};base64,{content_b64}"
                    }
                })
            else:
                content_parts.append({
                    "type": "file",
                    "file": {
                        "filename": filename,
                        "file_data": f"data:{mime_type};base64,{content_b64}"
                    }
                })
            
            # Use OpenRouter with vision-capable model
            if self._openrouter_client:
                logger.info(f"Extracting content via OpenRouter Vision API: {filename} ({mime_type})")
                
                # Use safe wrapper
                response = self._safe_api_call(
                    self._openrouter_client.chat.completions.create,
                    model=settings.OPENROUTER_MODEL,  # Use configured model (default: gpt-4o-mini)
                    messages=[
                        {
                            "role": "user", 
                            "content": content_parts
                        }
                    ],
                    max_tokens=8000,
                    extra_headers={
                        "HTTP-Referer": settings.FRONTEND_URL or "https://legalops.apexneural.cloud",
                        "X-Title": "Legal-Ops PDF Extractor"
                    }
                )
                if not response.choices or len(response.choices) == 0:
                    logger.warning(f"OpenRouter returned no choices for PDF: {filename}")
                    return "[Error: LLM returned empty response]"

                # Safe access
                choice = response.choices[0]
                if not choice.message or not choice.message.content:
                     logger.warning(f"OpenRouter returned empty content for PDF: {filename}")
                     return "[Error: LLM returned no content]"

                return choice.message.content
            
            # Fallback to Gemini if OpenRouter not available
            elif self._gemini_model:
                import google.generativeai as genai
                
                # Gemini doesn't support bytes upload directly via generate_content easily for PDFs usually
                # Need to use upload_file which requires a path.
                # We can write to temp file
                import tempfile
                import os
                
                with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
                    tmp.write(pdf_bytes)
                    tmp_path = tmp.name
                
                try:
                    uploaded_file = genai.upload_file(tmp_path, mime_type="application/pdf")
                    
                    prompt = """Extract ALL text content from this PDF document. 
Include headings, paragraphs, lists, tables, and any other text.
Use formatting '--- PAGE [NUMBER] ---' to separate pages if the document has multiple pages.
Return ONLY the extracted text, no explanations."""

                    response = self._gemini_model.generate_content([prompt, uploaded_file])
                    
                    try:
                        genai.delete_file(uploaded_file.name)
                    except:
                        pass
                    
                    return response.text
                finally:
                    if os.path.exists(tmp_path):
                        os.unlink(tmp_path)
            
            return "[No vision-capable model available]"
            
        except Exception as e:
            # Fallback to Gemini on specific errors or if OpenRouter fails generally
            error_str = str(e).lower()
            if "invalid value" in error_str or "does not support file content" in error_str or "400" in error_str:
                 logger.warning(f"OpenRouter rejected PDF (unsupported model/type?): {e}. Falling back to Gemini.")
                 
                 if self._gemini_model:
                     return await self._extract_via_gemini(pdf_bytes, filename)
            
            logger.error(f"PDF vision extraction error: {e}")
            return f"[PDF extraction failed: {str(e)}]"

    async def _extract_via_gemini(self, pdf_bytes, filename):
        """Helper to upload and extract via Gemini."""
        try:
            import google.generativeai as genai
            import tempfile
            import os
            
            with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
                tmp.write(pdf_bytes)
                tmp_path = tmp.name
                
            try:
                uploaded_file = genai.upload_file(tmp_path, mime_type="application/pdf")
                
                prompt = """Extract ALL text content from this PDF document. 
                Include headings, paragraphs, lists, tables, and any other text.
                Use formatting '--- PAGE [NUMBER] ---' to separate pages if the document has multiple pages.
                Return ONLY the extracted text, no explanations."""

                response = self._gemini_model.generate_content([prompt, uploaded_file])
                
                try:
                    genai.delete_file(uploaded_file.name)
                except:
                    pass
                
                return response.text
            finally:
                if os.path.exists(tmp_path):
                    os.unlink(tmp_path)
        except Exception as gemini_err:
             logger.error(f"Gemini fallback failed: {gemini_err}")
             return f"[Gemini fallback failed: {gemini_err}]"


def get_llm_service() -> LLMService:
    """
    Get or create the global LLM service instance.
    
    Returns:
        LLMService: The LLM service singleton
    """
    global _llm_service
    if _llm_service is None:
        _llm_service = LLMService()
    return _llm_service


def reset_llm_service():
    """Reset the global LLM service (useful for testing)."""
    global _llm_service
    _llm_service = None

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
    
    def _generate_openrouter(self, prompt: str, max_tokens: int = 4096) -> str:
        """Generate using OpenRouter API."""
        try:
            response = self._openrouter_client.chat.completions.create(
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
            return response.choices[0].message.content
        except Exception as e:
            logger.error(f"OpenRouter generation error: {e}")
            raise


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

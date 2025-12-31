import sys
import os

# Add the project root to the python path so we can import backend
sys.path.append(os.getcwd())

try:
    from backend.config import settings
    print(f"Current LLM_PROVIDER: '{settings.LLM_PROVIDER}'")
    print(f"OpenRouter API Key Set: {'Yes' if settings.OPENROUTER_API_KEY else 'No'}")
    print(f"Gemini API Key Set: {'Yes' if settings.GEMINI_API_KEY else 'No'}")
except Exception as e:
    print(f"Error importing settings: {e}")

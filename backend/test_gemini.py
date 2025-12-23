"""
Quick diagnostic test for Gemini API
"""
import google.generativeai as genai
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import settings

def test_gemini_api():
    """Test if Gemini API is working"""
    try:
        print(f"Testing Gemini API...")
        print(f"API Key configured: {settings.GEMINI_API_KEY[:10]}...")
        print(f"Model: {settings.GEMINI_MODEL}")
        
        genai.configure(api_key=settings.GEMINI_API_KEY)
        model = genai.GenerativeModel(settings.GEMINI_MODEL)
        
        # Simple test
        response = model.generate_content("Say 'API Working'")
        print(f"\n✅ SUCCESS: {response.text}")
        return True
        
    except Exception as e:
        print(f"\n❌ FAILED: {str(e)}")
        print(f"Error type: {type(e).__name__}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    test_gemini_api()

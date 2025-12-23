"""
Test API with retry to see if it's rate limiting or quota issue
"""
import google.generativeai as genai
import sys
import os
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import settings

def test_with_retry():
    """Test API with retry logic"""
    
    print(f"Testing Gemini API (Paid Tier)")
    print(f"API Key: {settings.GEMINI_API_KEY[:15]}...")
    print(f"Model: {settings.GEMINI_MODEL}\n")
    
    genai.configure(api_key=settings.GEMINI_API_KEY)
    
    # Try 3 times with backoff
    for attempt in range(1, 4):
        try:
            print(f"Attempt {attempt}/3...", end=" ")
            model = genai.GenerativeModel(settings.GEMINI_MODEL)
            response = model.generate_content("Say 'API is working!'")
            print(f"✅ SUCCESS!")
            print(f"Response: {response.text}")
            return True
            
        except Exception as e:
            error_str = str(e)
            print(f"❌ FAILED")
            print(f"Error: {error_str[:100]}")
            
            if "429" in error_str or "quota" in error_str.lower():
                print(f"Rate limit hit. Waiting {2**attempt} seconds...")
                if attempt < 3:
                    time.sleep(2**attempt)
            elif "404" in error_str:
                print("Model not found error")
                return False
            else:
                print(f"Other error: {error_str[:200]}")
                return False
    
    print("\n❌ Failed after 3 attempts")
    return False

if __name__ == "__main__":
    success = test_with_retry()
    sys.exit(0 if success else 1)

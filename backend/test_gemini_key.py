"""
Simple Gemini API Key Test
Tests if the Gemini API key is valid and responding.
"""
import sys
sys.path.insert(0, '.')

try:
    import google.generativeai as genai
    from config import settings
    
    print("=" * 50)
    print("GEMINI API KEY TEST")
    print("=" * 50)
    
    # Show key (masked)
    key = settings.GEMINI_API_KEY
    print(f"\n1. API Key loaded: {key[:15]}...{key[-4:]}")
    print(f"   Key length: {len(key)} characters")
    
    # Configure Gemini
    genai.configure(api_key=key)
    print("\n2. Gemini API configured successfully")
    
    # Test model
    model = genai.GenerativeModel('gemini-1.5-flash')
    print(f"   Model: gemini-1.5-flash")
    
    # Make a simple request
    print("\n3. Testing API with simple request...")
    response = model.generate_content("Respond with just: OK")
    
    print(f"\n✅ GEMINI API IS WORKING!")
    print(f"   Response: {response.text.strip()}")
    print("=" * 50)
    
except ImportError as e:
    print(f"\n❌ Import Error: {e}")
    print("   Please run: pip install google-generativeai")
    
except Exception as e:
    print(f"\n❌ API Error: {type(e).__name__}")
    print(f"   Details: {str(e)}")
    
    if "API_KEY" in str(e).upper() or "INVALID" in str(e).upper():
        print("\n⚠️  Your Gemini API key appears to be invalid!")
        print("   Get a new key from: https://makersuite.google.com/app/apikey")

"""
Test all Gemini models to find which ones work
"""
import google.generativeai as genai
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import settings

def test_all_models():
    """Test multiple Gemini model names to find working ones"""
    
    print(f"Testing Gemini API with key: {settings.GEMINI_API_KEY[:10]}...\n")
    genai.configure(api_key=settings.GEMINI_API_KEY)
    
    # List of model names to try
    models_to_test = [
        "gemini-pro",
        "gemini-1.5-pro",
        "gemini-1.5-flash",
        "gemini-1.5-flash-latest",
        "gemini-2.0-flash-exp",
        "models/gemini-pro",
        "models/gemini-1.5-pro",
        "models/gemini-1.5-flash",
    ]
    
    working_models = []
    
    print("=" * 60)
    for model_name in models_to_test:
        try:
            print(f"Testing: {model_name}...", end=" ")
            model = genai.GenerativeModel(model_name)
            response = model.generate_content("Say 'OK'")
            print(f"✅ WORKS - Response: {response.text.strip()}")
            working_models.append(model_name)
        except Exception as e:
            error_msg = str(e)
            if "404" in error_msg:
                print(f"❌ Not found")
            elif "429" in error_msg or "quota" in error_msg.lower():
                print(f"⚠️ Quota exceeded - but model exists!")
                working_models.append(f"{model_name} (needs quota)")
            else:
                print(f"❌ Error: {error_msg[:50]}...")
    
    print("=" * 60)
    print(f"\n{'='*60}")
    print("WORKING MODELS:")
    print("=" * 60)
    if working_models:
        for model in working_models:
            print(f"  ✅ {model}")
        print(f"\n🎯 RECOMMENDED: {working_models[0]}")
    else:
        print("  ❌ No working models found!")
        print("\nTrying to list all available models...")
        try:
            for m in genai.list_models():
                if 'generateContent' in m.supported_generation_methods:
                    print(f"  📋 {m.name}")
        except Exception as e:
            print(f"  Could not list models: {e}")
    
    return working_models

if __name__ == "__main__":
    working = test_all_models()
    sys.exit(0 if working else 1)

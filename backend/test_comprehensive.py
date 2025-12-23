"""
Comprehensive test for ALL possible Gemini models
"""
import google.generativeai as genai
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import settings

def test_comprehensive():
    """Test every possible model name"""
    
    print(f"Comprehensive Model Test")
    print(f"API Key: {settings.GEMINI_API_KEY[:15]}...")
    print("=" * 70 + "\n")
    
    genai.configure(api_key=settings.GEMINI_API_KEY)
    
    # Comprehensive list
    models_to_test = [
        # Current models
        "gemini-2.0-flash-exp",
        "gemini-1.5-pro",
        "gemini-1.5-flash",
        "gemini-1.5-pro-latest",
        "gemini-1.5-flash-latest",
        
        # Older models
        "gemini-pro",
        "gemini-1.0-pro",
        "gemini-1.0-pro-latest",
        
        # With models/ prefix
        "models/gemini-2.0-flash-exp",
        "models/gemini-1.5-pro",
        "models/gemini-1.5-flash",
        "models/gemini-pro",
        "models/gemini-1.0-pro",
        
        # Alternative names
        "gemini-pro-vision",
        "models/gemini-pro-vision",
    ]
    
    working_models = []
    quota_exceeded = []
    
    for model_name in models_to_test:
        try:
            print(f"Testing: {model_name:40}", end=" ")
            model = genai.GenerativeModel(model_name)
            response = model.generate_content("test", request_options={'timeout': 5})
            print(f"✅ WORKS!")
            working_models.append(model_name)
        except Exception as e:
            error_str = str(e)
            if "404" in error_str or "not found" in error_str.lower():
                print(f"❌ Not found")
            elif "429" in error_str or "quota" in error_str.lower() or "exceeded" in error_str.lower():
                print(f"⚠️  Quota exceeded (model exists)")
                quota_exceeded.append(model_name)
            else:
                print(f"❌ {error_str[:40]}...")
    
    print("\n" + "=" * 70)
    print("RESULTS:")
    print("=" * 70)
    
    if working_models:
        print("\n✅ WORKING MODELS (ready to use):")
        for m in working_models:
            print(f"   {m}")
        print(f"\n🎯 RECOMMEND: {working_models[0]}")
        return working_models[0]
    
    if quota_exceeded:
        print("\n⚠️  QUOTA EXCEEDED (models exist but need billing/wait):")
        for m in quota_exceeded:
            print(f"   {m}")
        print(f"\n⏳ Will use: {quota_exceeded[0]} (if quota resets)")
        return quota_exceeded[0]
    
    print("\n❌ NO MODELS AVAILABLE")
    print("\nTrying to list all enabled models...")
    try:
        available = []
        for m in genai.list_models():
            if 'generateContent' in m.supported_generation_methods:
                available.append(m.name)
                print(f"   📋 {m.name}")
        if available:
            return available[0]
    except Exception as e:
        print(f"   Error listing: {e}")
    
    return None

if __name__ == "__main__":
    result = test_comprehensive()
    if result:
        print(f"\n{'='*70}")
        print(f"FINAL RECOMMENDATION: {result}")
        print(f"{'='*70}")
    sys.exit(0 if result else 1)

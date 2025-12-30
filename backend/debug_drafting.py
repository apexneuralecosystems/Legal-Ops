
import asyncio
import os
import sys

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from agents.malay_drafting import MalayDraftingAgent
from config import settings

async def debug_drafting():
    print(f"[*] Initializing MalayDraftingAgent...")
    print(f"[*] Using API Key: {settings.GEMINI_API_KEY[:10]}...")
    
    agent = MalayDraftingAgent()
    
    # Mock Inputs for Drafting
    mock_inputs = {
        "matter_snapshot": {
            "title": "Ahmad bin Ali v Construction Sdn Bhd",
            "court": "Mahkamah Tinggi Kuala Lumpur",
            "case_type": "Breach of Contract",
            "parties": [
                {"name": "Ahmad bin Ali", "role": "plaintiff"},
                {"name": "Construction Sdn Bhd", "role": "defendant"}
            ]
        },
        "template_id": "TPL-HighCourt-MS-v2",
        "issues_selected": [
            {"text_ms": "Gagal menyiapkan kerja pembinaan dalam masa yang ditetapkan", "text_en": "Failure to complete construction work within stipulated time"},
            {"text_ms": "Kecacatan pada kerja-kerja bangunan", "text_en": "Defects in building works"}
        ],
        "prayers_selected": [
            {"text": "Ganti rugi am (General damages)"},
            {"text": "Ganti rugi khas sebanyak RM50,000"}
        ]
    }
    
    print(f"[*] Calling process()...")
    try:
        result = await agent.process(mock_inputs)
        print(f"\n[+] Success!")
        print(f"Keys returned: {result.keys()}")
        data = result.get('data', {})
        print(f"Data keys: {data.keys()}")
        print(f"Pleading Text (Preview): {data.get('pleading_ms_text', '')[:100]}...")
        if not data.get('pleading_ms_text'):
            print("[-] Pleading text is empty!")
    except Exception as e:
        print(f"\n[-] Failed with error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(debug_drafting())

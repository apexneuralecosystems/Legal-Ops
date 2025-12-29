
import asyncio
import os
import sys

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from agents.hearing_prep import HearingPrepAgent
from config import settings

async def debug_hearing_prep():
    print(f"[*] Initializing HearingPrepAgent...")
    print(f"[*] Using API Key: {settings.GEMINI_API_KEY[:10]}...")
    print(f"[*] Using Model: {settings.GEMINI_MODEL}")
    
    agent = HearingPrepAgent()
    
    # Mock Inputs
    mock_inputs = {
        "matter_snapshot": {
            "title": "Test Matter vs Defendant Ltd",
            "case_type": "Civil Suit",
            "parties": [
                {"name": "Test Plaintiff", "role": "plaintiff"},
                {"name": "Defendant Ltd", "role": "defendant"}
            ]
        },
        "pleadings": [
            {"pleading_type": "Statement of Claim", "file_name": "soc.pdf"}
        ],
        "cases": [
            {"citation": "123 CLJ 456", "headnote_en": "This is a binding precedent regarding contract breach.", "weight": "binding"}
        ],
        "issues": [
            {"title": "Breach of Contract"},
            {"title": "Damages Assessment"}
        ]
    }
    
    print(f"[*] Calling process()...")
    try:
        result = await agent.process(mock_inputs)
        print(f"\n[+] Success!")
        print(f"Keys returned: {result.keys()}")
        print(f"Data keys: {result['data'].keys()}")
        print(f"Oral Script MS (Preview): {result['data']['oral_script_ms'][:50]}...")
    except Exception as e:
        print(f"\n[-] Failed with error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(debug_hearing_prep())

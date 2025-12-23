"""
Debug intake workflow by running it directly
"""
import asyncio
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from orchestrator import OrchestrationController
import logging

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

async def test_intake():
    """Test intake workflow with sample file"""
    
    print("=" * 70)
    print("TESTING INTAKE WORKFLOW")
    print("=" * 70)
    
    controller = OrchestrationController()
    
    # Create test file data
    test_file = {
        "filename": "test.txt",
        "content": b"This is a test legal document for processing.",
        "mime_type": "text/plain"
    }
    
    try:
        print("\n[*] Starting workflow...")
        result = await controller.run_intake_workflow(
            files=[test_file],
            connector_type="upload",
            metadata={},
            matter_id="TEST-001"
        )
        
        print("\n" + "=" * 70)
        print("RESULT:")
        print("=" * 70)
        print(f"Status: {result.get('workflow_status')}")
        
        if result.get('workflow_status') == 'failed':
            print(f"\n[ERROR]:")
            print(f"   {result.get('error', 'Unknown error')}")
            print(f"\n[FULL RESULT]:")
            import json
            print(json.dumps(result, indent=2, default=str))
        else:
            print("\n✅ SUCCESS!")
            print(f"Documents: {len(result.get('document_manifest', []))}")
            if result.get('matter_snapshot'):
                print(f"Title: {result['matter_snapshot'].get('title')}")
        
        return result
        
    except Exception as e:
        print("\n" + "=" * 70)
        print("EXCEPTION CAUGHT:")
        print("=" * 70)
        print(f"Type: {type(e).__name__}")
        print(f"Message: {str(e)}")
        import traceback
        traceback.print_exc()
        return None

if __name__ == "__main__":
    result = asyncio.run(test_intake())
    sys.exit(0 if result and result.get('workflow_status') != 'failed' else 1)

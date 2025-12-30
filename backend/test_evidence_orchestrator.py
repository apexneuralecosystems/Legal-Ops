
import asyncio
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from orchestrator import OrchestrationController

async def test_evidence():
    print("Initializing Controller...", flush=True)
    try:
        controller = OrchestrationController()
    except Exception as e:
        print(f"Controller init failed: {e}", flush=True)
        return

    print("Running Evidence Workflow...", flush=True)
    try:
        # Create a mock document record for testing
        documents = [
            {
                "id": "DOC-TEST-001",
                "filename": "test_evidence.pdf", 
                "doc_lang_hint": "en",
                "file_path": "test_path", 
                "mime_type": "application/pdf"
            }
        ]
        
        result = await controller.run_evidence_workflow(
            matter_id="TEST-EVIDENCE",
            documents=documents
        )
        print(f"Result Status: {result.get('workflow_status')}", flush=True)
        
        if result.get('workflow_status') == 'failed':
            print(f"Error: {result.get('error')}", flush=True)
        else:
            print("Evidence packet built successfully.", flush=True)
            
    except Exception as e:
        print(f"Execution failed: {e}", flush=True)
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_evidence())


import asyncio
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from orchestrator import OrchestrationController

async def test_drafting():
    print("Initializing Controller...", flush=True)
    try:
        controller = OrchestrationController()
    except Exception as e:
        print(f"Controller init failed: {e}", flush=True)
        return

    print("Running Drafting Workflow...", flush=True)
    try:
        matter_snapshot = {
            "title": "Test Case",
            "case_type": "contract",
            "jurisdiction": "Peninsular Malaysia",
            "court": "High Court",
            "parties": [{"role": "plaintiff", "name": "Test Plaintiff"}]
        }
        result = await controller.run_drafting_workflow(
            matter_snapshot=matter_snapshot,
            template_id="TPL-HighCourt-MS-v2",
            issues_selected=[{"text_ms": "Isu 1", "text_en": "Issue 1"}],
            prayers_selected=[{"text": "Prayer 1"}]
        )
        print(f"Result Status: {result.get('workflow_status')}", flush=True)
        if result.get('workflow_status') == 'failed':
            print(f"Error: {result.get('error')}", flush=True)
            
    except Exception as e:
        print(f"Execution failed: {e}", flush=True)
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_drafting())

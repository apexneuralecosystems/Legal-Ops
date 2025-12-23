"""
Test all workflows to ensure state compatibility
"""
import asyncio
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from orchestrator import OrchestrationController

async def test_all_workflows():
    """Test all four workflows"""
    
    controller = OrchestrationController()
    results = {}
    
    # Test 1: Intake Workflow
    print("\n" + "="*70)
    print("1. TESTING INTAKE WORKFLOW")
    print("="*70)
    try:
        result = await controller.run_intake_workflow(
            files=[{"filename": "test.txt", "content": b"Test legal document.", "mime_type": "text/plain"}],
            connector_type="upload",
            metadata={},
            matter_id="TEST-INTAKE"
        )
        status = result.get('workflow_status')
        print(f"Status: {status}")
        results['intake'] = status == 'completed'
    except Exception as e:
        print(f"ERROR: {str(e)[:100]}")
        results['intake'] = False
    
    # Test 2: Drafting Workflow
    print("\n" + "="*70)
    print("2. TESTING DRAFTING WORKFLOW")
    print("="*70)
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
            issues_selected=[],
            prayers_selected=[]
        )
        status = result.get('workflow_status')
        print(f"Status: {status}")
        results['drafting'] = status == 'completed'
    except Exception as e:
        print(f"ERROR: {str(e)[:100]}")
        results['drafting'] = False
    
    # Test 3: Research Workflow
    print("\n" + "="*70)
    print("3. TESTING RESEARCH WORKFLOW")
    print("="*70)
    try:
        result = await controller.run_research_workflow(
            query="contract breach Malaysia",
            filters={}
        )
        status = result.get('workflow_status')
        print(f"Status: {status}")
        results['research'] = status == 'completed'
    except Exception as e:
        print(f"ERROR: {str(e)[:100]}")
        results['research'] = False
    
    # Test 4: Evidence Workflow
    print("\n" + "="*70)
    print("4. TESTING EVIDENCE WORKFLOW")
    print("="*70)
    try:
        result = await controller.run_evidence_workflow(
            matter_id="TEST-EVIDENCE",
            documents=[]
        )
        status = result.get('workflow_status')
        print(f"Status: {status}")
        results['evidence'] = status == 'completed'
    except Exception as e:
        print(f"ERROR: {str(e)[:100]}")
        results['evidence'] = False
    
    # Summary
    print("\n" + "="*70)
    print("SUMMARY")
    print("="*70)
    for workflow, passed in results.items():
        status_str = "[PASS]" if passed else "[FAIL]"
        print(f"{status_str} {workflow.upper()}")
    
    all_passed = all(results.values())
    print(f"\nOverall: {'ALL WORKFLOWS WORKING' if all_passed else 'SOME WORKFLOWS FAILED'}")
    
    return all_passed

if __name__ == "__main__":
    success = asyncio.run(test_all_workflows())
    sys.exit(0 if success else 1)

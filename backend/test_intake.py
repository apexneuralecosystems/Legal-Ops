import asyncio
import sys

async def test():
    from orchestrator.controller import OrchestrationController
    c = OrchestrationController()
    
    # Read PDF file
    with open('../uploads/1464_fc-01(f)-15-05-2016(w).pdf', 'rb') as f:
        content = f.read()
    
    files = [{
        'filename': '1464_fc-01(f)-15-05-2016(w).pdf',
        'content': content,
        'mime_type': 'application/pdf'
    }]
    
    result = await c.run_intake_workflow(
        files=files,
        connector_type='upload',
        metadata={},
        matter_id='TEST-001'
    )
    
    # Write result to file
    with open('test_result.txt', 'w') as f:
        f.write(f"workflow_status: {result.get('workflow_status')}\n")
        f.write(f"error: {result.get('error')}\n")
        if result.get('matter_snapshot'):
            ms = result.get('matter_snapshot')
            f.write(f"title: {ms.get('title')}\n")
            f.write(f"estimated_pages: {ms.get('estimated_pages')}\n")
            f.write(f"parties: {ms.get('parties')}\n")
            f.write(f"court: {ms.get('court')}\n")
        if result.get('risk_scores'):
            rs = result.get('risk_scores')
            f.write(f"risk_scores: {rs}\n")
    
    print("Result written to test_result.txt")
    
asyncio.run(test())

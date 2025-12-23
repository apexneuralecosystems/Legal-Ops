import asyncio
import os
import sys
# Suppress all debug output
os.environ['PYTHONDONTWRITEBYTECODE'] = '1'

async def test():
    print("Starting test...")
    
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
    
    print("Running workflow...")
    result = await c.run_intake_workflow(
        files=files,
        connector_type='upload',
        metadata={},
        matter_id='TEST-001'
    )
    
    print("\n" + "="*50)
    print("WORKFLOW RESULT:")
    print("="*50)
    print(f"workflow_status: {result.get('workflow_status')}")
    print(f"error: {result.get('error')}")
    print(f"matter_id: {result.get('matter_id')}")
    print(f"total_page_count: {result.get('total_page_count')}")
    
    if result.get('matter_snapshot'):
        ms = result.get('matter_snapshot')
        print(f"\nMATTER SNAPSHOT:")
        print(f"  title: {ms.get('title')}")
        print(f"  estimated_pages: {ms.get('estimated_pages')}")
        print(f"  court: {ms.get('court')}")
        print(f"  parties count: {len(ms.get('parties', []))}")
    else:
        print("\nNO MATTER SNAPSHOT!")
        
    if result.get('risk_scores'):
        rs = result.get('risk_scores')
        print(f"\nRISK SCORES: {rs}")
    else:
        print("\nNO RISK SCORES!")
    
asyncio.run(test())

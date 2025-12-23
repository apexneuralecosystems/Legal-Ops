import asyncio
from orchestrator import OrchestrationController

async def seed_document():
    controller = OrchestrationController()
    
    # Create a test matter if it doesn't exist (or use a fixed ID)
    matter_id = "test-matter-evidence-001"
    
    # Mock document structure matching what the frontend expects
    doc = {
        "id": "doc-test-001",
        "filename": "dummy_evidence.pdf",
        "mime_type": "application/pdf",
        "content": "Dummy content",
        "matter_id": matter_id
    }
    
    # In a real app, we would save this to the DB.
    # Since the app uses an in-memory or mock DB for now (based on previous files),
    # we might need to inject it or ensure the backend serves it.
    # Looking at `api.getMatterDocuments`, it likely fetches from a store.
    
    # For now, let's assume the backend has a way to add documents.
    # If not, I'll rely on the existing "test-matter-evidence-001" which I saw in the verification script result.
    # The verification script result showed:
    # "documents": [ { "id": "doc-evidence-001", ... } ]
    
    print(f"Seeding document for matter {matter_id}")
    # This script is a placeholder. The actual verification relies on the backend serving this data.
    # If the backend is using in-memory storage that resets on restart, we need to populate it.
    
    # Let's check if we can hit the API to upload a document.
    import requests
    
    url = "http://localhost:8005/upload" # Guessing endpoint
    # Actually, let's just use the matter ID that already has documents from the previous run if persistence is enabled.
    # If not, we might need to use the `test_all_agents.py` logic to populate it.

if __name__ == "__main__":
    asyncio.run(seed_document())

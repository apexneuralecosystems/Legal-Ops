"""
Evidence workflow endpoints - Build evidence packets and hearing bundles.
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Dict, Any
from database import get_sync_db as get_db
from orchestrator import OrchestrationController
from pydantic import BaseModel

router = APIRouter()

class EvidenceRequest(BaseModel):
    matter_id: str
    documents: List[Dict] = []

@router.post("/build", response_model=dict)
async def build_evidence_packet(
    request: EvidenceRequest,
    db: Session = Depends(get_db)
):
    """
    Build evidence packet for a matter.
    Runs: Translation certification → Evidence packet → Hearing prep
    """
    controller = OrchestrationController()
    
    result = await controller.run_evidence_workflow(
        matter_id=request.matter_id,
        documents=request.documents
    )
    
    if result.get("workflow_status") == "failed":
        raise HTTPException(status_code=500, detail=result.get("error", "Evidence workflow failed"))
    
    return {
        "status": "success",
        "message": "Evidence packet built successfully",
        "data": {
            "translation_cert": result.get("translation_cert", {}),
            "evidence_packet": result.get("evidence_packet", {}),
            "hearing_bundle": result.get("hearing_bundle", {})
        }
    }

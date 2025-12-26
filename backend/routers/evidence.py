"""
Evidence workflow endpoints - Build evidence packets and hearing bundles.
"""
from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from typing import List, Dict, Any, Union
from database import get_sync_db as get_db
from orchestrator import OrchestrationController
from pydantic import BaseModel
from utils.sync_usage_tracker import SyncUsageTracker
from config import settings
from jose import JWTError, jwt

router = APIRouter()
security = HTTPBearer()


def get_current_user_sync(
    credentials: HTTPAuthorizationCredentials = Depends(security),
) -> Dict[str, Any]:
    """Sync auth dependency for evidence endpoints."""
    token = credentials.credentials
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        user_id = payload.get("sub")
        if user_id is None:
            raise HTTPException(status_code=401, detail="Invalid credentials")
        return {"user_id": user_id, "email": payload.get("email")}
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid credentials")

class EvidenceRequest(BaseModel):
    matter_id: Union[int, str]
    documents: List[Dict] = []

@router.post("/build", response_model=dict)
async def build_evidence_packet(
    request: EvidenceRequest,
    db: Session = Depends(get_db),
    current_user: Dict[str, Any] = Depends(get_current_user_sync)
):
    """
    Build evidence packet for a matter.
    Runs: Translation certification → Evidence packet → Hearing prep
    
    Args:
        request: Evidence request with matter_id (accepts both int and string) and documents list
        
    Raises:
        402 Payment Required: If user has exhausted free evidence uses
    """
    # Check usage limits - will raise 402 if payment required
    user_id = current_user["user_id"]
    SyncUsageTracker.require_usage_or_payment(user_id, "evidence", db)
    
    controller = OrchestrationController()
    
    # Convert matter_id to string for internal consistency
    matter_id_str = str(request.matter_id)
    
    result = await controller.run_evidence_workflow(
        matter_id=matter_id_str,
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

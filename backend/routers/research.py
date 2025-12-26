"""
Research API router - Endpoints for legal research and argument building.
"""
from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from typing import List, Optional, Union, Dict, Any
from pydantic import BaseModel
from database import get_sync_db as get_db
from orchestrator import OrchestrationController
from utils.sync_usage_tracker import SyncUsageTracker
from config import settings
from jose import JWTError, jwt

router = APIRouter()
controller = OrchestrationController()
security = HTTPBearer()


def get_current_user_sync(
    credentials: HTTPAuthorizationCredentials = Depends(security),
) -> Dict[str, Any]:
    """Sync auth dependency for research endpoints."""
    token = credentials.credentials
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        user_id = payload.get("sub")
        if user_id is None:
            raise HTTPException(status_code=401, detail="Invalid credentials")
        return {"user_id": user_id, "email": payload.get("email")}
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid credentials")


# Pydantic schemas
class SearchRequest(BaseModel):
    query: str
    filters: dict = {}


class ArgumentRequest(BaseModel):
    matter_id: Optional[Union[int, str]] = None
    issues: List[dict] = []
    cases: List[dict] = []


@router.post("/search", response_model=dict)
async def search_cases(request: SearchRequest, db: Session = Depends(get_db)):
    """
    Search for legal cases based on query and filters.
    
    Workflow: Research Agent searches case law database
    
    Args:
        request: Search query and optional filters (jurisdiction, date range, etc.)
        
    Returns:
        List of relevant cases with citations and summaries
    """
    
    try:
        # For search-only requests, bypass the full workflow (which includes argument building)
        # and call the research agent directly
        from agents import ResearchAgent
        import logging
        
        logger = logging.getLogger(__name__)
        logger.info(f"Research search request: query='{request.query}'")
        
        research_agent = ResearchAgent()
        
        result = await research_agent.process({
            "query": request.query,
            "filters": request.filters or {},
            "limit": 20
        })
        
        # Extract data from research agent response
        data = result.get("data", {})
        cases = data.get("cases", [])
        
        logger.info(f"Research search completed: {len(cases)} cases found")
        
        return {
            "status": "success",
            "cases": cases,
            "query": request.query,
            "total_results": len(cases),
            "data_source": data.get("data_source", "mock"),
            "live_data": data.get("live_data", False)
        }
            
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Research search failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Research search failed: {str(e)}"
        )


@router.post("/build-argument", response_model=dict)
async def build_argument(
    request: ArgumentRequest,
    db: Session = Depends(get_db),
    current_user: Dict[str, Any] = Depends(get_current_user_sync)
):
    """
    Build legal argument memo from selected cases and issues.
    
    Workflow: Argument Builder Agent creates structured memo
    
    Args:
        request: Matter ID (accepts both int and string), selected issues, and relevant cases
        
    Returns:
        Structured argument memo with case citations and analysis
        
    Raises:
        402 Payment Required: If user has exhausted free research uses
    """
    
    # Check usage limits - will raise 402 if payment required
    user_id = current_user["user_id"]
    SyncUsageTracker.require_usage_or_payment(user_id, "research", db)
    
    try:
        # Convert matter_id to string if provided
        matter_id_str = str(request.matter_id) if request.matter_id is not None else None
        
        # Run research workflow (just the argument builder part)
        # Use public method instead of private node access
        updated_state = await controller.build_argument_only(
            cases=request.cases,
            issues=request.issues
        )
        
        return {
            "status": "success",
            "argument_memo": updated_state.get("argument_memo", {}),
            "matter_id": matter_id_str,
            "cases_used": len(request.cases),
            "issues_addressed": len(request.issues)
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Argument building failed: {str(e)}"
        )

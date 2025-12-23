"""
Research API router - Endpoints for legal research and argument building.
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional
from pydantic import BaseModel
from database import get_sync_db as get_db
from orchestrator import OrchestrationController

router = APIRouter()
controller = OrchestrationController()


# Pydantic schemas
class SearchRequest(BaseModel):
    query: str
    filters: dict = {}


class ArgumentRequest(BaseModel):
    matter_id: Optional[str] = None
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
async def build_argument(request: ArgumentRequest, db: Session = Depends(get_db)):
    """
    Build legal argument memo from selected cases and issues.
    
    Workflow: Argument Builder Agent creates structured memo
    
    Args:
        request: Matter ID, selected issues, and relevant cases
        
    Returns:
        Structured argument memo with case citations and analysis
    """
    
    try:
        # Run research workflow (just the argument builder part)
        # Use public method instead of private node access
        updated_state = await controller.build_argument_only(
            cases=request.cases,
            issues=request.issues
        )
        
        return {
            "status": "success",
            "argument_memo": updated_state.get("argument_memo", {}),
            "matter_id": request.matter_id,
            "cases_used": len(request.cases),
            "issues_addressed": len(request.issues)
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Argument building failed: {str(e)}"
        )

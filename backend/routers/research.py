"""
Research API router - Endpoints for legal research and argument building.
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional, Union, Dict, Any
from pydantic import BaseModel
from database import get_db
from dependencies import get_current_user
from orchestrator import OrchestrationController
from utils.usage_tracker import UsageTracker
from config import settings
import logging

router = APIRouter()
controller = OrchestrationController()


# Pydantic schemas
class SearchRequest(BaseModel):
    query: str
    filters: dict = {}
    force_refresh: bool = False  # Skip cache and fetch fresh data


class ArgumentRequest(BaseModel):
    matter_id: Optional[Union[int, str]] = None
    issues: List[dict] = []
    cases: List[dict] = []
    query: Optional[str] = None


@router.post("/search", response_model=dict)
async def search_cases(request: SearchRequest, db: AsyncSession = Depends(get_db)):
    """
    Search for legal cases based on query and filters.
    
    Performance Optimizations:
    - Results are cached in Redis for 24 hours
    - Use force_refresh=true to skip cache and get fresh data
    - Browser connections are pooled for faster execution
    
    Workflow: Research Agent searches case law database
    
    Args:
        request: Search query, optional filters, and force_refresh flag
        
    Returns:
        List of relevant cases with citations and summaries
        Includes `cached` field indicating if result was from cache
    """
    
    try:
        # For search-only requests, bypass the full workflow (which includes argument building)
        # and call the research agent directly
        from agents import ResearchAgent
        
        logger = logging.getLogger(__name__)
        cache_status = "force_refresh" if request.force_refresh else "normal"
        logger.info(f"Research search request: query='{request.query}' mode={cache_status}")
        
        research_agent = ResearchAgent()
        
        result = await research_agent.process({
            "query": request.query,
            "filters": request.filters or {},
            "force_refresh": request.force_refresh,
            "limit": 20
        })
        
        # Extract data from research agent response
        data = result.get("data", {})
        cases = data.get("cases", [])
        cached = result.get("cached", False)
        
        cache_msg = "from cache ⚡" if cached else "live search"
        logger.info(f"Research search completed: {len(cases)} cases found ({cache_msg})")
        
        return {
            "status": "success",
            "cases": cases,
            "query": request.query,
            "total_results": len(cases),
            "data_source": data.get("data_source", "lexis_advance"),
            "live_data": data.get("live_data", False),
            "cached": cached,
            "search_duration_seconds": data.get("search_duration_seconds", 0)
        }
            
    except Exception as e:
        logger = logging.getLogger(__name__)
        logger.error(f"Research search failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Research search failed: {str(e)}"
        )


@router.post("/build-argument", response_model=dict)
async def build_argument(
    request: ArgumentRequest,
    db: AsyncSession = Depends(get_db),
    current_user: Dict[str, Any] = Depends(get_current_user)
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
    await UsageTracker.require_usage_or_payment(user_id, "research", db)
    
    try:
        # Convert matter_id to string if provided
        matter_id_str = str(request.matter_id) if request.matter_id is not None else None
        
        # Run research workflow (just the argument builder part)
        updated_state = await controller.build_argument_only(
            cases=request.cases,
            issues=request.issues,
            query=request.query
        )
        
        # Create Audit Log entry for research
        from models.audit import AuditLog
        audit_entry = AuditLog(
            matter_id=matter_id_str,
            agent_id="ResearchOrchestrator",
            action_type="argument_built",
            action_description=f"Generated legal argument memo addressing {len(request.issues)} issues with {len(request.cases)} case citations.",
            entity_type="research_memo",
            user_id=current_user["user_id"]
        )
        db.add(audit_entry)
        # We can't commit if it's an async session without await, 
        # but db is AsyncSession here.
        await db.commit()

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

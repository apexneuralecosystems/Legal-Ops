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

# ═══════════════════════════════════════════════════════════════
# Judgment fetch status tracker (in-memory, per-query)
# Frontend polls this to show progress notifications
# ═══════════════════════════════════════════════════════════════
_fetch_status: Dict[str, Dict[str, Any]] = {}


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
async def search_cases(
    request: SearchRequest, 
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    Search for legal cases based on query and filters.
    
    Performance Optimizations:
    - Results are cached in Redis for 24 hours
    - Use force_refresh=true to skip cache and get fresh data
    - Browser connections are pooled for faster execution
    - Uses saved Lexis cookies if available (60-70% faster)
    
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
            "limit": 20,
            "user_id": current_user.get("user_id")  # Pass user_id for cookie lookup
        })
        
        # Extract data from research agent response
        data = result.get("data", {})
        cases = data.get("cases", [])
        cached = result.get("cached", False)
        
        cache_msg = "from cache ⚡" if cached else "live search"
        logger.info(f"Research search completed: {len(cases)} cases found ({cache_msg})")
        
        # ═══════════════════════════════════════════════════════════════
        # ⭐ OPTION B: Citation-Based Judgment Prefetching (BACKGROUND)
        # Returns search results IMMEDIATELY to avoid frontend timeout.
        # Fires a background task that fetches judgments via citation search.
        # Results are stored in memory cache — argument_builder checks it.
        # ═══════════════════════════════════════════════════════════════
        
        if cases and not cached:
            import asyncio as _asyncio
            
            cases_with_citations = [c for c in cases if c.get("citation") and c.get("citation") != "No Citation"]
            logger.info(f"📚 OPTION B: Launching BACKGROUND fetch for {len(cases_with_citations)}/{len(cases)} cases with citations")
            
            # Track fetch status so frontend can poll for progress
            fetch_id = request.query.strip().lower()[:100]
            _fetch_status[fetch_id] = {
                "status": "running",
                "total": len(cases),
                "with_citations": len(cases_with_citations),
                "fetched": 0,
                "failed": 0,
                "skipped": 0,
            }
            
            # Fire and forget — don't block the API response
            _asyncio.create_task(
                _background_citation_fetch(cases, current_user.get("user_id"), fetch_id),
                name="option_b_citation_fetch"
            )
        
        return {
            "status": "success",
            "cases": cases,
            "query": request.query,
            "total_results": len(cases),
            "data_source": data.get("data_source", "lexis_advance"),
            "live_data": data.get("live_data", False),
            "cached": cached,
            "search_duration_seconds": data.get("search_duration_seconds", 0),
            "judgments_prefetching": bool(cases and not cached),  # Background fetch is running
            "judgments_available": len([c for c in cases if c.get("full_judgment_fetched")]) if cases else 0
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
        
        # ⭐ PHASE 2: Run research workflow with KB enrichment (pass db_session and matter_id)
        updated_state = await controller.build_argument_only(
            cases=request.cases,
            issues=request.issues,
            query=request.query,
            user_id=current_user.get("user_id"),
            db_session=db,  # ⭐ NEW: Pass database session for KB queries
            matter_id=matter_id_str  # ⭐ NEW: Pass matter_id for KB comparison
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
        await db.commit()

        # ⭐ PHASE 2: Include KB insights in response
        kb_insights = updated_state.get("kb_insights", {})
        
        return {
            "status": "success",
            "argument_memo": updated_state.get("argument_memo", {}),
            "matter_id": matter_id_str,
            "cases_used": len(request.cases),
            "issues_addressed": len(request.issues),
            "kb_insights": kb_insights,  # ⭐ NEW: KB data for frontend
            "kb_available": kb_insights.get("kb_available", False),
            "similar_matters_count": kb_insights.get("similar_matters_count", 0)
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Argument building failed: {str(e)}"
        )


@router.get("/judgment-fetch-status")
async def get_judgment_fetch_status(
    query: str,
    current_user: dict = Depends(get_current_user)
):
    """
    Poll endpoint for background judgment fetch progress.
    Frontend calls this every few seconds after search to show progress.
    """
    fetch_id = query.strip().lower()[:100]
    status = _fetch_status.get(fetch_id)
    
    if not status:
        return {"status": "none", "message": "No active fetch for this query"}
    
    return status


@router.get("/judgment-cache")
async def get_judgment_cache(
    current_user: dict = Depends(get_current_user)
):
    """
    Inspect the in-memory judgment cache.
    Returns cached case titles, word counts, sections, and metadata.
    Full text is truncated to first 500 chars for inspection.
    """
    from services.background_judgment_fetcher import BackgroundJudgmentFetcher
    
    cache = BackgroundJudgmentFetcher._get_cache()
    stats = await cache.stats()
    
    entries = []
    async with cache._lock:
        for key, entry in cache._cache.items():
            jd = entry.get("judgment_data", {})
            entries.append({
                "case_title": entry.get("case_title", "Unknown"),
                "case_link": entry.get("case_link", ""),
                "cached_at": entry.get("_cached_at", "").isoformat() if entry.get("_cached_at") else "",
                "success": jd.get("success", False),
                "word_count": jd.get("word_count", 0),
                "has_headnotes": bool(jd.get("headnotes")),
                "has_facts": bool(jd.get("facts")),
                "has_issues": bool(jd.get("issues_text")),
                "has_reasoning": bool(jd.get("reasoning")),
                "judges": jd.get("judges", []),
                "sections": jd.get("sections", []),
                "page_title": jd.get("page_title", ""),
                "fetched_by": jd.get("fetched_by", ""),
                "full_text_preview": (jd.get("full_text", "") or "")[:500] + ("..." if len(jd.get("full_text", "") or "") > 500 else ""),
                "headnotes_preview": (jd.get("headnotes", "") or "")[:300],
                "facts_preview": (jd.get("facts", "") or "")[:300],
                "reasoning_preview": (jd.get("reasoning", "") or "")[:300],
            })
    
    return {
        "cache_size": stats["size"],
        "max_size": stats["max_size"],
        "ttl_minutes": stats["ttl_minutes"],
        "entries": entries
    }


# ═══════════════════════════════════════════════════════════════════════
# BACKGROUND TASK: Citation-based judgment fetching (Option B)
# Runs after search returns results to user. Stores judgments in
# BackgroundJudgmentFetcher memory cache for argument_builder to find.
# ═══════════════════════════════════════════════════════════════════════

async def _background_citation_fetch(cases: list, user_id: str = None, fetch_id: str = None):
    """
    Background task: Fetch judgments by citation using the pooled browser page.
    Updates _fetch_status so frontend can poll for progress.
    """
    from services.lexis_scraper import LexisScraper
    from services.background_judgment_fetcher import BackgroundJudgmentFetcher
    
    _logger = logging.getLogger("background_citation_fetch")
    
    scraper = None
    success_count = 0
    fail_count = 0
    skip_count = 0
    
    try:
        _logger.info(f"🚀 Background citation fetch starting for {len(cases)} cases...")
        
        # Get pooled browser page (still on Lexis from the search)
        scraper = LexisScraper(use_pool=True)
        await scraper.start_robot()
        
        if not scraper._page or scraper._page.is_closed():
            _logger.warning("⚠️ No browser page available from pool, aborting")
            if fetch_id and fetch_id in _fetch_status:
                _fetch_status[fetch_id].update({"status": "error", "error": "Browser page not available from pool"})
            return
        
        page_url = scraper._page.url
        _logger.info(f"📄 Got pooled page: {page_url}")
        
        if "advance.lexis.com" not in page_url:
            _logger.warning(f"⚠️ Page not on Lexis ({page_url}), aborting")
            if fetch_id and fetch_id in _fetch_status:
                _fetch_status[fetch_id].update({"status": "error", "error": f"Browser not on Lexis (at {page_url})"})
            await scraper.close_robot()
            return
        
        reauth_attempts = 0
        max_reauth = 2  # Max times we'll try re-authenticating
        
        for i, case in enumerate(cases, 1):
            citation = case.get("citation", "No Citation")
            case_title = case.get("title", f"Case {i}")
            case_link = case.get("link", "")
            
            if not citation or citation == "No Citation":
                skip_count += 1
                if fetch_id and fetch_id in _fetch_status:
                    _fetch_status[fetch_id]["skipped"] = skip_count
                continue
            
            # Check if browser is still alive
            if scraper._page.is_closed():
                _logger.error(f"❌ Browser closed at case {i}/{len(cases)}, stopping")
                if fetch_id and fetch_id in _fetch_status:
                    _fetch_status[fetch_id].update({"status": "error", "error": f"Browser crashed at case {i}/{len(cases)}"})
                break
            
            _logger.info(f"[{i}/{len(cases)}] Fetching: {citation} - {case_title[:40]}...")
            
            # Fetch by citation
            judgment_data = await scraper.fetch_judgment_by_citation(citation, case_title)
            
            if judgment_data and judgment_data.get("success"):
                # Store in the memory cache that argument_builder checks
                cache_key = case_link if case_link else citation
                await BackgroundJudgmentFetcher._get_cache().set(
                    cache_key, case_title, judgment_data
                )
                success_count += 1
                _logger.info(f"   ✅ Cached: {judgment_data.get('word_count', 0):,} words")
                if fetch_id and fetch_id in _fetch_status:
                    _fetch_status[fetch_id]["fetched"] = success_count
            else:
                error = judgment_data.get("error", "Unknown") if judgment_data else "No data"
                _logger.warning(f"   ❌ Failed: {error}")
                
                # ─── AUTH ERROR DETECTION & RECOVERY ───────────────
                # If error is auth-related (401/session expired),
                # re-authenticate and retry this case
                from services.lexis_scraper import LexisScraper as _LS
                if _LS._is_auth_error(error) and reauth_attempts < max_reauth:
                    reauth_attempts += 1
                    _logger.info(f"🔄 Session expired — re-authenticating (attempt {reauth_attempts}/{max_reauth})...")
                    if fetch_id and fetch_id in _fetch_status:
                        _fetch_status[fetch_id]["status"] = "re-authenticating"
                        _fetch_status[fetch_id]["reauth_attempts"] = reauth_attempts
                    
                    try:
                        reauth_ok = await scraper.re_authenticate()
                        if reauth_ok:
                            _logger.info(f"✅ Re-auth successful — retrying case {i}: {citation}")
                            if fetch_id and fetch_id in _fetch_status:
                                _fetch_status[fetch_id]["status"] = "running"
                            
                            # Navigate back to search page for citation fetching
                            try:
                                await scraper._page.goto("https://advance.lexis.com/search", timeout=20000, wait_until="domcontentloaded")
                                await asyncio.sleep(2)
                            except Exception as nav_err:
                                _logger.warning(f"⚠️ Could not navigate to search page: {nav_err}")
                            
                            # Retry the failed case
                            retry_data = await scraper.fetch_judgment_by_citation(citation, case_title)
                            if retry_data and retry_data.get("success"):
                                cache_key = case_link if case_link else citation
                                await BackgroundJudgmentFetcher._get_cache().set(
                                    cache_key, case_title, retry_data
                                )
                                success_count += 1
                                _logger.info(f"   ✅ Retry succeeded: {retry_data.get('word_count', 0):,} words")
                                if fetch_id and fetch_id in _fetch_status:
                                    _fetch_status[fetch_id]["fetched"] = success_count
                                # Delay before next case
                                import asyncio as _aio
                                await _aio.sleep(2)
                                continue
                            else:
                                _logger.warning(f"   ❌ Retry also failed after re-auth")
                                fail_count += 1
                        else:
                            _logger.error(f"❌ Re-auth failed — stopping fetch")
                            fail_count += 1
                            if fetch_id and fetch_id in _fetch_status:
                                _fetch_status[fetch_id].update({
                                    "status": "error",
                                    "error": f"Session expired and re-authentication failed at case {i}/{len(cases)}"
                                })
                            break
                    except Exception as reauth_err:
                        _logger.error(f"❌ Re-auth exception: {reauth_err}")
                        fail_count += 1
                        if fetch_id and fetch_id in _fetch_status:
                            _fetch_status[fetch_id].update({
                                "status": "error",
                                "error": f"Re-authentication error: {str(reauth_err)}"
                            })
                        break
                else:
                    fail_count += 1
                
                if fetch_id and fetch_id in _fetch_status:
                    _fetch_status[fetch_id]["failed"] = fail_count
            
            # Delay between fetches (2s to reduce session pressure)
            import asyncio as _aio
            await _aio.sleep(2)
        
        _logger.info(f"🏁 Background fetch done: {success_count} success, {fail_count} failed, {skip_count} skipped")
        
        # Update final status
        if fetch_id and fetch_id in _fetch_status:
            _fetch_status[fetch_id].update({
                "status": "complete",
                "fetched": success_count,
                "failed": fail_count,
                "skipped": skip_count,
            })
        
    except Exception as e:
        _logger.error(f"❌ Background citation fetch error: {e}", exc_info=True)
        if fetch_id and fetch_id in _fetch_status:
            _fetch_status[fetch_id]["status"] = "error"
            _fetch_status[fetch_id]["error"] = str(e)
    finally:
        if scraper:
            try:
                await scraper.close_robot()
            except:
                pass


# ═══════════════════════════════════════════════════════════════
# Cache Management
# ═══════════════════════════════════════════════════════════════

@router.delete("/search-cache")
async def clear_search_cache(
    current_user: dict = Depends(get_current_user)
):
    """
    Clear all Redis search result caches.
    Use when stale/empty results are cached from previous failures.
    """
    logger = logging.getLogger(__name__)
    try:
        from agents import ResearchAgent
        agent = ResearchAgent()
        await agent.invalidate_cache()
        logger.info("🗑️ Search cache cleared by user")
        return {"status": "success", "message": "Search cache cleared"}
    except Exception as e:
        logger.error(f"Cache clear failed: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to clear cache: {str(e)}")

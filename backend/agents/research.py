"""
Research Agent - Find Malaysian caselaw and English authorities.
Now with Lexis Advance integration ("Robot Browser") and Redis caching.

Performance Optimizations:
- Browser connection pooling (saves 5-10s per search)
- Redis caching (instant results for repeated queries)
- Force refresh option for fresh data
"""
from agents.base_agent import BaseAgent
from typing import Dict, Any, List, Optional
from datetime import datetime
from pathlib import Path
from services.lexis_scraper import LexisScraper
from config import settings
import logging
import os
import json
import hashlib

logger = logging.getLogger(__name__)


class ResearchAgent(BaseAgent):
    """
    Find Malaysian caselaw using Lexis Advance.
    
    Features:
    - Real-time "Robot Browser" search with connection pooling
    - Redis caching for instant repeated searches
    - Strict Real Data (No Mock)
    - Jurisdiction Filtering
    - Force refresh option
    
    Inputs:
    - query: search query (natural language)
    - filters: {jurisdiction, year, court}
    - force_refresh: bool (skip cache, fetch fresh data)
    
    Outputs:
    - cases: array of {citation, court, summary, link}
    - cached: bool (whether result came from cache)
    """
    
    # Cache configuration
    CACHE_TTL = 86400  # 24 hours in seconds
    CACHE_PREFIX = "lexis_search:"
    
    def __init__(self):
        super().__init__(agent_id="Research")
        
        # Initialize the Robot (with pooling enabled)
        self.lexis_scraper = LexisScraper(use_pool=True)
        
        # Initialize Redis connection
        self._redis: Optional[redis.Redis] = None
        
        logger.info(f"Research Agent initialized (Source: Lexis Advance, Caching: Redis)")

    async def _get_redis(self) -> Optional[Any]:
        """Get or create Redis connection."""
        if self._redis is None:
            try:
                import redis.asyncio as redis
                self._redis = redis.from_url(
                    settings.REDIS_URL,
                    encoding="utf-8",
                    decode_responses=True
                )
                # Test connection
                await self._redis.ping()
                logger.info("✅ Redis connected for caching")
            except Exception as e:
                # Silent failure for Redis - it's an optional cache
                self._redis = None
        return self._redis
    
    def _generate_cache_key(self, query: str, filters: Dict) -> str:
        """Generate a unique cache key for the query + filters."""
        # Normalize query and filters for consistent hashing
        normalized = {
            "query": query.lower().strip(),
            "filters": json.dumps(filters, sort_keys=True) if filters else "{}"
        }
        key_data = json.dumps(normalized, sort_keys=True)
        key_hash = hashlib.sha256(key_data.encode()).hexdigest()[:16]
        return f"{self.CACHE_PREFIX}{key_hash}"
    
    async def _get_cached_result(self, cache_key: str) -> Optional[Dict]:
        """Try to get cached result from Redis."""
        try:
            redis_client = await self._get_redis()
            if redis_client:
                cached = await redis_client.get(cache_key)
                if cached:
                    return json.loads(cached)
        except Exception as e:
            logger.warning(f"Cache read error: {e}")
        return None
    
    async def _set_cached_result(self, cache_key: str, result: Dict):
        """Store result in Redis cache."""
        try:
            redis_client = await self._get_redis()
            if redis_client:
                await redis_client.setex(
                    cache_key,
                    self.CACHE_TTL,
                    json.dumps(result)
                )
                logger.info(f"💾 Result cached (TTL: {self.CACHE_TTL}s)")
        except Exception as e:
            logger.warning(f"Cache write error: {e}")

    async def process(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process research request using Lexis Advance.
        
        Uses Redis cache for performance. Pass force_refresh=True to skip cache.
        """
        await self.validate_input(inputs, ["query"])
        
        query = inputs["query"]
        filters = inputs.get("filters", {})
        if filters is None: 
            filters = {}
        force_refresh = inputs.get("force_refresh", False)
        user_id = inputs.get("user_id")  # Get user_id for cookie lookup
        
        # Jurisdiction defaults to Malaysia
        jurisdiction = filters.get("jurisdiction", "Malaysia")
        
        # Generate cache key
        cache_key = self._generate_cache_key(query, filters)
        
        # Check cache first (unless force refresh)
        if not force_refresh:
            cached_result = await self._get_cached_result(cache_key)
            if cached_result:
                # Don't serve cached empty results — they may be from transient failures
                cached_cases = cached_result.get("data", {}).get("cases", [])
                if cached_cases:
                    logger.info(f"⚡ Cache HIT for: '{query[:50]}...' ({len(cached_cases)} cases)")
                    cached_result["cached"] = True
                    cached_result["cache_key"] = cache_key
                    return cached_result
                else:
                    logger.warning(f"⚠️ Cache HIT but empty results — ignoring stale cache, doing live search")
                    # Delete stale empty cache entry
                    try:
                        redis_client = await self._get_redis()
                        if redis_client:
                            await redis_client.delete(cache_key)
                    except Exception:
                        pass
        else:
            logger.info(f"🔄 Force refresh requested - skipping cache")
        
        logger.info(f"📡 Cache MISS - executing live search for: '{query}'")
        
        results = []
        data_source = "lexis_advance"
        search_start = datetime.now()
        
        try:
            logger.info(f"🤖 Research Robot activating for: '{query}' ({jurisdiction})")
            
            # Execute Robot Search with ALL filters
            results = await self.lexis_scraper.search(
                query=query,
                country=jurisdiction,
                filters=filters,  # Pass all filters
                user_id=user_id  # Pass user_id for cookie lookup
            )
            
            search_duration = (datetime.now() - search_start).total_seconds()
            logger.info(f"[OK] Retrieved {len(results)} cases from Lexis in {search_duration:.1f}s")
            
        except (ImportError, ModuleNotFoundError) as e:
            logger.warning(f"🚫 Research skipped: {e}")
            return {
                "error": f"Research feature unavailable: {str(e)}",
                "status": "unavailable",
                "cases": [],
                "cached": False
            }
        except Exception as e:
            logger.error(f"Lexis Robot failed: {e}") # Removed exc_info=True for general errors
            # STRICT REAL DATA POLICY: Return Error, NO MOCK
            return {
                "error": f"Research failed: {str(e)}",
                "status": "error",
                "data_source": "lexis_advance",
                "cases": [],
                "cached": False
            }
        
        # Format output
        output = self.format_output(
            data={
                "cases": results,
                "total_results": len(results),
                "query": query,
                "filters_applied": filters,
                "data_source": data_source,
                "live_data": True,
                "search_duration_seconds": (datetime.now() - search_start).total_seconds()
            },
            confidence=0.95 if results else 0.0
        )
        
        # Add cache metadata
        output["cached"] = False
        output["cache_key"] = cache_key
        
        # Only cache results that actually contain cases
        # Never cache empty results — they may be from transient failures
        if results:
            await self._set_cached_result(cache_key, output)
        else:
            logger.warning(f"⚠️ Skipping cache for empty results (query: '{query[:50]}...') — may be a transient failure")
        
        return output
    
    async def invalidate_cache(self, query: str = None, filters: Dict = None):
        """
        Invalidate cached results.
        
        If query/filters provided, invalidate specific cache.
        If not provided, invalidate all research cache.
        """
        try:
            redis_client = await self._get_redis()
            if not redis_client:
                return
            
            if query:
                cache_key = self._generate_cache_key(query, filters or {})
                await redis_client.delete(cache_key)
                logger.info(f"🗑️ Invalidated cache for: {query[:50]}...")
            else:
                # Delete all research cache keys
                async for key in redis_client.scan_iter(f"{self.CACHE_PREFIX}*"):
                    await redis_client.delete(key)
                logger.info("🗑️ Invalidated all research cache")
        except Exception as e:
            logger.warning(f"Cache invalidation error: {e}")

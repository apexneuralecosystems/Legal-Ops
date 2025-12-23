"""
Research Agent - Find Malaysian caselaw and English authorities.
Now with real-time CommonLII web scraping!
"""
from agents.base_agent import BaseAgent
from typing import Dict, Any, List
from datetime import datetime
from pathlib import Path
from services.commonlii_scraper import get_commonlii_scraper
import logging
import os

logger = logging.getLogger(__name__)


class ResearchAgent(BaseAgent):
    """
    Find Malaysian caselaw and English authorities, produce bilingual summaries.
    
    Now features real-time web scraping from CommonLII Malaysia!
    
    Inputs:
    - query: search query (natural language or keywords)
    - filters: {court, year, jurisdiction, binding}
    - limit: max results (default 10)
    
    Outputs:
    - cases: array of {citation, court, headnote_en, headnote_ms, key_quotes, weight}
    """
    
    def __init__(self):
        super().__init__(agent_id="Research")
        
        # Configuration: Use CommonLII by default, fallback to mock on errors
        self.use_commonlii = os.getenv("USE_COMMONLII", "false").lower() == "true"
        
        # Initialize data source
        self.commonlii_scraper = get_commonlii_scraper()
        
        logger.info(f"Research Agent initialized (USE_COMMONLII={self.use_commonlii})")

    
    async def process(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process research request using CommonLII.
        
        Args:
            inputs: {
                "query": str,
                "filters": Dict (optional),
                "limit": int (default 10)
            }
            
        Returns:
            {
                "cases": List[Dict],
                "total_results": int,
                "data_source": "commonlii"
            }
        """
        await self.validate_input(inputs, ["query"])
        
        query = inputs["query"]
        filters = inputs.get("filters", {})
        if filters is None:
            filters = {}
        limit = inputs.get("limit", 10)
        
        results = []
        data_source = "commonlii"
        
        try:
            logger.info(f"Searching CommonLII for: '{query}'")
            # Ensure we pass a valid dict for filters
            search_filters = dict(filters) if filters else {}
            search_filters["limit"] = limit
            
            results = await self.commonlii_scraper.search(
                query=query,
                filters=search_filters
            )
            logger.info(f"[OK] Retrieved {len(results)} cases from CommonLII")
            
        except Exception as e:
            logger.error(f"CommonLII search failed: {e}", exc_info=True)
            # No fallback to mock data as per user request
            results = []
            data_source = "error"
        
        return self.format_output(
            data={
                "cases": results,
                "total_results": len(results),
                "query": query,
                "filters_applied": filters,
                "data_source": data_source,
                "live_data": True
            },
            confidence=0.85 if results else 0.0
        )


    


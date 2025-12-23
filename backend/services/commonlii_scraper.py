"""
CommonLII Malaysia Web Scraper Service

Real-time web scraping of Malaysian legal cases from CommonLII.
Provides search functionality with HTML parsing and error handling.
"""
import asyncio
import hashlib
import logging
import time
from typing import Dict, Any, List, Optional
from functools import wraps
from datetime import datetime

import httpx
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)


# Rate limiting decorator
def rate_limit(calls_per_second: float = 1.0):
    """Rate limiting decorator to prevent overwhelming CommonLII servers."""
    min_interval = 1.0 / calls_per_second
    last_called = [0.0]
    
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            elapsed = time.time() - last_called[0]
            wait_time = min_interval - elapsed
            if wait_time > 0:
                await asyncio.sleep(wait_time)
            result = await func(*args, **kwargs)
            last_called[0] = time.time()
            return result
        return wrapper
    return decorator


class CommonLIIScraper:
    """
    Web scraper for CommonLII Malaysia legal database.
    
    Features:
    - Search Malaysian court cases
    - Support for multiple courts (Federal, Appeal, High Court)
    - Rate limiting (1 request/second)
    - Error handling with retries
    - HTML parsing for case metadata
    """
    
    # CommonLII endpoints
    BASE_URL = "http://www.commonlii.org"
    SEARCH_ENDPOINT = f"{BASE_URL}/cgi-bin/sinosrch.cgi"
    
    # Court database mappings
    COURT_DATABASES = {
        "federal": "my/cases/MYFC",
        "appeal": "my/cases/MYCA",
        "high_court": "my/cases/MYHC",
        "high_court_sabah": "my/cases/MYHCSS",
        "all": "my"  # Search all Malaysian databases
    }
    
    def __init__(self, timeout: int = 30, max_retries: int = 3):
        """
        Initialize CommonLII scraper.
        
        Args:
            timeout: HTTP request timeout in seconds
            max_retries: Maximum number of retry attempts on failure
        """
        self.timeout = timeout
        self.max_retries = max_retries
        self.session = httpx.AsyncClient(
            timeout=timeout,
            headers={
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
                "Accept-Language": "en-US,en;q=0.5",
                "Referer": "http://www.commonlii.org/",
            }
        )
        logger.info("CommonLII scraper initialized")
    
    @rate_limit(calls_per_second=1.0)
    async def search(
        self,
        query: str,
        filters: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """
        Search CommonLII for Malaysian legal cases.
        
        Args:
            query: Search query string
            filters: Optional filters {
                "court": "federal" | "appeal" | "high_court" | "all",
                "year": int,
                "limit": int (default 20)
            }
            
        Returns:
            List of case dictionaries with metadata
            
        Raises:
            Exception: On network errors or parsing failures
        """
        filters = filters or {}
        court = filters.get("court", "all")
        limit = filters.get("limit", 20)
        
        # Map court to database mask
        # Build mask_path with SPACES between court paths (CommonLII requirement)
        if court and court != "all":
            database_mask = self.COURT_DATABASES.get(court, "my")
            mask_path = database_mask
        else:
            # All courts: space-separated list
            mask_path = "my/cases/MYFC my/cases/MYCA my/cases/MYHC my/cases/MYHCSS"
        
        # Build search parameters
        params = {
            "query": query,
            "mask_path": mask_path,  # Use mask_path instead of mask
            "method": "auto",
            "meta": "/commonlii",  # Required for results to appear
            "results": str(limit),
            "submit": "Search",
            "rank": "rank",  # Sort by relevance
        }
        
        logger.info(f"Searching CommonLII: query='{query}', court='{court}'")
        
        # Retry logic
        for attempt in range(self.max_retries):
            try:
                response = await self.session.get(
                    self.SEARCH_ENDPOINT,
                    params=params
                )
                response.raise_for_status()
                
                # Debug: Log response details
                logger.info(f"CommonLII response: {len(response.text)} bytes, content-type: {response.headers.get('content-type')}")
                
                # Parse results
                cases = self._parse_search_results(response.text, filters)
                
                # Debug: Save HTML if no cases found
                if len(cases) == 0 and attempt == 0:
                    debug_file = f"commonlii_debug_{query[:20].replace(' ', '_')}.html"
                    try:
                        with open(debug_file, 'w', encoding='utf-8') as f:
                            f.write(response.text)
                        logger.warning(f"No cases found. HTML saved to {debug_file} for debugging")
                    except Exception as e:
                        logger.debug(f"Could not save debug HTML: {e}")
                
                logger.info(f"Found {len(cases)} cases from CommonLII")
                return cases
                
            except httpx.HTTPError as e:
                logger.warning(f"CommonLII request failed (attempt {attempt + 1}/{self.max_retries}): {e}")
                if attempt < self.max_retries - 1:
                    await asyncio.sleep(2 ** attempt)  # Exponential backoff
                else:
                    raise Exception(f"CommonLII search failed after {self.max_retries} attempts: {e}")
            except Exception as e:
                logger.error(f"Unexpected error in CommonLII search: {e}")
                raise
    
    def _parse_search_results(
        self,
        html_content: str,
        filters: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """
        Parse CommonLII search results HTML.
        
        Args:
            html_content: Raw HTML response
            filters: Search filters for additional filtering
            
        Returns:
            List of parsed case dictionaries
        """
        soup = BeautifulSoup(html_content, 'lxml')
        cases = []
        
        try:
            # CommonLII results are NOT in lists - they're direct <a> tags in the body
            # Format: [36] Case Title [PDF] Court info
            # Find all links that contain /cases/ in href
            
            all_links = soup.find_all('a', href=True)
            case_links = [link for link in all_links if '/cases/' in link.get('href', '')]
            
            logger.info(f"Found {len(case_links)} potential case links in HTML")
            
            for idx, case_link in enumerate(case_links):
                try:
                    case_url = case_link['href']
                    case_text = case_link.get_text(strip=True)
                    
                    # Skip empty links or non-case links
                    if not case_text or case_text.lower() in ['pdf', 'rtf', 'help']:
                        continue
                    
                    # Skip if URL doesn't look like a case
                    if not any(court in case_url for court in ['MYFC', 'MYCA', 'MYHC', 'MYHCSS']):
                        continue
                    
                    # Extract citation and title
                    citation = self._extract_citation(case_text, case_url)
                    title = self._extract_title(case_text)
                    
                    # Extract court from URL
                    court_name = self._extract_court_from_url(case_url)
                    
                    # Extract year
                    year = self._extract_year(case_text, case_url)
                    
                    # Try to get surrounding context for headnote
                    # Look at next siblings or parent text
                    headnote_en = "No summary available"
                    parent = case_link.parent
                    if parent:
                        parent_text = parent.get_text(separator=' ', strip=True)
                        headnote_en = self._clean_snippet(parent_text, case_text)
                    
                    # Build case dictionary
                    case = {
                        "citation": citation,
                        "title": title,
                        "court": court_name,
                        "year": year,
                        "jurisdiction": "Malaysian",
                        "binding": court_name in ["Federal Court", "Court of Appeal"],
                        "headnote_en": headnote_en,
                        "headnote_ms": "",  # Not available from search results
                        "url": self.BASE_URL + case_url if not case_url.startswith('http') else case_url,
                        "relevance_score": max(0.5, 1.0 - (idx * 0.02)),  # Decreasing relevance
                        "keywords": self._extract_keywords(title + " " + headnote_en),
                    }
                    
                    # Apply year filter if specified
                    if filters and filters.get("year"):
                        if year != int(filters["year"]):
                            continue
                    
                    cases.append(case)
                    
                    # Stop if we have enough cases
                    limit_check = filters.get("limit", 20) if filters else 20
                    if len(cases) >= limit_check:
                        break
                    
                except Exception as e:
                    logger.debug(f"Error parsing case link {idx}: {e}")
                    continue
                    
        except Exception as e:
            logger.error(f"Error parsing CommonLII results: {e}", exc_info=True)
            # Return empty list on parse errors
            return []
        
        logger.info(f"Successfully parsed {len(cases)} cases from HTML")
        return cases
    
    def _extract_citation(self, text: str, url: str) -> str:
        """Extract citation from text or URL."""
        # Look for citation patterns like [2020] 1 MLJ 456
        import re
        citation_pattern = r'\[(\d{4})\]\s*\d+\s+[A-Z]+\s+\d+'
        match = re.search(citation_pattern, text)
        if match:
            return match.group(0)
        
        # Fallback: extract from URL
        parts = url.split('/')
        if len(parts) > 2:
            return parts[-1].replace('.html', '').replace('_', ' ')
        
        return "Unknown Citation"
    
    def _extract_title(self, text: str) -> str:
        """Extract case title from text."""
        # Usually format: "Citation - Title" or just "Title"
        if ' - ' in text:
            return text.split(' - ', 1)[1].strip()
        
        # Remove citation part
        import re
        text = re.sub(r'\[\d{4}\]\s*\d+\s+[A-Z]+\s+\d+', '', text).strip()
        
        return text if text else "Untitled Case"
    
    def _extract_court_from_url(self, url: str) -> str:
        """Extract court name from URL."""
        court_map = {
            'MYFC': 'Federal Court',
            'MYCA': 'Court of Appeal',
            'MYHC': 'High Court',
            'MYHCSS': 'High Court Sabah & Sarawak',
        }
        
        for code, name in court_map.items():
            if code in url:
                return name
        
        return "Malaysian Court"
    
    def _extract_year(self, text: str, url: str) -> int:
        """Extract year from text or URL."""
        import re
        
        # Try to find [YYYY] pattern
        match = re.search(r'\[(\d{4})\]', text)
        if match:
            return int(match.group(1))
        
        # Try to find year in URL or text
        match = re.search(r'(19|20)\d{2}', text + url)
        if match:
            return int(match.group(0))
        
        return datetime.now().year
    
    def _clean_snippet(self, full_text: str, case_title: str) -> str:
        """Extract and clean case snippet/headnote."""
        # Remove case title from snippet
        snippet = full_text.replace(case_title, '').strip()
        
        # Limit length
        if len(snippet) > 300:
            snippet = snippet[:297] + "..."
        
        return snippet if snippet else "No summary available"
    
    def _extract_keywords(self, text: str) -> List[str]:
        """Extract keywords from headnote text."""
        # Simple keyword extraction (could be enhanced with NLP)
        stop_words = {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for'}
        words = text.lower().split()
        keywords = [w.strip('.,;:') for w in words if len(w) > 4 and w not in stop_words]
        return list(set(keywords[:10]))  # Return top 10 unique keywords
    
    async def close(self):
        """Close HTTP session."""
        await self.session.aclose()
        logger.info("CommonLII scraper session closed")


# Singleton instance
_scraper_instance: Optional[CommonLIIScraper] = None


def get_commonlii_scraper() -> CommonLIIScraper:
    """Get singleton instance of CommonLII scraper."""
    global _scraper_instance
    if _scraper_instance is None:
        _scraper_instance = CommonLIIScraper()
    return _scraper_instance

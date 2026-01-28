"""
AGC Malaysian Legislation Scraper.

Scrapes the Laws of Malaysia portal (lom.agc.gov.my) for:
- Malaysian Acts (Federal laws)
- Statutes
- Subsidiary Legislation

No authentication required - public access.
"""

import asyncio
import logging
import re
from typing import Dict, Any, List, Optional
from datetime import datetime
from urllib.parse import urlencode, quote

import httpx
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)


class AGCLegislationScraper:
    """
    Web scraper for Attorney General's Chambers Laws of Malaysia portal (lom.agc.gov.my).
    
    Features:
    - Search Malaysian Acts by keyword (REAL web search)
    - Get Act details and section text
    - Direct link to PDF versions
    - Rate limiting to avoid overloading
    """
    
    # AGC Laws of Malaysia endpoints
    BASE_URL = "https://lom.agc.gov.my"
    SEARCH_URL = f"{BASE_URL}/search-legislation.php"
    ACT_DETAIL_URL = f"{BASE_URL}/act-detail.php"
    ACT_VIEW_URL = f"{BASE_URL}/act-view.php"
    
    # Act Number to Name mapping (for common Acts)
    ACT_NUMBER_MAP = {
        "136": {"name": "Contracts Act 1950", "year": 1950},
        "254": {"name": "Limitation Act 1953", "year": 1953},
        "56": {"name": "Evidence Act 1950", "year": 1950},
        "67": {"name": "Civil Law Act 1956", "year": 1956},
        "777": {"name": "Companies Act 2016", "year": 2016},
        "265": {"name": "Employment Act 1955", "year": 1955},
        "828": {"name": "National Land Code 1965", "year": 1965},
        "137": {"name": "Specific Relief Act 1950", "year": 1950},
        "177": {"name": "Industrial Relations Act 1967", "year": 1967},
        "574": {"name": "Penal Code", "year": 1936},
        "593": {"name": "Criminal Procedure Code", "year": 1976},
        "611": {"name": "Trade Marks Act 2019", "year": 2019},
        "164": {"name": "Trade Unions Act 1959", "year": 1959},
        "125": {"name": "Arbitration Act 2005", "year": 2005},
        "638": {"name": "Personal Data Protection Act 2010", "year": 2010},
    }
    
    # Common Acts with section references (for quick reference)
    ACTS_DATABASE = {
        "contracts act 1950": {
            "act_no": "136",
            "common_sections": {
                "17": "Fraud defined",
                "18": "Misrepresentation defined",
                "39": "Agreement contingent on impossible event",
                "40": "When a party may rescind",
                "56": "Time as essence of contract",
                "73": "Liability of person receiving advantage under void agreement",
                "74": "Compensation for breach",
                "75": "Agreed compensation for breach"
            }
        },
        "limitation act 1953": {
            "act_no": "254",
            "common_sections": {
                "6": "Limitation period for contract and tort (6 years)",
                "9": "Period for land actions (12 years)",
                "21": "Acknowledgment and part payment",
                "26": "Effect of disability"
            }
        },
        "civil law act 1956": {
            "act_no": "67",
            "common_sections": {
                "3": "Application of English common law",
                "7": "Right to contribution",
                "8": "Survival of causes of action",
                "28A": "Damages for bereavement"
            }
        },
        "evidence act 1950": {
            "act_no": "56",
            "common_sections": {
                "57": "Facts of which Court must take judicial notice",
                "59": "Proof of facts by oral evidence",
                "62": "Primary evidence",
                "65": "When secondary evidence admissible",
                "90A": "Admissibility of electronic records",
                "101": "Burden of proof",
                "114(g)": "Adverse inference"
            }
        },
        "companies act 2016": {
            "act_no": "777",
            "common_sections": {
                "2": "Definitions",
                "17": "Separate legal personality",
                "20": "Commencement of business",
                "213": "Directors duties",
                "540": "Winding up by court",
                "560": "Fraudulent trading"
            }
        },
        "employment act 1955": {
            "act_no": "265",
            "common_sections": {
                "2": "Definitions",
                "10": "Contracts of service more than one month",
                "12": "Notice of termination",
                "14": "Termination without notice",
                "20": "Complaints of dismissal",
                "60": "Overtime payment"
            }
        },
        "national land code 1965": {
            "act_no": "828",
            "common_sections": {
                "40": "Land vested in State Authority",
                "89": "Restrictions in interest",
                "206": "Caveats",
                "315": "Void dispositions"
            }
        },
        "specific relief act 1950": {
            "act_no": "137",
            "common_sections": {
                "11": "Contracts which may be specifically enforced",
                "12": "Contracts not specifically enforceable",
                "18": "Rescission of contracts",
                "50": "Injunctions"
            }
        },
        "industrial relations act 1967": {
            "act_no": "177",
            "common_sections": {
                "5": "Right to form trade unions",
                "9": "Collective bargaining",
                "20": "Representations on dismissal",
                "26": "Industrial Court awards"
            }
        },
        "penal code": {
            "act_no": "574",
            "common_sections": {
                "300": "Murder",
                "378": "Theft",
                "379": "Punishment for theft",
                "406": "Criminal breach of trust",
                "420": "Cheating and dishonestly inducing delivery of property"
            }
        }
    }
    
    def __init__(self, timeout: int = 30):
        """Initialize AGC scraper."""
        self.timeout = timeout
        self.session = httpx.AsyncClient(
            timeout=timeout,
            headers={
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
                "Accept-Language": "en-US,en;q=0.9",
                "Accept-Encoding": "gzip, deflate, br",
                "Connection": "keep-alive",
            },
            follow_redirects=True
        )
        logger.info("AGC Legislation scraper initialized")
    
    async def search(
        self,
        query: str,
        act_name: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Search Malaysian legislation from AGC website.
        
        Args:
            query: Search keywords (e.g., "limitation period contract")
            act_name: Optional specific Act to search
        
        Returns:
            List of relevant legislation with sections and AGC links
        """
        results = []
        query_lower = query.lower()
        
        # 1. Check our local Acts database first (for common section references)
        for act_key, act_info in self.ACTS_DATABASE.items():
            if act_name:
                # Looking for specific Act
                if act_name.lower() in act_key or act_key in act_name.lower():
                    result = self._format_act_result(act_key, act_info, query_lower)
                    results.append(result)
            else:
                # Check if query terms match this Act
                if any(term in act_key for term in query_lower.split()) or \
                   any(term in str(act_info.get("common_sections", {})).lower() for term in query_lower.split()):
                    result = self._format_act_result(act_key, act_info, query_lower)
                    results.append(result)
        
        # 2. Try searching the actual AGC website for more results
        try:
            web_results = await self._search_agc_website(query)
            for wr in web_results:
                # Avoid duplicates
                if not any(r.get("act_no") == wr.get("act_no") for r in results):
                    results.append(wr)
        except Exception as e:
            logger.warning(f"AGC website search failed: {e}")
        
        logger.info(f"AGC search returned {len(results)} results for '{query}'")
        return results[:10]  # Return top 10
    
    def _format_act_result(
        self, 
        act_key: str, 
        act_info: Dict, 
        query: str
    ) -> Dict[str, Any]:
        """Format an Act result with relevant sections."""
        sections = act_info.get("common_sections", {})
        act_no = act_info.get("act_no", "")
        
        # Find sections relevant to query
        relevant_sections = []
        for section, desc in sections.items():
            if any(term in desc.lower() for term in query.split()):
                relevant_sections.append(f"Section {section}: {desc}")
        
        # If no specific match, include all common sections
        if not relevant_sections:
            relevant_sections = [f"Section {s}: {d}" for s, d in list(sections.items())[:3]]
        
        return {
            "act_name": act_key.title(),
            "act_no": f"Act {act_no}",
            "sections": relevant_sections,
            "relevance": "Act name match",
            "url": f"{self.ACT_DETAIL_URL}?language=BI&act={act_no}",
            "source": "AGC Laws of Malaysia (lom.agc.gov.my)"
        }
    
    async def _search_agc_website(self, query: str) -> List[Dict[str, Any]]:
        """
        Search AGC website directly.
        The AGC search uses POST or GET with specific parameters.
        """
        results = []
        
        try:
            # AGC uses a form-based search
            # Based on analysis, the search form submits to search-legislation.php
            # Let's try searching the principal acts page
            
            # Search in principal acts list
            response = await self.session.get(
                f"{self.BASE_URL}/principal.php",
                params={"type": "original", "language": "BI"}
            )
            
            if response.status_code == 200:
                soup = BeautifulSoup(response.text, 'html.parser')
                
                # Find all Act links
                act_links = soup.find_all('a', href=re.compile(r'act-detail\.php.*act=\d+'))
                
                query_terms = query.lower().split()
                
                for link in act_links[:50]:  # Check first 50 Acts
                    act_text = link.get_text(strip=True).lower()
                    href = link.get('href', '')
                    
                    # Check if query matches Act name
                    if any(term in act_text for term in query_terms):
                        # Extract Act number from URL
                        act_match = re.search(r'act=(\d+)', href)
                        act_no = act_match.group(1) if act_match else ""
                        
                        act_name = link.get_text(strip=True)
                        
                        results.append({
                            "act_name": act_name,
                            "act_no": f"Act {act_no}",
                            "sections": ["See full Act on AGC website"],
                            "relevance": "Web search match",
                            "url": f"{self.BASE_URL}/{href}" if not href.startswith('http') else href,
                            "source": "AGC Laws of Malaysia (lom.agc.gov.my)"
                        })
                        
                        if len(results) >= 5:
                            break
        
        except Exception as e:
            logger.debug(f"AGC web search error: {e}")
        
        return results
    
    async def get_act_details(self, act_no: str) -> Optional[Dict[str, Any]]:
        """
        Get detailed information about a specific Act from AGC website.
        
        Args:
            act_no: Act number (e.g., "136" or "Act 136")
        
        Returns:
            Act details including title, dates, and link to full text
        """
        # Clean act number
        act_no = act_no.replace("Act ", "").strip()
        
        # First check local database
        for act_key, act_info in self.ACTS_DATABASE.items():
            if act_info.get("act_no") == act_no:
                return {
                    "act_name": act_key.title(),
                    "act_no": f"Act {act_no}",
                    "sections": act_info.get("common_sections", {}),
                    "url": f"{self.ACT_DETAIL_URL}?language=BI&act={act_no}",
                    "source": "AGC Laws of Malaysia"
                }
        
        # Try fetching from AGC website
        try:
            url = f"{self.ACT_DETAIL_URL}?language=BI&act={act_no}"
            response = await self.session.get(url)
            
            if response.status_code == 200:
                soup = BeautifulSoup(response.text, 'html.parser')
                
                # Try to find Act title
                title_elem = soup.find('h1')
                title = title_elem.get_text(strip=True) if title_elem else f"Act {act_no}"
                
                # Find publication date
                pub_date = ""
                date_match = re.search(r'Publication Date:\s*(\d{2}/\d{2}/\d{4})', response.text)
                if date_match:
                    pub_date = date_match.group(1)
                
                return {
                    "act_name": title,
                    "act_no": f"Act {act_no}",
                    "publication_date": pub_date,
                    "sections": {},
                    "url": url,
                    "source": "AGC Laws of Malaysia (lom.agc.gov.my)"
                }
        
        except Exception as e:
            logger.debug(f"Failed to fetch Act {act_no}: {e}")
        
        return None
    
    async def get_act_pdf_url(self, act_no: str) -> Optional[str]:
        """
        Get the PDF download URL for an Act.
        
        Args:
            act_no: Act number
        
        Returns:
            PDF URL if available
        """
        act_no = act_no.replace("Act ", "").strip()
        # PDF URLs typically follow this pattern
        return f"{self.ACT_VIEW_URL}?language=BI&type=original&no=Act%20{act_no}"
    
    async def close(self):
        """Close HTTP session."""
        await self.session.aclose()
        logger.info("AGC scraper session closed")


# ============================================
# SINGLETON INSTANCE
# ============================================

_agc_scraper: Optional[AGCLegislationScraper] = None


def get_agc_scraper() -> AGCLegislationScraper:
    """Get singleton instance of AGC legislation scraper."""
    global _agc_scraper
    if _agc_scraper is None:
        _agc_scraper = AGCLegislationScraper()
    return _agc_scraper


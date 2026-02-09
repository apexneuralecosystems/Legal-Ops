"""
Judgment Cache Service
Manages caching of full court judgments to eliminate repeated Lexis fetching.

Phase 3: Caching & Optimization
- Stores complete 50-200 page judgments in PostgreSQL
- Provides instant retrieval (0s vs 3-5s per fetch)
- Tracks cache statistics and access patterns
"""

from sqlalchemy.orm import Session
from sqlalchemy import func, delete as sql_delete
from datetime import datetime, timezone
from typing import Optional, Dict, Any, List
import uuid
from models.cached_judgment import CachedJudgment


class JudgmentCacheService:
    """Service for managing judgment cache operations"""

    def __init__(self, db: Session):
        """Initialize cache service with database session"""
        self.db = db
    
    def check_cache_exists(self, case_link: str) -> bool:
        """
        Quick boolean check if judgment is cached.
        
        Args:
            case_link: URL to the Lexis case page
            
        Returns:
            True if cached, False if not
        """
        from sqlalchemy import select
        stmt = select(CachedJudgment).where(CachedJudgment.case_link == case_link)
        result = self.db.execute(stmt)
        exists = result.scalar_one_or_none() is not None
        
        return exists
    
    def get_cached_judgment(self, case_link: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve cached judgment and update access tracking.
        
        Args:
            case_link: URL to the Lexis case page
            
        Returns:
            Judgment data dict if cached, None if not cached
        """
        cached = self.db.query(CachedJudgment).filter(
            CachedJudgment.case_link == case_link
        ).first()
        
        if not cached:
            return None
        
        # Update access tracking
        cached.access_count += 1
        cached.last_accessed_at = datetime.now(timezone.utc)
        self.db.commit()
        
        # Return judgment data
        return cached.to_dict()
    
    def store_judgment(
        self,
        case_link: str,
        judgment_data: Dict[str, Any]
    ) -> CachedJudgment:
        """
        Store newly fetched judgment in cache.
        
        Args:
            case_link: URL to the Lexis case page
            judgment_data: Full judgment data from LexisScraper
            
        Returns:
            Created CachedJudgment instance
        """
        # Check if already exists (avoid duplicates)
        existing = self.db.query(CachedJudgment).filter(
            CachedJudgment.case_link == case_link
        ).first()
        
        if existing:
            # Update existing entry
            self._update_cached_judgment(existing, judgment_data)
            return existing
        
        # Create new cache entry
        cached = CachedJudgment(
            id=str(uuid.uuid4()),
            case_link=case_link,
            citation=judgment_data.get('citation'),
            case_title=judgment_data.get('title'),
            court=judgment_data.get('court'),
            judgment_date=judgment_data.get('date'),
            full_text=judgment_data.get('full_text', ''),
            headnotes=judgment_data.get('headnotes'),
            facts=judgment_data.get('facts'),
            issues_text=judgment_data.get('issues'),
            reasoning=judgment_data.get('reasoning'),
            judges=judgment_data.get('judges'),
            word_count=judgment_data.get('word_count', 0),
            sections_count=judgment_data.get('sections_count', 0),
            fetched_at=datetime.now(timezone.utc),
            fetch_success='true',
            access_count=0,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc)
        )
        
        self.db.add(cached)
        self.db.commit()
        self.db.refresh(cached)
        
        return cached
    
    def _update_cached_judgment(
        self,
        cached: CachedJudgment,
        judgment_data: Dict[str, Any]
    ) -> None:
        """Update existing cached judgment with new data"""
        cached.citation = judgment_data.get('citation', cached.citation)
        cached.case_title = judgment_data.get('title', cached.case_title)
        cached.court = judgment_data.get('court', cached.court)
        cached.judgment_date = judgment_data.get('date', cached.judgment_date)
        cached.full_text = judgment_data.get('full_text', cached.full_text)
        cached.headnotes = judgment_data.get('headnotes', cached.headnotes)
        cached.facts = judgment_data.get('facts', cached.facts)
        cached.issues_text = judgment_data.get('issues', cached.issues_text)
        cached.reasoning = judgment_data.get('reasoning', cached.reasoning)
        cached.judges = judgment_data.get('judges', cached.judges)
        cached.word_count = judgment_data.get('word_count', cached.word_count)
        cached.sections_count = judgment_data.get('sections_count', cached.sections_count)
        cached.updated_at = datetime.now(timezone.utc)
        
        self.db.commit()
    
    def get_cache_statistics(self) -> Dict[str, Any]:
        """
        Get cache performance statistics.
        
        Returns:
            Dict with cache metrics:
            - total_cached: Number of judgments stored
            - total_words: Total words cached
            - avg_word_count: Average judgment length
            - total_accesses: Total cache hits
            - most_accessed: Top 5 most accessed judgments
        """
        # Total cached judgments
        total_cached = self.db.query(CachedJudgment).count()
        
        if total_cached == 0:
            return {
                'total_cached': 0,
                'total_words': 0,
                'avg_word_count': 0,
                'total_accesses': 0,
                'most_accessed': []
            }
        
        # Total words
        total_words = self.db.query(
            self.db.func.sum(CachedJudgment.word_count)
        ).scalar() or 0
        
        # Average word count
        avg_word_count = total_words // total_cached if total_cached > 0 else 0
        
        # Total accesses
        total_accesses = self.db.query(
            self.db.func.sum(CachedJudgment.access_count)
        ).scalar() or 0
        
        # Most accessed judgments
        most_accessed = self.db.query(CachedJudgment).order_by(
            CachedJudgment.access_count.desc()
        ).limit(5).all()
        
        most_accessed_list = [
            {
                'case_title': c.case_title,
                'citation': c.citation,
                'access_count': c.access_count,
                'word_count': c.word_count,
                'last_accessed': c.last_accessed_at.isoformat() if c.last_accessed_at else None
            }
            for c in most_accessed
        ]
        
        return {
            'total_cached': total_cached,
            'total_words': total_words,
            'avg_word_count': avg_word_count,
            'total_accesses': total_accesses,
            'most_accessed': most_accessed_list,
            'cache_hit_rate': self._calculate_hit_rate(),
            'storage_saved_mb': self._estimate_storage_saved(total_words)
        }
    
    def _calculate_hit_rate(self) -> float:
        """Calculate cache hit rate as percentage"""
        total_accesses = self.db.query(
            self.db.func.sum(CachedJudgment.access_count)
        ).scalar() or 0
        
        total_cached = self.db.query(CachedJudgment).count()
        
        if total_cached == 0:
            return 0.0
        
        # Estimate: Each judgment fetched once + all subsequent accesses are hits
        # Hit rate = (total_accesses) / (total_accesses + total_cached) * 100
        total_requests = total_accesses + total_cached
        hit_rate = (total_accesses / total_requests * 100) if total_requests > 0 else 0.0
        
        return round(hit_rate, 2)
    
    def _estimate_storage_saved(self, total_words: int) -> float:
        """Estimate storage space savings in MB"""
        # Approximate: 1 word = 6 bytes average (including whitespace)
        bytes_saved = total_words * 6
        mb_saved = bytes_saved / (1024 * 1024)
        return round(mb_saved, 2)
    
    def get_batch_cached_judgments(
        self,
        case_links: List[str]
    ) -> Dict[str, Dict[str, Any]]:
        """
        Retrieve multiple cached judgments in one query.
        
        Args:
            case_links: List of case URLs to check
            
        Returns:
            Dict mapping case_link -> judgment data
        """
        cached_judgments = self.db.query(CachedJudgment).filter(
            CachedJudgment.case_link.in_(case_links)
        ).all()
        
        result = {}
        for cached in cached_judgments:
            # Update access tracking
            cached.access_count += 1
            cached.last_accessed_at = datetime.now(timezone.utc)
            result[cached.case_link] = cached.to_dict()
        
        if result:
            self.db.commit()
        
        return result
    
    def clear_old_cache(self, days: int = 90) -> int:
        """
        Clear cache entries older than specified days.
        
        Args:
            days: Age threshold in days (default 90)
            
        Returns:
            Number of entries deleted
        """
        from datetime import timedelta
        cutoff_date = datetime.now(timezone.utc) - timedelta(days=days)
        
        deleted = self.db.query(CachedJudgment).filter(
            CachedJudgment.fetched_at < cutoff_date
        ).delete()
        
        self.db.commit()
        return deleted
    
    def clear_all_cache(self) -> int:
        """
        Clear entire cache (use with caution).
        
        Returns:
            Number of entries deleted
        """
        deleted = self.db.query(CachedJudgment).delete()
        self.db.commit()
        return deleted

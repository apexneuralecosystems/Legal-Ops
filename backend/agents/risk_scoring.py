"""
Risk and Complexity Scoring Agent.
"""
from agents.base_agent import BaseAgent
from typing import Dict, Any, List
from datetime import datetime, timedelta


class RiskScoringAgent(BaseAgent):
    """
    Produces 1-5 scores for jurisdictional, language, volume, and time pressure.
    
    Inputs:
    - matter_snapshot: structured case information
    - document_manifest: list of documents
    - user_deadline: optional deadline date
    
    Outputs:
    - risk_scores: {jurisdictional_complexity, language_complexity, volume_risk, time_pressure, composite_score, rationale}
    """
    
    def __init__(self):
        super().__init__(agent_id="RiskScoring")
    
    async def process(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process risk scoring request.
        
        Args:
            inputs: {
                "matter_snapshot": Dict,
                "document_manifest": List[Dict],
                "user_deadline": str (ISO format, optional)
            }
            
        Returns:
            {
                "risk_scores": Dict with all scores and rationale
            }
        """
        await self.validate_input(inputs, ["matter_snapshot"])
        
        matter = inputs["matter_snapshot"]
        doc_manifest = inputs.get("document_manifest", [])
        user_deadline = inputs.get("user_deadline")
        
        # Calculate individual risk scores
        jurisdictional = self._score_jurisdictional_complexity(matter)
        language = self._score_language_complexity(matter, doc_manifest)
        volume = self._score_volume_risk(matter, doc_manifest)
        time_pressure = self._score_time_pressure(user_deadline)
        
        # Calculate composite score (weighted average)
        composite = (
            jurisdictional * 0.25 +
            language * 0.30 +
            volume * 0.20 +
            time_pressure * 0.25
        )
        
        # Generate rationale
        rationale = self._generate_rationale(
            jurisdictional, language, volume, time_pressure, matter
        )
        
        # Determine if human review is required
        human_review_required = composite >= 4.0 or language >= 4
        
        risk_scores = {
            "jurisdictional_complexity": jurisdictional,
            "language_complexity": language,
            "volume_risk": volume,
            "time_pressure": time_pressure,
            "composite_score": round(composite, 2),
            "rationale": rationale,
            "human_review_required": human_review_required,
            "suggested_next_steps": self._suggest_next_steps(
                jurisdictional, language, volume, time_pressure
            )
        }
        
        return self.format_output(
            data={"risk_scores": risk_scores},
            confidence=0.85,
            human_review_required=human_review_required
        )
    
    def _score_jurisdictional_complexity(self, matter: Dict[str, Any]) -> int:
        """
        Score jurisdictional complexity (1-5).
        
        Factors:
        - Cross-state elements
        - Foreign parties
        - Multiple jurisdictions
        - Court level
        """
        score = 1
        
        court = str(matter.get("court", "")).lower() if matter.get("court") else ""
        jurisdiction = str(matter.get("jurisdiction", "")).lower() if matter.get("jurisdiction") else ""
        parties = matter.get("parties", [])
        
        # Court level
        if "federal court" in court or "court of appeal" in court:
            score += 2
        elif "high court" in court:
            score += 1
        
        # Cross-state or international elements
        if "east malaysia" in jurisdiction and "peninsular" in jurisdiction:
            score += 1
        
        # Foreign parties (check for non-Malaysian addresses)
        for party in parties:
            address = str(party.get("address", "")).lower() if party.get("address") else ""
            if any(country in address for country in ["singapore", "uk", "usa", "china", "indonesia"]):
                score += 1
                break
        
        return min(score, 5)
    
    def _score_language_complexity(
        self,
        matter: Dict[str, Any],
        doc_manifest: List[Dict]
    ) -> int:
        """
        Score language complexity (1-5).
        
        Factors:
        - Mixed language documents
        - Low translation confidence
        - Technical legal Malay
        """
        score = 1
        
        # Check document language distribution
        lang_counts = {"ms": 0, "en": 0, "mixed": 0, "unknown": 0}
        low_confidence_count = 0
        
        for doc in doc_manifest:
            lang_hint = doc.get("doc_lang_hint", "unknown")
            lang_counts[lang_hint] = lang_counts.get(lang_hint, 0) + 1
            # Safely handle None confidence values
            doc_conf = doc.get("confidence") or 1.0
            if doc_conf < 0.7:
                low_confidence_count += 1
        
        # Mixed language documents
        if lang_counts["mixed"] > 0:
            score += 1
        
        # Both Malay and English documents
        if lang_counts["ms"] > 0 and lang_counts["en"] > 0:
            score += 1
        
        # Low confidence documents
        if low_confidence_count > len(doc_manifest) * 0.3:
            score += 2
        elif low_confidence_count > 0:
            score += 1
        
        return min(score, 5)
    
    def _score_volume_risk(
        self,
        matter: Dict[str, Any],
        doc_manifest: List[Dict]
    ) -> int:
        """
        Score volume risk (1-5).
        
        Factors:
        - Number of documents
        - Total word count
        - Estimated pages
        """
        score = 1
        
        doc_count = len(doc_manifest)
        volume_estimate = matter.get("volume_estimate", 0)
        estimated_pages = matter.get("estimated_pages", 0)
        
        # Document count
        if doc_count > 50:
            score += 2
        elif doc_count > 20:
            score += 1
        
        # Word count
        if volume_estimate > 100000:
            score += 2
        elif volume_estimate > 50000:
            score += 1
        
        # Pages
        if estimated_pages > 100:
            score += 1
        
        return min(score, 5)
    
    def _score_time_pressure(self, user_deadline: str = None) -> int:
        """
        Score time pressure (1-5).
        
        Factors:
        - Days until deadline
        """
        if not user_deadline:
            return 2  # Default moderate pressure
        
        try:
            deadline = datetime.fromisoformat(user_deadline.replace('Z', '+00:00'))
            days_remaining = (deadline - datetime.utcnow()).days
            
            if days_remaining < 7:
                return 5
            elif days_remaining < 14:
                return 4
            elif days_remaining < 30:
                return 3
            elif days_remaining < 60:
                return 2
            else:
                return 1
        except:
            return 2  # Default if parsing fails
    
    def _generate_rationale(
        self,
        jurisdictional: int,
        language: int,
        volume: int,
        time_pressure: int,
        matter: Dict[str, Any]
    ) -> List[str]:
        """Generate human-readable rationale for scores."""
        rationale = []
        
        if jurisdictional >= 4:
            rationale.append(f"High jurisdictional complexity due to {matter.get('court', 'complex court')} level")
        
        if language >= 4:
            rationale.append("Significant language complexity with mixed Malay/English documents and low translation confidence")
        elif language >= 3:
            rationale.append("Moderate language complexity with bilingual documents")
        
        if volume >= 4:
            rationale.append(f"High volume risk with {matter.get('estimated_pages', 'many')} estimated pages")
        
        if time_pressure >= 4:
            rationale.append("Urgent deadline requiring immediate attention")
        
        return rationale
    
    def _suggest_next_steps(
        self,
        jurisdictional: int,
        language: int,
        volume: int,
        time_pressure: int
    ) -> List[str]:
        """Suggest next steps based on risk scores."""
        steps = []
        
        if language >= 4:
            steps.append("Assign certified translator for high-accuracy translation")
        
        if jurisdictional >= 4:
            steps.append("Consult senior partner on jurisdictional issues")
        
        if volume >= 4:
            steps.append("Allocate additional paralegal resources for document review")
        
        if time_pressure >= 4:
            steps.append("Prioritize this matter and consider expedited workflows")
        
        if not steps:
            steps.append("Proceed with standard workflow")
        
        return steps

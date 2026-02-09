"""
Knowledge Base Enrichment Service

Enriches legal arguments with historical insights by:
1. Finding similar historical matters
2. Extracting success patterns
3. Identifying risk factors
4. Predicting outcomes
5. Generating strategic recommendations

IMPORTANT: This compares CLIENT MATTERS to HISTORICAL MATTERS,
NOT Lexis cases to each other.
"""

import logging
from typing import Dict, List, Optional, Any
from sqlalchemy.orm import Session
from services.cross_case_learning_service import get_cross_case_learning_service
from services.case_insight_service import get_case_insight_service

logger = logging.getLogger(__name__)


class KBEnrichmentService:
    """Enriches arguments with knowledge base insights"""
    
    def __init__(self):
        self.cross_case_service = get_cross_case_learning_service()
        self.insight_service = get_case_insight_service()
    
    async def enrich_argument_data(
        self,
        matter_id: Optional[str],
        user_selected_cases: List[Dict[str, Any]],
        issues: List[Dict[str, Any]],
        db: Session
    ) -> Dict[str, Any]:
        """
        Main enrichment method: Query knowledge base for strategic insights.
        
        Args:
            matter_id: The client matter ID (if working on specific case)
            user_selected_cases: Cases selected from Lexis
            issues: Legal issues being addressed
            db: Database session
            
        Returns:
            {
                "kb_available": bool,
                "similar_matters": [...],
                "success_patterns": [...],
                "risk_factors": [...],
                "outcome_prediction": {...},
                "strategic_recommendations": [...],
                "additional_cases": [...],  # Cases from KB (not Lexis)
                "insights": {...}
            }
        """
        
        # If no matter_id, KB cannot provide insights
        if not matter_id:
            logger.info("ℹ️ No matter_id provided - KB insights not available for general research")
            return {
                "kb_available": False,
                "message": "Knowledge Base insights require a specific matter for comparison. Select a matter to enable strategic analysis.",
                "similar_matters": [],
                "success_patterns": [],
                "risk_factors": [],
                "outcome_prediction": {},
                "strategic_recommendations": [],
                "additional_cases": [],
                "insights": {}
            }
        
        try:
            logger.info(f"📚 Querying Knowledge Base for matter: {matter_id}")
            
            # 1. Find similar historical matters
            similar_cases_data = await self.cross_case_service.analyze_similar_cases(
                matter_id=matter_id,
                db=db,
                limit=10
            )
            
            similar_matters = similar_cases_data.get("similar_cases", [])
            success_patterns = similar_cases_data.get("success_patterns", [])
            outcome_prediction = similar_cases_data.get("outcome_prediction", {})
            strategic_recs = similar_cases_data.get("strategic_recommendations", [])
            
            logger.info(f"✅ Found {len(similar_matters)} similar historical matters")
            
            # 2. Get case-specific insights for user-selected Lexis cases
            case_insights = []
            for case in user_selected_cases[:5]:  # Top 5 cases
                # Note: This would require storing Lexis case IDs in our insights table
                # For now, we'll skip this as it requires more setup
                pass
            
            # 3. Extract risk factors (patterns from losing cases)
            risk_factors = []
            for pattern in success_patterns:
                if pattern.get("pattern_type") == "risk_factor":
                    risk_factors.append(pattern)
            
            # Remove risk factors from success patterns
            success_patterns = [p for p in success_patterns if p.get("pattern_type") != "risk_factor"]
            
            # 4. Format additional cases from similar matters (if any)
            additional_cases = []
            for similar in similar_matters[:3]:  # Top 3 most similar
                matter_data = similar.get("matter", {})
                if isinstance(matter_data, dict):
                    additional_cases.append({
                        "title": matter_data.get("title", "Unknown Matter"),
                        "citation": f"Internal Ref: {matter_data.get('id', 'N/A')[:8]}",
                        "court": matter_data.get("jurisdiction", "N/A"),
                        "similarity_score": similar.get("similarity_score", 0),
                        "outcome": similar.get("outcome_type", "Unknown"),
                        "from_knowledge_base": True
                    })
            
            return {
                "kb_available": True,
                "similar_matters_count": len(similar_matters),
                "similar_matters": similar_matters,
                "success_patterns": success_patterns,
                "risk_factors": risk_factors,
                "outcome_prediction": outcome_prediction,
                "strategic_recommendations": strategic_recs,
                "additional_cases": additional_cases,
                "insights": {
                    "success_patterns": success_patterns,
                    "risk_factors": risk_factors,
                    "outcome_prediction": outcome_prediction,
                    "strategic_recommendations": strategic_recs,
                    "case_insights": case_insights
                }
            }
            
        except Exception as e:
            logger.error(f"❌ KB enrichment failed: {str(e)}", exc_info=True)
            # Return empty structure on error (graceful degradation)
            return {
                "kb_available": False,
                "error": str(e),
                "similar_matters": [],
                "success_patterns": [],
                "risk_factors": [],
                "outcome_prediction": {},
                "strategic_recommendations": [],
                "additional_cases": [],
                "insights": {}
            }
    
    def format_kb_insights_for_memo(self, kb_data: Dict[str, Any]) -> str:
        """
        Format KB insights into markdown section for inclusion in memo.
        
        Returns formatted markdown string.
        """
        if not kb_data.get("kb_available"):
            return ""
        
        similar_count = kb_data.get("similar_matters_count", 0)
        if similar_count == 0:
            return """
## 📚 KNOWLEDGE BASE INSIGHTS

No similar historical matters found in the database. This appears to be a novel case type for your practice.

**Recommendation:** Consider documenting the outcome of this matter to build knowledge base for future similar cases.

---
"""
        
        md = f"""
## 📚 KNOWLEDGE BASE INSIGHTS

Based on analysis of **{similar_count} similar historical matters** in your practice database:

"""
        
        # Success Patterns
        success_patterns = kb_data.get("success_patterns", [])
        if success_patterns:
            md += """
### ✅ SUCCESS PATTERNS IDENTIFIED

"""
            for i, pattern in enumerate(success_patterns[:5], 1):
                title = pattern.get("title", "Unknown Pattern")
                description = pattern.get("description", "")
                success_rate = pattern.get("success_rate", 0) * 100
                confidence = pattern.get("confidence", 0) * 100
                
                md += f"""**{i}. {title}**
- Success Rate: {success_rate:.0f}%
- Confidence: {confidence:.0f}%
- Details: {description}

"""
        
        # Risk Factors
        risk_factors = kb_data.get("risk_factors", [])
        if risk_factors:
            md += """
### ⚠️ RISK FACTORS TO ADDRESS

"""
            for i, risk in enumerate(risk_factors[:5], 1):
                title = risk.get("title", "Unknown Risk")
                description = risk.get("description", "")
                
                md += f"""**{i}. {title}**
- Details: {description}
- Mitigation: Address this proactively in pleadings and evidence

"""
        
        # Outcome Prediction
        outcome_pred = kb_data.get("outcome_prediction", {})
        if outcome_pred:
            predicted_outcome = outcome_pred.get("predicted_outcome", "Unknown")
            confidence = outcome_pred.get("confidence", 0) * 100
            key_factors = outcome_pred.get("key_factors", [])
            
            md += f"""
### 📊 PREDICTED OUTCOME

Based on historical patterns:
- **Predicted Result:** {predicted_outcome}
- **Confidence Level:** {confidence:.0f}%
"""
            
            if key_factors:
                md += "\n**Key Determinants:**\n"
                for factor in key_factors[:3]:
                    md += f"- {factor}\n"
        
        # Strategic Recommendations
        strategic_recs = kb_data.get("strategic_recommendations", [])
        if strategic_recs:
            md += """

### 💡 STRATEGIC RECOMMENDATIONS

"""
            for i, rec in enumerate(strategic_recs[:5], 1):
                if isinstance(rec, dict):
                    rec_text = rec.get("recommendation", rec.get("title", ""))
                    category = rec.get("category", "general")
                else:
                    rec_text = str(rec)
                    category = "general"
                
                md += f"{i}. **{category.title()}:** {rec_text}\n"
        
        md += "\n---\n"
        return md


# Singleton instance
_kb_enrichment_service = None


def get_kb_enrichment_service() -> KBEnrichmentService:
    """Get or create KB enrichment service singleton"""
    global _kb_enrichment_service
    if _kb_enrichment_service is None:
        _kb_enrichment_service = KBEnrichmentService()
    return _kb_enrichment_service

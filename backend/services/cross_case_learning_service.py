"""Cross-Case Learning Service - Learn from Historical Similar Cases"""

import json
import logging
from typing import Dict, List, Optional, Any
from uuid import uuid4
from datetime import datetime, timezone
from decimal import Decimal

from sqlalchemy.orm import Session
from sqlalchemy import func, and_
from models.cross_case_learning import CasePattern, CaseOutcome, CaseSimilarity
from models.case_intelligence import CaseEntity
from models.matter import Matter
from services.llm_service import get_llm_service

logger = logging.getLogger(__name__)


class CrossCaseLearningService:
    """Analyzes historical cases to predict outcomes and suggest strategies"""
    
    def __init__(self):
        self.llm = get_llm_service()
    
    async def analyze_similar_cases(
        self, 
        matter_id: str, 
        db: Session,
        limit: int = 5
    ) -> Dict[str, Any]:
        """
        Find similar historical cases and extract learnings.
        
        Returns:
            {
                "similar_cases": [...],
                "success_patterns": [...],
                "outcome_prediction": {...},
                "strategic_recommendations": [...]
            }
        """
        try:
            # Get current case details (async syntax)
            from sqlalchemy import select
            stmt = select(Matter).where(Matter.id == matter_id)
            result = await db.execute(stmt)
            current_matter = result.scalar_one_or_none()
            
            if not current_matter:
                raise ValueError(f"Matter {matter_id} not found")
            
            stmt = select(CaseEntity).where(CaseEntity.matter_id == matter_id)
            result = await db.execute(stmt)
            current_entities = result.scalars().all()
            
            logger.info(f"Analyzing similar cases for matter {matter_id}")
            
            # Find similar cases
            similar_cases = await self._find_similar_cases(
                matter_id, current_matter, current_entities, db, limit
            )
            
            if not similar_cases:
                return {
                    "similar_cases_found": 0,
                    "message": "No similar historical cases found. Need cases with outcomes to learn from.",
                    "similar_cases": [],
                    "success_patterns": [],
                    "outcome_prediction": {},
                    "strategic_recommendations": []
                }
            
            logger.info(f"Found {len(similar_cases)} similar cases")
            
            # Extract success patterns
            patterns = await self._extract_patterns(similar_cases, db)
            
            # Predict outcome
            prediction = await self._predict_outcome(
                current_matter, current_entities, similar_cases, patterns, db
            )
            
            # Generate recommendations
            recommendations = await self._generate_strategic_recommendations(
                current_matter, current_entities, patterns, similar_cases, db
            )
            
            return {
                "similar_cases_found": len(similar_cases),
                "similar_cases": [self._format_case_summary(c) for c in similar_cases],
                "success_patterns": patterns,
                "outcome_prediction": prediction,
                "strategic_recommendations": recommendations
            }
            
        except Exception as e:
            logger.error(f"Error analyzing similar cases: {str(e)}", exc_info=True)
            raise
    
    async def _find_similar_cases(
        self, 
        matter_id: str,
        current_matter: Matter,
        current_entities: List,
        db: Session,
        limit: int
    ) -> List[Dict]:
        """Find cases similar to the current one"""
        
        # Get all matters with outcomes (exclude current case) - async syntax
        from sqlalchemy import select
        stmt = select(Matter, CaseOutcome).join(
            CaseOutcome, Matter.id == CaseOutcome.matter_id
        ).where(
            Matter.id != matter_id
        )
        result = await db.execute(stmt)
        cases_with_outcomes = result.all()
        
        if not cases_with_outcomes:
            logger.warning("No cases with outcomes found in database")
            return []
        
        # Fetch entities for all matters upfront (async)
        from sqlalchemy import select
        matter_ids = [matter.id for matter, _ in cases_with_outcomes]
        stmt = select(CaseEntity).where(CaseEntity.matter_id.in_(matter_ids))
        result = await db.execute(stmt)
        all_entities = result.scalars().all()
        
        # Group entities by matter_id
        entities_by_matter = {}
        for entity in all_entities:
            if entity.matter_id not in entities_by_matter:
                entities_by_matter[entity.matter_id] = []
            entities_by_matter[entity.matter_id].append(entity)
        
        # Calculate similarity scores
        similarities = []
        for matter, outcome in cases_with_outcomes:
            entities2 = entities_by_matter.get(matter.id, [])
            score = self._calculate_similarity_score(
                current_matter, current_entities, matter, entities2
            )
            
            logger.info(f"Similarity with {matter.title}: {score:.2f}")
            
            if score > 0.3:  # Only include if similarity > 30%
                similarities.append({
                    "matter": matter,
                    "outcome": outcome,
                    "similarity_score": score
                })
        
        # Sort by similarity and take top N
        similarities.sort(key=lambda x: x['similarity_score'], reverse=True)
        return similarities[:limit]
    
    def _calculate_similarity_score(
        self,
        matter1: Matter,
        entities1: List,
        matter2: Matter,
        entities2: List
    ) -> float:
        """Calculate similarity score between two cases"""
        
        scores = []
        
        # 1. Case type similarity (40% weight)
        if matter1.matter_type == matter2.matter_type:
            scores.append(('type', 1.0, 0.4))
        else:
            scores.append(('type', 0.0, 0.4))
        
        # 2. Jurisdiction similarity (20% weight)
        if matter1.jurisdiction == matter2.jurisdiction:
            scores.append(('jurisdiction', 1.0, 0.2))
        else:
            scores.append(('jurisdiction', 0.5, 0.2))
        
        # 3. Entity similarity (30% weight) - check if similar parties/claims
        entity_score = self._compare_entities(entities1, entities2)
        scores.append(('entities', entity_score, 0.3))
        
        # 4. Issue similarity (10% weight)
        issues1 = matter1.issues or []
        issues2 = matter2.issues or []
        issue_score = len(set(str(i) for i in issues1) & set(str(i) for i in issues2)) / max(len(issues1), len(issues2), 1)
        scores.append(('issues', issue_score, 0.1))
        
        # Calculate weighted average
        total_score = sum(score * weight for _, score, weight in scores)
        
        return total_score
    
    def _compare_entities(self, entities1: List, entities2: List) -> float:
        """Compare entity lists for similarity"""
        
        types1 = {e.entity_type for e in entities1}
        types2 = {e.entity_type for e in entities2}
        
        if not types1 or not types2:
            return 0.0
        
        # Jaccard similarity of entity types
        intersection = len(types1 & types2)
        union = len(types1 | types2)
        
        return intersection / union if union > 0 else 0.0
    
    async def _extract_patterns(self, similar_cases: List[Dict], db: Session) -> List[Dict]:
        """Extract success patterns from similar cases"""
        
        patterns = []
        
        # Analyze winning vs losing cases
        winning_cases = [c for c in similar_cases if 
                        c['outcome'].outcome_type in ['judgment_plaintiff', 'settlement']]
        losing_cases = [c for c in similar_cases if 
                       c['outcome'].outcome_type in ['judgment_defendant', 'dismissed']]
        
        total_cases = len(similar_cases)
        success_rate = len(winning_cases) / total_cases if total_cases > 0 else 0.0
        
        # Pattern: Overall success rate
        patterns.append({
            "pattern_type": "overall_success_rate",
            "title": f"Overall Success Rate for Similar Cases",
            "description": f"{len(winning_cases)} of {total_cases} similar cases resulted in favorable outcomes",
            "success_rate": success_rate,
            "confidence": min(total_cases / 10.0, 1.0),  # More cases = higher confidence
            "applicable_to": "current_case"
        })
        
        # Pattern: Common success factors
        if winning_cases:
            common_factors = self._find_common_factors(winning_cases)
            for factor, frequency in common_factors.items():
                factor_success_rate = frequency / len(winning_cases)
                if factor_success_rate >= 0.6:  # Appears in 60%+ of winning cases
                    patterns.append({
                        "pattern_type": "success_factor",
                        "title": f"Success Factor: {factor}",
                        "description": f"Present in {frequency}/{len(winning_cases)} winning cases",
                        "success_rate": factor_success_rate,
                        "confidence": 0.8,
                        "applicable_to": "evidence_strategy"
                    })
        
        # Pattern: Common failure factors
        if losing_cases:
            failure_factors = self._find_common_factors(losing_cases)
            for factor, frequency in failure_factors.items():
                factor_failure_rate = frequency / len(losing_cases)
                if factor_failure_rate >= 0.6:
                    patterns.append({
                        "pattern_type": "risk_factor",
                        "title": f"Risk Factor: {factor}",
                        "description": f"Present in {frequency}/{len(losing_cases)} losing cases",
                        "success_rate": 1.0 - factor_failure_rate,
                        "confidence": 0.75,
                        "applicable_to": "risk_mitigation"
                    })
        
        return patterns
    
    def _find_common_factors(self, cases: List[Dict]) -> Dict[str, int]:
        """Find factors that appear frequently in a set of cases"""
        
        factor_counts = {}
        
        for case in cases:
            outcome = case['outcome']
            
            # Count key factors
            for factor in (outcome.key_factors or []):
                factor_counts[factor] = factor_counts.get(factor, 0) + 1
            
            # Count decisive evidence
            for evidence in (outcome.decisive_evidence or []):
                evidence_key = f"evidence_{evidence}"
                factor_counts[evidence_key] = factor_counts.get(evidence_key, 0) + 1
            
            # Count winning arguments
            for arg in (outcome.winning_arguments or []):
                arg_key = f"argument_{arg}"
                factor_counts[arg_key] = factor_counts.get(arg_key, 0) + 1
        
        return factor_counts
    
    async def _predict_outcome(
        self,
        current_matter: Matter,
        current_entities: List,
        similar_cases: List[Dict],
        patterns: List[Dict],
        db: Session
    ) -> Dict:
        """Predict likely outcome based on similar cases"""
        
        if not similar_cases:
            return {}
        
        # Calculate success probability
        favorable_outcomes = sum(1 for c in similar_cases if 
                                c['outcome'].outcome_type in ['judgment_plaintiff', 'settlement'])
        success_probability = favorable_outcomes / len(similar_cases)
        
        # Calculate average settlement amount
        settlements = [float(c['outcome'].settlement_amount or 0) 
                      for c in similar_cases if c['outcome'].settlement_amount]
        avg_settlement = sum(settlements) / len(settlements) if settlements else 0
        
        # Calculate average settlement percentage of claim
        settlement_percentages = []
        for c in similar_cases:
            if c['outcome'].settlement_amount and c['outcome'].claim_amount:
                percentage = float(c['outcome'].settlement_amount) / float(c['outcome'].claim_amount)
                settlement_percentages.append(percentage)
        
        avg_settlement_pct = sum(settlement_percentages) / len(settlement_percentages) if settlement_percentages else 0
        
        # Calculate average duration
        durations = [c['outcome'].duration_months for c in similar_cases 
                    if c['outcome'].duration_months]
        avg_duration = sum(durations) / len(durations) if durations else 0
        
        return {
            "success_probability": round(success_probability, 2),
            "predicted_outcome": "favorable" if success_probability > 0.5 else "unfavorable",
            "confidence": min(len(similar_cases) / 10.0, 1.0),
            "average_settlement_amount": f"RM {avg_settlement:,.2f}" if avg_settlement > 0 else "N/A",
            "average_settlement_percentage": f"{avg_settlement_pct * 100:.1f}% of claim" if avg_settlement_pct > 0 else "N/A",
            "average_duration_months": round(avg_duration) if avg_duration > 0 else "N/A",
            "cases_analyzed": len(similar_cases)
        }
    
    async def _generate_strategic_recommendations(
        self,
        current_matter: Matter,
        current_entities: List,
        patterns: List[Dict],
        similar_cases: List[Dict],
        db: Session
    ) -> List[Dict]:
        """Generate strategic recommendations based on learned patterns"""
        
        recommendations = []
        
        # Recommendation 1: Focus on high-success factors
        success_factors = [p for p in patterns if p['pattern_type'] == 'success_factor']
        if success_factors:
            top_factor = max(success_factors, key=lambda x: x['success_rate'])
            recommendations.append({
                "title": f"Prioritize {top_factor['title']}",
                "description": f"This factor has a {top_factor['success_rate']:.0%} success rate in similar cases",
                "priority": "high",
                "action": f"Strengthen evidence and arguments related to {top_factor['title'].lower()}",
                "based_on_cases": len([c for c in similar_cases if top_factor['title'].lower() in str(c['outcome'].key_factors).lower()])
            })
        
        # Recommendation 2: Mitigate risk factors
        risk_factors = [p for p in patterns if p['pattern_type'] == 'risk_factor']
        if risk_factors:
            top_risk = max(risk_factors, key=lambda x: 1 - x['success_rate'])
            recommendations.append({
                "title": f"Mitigate Risk: {top_risk['title']}",
                "description": f"This factor led to unfavorable outcomes in {len([c for c in similar_cases if top_risk['title'].lower() in str(c['outcome'].failed_arguments).lower()])} cases",
                "priority": "high",
                "action": f"Develop strategy to address or avoid {top_risk['title'].lower()}",
                "based_on_cases": len(similar_cases)
            })
        
        # Recommendation 3: Settlement strategy
        settlements = [c for c in similar_cases if c['outcome'].outcome_type == 'settlement']
        if len(settlements) >= 2:
            settlement_rate = len(settlements) / len(similar_cases)
            recommendations.append({
                "title": "Consider Settlement Option",
                "description": f"{settlement_rate:.0%} of similar cases settled",
                "priority": "medium",
                "action": "Evaluate settlement opportunities based on similar case outcomes",
                "based_on_cases": len(settlements)
            })
        
        # Recommendation 4: Timeline strategy
        durations = [c['outcome'].duration_months for c in similar_cases if c['outcome'].duration_months]
        if durations:
            avg_duration = sum(durations) / len(durations)
            if avg_duration > 18:
                recommendations.append({
                    "title": "Anticipate Extended Timeline",
                    "description": f"Similar cases take an average of {avg_duration:.0f} months to resolve",
                    "priority": "medium",
                    "action": "Plan for long-term litigation strategy and resource allocation",
                    "based_on_cases": len(durations)
                })
        
        return recommendations
    
    def _format_case_summary(self, case_data: Dict) -> Dict:
        """Format case for API response"""
        
        matter = case_data['matter']
        outcome = case_data['outcome']
        
        return {
            "matter_id": matter.id,
            "case_title": matter.title,
            "matter_type": matter.matter_type,
            "jurisdiction": matter.jurisdiction,
            "similarity_score": round(case_data['similarity_score'], 2),
            "outcome_type": outcome.outcome_type,
            "settlement_amount": f"RM {float(outcome.settlement_amount):,.2f}" if outcome.settlement_amount else None,
            "duration_months": outcome.duration_months,
            "key_factors": outcome.key_factors or [],
            "lessons_learned": outcome.lessons_learned
        }
    
    async def record_case_outcome(
        self,
        matter_id: str,
        outcome_data: Dict,
        db: Session
    ) -> CaseOutcome:
        """Record outcome for a closed case"""
        
        try:
            outcome = CaseOutcome(
                id=str(uuid4()),
                matter_id=matter_id,
                outcome_type=outcome_data['outcome_type'],
                outcome_date=outcome_data.get('outcome_date'),
                claim_amount=Decimal(str(outcome_data.get('claim_amount', 0))),
                settlement_amount=Decimal(str(outcome_data.get('settlement_amount', 0))) if outcome_data.get('settlement_amount') else None,
                costs_awarded=Decimal(str(outcome_data.get('costs_awarded', 0))) if outcome_data.get('costs_awarded') else None,
                filing_date=outcome_data.get('filing_date'),
                duration_months=outcome_data.get('duration_months'),
                key_factors=outcome_data.get('key_factors', []),
                decisive_evidence=outcome_data.get('decisive_evidence', []),
                winning_arguments=outcome_data.get('winning_arguments', []),
                failed_arguments=outcome_data.get('failed_arguments', []),
                motions_filed=outcome_data.get('motions_filed', []),
                appeals_filed=outcome_data.get('appeals_filed', False),
                appeal_outcome=outcome_data.get('appeal_outcome'),
                lessons_learned=outcome_data.get('lessons_learned'),
                recommendations=outcome_data.get('recommendations'),
                created_at=datetime.now(timezone.utc),
                created_by=outcome_data.get('created_by')
            )
            
            db.add(outcome)
            db.commit()
            
            logger.info(f"Recorded outcome for matter {matter_id}: {outcome_data['outcome_type']}")
            
            return outcome
            
        except Exception as e:
            logger.error(f"Error recording case outcome: {str(e)}", exc_info=True)
            db.rollback()
            raise


# Singleton
_cross_case_learning_service = None


def get_cross_case_learning_service() -> CrossCaseLearningService:
    """Get or create cross-case learning service singleton"""
    global _cross_case_learning_service
    if _cross_case_learning_service is None:
        _cross_case_learning_service = CrossCaseLearningService()
    return _cross_case_learning_service

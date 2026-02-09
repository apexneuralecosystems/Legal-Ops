"""Case Insight Service - Automated Case Analysis"""

import json
import logging
from typing import Dict, List, Optional, Any
from uuid import uuid4
from datetime import datetime, timezone, timedelta

from sqlalchemy.orm import Session
from models.case_insights import CaseInsight, CaseMetric
from models.case_intelligence import CaseEntity, CaseRelationship
from models.ocr_models import OCRDocument
from models.chat import ChatMessage
from services.llm_service import get_llm_service

logger = logging.getLogger(__name__)


class CaseInsightService:
    """Generates automated insights about cases - risks, gaps, recommendations"""
    
    def __init__(self):
        self.llm = get_llm_service()
    
    async def generate_all_insights(
        self, 
        matter_id: str, 
        db: Session,
        force_refresh: bool = False
    ) -> Dict[str, Any]:
        """
        Generate all types of insights for a matter.
        
        Returns:
            {
                "insights_generated": int,
                "swot": [...],
                "risks": [...],
                "evidence_gaps": [...],
                "timeline_analysis": {...},
                "recommendations": [...]
            }
        """
        try:
            # Check if already generated recently
            if not force_refresh:
                recent_insights = db.query(CaseInsight).filter(
                    CaseInsight.matter_id == matter_id,
                    CaseInsight.generated_at >= datetime.now(timezone.utc) - timedelta(hours=24)
                ).count()
                
                if recent_insights > 0:
                    logger.info(f"Matter {matter_id} has {recent_insights} insights from last 24h. Use force_refresh=True to regenerate.")
                    # Return existing insights
                    return await self._get_existing_insights(matter_id, db)
            
            # Delete old insights if force refresh
            if force_refresh:
                db.query(CaseInsight).filter(
                    CaseInsight.matter_id == matter_id
                ).delete()
                db.commit()
            
            logger.info(f"Generating insights for matter {matter_id}")
            
            # Load case context (entities, documents, conversations)
            case_context = await self._load_case_context(matter_id, db)
            
            # Generate different types of insights
            all_insights = []
            
            # 1. SWOT Analysis
            swot_insights = await self._generate_swot_analysis(matter_id, case_context, db)
            all_insights.extend(swot_insights)
            
            # 2. Risk Assessment
            risk_insights = await self._generate_risk_assessment(matter_id, case_context, db)
            all_insights.extend(risk_insights)
            
            # 3. Evidence Gap Detection
            evidence_insights = await self._generate_evidence_gaps(matter_id, case_context, db)
            all_insights.extend(evidence_insights)
            
            # 4. Timeline Analysis
            timeline_insights = await self._generate_timeline_analysis(matter_id, case_context, db)
            all_insights.extend(timeline_insights)
            
            # 5. Strategic Recommendations
            recommendation_insights = await self._generate_recommendations(matter_id, case_context, db)
            all_insights.extend(recommendation_insights)
            
            # Save to database
            for insight_data in all_insights:
                insight = CaseInsight(
                    id=str(uuid4()),
                    matter_id=matter_id,
                    insight_type=insight_data['type'],
                    title=insight_data['title'],
                    description=insight_data['description'],
                    severity=insight_data.get('severity'),
                    category=insight_data.get('category'),
                    insight_data=insight_data.get('data'),
                    confidence=insight_data.get('confidence', 0.8),
                    actionable=insight_data.get('actionable', False),
                    action_deadline=insight_data.get('action_deadline'),
                    generated_at=datetime.now(timezone.utc)
                )
                db.add(insight)
            
            db.commit()
            
            logger.info(f"Generated {len(all_insights)} insights for matter {matter_id}")
            
            # Group by type for response
            return self._format_insights_response(all_insights, matter_id)
            
        except Exception as e:
            logger.error(f"Error generating insights: {str(e)}", exc_info=True)
            db.rollback()
            raise
    
    async def _load_case_context(self, matter_id: str, db: Session) -> Dict:
        """Load all relevant case data for analysis"""
        
        # Get entities
        entities = db.query(CaseEntity).filter(
            CaseEntity.matter_id == matter_id
        ).all()
        
        # Get relationships
        relationships = db.query(CaseRelationship).filter(
            CaseRelationship.matter_id == matter_id
        ).all()
        
        # Get documents
        documents = db.query(OCRDocument).filter(
            OCRDocument.matter_id == matter_id
        ).all()
        
        # Get chat history (last 20 messages for context)
        recent_chats = db.query(ChatMessage).filter(
            ChatMessage.matter_id == matter_id
        ).order_by(ChatMessage.created_at.desc()).limit(20).all()
        
        return {
            "entities": entities,
            "relationships": relationships,
            "documents": documents,
            "recent_chats": recent_chats,
            "entity_count": len(entities),
            "document_count": len(documents)
        }
    
    async def _generate_swot_analysis(self, matter_id: str, context: Dict, db: Session) -> List[Dict]:
        """Generate SWOT (Strengths, Weaknesses, Opportunities, Threats) analysis"""
        
        # Build entity summary
        entity_summary = self._build_entity_summary(context['entities'])
        doc_summary = f"{context['document_count']} documents uploaded"
        
        prompt = f"""Analyze this legal case and identify Strengths, Weaknesses, Opportunities, and Threats (SWOT).

CASE INFORMATION:
{entity_summary}
{doc_summary}

Generate a SWOT analysis:

**STRENGTHS** (What's working in our favor):
- List 2-4 strengths with brief explanations

**WEAKNESSES** (Vulnerabilities in our case):
- List 2-4 weaknesses with brief explanations

**OPPORTUNITIES** (Favorable circumstances to leverage):
- List 1-3 opportunities

**THREATS** (External risks or opposing party advantages):
- List 1-3 threats

Return as JSON:
```json
{{
  "strengths": [
    {{"title": "Strong Documentary Evidence", "description": "5 invoices and delivery receipts", "confidence": 0.9}}
  ],
  "weaknesses": [...],
  "opportunities": [...],
  "threats": [...]
}}
```"""
        
        try:
            response = await self.llm.generate(prompt, temperature=0.2, max_tokens=2000)
            
            # Parse JSON
            json_start = response.find("{")
            json_end = response.rfind("}") + 1
            if json_start != -1 and json_end > json_start:
                swot_data = json.loads(response[json_start:json_end])
                
                # Convert to insights format
                insights = []
                for category in ['strengths', 'weaknesses', 'opportunities', 'threats']:
                    for item in swot_data.get(category, []):
                        insights.append({
                            'type': 'swot_analysis',
                            'category': category[:-1],  # Remove 's' (strength, weakness, etc.)
                            'title': item['title'],
                            'description': item['description'],
                            'confidence': item.get('confidence', 0.8),
                            'actionable': False
                        })
                
                return insights
            else:
                logger.warning("No JSON found in SWOT analysis response")
                return []
                
        except Exception as e:
            logger.error(f"Error in SWOT analysis: {str(e)}")
            return []
    
    async def _generate_risk_assessment(self, matter_id: str, context: Dict, db: Session) -> List[Dict]:
        """Identify litigation risks and vulnerabilities"""
        
        entity_summary = self._build_entity_summary(context['entities'])
        
        prompt = f"""Identify litigation RISKS in this case. Focus on:
1. Procedural risks (deadlines, service issues, jurisdiction)
2. Evidentiary risks (missing evidence, weak proof)
3. Legal risks (weak arguments, adverse precedents)
4. Strategic risks (opposing party strengths)

CASE INFORMATION:
{entity_summary}

Return as JSON array:
```json
[
  {{
    "title": "Statute of Limitations Risk",
    "description": "Claim may be time-barred if filed after 6 years",
    "severity": "high",
    "confidence": 0.85,
    "actionable": true,
    "action": "Verify exact cause of action date"
  }}
]
```

Severity: critical, high, medium, low"""
        
        try:
            response = await self.llm.generate(prompt, temperature=0.1, max_tokens=2000)
            
            json_start = response.find("[")
            json_end = response.rfind("]") + 1
            if json_start != -1 and json_end > json_start:
                risks = json.loads(response[json_start:json_end])
                
                insights = []
                for risk in risks:
                    insights.append({
                        'type': 'risk_assessment',
                        'title': risk['title'],
                        'description': risk['description'],
                        'severity': risk.get('severity', 'medium'),
                        'confidence': risk.get('confidence', 0.8),
                        'actionable': risk.get('actionable', True),
                        'data': {'action': risk.get('action')}
                    })
                
                return insights
            else:
                return []
                
        except Exception as e:
            logger.error(f"Error in risk assessment: {str(e)}")
            return []
    
    async def _generate_evidence_gaps(self, matter_id: str, context: Dict, db: Session) -> List[Dict]:
        """Detect missing evidence or documentation"""
        
        entity_summary = self._build_entity_summary(context['entities'])
        doc_list = ", ".join([doc.filename for doc in context['documents'][:10]])
        
        prompt = f"""Identify MISSING EVIDENCE or documentation gaps in this case.

CASE INFORMATION:
{entity_summary}

DOCUMENTS AVAILABLE:
{doc_list}

What evidence is typically required but appears to be missing? Consider:
- Contracts/agreements
- Invoices/receipts
- Correspondence/emails
- Witness statements
- Expert reports
- Bank statements
- Delivery receipts

Return as JSON array:
```json
[
  {{
    "title": "Missing Written Contract",
    "description": "No formal contract document uploaded, relying on email trail",
    "severity": "high",
    "actionable": true,
    "action": "Request original contract or confirm email constitutes binding agreement"
  }}
]
```"""
        
        try:
            response = await self.llm.generate(prompt, temperature=0.1, max_tokens=1500)
            
            json_start = response.find("[")
            json_end = response.rfind("]") + 1
            if json_start != -1 and json_end > json_start:
                gaps = json.loads(response[json_start:json_end])
                
                insights = []
                for gap in gaps:
                    insights.append({
                        'type': 'evidence_gap',
                        'title': gap['title'],
                        'description': gap['description'],
                        'severity': gap.get('severity', 'medium'),
                        'confidence': 0.75,
                        'actionable': True,
                        'data': {'action': gap.get('action')}
                    })
                
                return insights
            else:
                return []
                
        except Exception as e:
            logger.error(f"Error in evidence gap detection: {str(e)}")
            return []
    
    async def _generate_timeline_analysis(self, matter_id: str, context: Dict, db: Session) -> List[Dict]:
        """Analyze case timeline for critical dates and gaps"""
        
        # Get date entities
        date_entities = [e for e in context['entities'] if e.entity_type == 'date']
        
        if not date_entities:
            return [{
                'type': 'timeline_analysis',
                'title': 'No Timeline Data',
                'description': 'No key dates have been extracted yet. Run entity extraction first.',
                'severity': 'low',
                'confidence': 1.0,
                'actionable': False
            }]
        
        date_summary = "\n".join([
            f"- {e.entity_name}: {e.entity_value.get('date') if e.entity_value else 'Unknown'}"
            for e in date_entities
        ])
        
        prompt = f"""Analyze this case timeline for:
1. Critical upcoming deadlines
2. Statute of limitations concerns
3. Timeline gaps or inconsistencies

KEY DATES:
{date_summary}

Return as JSON array:
```json
[
  {{
    "title": "Appeal Deadline Approaching",
    "description": "14 days to file appeal from judgment date",
    "severity": "critical",
    "actionable": true,
    "action_deadline": "2026-02-15",
    "action": "Prepare and file appeal notice"
  }}
]
```"""
        
        try:
            response = await self.llm.generate(prompt, temperature=0.1, max_tokens=1500)
            
            json_start = response.find("[")
            json_end = response.rfind("]") + 1
            if json_start != -1 and json_end > json_start:
                timeline_issues = json.loads(response[json_start:json_end])
                
                insights = []
                for issue in timeline_issues:
                    deadline = None
                    if issue.get('action_deadline'):
                        try:
                            deadline = datetime.fromisoformat(issue['action_deadline'])
                        except:
                            pass
                    
                    insights.append({
                        'type': 'timeline_analysis',
                        'title': issue['title'],
                        'description': issue['description'],
                        'severity': issue.get('severity', 'medium'),
                        'confidence': 0.8,
                        'actionable': True,
                        'action_deadline': deadline,
                        'data': {'action': issue.get('action')}
                    })
                
                return insights
            else:
                return []
                
        except Exception as e:
            logger.error(f"Error in timeline analysis: {str(e)}")
            return []
    
    async def _generate_recommendations(self, matter_id: str, context: Dict, db: Session) -> List[Dict]:
        """Generate strategic recommendations"""
        
        entity_summary = self._build_entity_summary(context['entities'])
        
        prompt = f"""Based on this case, suggest 3-5 STRATEGIC ACTIONS the legal team should take:

CASE INFORMATION:
{entity_summary}

Focus on:
- Next tactical steps
- Document requests
- Motion opportunities
- Settlement considerations

Return as JSON array:
```json
[
  {{
    "title": "File Summary Judgment Motion",
    "description": "Strong documentary evidence supports early summary judgment application",
    "confidence": 0.85,
    "actionable": true,
    "priority": "high"
  }}
]
```"""
        
        try:
            response = await self.llm.generate(prompt, temperature=0.3, max_tokens=1500)
            
            json_start = response.find("[")
            json_end = response.rfind("]") + 1
            if json_start != -1 and json_end > json_start:
                recommendations = json.loads(response[json_start:json_end])
                
                insights = []
                for rec in recommendations:
                    insights.append({
                        'type': 'strategic_recommendation',
                        'title': rec['title'],
                        'description': rec['description'],
                        'confidence': rec.get('confidence', 0.8),
                        'actionable': True,
                        'data': {'priority': rec.get('priority', 'medium')}
                    })
                
                return insights
            else:
                return []
                
        except Exception as e:
            logger.error(f"Error generating recommendations: {str(e)}")
            return []
    
    def _build_entity_summary(self, entities: List) -> str:
        """Build human-readable summary of entities"""
        
        by_type = {}
        for entity in entities:
            if entity.entity_type not in by_type:
                by_type[entity.entity_type] = []
            by_type[entity.entity_type].append(entity)
        
        summary = ""
        for entity_type, entity_list in by_type.items():
            summary += f"\n{entity_type.upper()}S:\n"
            for entity in entity_list[:5]:  # Limit to 5 per type
                summary += f"  - {entity.entity_name}"
                if entity.entity_value and isinstance(entity.entity_value, dict):
                    key_info = []
                    for k, v in entity.entity_value.items():
                        if k in ['role', 'amount', 'date', 'claim_type']:
                            key_info.append(f"{k}: {v}")
                    if key_info:
                        summary += f" ({', '.join(key_info)})"
                summary += "\n"
        
        return summary
    
    async def _get_existing_insights(self, matter_id: str, db: Session) -> Dict:
        """Get existing insights from database"""
        
        insights = db.query(CaseInsight).filter(
            CaseInsight.matter_id == matter_id
        ).all()
        
        insights_data = [self._insight_to_dict(i) for i in insights]
        
        return self._format_insights_response(insights_data, matter_id)
    
    def _format_insights_response(self, insights: List[Dict], matter_id: str) -> Dict:
        """Format insights by type for API response"""
        
        by_type = {
            'swot_analysis': [],
            'risk_assessment': [],
            'evidence_gap': [],
            'timeline_analysis': [],
            'strategic_recommendation': []
        }
        
        for insight in insights:
            insight_type = insight.get('type')
            if insight_type in by_type:
                by_type[insight_type].append(insight)
        
        return {
            "matter_id": matter_id,
            "insights_generated": len(insights),
            "swot": by_type['swot_analysis'],
            "risks": by_type['risk_assessment'],
            "evidence_gaps": by_type['evidence_gap'],
            "timeline_analysis": by_type['timeline_analysis'],
            "recommendations": by_type['strategic_recommendation']
        }
    
    def get_insights(self, matter_id: str, db: Session, insight_type: Optional[str] = None) -> List[Dict]:
        """Get insights from database"""
        
        query = db.query(CaseInsight).filter(CaseInsight.matter_id == matter_id)
        
        if insight_type:
            query = query.filter(CaseInsight.insight_type == insight_type)
        
        insights = query.order_by(CaseInsight.generated_at.desc()).all()
        
        return [self._insight_to_dict(i) for i in insights]
    
    def _insight_to_dict(self, insight: CaseInsight) -> Dict:
        """Convert insight model to dictionary"""
        return {
            "id": insight.id,
            "type": insight.insight_type,
            "title": insight.title,
            "description": insight.description,
            "severity": insight.severity,
            "category": insight.category,
            "confidence": insight.confidence,
            "actionable": insight.actionable,
            "action_deadline": insight.action_deadline.isoformat() if insight.action_deadline else None,
            "resolved": insight.resolved,
            "data": insight.insight_data,
            "generated_at": insight.generated_at.isoformat() if insight.generated_at else None
        }


# Singleton
_case_insight_service = None


def get_case_insight_service() -> CaseInsightService:
    """Get or create case insight service singleton"""
    global _case_insight_service
    if _case_insight_service is None:
        _case_insight_service = CaseInsightService()
    return _case_insight_service

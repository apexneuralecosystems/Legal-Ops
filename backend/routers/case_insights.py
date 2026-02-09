"""Case Insights Router - Automated Analysis Endpoints"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import Optional
import logging

from database import get_db
from dependencies import get_current_user
from services.case_insight_service import get_case_insight_service

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/generate/{matter_id}")
async def generate_case_insights(
    matter_id: str,
    force_refresh: bool = False,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    Generate automated case insights including:
    - SWOT Analysis (Strengths, Weaknesses, Opportunities, Threats)
    - Risk Assessment (litigation risks, vulnerabilities)
    - Evidence Gaps (missing documentation)
    - Timeline Analysis (deadlines, statute limitations)
    - Strategic Recommendations (next actions)
    
    Args:
        matter_id: The matter ID to analyze
        force_refresh: If True, regenerate even if recent insights exist
    """
    try:
        insight_service = get_case_insight_service()
        
        result = await insight_service.generate_all_insights(
            matter_id=matter_id,
            db=db,
            force_refresh=force_refresh
        )
        
        return {
            "success": True,
            **result
        }
        
    except Exception as e:
        logger.error(f"Error generating insights: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Insight generation failed: {str(e)}")


@router.get("/{matter_id}")
async def get_case_insights(
    matter_id: str,
    insight_type: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    Get all insights for a matter.
    
    Args:
        matter_id: The matter ID
        insight_type: Optional filter by type (swot_analysis, risk_assessment, 
                     evidence_gap, timeline_analysis, strategic_recommendation)
    """
    try:
        insight_service = get_case_insight_service()
        
        insights = insight_service.get_insights(
            matter_id=matter_id,
            db=db,
            insight_type=insight_type
        )
        
        # Group by type
        by_type = {
            'swot_analysis': [],
            'risk_assessment': [],
            'evidence_gap': [],
            'timeline_analysis': [],
            'strategic_recommendation': []
        }
        
        for insight in insights:
            if insight['type'] in by_type:
                by_type[insight['type']].append(insight)
        
        return {
            "success": True,
            "matter_id": matter_id,
            "total": len(insights),
            "swot": by_type['swot_analysis'],
            "risks": by_type['risk_assessment'],
            "evidence_gaps": by_type['evidence_gap'],
            "timeline_analysis": by_type['timeline_analysis'],
            "recommendations": by_type['strategic_recommendation']
        }
        
    except Exception as e:
        logger.error(f"Error getting insights: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{insight_id}/resolve")
async def resolve_insight(
    insight_id: str,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    Mark an insight as resolved (e.g., evidence uploaded, risk mitigated).
    """
    try:
        from models.case_insights import CaseInsight
        from datetime import datetime, timezone
        
        insight = db.query(CaseInsight).filter(CaseInsight.id == insight_id).first()
        
        if not insight:
            raise HTTPException(status_code=404, detail="Insight not found")
        
        insight.resolved = True
        insight.resolved_at = datetime.now(timezone.utc)
        insight.resolved_by = current_user.get('sub', 'unknown')
        
        db.commit()
        
        return {
            "success": True,
            "message": "Insight marked as resolved",
            "insight_id": insight_id
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error resolving insight: {str(e)}")
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

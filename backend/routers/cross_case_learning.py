"""Cross-Case Learning API Endpoints"""

from typing import Dict
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel

from database import get_db
from services.cross_case_learning_service import get_cross_case_learning_service
from models.cross_case_learning import CaseOutcome

router = APIRouter()


class OutcomeData(BaseModel):
    """Case outcome data"""
    outcome_type: str  # judgment_plaintiff, judgment_defendant, settlement, dismissed
    outcome_date: str = None
    claim_amount: float = 0.0
    settlement_amount: float = None
    costs_awarded: float = None
    filing_date: str = None
    duration_months: int = None
    key_factors: list = []
    decisive_evidence: list = []
    winning_arguments: list = []
    failed_arguments: list = []
    motions_filed: list = []
    appeals_filed: bool = False
    appeal_outcome: str = None
    lessons_learned: str = None
    recommendations: str = None
    created_by: str = None


@router.post("/api/learning/analyze/{matter_id}")
async def analyze_similar_cases(
    matter_id: str,
    limit: int = 5,
    db: Session = Depends(get_db)
) -> Dict:
    """
    Analyze similar historical cases and generate predictions/recommendations.
    
    Returns similar cases, success patterns, outcome predictions, and strategic recommendations.
    """
    try:
        service = get_cross_case_learning_service()
        result = await service.analyze_similar_cases(matter_id, db, limit)
        return result
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error analyzing similar cases: {str(e)}")


@router.post("/api/learning/outcome/{matter_id}")
async def record_case_outcome(
    matter_id: str,
    outcome_data: OutcomeData,
    db: Session = Depends(get_db)
) -> Dict:
    """
    Record outcome for a closed case to enable cross-case learning.
    
    This data will be used to find patterns and make predictions for future cases.
    """
    try:
        service = get_cross_case_learning_service()
        outcome = await service.record_case_outcome(
            matter_id, 
            outcome_data.dict(),
            db
        )
        return {
            "success": True,
            "outcome_id": outcome.id,
            "message": "Case outcome recorded successfully. Will be used for future predictions."
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error recording outcome: {str(e)}")


@router.get("/api/learning/outcomes")
async def get_all_outcomes(
    db: Session = Depends(get_db),
    limit: int = 50
) -> Dict:
    """Get all recorded case outcomes"""
    try:
        outcomes = db.query(CaseOutcome).order_by(
            CaseOutcome.outcome_date.desc()
        ).limit(limit).all()
        
        return {
            "count": len(outcomes),
            "outcomes": [
                {
                    "id": o.id,
                    "matter_id": o.matter_id,
                    "outcome_type": o.outcome_type,
                    "outcome_date": o.outcome_date.isoformat() if o.outcome_date else None,
                    "settlement_amount": float(o.settlement_amount) if o.settlement_amount else None,
                    "duration_months": o.duration_months,
                    "key_factors": o.key_factors,
                    "lessons_learned": o.lessons_learned
                }
                for o in outcomes
            ]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching outcomes: {str(e)}")

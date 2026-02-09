"""Case Intelligence Router - Knowledge Graph Endpoints"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import Optional
import logging

from database import get_db
from dependencies import get_current_user
from services.case_intelligence_service import get_case_intelligence_service

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/extract/{matter_id}")
async def extract_case_entities(
    matter_id: str,
    force_refresh: bool = False,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    Extract all case entities and relationships from matter documents.
    
    This analyzes all documents and builds a knowledge graph with:
    - Parties (plaintiff, defendant, third parties)
    - Claims (amounts, types, legal basis)
    - Defenses raised
    - Key dates and deadlines
    - Legal issues
    - Document references
    - Relationships between all entities
    
    Args:
        matter_id: The matter ID to extract from
        force_refresh: If True, re-extract even if already done
    """
    try:
        case_intel = get_case_intelligence_service()
        
        result = await case_intel.extract_case_entities(
            matter_id=matter_id,
            db=db,
            force_refresh=force_refresh
        )
        
        return {
            "success": True,
            "matter_id": matter_id,
            **result
        }
        
    except Exception as e:
        logger.error(f"Error extracting case entities: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Extraction failed: {str(e)}")


@router.get("/entities/{matter_id}")
async def get_case_entities(
    matter_id: str,
    entity_type: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    Get all extracted entities for a matter.
    
    Args:
        matter_id: The matter ID
        entity_type: Optional filter by entity type (party, claim, defense, date, issue, document)
    """
    try:
        case_intel = get_case_intelligence_service()
        
        entities = case_intel.get_entities(
            matter_id=matter_id,
            db=db,
            entity_type=entity_type
        )
        
        return {
            "success": True,
            "matter_id": matter_id,
            "entity_type": entity_type,
            "total": len(entities),
            "entities": entities
        }
        
    except Exception as e:
        logger.error(f"Error getting case entities: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/relationships/{matter_id}")
async def get_case_relationships(
    matter_id: str,
    relationship_type: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    Get all relationships between entities for a matter.
    
    Args:
        matter_id: The matter ID
        relationship_type: Optional filter by type (claims_against, defended_by, relies_on, etc.)
    """
    try:
        case_intel = get_case_intelligence_service()
        
        relationships = case_intel.get_relationships(
            matter_id=matter_id,
            db=db,
            relationship_type=relationship_type
        )
        
        return {
            "success": True,
            "matter_id": matter_id,
            "relationship_type": relationship_type,
            "total": len(relationships),
            "relationships": relationships
        }
        
    except Exception as e:
        logger.error(f"Error getting relationships: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/graph/{matter_id}")
async def get_knowledge_graph(
    matter_id: str,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    Get complete knowledge graph for a matter - all entities and relationships organized by type.
    
    Returns:
        {
            "matter_id": str,
            "total_entities": int,
            "total_relationships": int,
            "entities_by_type": {
                "party": [...],
                "claim": [...],
                "defense": [...],
                ...
            },
            "relationships": [...]
        }
    """
    try:
        case_intel = get_case_intelligence_service()
        
        graph = case_intel.get_knowledge_graph(matter_id, db)
        
        return {
            "success": True,
            **graph
        }
        
    except Exception as e:
        logger.error(f"Error getting knowledge graph: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

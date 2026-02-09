"""Case Intelligence Service - Extract and manage case knowledge graph"""

import json
import logging
from typing import Dict, List, Optional, Any
from uuid import uuid4
from datetime import datetime, timezone

from sqlalchemy.orm import Session
from models.case_intelligence import CaseEntity, CaseRelationship
from models.matter import Matter
from models.ocr_models import OCRChunk
from services.llm_service import get_llm_service

logger = logging.getLogger(__name__)


class CaseIntelligenceService:
    """Extracts and manages case knowledge graph - entities and relationships"""
    
    def __init__(self):
        self.llm = get_llm_service()
    
    async def extract_case_entities(
        self, 
        matter_id: str, 
        db: Session,
        force_refresh: bool = False
    ) -> Dict[str, Any]:
        """
        Extract all case entities from matter documents.
        
        Returns:
            {
                "entities_extracted": int,
                "relationships_extracted": int,
                "entities": List[Dict],
                "relationships": List[Dict]
            }
        """
        try:
            # Check if already extracted
            existing_count = db.query(CaseEntity).filter(
                CaseEntity.matter_id == matter_id
            ).count()
            
            if existing_count > 0 and not force_refresh:
                logger.info(f"Matter {matter_id} already has {existing_count} entities. Use force_refresh=True to re-extract.")
                return {
                    "entities_extracted": 0,
                    "relationships_extracted": 0,
                    "message": f"Already extracted {existing_count} entities. Use force_refresh to re-extract."
                }
            
            # Delete existing if force refresh
            if force_refresh:
                db.query(CaseRelationship).filter(
                    CaseRelationship.matter_id == matter_id
                ).delete()
                db.query(CaseEntity).filter(
                    CaseEntity.matter_id == matter_id
                ).delete()
                db.commit()
            
            # Load all OCR chunks for this matter
            chunks = db.query(OCRChunk).join(OCRChunk.document).filter(
                OCRChunk.document.has(matter_id=matter_id)
            ).all()
            
            if not chunks:
                return {
                    "entities_extracted": 0,
                    "relationships_extracted": 0,
                    "error": "No OCR chunks found for this matter"
                }
            
            # Combine all text (limit to reasonable size)
            full_text = "\n\n".join([
                f"=== {chunk.document.filename} (Page {chunk.source_page_start}) ===\n{chunk.chunk_text}"
                for chunk in chunks[:50]  # Limit to first 50 chunks (~100 pages)
            ])
            
            # Truncate if too large
            if len(full_text) > 700000:  # ~280 pages
                full_text = full_text[:700000]
                logger.warning(f"Truncated full text to 700k chars for matter {matter_id}")
            
            logger.info(f"Extracting entities from {len(chunks)} chunks for matter {matter_id}")
            
            # Extract entities using LLM
            extraction_result = await self._llm_extract_entities(full_text, matter_id)
            
            # Save entities to database
            saved_entities = []
            entity_id_map = {}  # Map LLM-generated IDs to DB IDs
            
            for entity_data in extraction_result.get("entities", []):
                entity_id = str(uuid4())
                entity = CaseEntity(
                    id=entity_id,
                    matter_id=matter_id,
                    entity_type=entity_data["type"],
                    entity_name=entity_data["name"],
                    entity_value=entity_data.get("details", {}),
                    confidence=entity_data.get("confidence", 0.8),
                    source_document=entity_data.get("source", None),
                    extracted_at=datetime.now(timezone.utc)
                )
                db.add(entity)
                saved_entities.append(entity)
                
                # Map temp ID to real ID
                if "id" in entity_data:
                    entity_id_map[entity_data["id"]] = entity_id
            
            db.commit()
            logger.info(f"Saved {len(saved_entities)} entities")
            
            # Save relationships
            saved_relationships = []
            for rel_data in extraction_result.get("relationships", []):
                # Map LLM IDs to real DB IDs
                entity_1_id = entity_id_map.get(rel_data.get("entity_1_id"))
                entity_2_id = entity_id_map.get(rel_data.get("entity_2_id"))
                
                if not entity_1_id or not entity_2_id:
                    logger.warning(f"Skipping relationship - couldn't map entity IDs")
                    continue
                
                relationship = CaseRelationship(
                    id=str(uuid4()),
                    matter_id=matter_id,
                    entity_1_id=entity_1_id,
                    entity_2_id=entity_2_id,
                    relationship_type=rel_data["type"],
                    relationship_description=rel_data.get("description"),
                    confidence=rel_data.get("confidence", 0.8),
                    extracted_at=datetime.now(timezone.utc)
                )
                db.add(relationship)
                saved_relationships.append(relationship)
            
            db.commit()
            logger.info(f"Saved {len(saved_relationships)} relationships")
            
            return {
                "entities_extracted": len(saved_entities),
                "relationships_extracted": len(saved_relationships),
                "entities": [self._entity_to_dict(e) for e in saved_entities],
                "relationships": [self._relationship_to_dict(r) for r in saved_relationships]
            }
            
        except Exception as e:
            logger.error(f"Error extracting case entities: {str(e)}", exc_info=True)
            db.rollback()
            raise
    
    async def _llm_extract_entities(self, full_text: str, matter_id: str) -> Dict:
        """Use LLM to extract entities and relationships from text"""
        
        prompt = f"""You are a legal case analyzer. Extract ALL structured information from the following case documents.

EXTRACT THE FOLLOWING:

1. **PARTIES** - All parties involved:
   - Type: "party"
   - Name: Full legal name
   - Details: {{"role": "plaintiff/defendant/third_party", "legal_status": "individual/company", "ic_no": "...", "company_no": "..."}}

2. **CLAIMS** - All claims made:
   - Type: "claim"
   - Name: Brief description
   - Details: {{"amount": "RM X", "claim_type": "breach of contract/tort/etc", "legal_basis": "...", "claimant": "party name", "against": "party name"}}

3. **DEFENSES** - All defenses raised:
   - Type: "defense"
   - Name: Defense name
   - Details: {{"defense_type": "...", "legal_basis": "...", "raised_by": "party name"}}

4. **KEY_DATES** - Important dates:
   - Type: "date"
   - Name: Event description
   - Details: {{"date": "YYYY-MM-DD", "event_type": "filing/incident/deadline", "significance": "..."}}

5. **LEGAL_ISSUES** - Primary legal issues:
   - Type: "issue"
   - Name: Issue description
   - Details: {{"issue_type": "contract/tort/etc", "applicable_law": "Act/Section", "complexity": "high/medium/low"}}

6. **KEY_DOCUMENTS** - Important documents referenced:
   - Type: "document"
   - Name: Document name
   - Details: {{"document_type": "invoice/contract/evidence", "significance": "..."}}

**RELATIONSHIPS** - Extract relationships:
- "claims_against": Plaintiff claims against Defendant
- "defended_by": Defendant defended by Defense
- "relies_on": Claim/Defense relies on Document
- "related_to": Entities related to each other

**OUTPUT FORMAT (JSON):**
```json
{{
  "entities": [
    {{
      "id": "temp_id_1",
      "type": "party",
      "name": "Sena Traffic Systems Sdn. Bhd.",
      "details": {{"role": "plaintiff", "legal_status": "company", "company_no": "..."}},
      "confidence": 0.95,
      "source": "Document X"
    }},
    ...
  ],
  "relationships": [
    {{
      "entity_1_id": "temp_id_1",
      "entity_2_id": "temp_id_2",
      "type": "claims_against",
      "description": "Sena claims RM6.3M against AR-Rifqi",
      "confidence": 0.9
    }},
    ...
  ]
}}
```

**CASE DOCUMENTS:**
{full_text}

Extract as much structured information as possible. Be thorough and accurate."""

        try:
            response = await self.llm.generate(
                prompt=prompt,
                temperature=0.1,  # Low temperature for factual extraction
                max_tokens=4000
            )
            
            # Parse JSON response
            # Try to find JSON in response
            json_start = response.find("{")
            json_end = response.rfind("}") + 1
            
            if json_start != -1 and json_end > json_start:
                json_str = response[json_start:json_end]
                result = json.loads(json_str)
                return result
            else:
                logger.error("No JSON found in LLM response")
                return {"entities": [], "relationships": []}
                
        except Exception as e:
            logger.error(f"Error in LLM entity extraction: {str(e)}")
            return {"entities": [], "relationships": []}
    
    def get_entities(
        self, 
        matter_id: str, 
        db: Session,
        entity_type: Optional[str] = None
    ) -> List[Dict]:
        """Get all entities for a matter, optionally filtered by type"""
        
        query = db.query(CaseEntity).filter(CaseEntity.matter_id == matter_id)
        
        if entity_type:
            query = query.filter(CaseEntity.entity_type == entity_type)
        
        entities = query.order_by(CaseEntity.confidence.desc()).all()
        
        return [self._entity_to_dict(e) for e in entities]
    
    def get_relationships(
        self, 
        matter_id: str, 
        db: Session,
        relationship_type: Optional[str] = None
    ) -> List[Dict]:
        """Get all relationships for a matter"""
        
        query = db.query(CaseRelationship).filter(
            CaseRelationship.matter_id == matter_id
        )
        
        if relationship_type:
            query = query.filter(CaseRelationship.relationship_type == relationship_type)
        
        relationships = query.all()
        
        return [self._relationship_to_dict(r) for r in relationships]
    
    def get_knowledge_graph(self, matter_id: str, db: Session) -> Dict[str, Any]:
        """Get complete knowledge graph for a matter"""
        
        entities = self.get_entities(matter_id, db)
        relationships = self.get_relationships(matter_id, db)
        
        # Group entities by type
        entities_by_type = {}
        for entity in entities:
            entity_type = entity["entity_type"]
            if entity_type not in entities_by_type:
                entities_by_type[entity_type] = []
            entities_by_type[entity_type].append(entity)
        
        return {
            "matter_id": matter_id,
            "total_entities": len(entities),
            "total_relationships": len(relationships),
            "entities_by_type": entities_by_type,
            "all_entities": entities,
            "relationships": relationships
        }
    
    def _entity_to_dict(self, entity: CaseEntity) -> Dict:
        """Convert entity model to dictionary"""
        return {
            "id": entity.id,
            "entity_type": entity.entity_type,
            "entity_name": entity.entity_name,
            "entity_value": entity.entity_value,
            "confidence": entity.confidence,
            "source_document": entity.source_document,
            "verified": entity.verified_by_user is not None,
            "extracted_at": entity.extracted_at.isoformat() if entity.extracted_at else None
        }
    
    def _relationship_to_dict(self, rel: CaseRelationship) -> Dict:
        """Convert relationship model to dictionary"""
        return {
            "id": rel.id,
            "entity_1_id": rel.entity_1_id,
            "entity_1_name": rel.entity_1.entity_name if rel.entity_1 else None,
            "entity_2_id": rel.entity_2_id,
            "entity_2_name": rel.entity_2.entity_name if rel.entity_2 else None,
            "relationship_type": rel.relationship_type,
            "relationship_description": rel.relationship_description,
            "confidence": rel.confidence
        }


# Singleton
_case_intelligence_service = None


def get_case_intelligence_service() -> CaseIntelligenceService:
    """Get or create case intelligence service singleton"""
    global _case_intelligence_service
    if _case_intelligence_service is None:
        _case_intelligence_service = CaseIntelligenceService()
    return _case_intelligence_service

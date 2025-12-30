"""
Case Structuring Agent - Extracts legal entities and creates matter snapshot.
"""
from agents.base_agent import BaseAgent
from typing import Dict, Any, List, Optional
import json
import re
from services.llm_service import get_llm_service
import re


class CaseStructuringAgent(BaseAgent):
    """
    Extracts parties, court, dates, issues, and remedies from documents.
    
    Inputs:
    - parallel_texts: aligned Malay/English segments
    - document_manifest: list of documents
    
    Outputs:
    - matter_snapshot: structured JSON with all extracted entities
    """
    
    def __init__(self):
        super().__init__(agent_id="CaseStructuring")
        self.llm = get_llm_service()
    
    async def process(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process case structuring request.
        
        Args:
            inputs: {
                "parallel_texts": List[Dict],  # from translation agent
                "document_manifest": List[Dict],  # from document collector
                "matter_id": str
            }
            
        Returns:
            {
                "matter_snapshot": Dict  # structured case information
            }
        """
        await self.validate_input(inputs, ["parallel_texts", "matter_id"])
        
        parallel_texts = inputs["parallel_texts"]
        matter_id = inputs["matter_id"]
        doc_manifest = inputs.get("document_manifest", [])
        
        # Combine all text for analysis
        combined_text_en = []
        combined_text_ms = []
        
        for pair in parallel_texts:
            if pair.get("src_lang") == "en":
                combined_text_en.append(pair["src"])
                combined_text_ms.append(pair.get("tgt_literal", ""))
            else:
                combined_text_ms.append(pair["src"])
                combined_text_en.append(pair.get("tgt_literal", ""))
        
        full_text_en = "\n".join(combined_text_en)
        full_text_ms = "\n".join(combined_text_ms)
        
        # Use LLM to extract structured information
        extraction_prompt = self._create_extraction_prompt(full_text_en, full_text_ms)
        
        response_text = await self.llm.generate(extraction_prompt)
        extracted_data = self._parse_llm_response(response_text)
        
        # Build matter snapshot
        # Use actual page count if provided, otherwise estimate from text
        actual_page_count = inputs.get("actual_page_count", 0)
        estimated_pages = actual_page_count if actual_page_count > 0 else (len(full_text_en) // 3000 + 1)
        
        matter_snapshot = {
            "matter_id": matter_id,
            "title": extracted_data.get("title", "Untitled Matter"),
            "parties": extracted_data.get("parties", []),
            "court": extracted_data.get("court", "Unknown Court"),
            "jurisdiction": extracted_data.get("jurisdiction", "Peninsular Malaysia"),
            "case_type": extracted_data.get("case_type", "general"),
            "key_dates": extracted_data.get("key_dates", []),
            "issues": extracted_data.get("issues", []),
            "requested_remedies": extracted_data.get("requested_remedies", []),
            "volume_estimate": len(full_text_en.split()),
            "estimated_pages": estimated_pages  # Use actual page count when available
        }
        
        # Calculate confidence based on completeness
        confidence = self._calculate_confidence(matter_snapshot)
        
        return self.format_output(
            data={"matter_snapshot": matter_snapshot},
            confidence=confidence,
            human_review_required=confidence < 0.75
        )
    
    def _create_extraction_prompt(self, text_en: str, text_ms: str) -> str:
        """Create prompt for LLM extraction."""
        return f"""You are a Malaysian legal AI assistant. Extract structured information from the following legal documents.

English Text:
{text_en[:5000]}  # Limit to first 5000 chars

Malay Text:
{text_ms[:5000]}

Extract and return a JSON object with the following structure:
{{
    "title": "Case title (e.g., ABC Sdn Bhd v XYZ Sdn Bhd)",
    "parties": [
        {{
            "role": "plaintiff" or "defendant",
            "name": "Party name",
            "address": "Address if available"
        }}
    ],
    "court": "Court name (e.g., High Court in Malaya, Sessions Court)",
    "jurisdiction": "Peninsular Malaysia" or "East Malaysia",
    "case_type": "contract", "tort", "criminal", "family", or "other",
    "key_dates": [
        {{
            "type": "contract_date", "incident_date", "filing_date", etc.,
            "date": "YYYY-MM-DD",
            "description": "Brief description"
        }}
    ],
    "issues": [
        {{
            "id": "ISS-1",
            "text_en": "Issue in English",
            "text_ms": "Issue in Malay",
            "confidence": 0.0-1.0
        }}
    ],
    "requested_remedies": [
        {{
            "text": "Remedy description",
            "confidence": 0.0-1.0
        }}
    ]
}}

Return ONLY the JSON object, no additional text."""
    
    def _parse_llm_response(self, response_text: str) -> Dict[str, Any]:
        """Parse LLM response and extract JSON."""
        try:
            # Try to find JSON in response
            json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
            if json_match:
                return json.loads(json_match.group())
            else:
                return json.loads(response_text)
        except json.JSONDecodeError:
            print("Failed to parse LLM response as JSON")
            return {}
    

    
    def _calculate_confidence(self, snapshot: Dict[str, Any]) -> float:
        """Calculate confidence score based on completeness."""
        score = 0.0
        
        # Check completeness of key fields
        if snapshot.get("title") and snapshot["title"] != "Unknown Matter":
            score += 0.15
        
        if snapshot.get("parties") and len(snapshot["parties"]) >= 2:
            score += 0.25
        elif snapshot.get("parties"):
            score += 0.15
        
        if snapshot.get("court") and snapshot["court"] != "Unknown Court":
            score += 0.15
        
        if snapshot.get("case_type") and snapshot["case_type"] != "general":
            score += 0.10
        
        if snapshot.get("key_dates"):
            score += 0.15
        
        if snapshot.get("issues"):
            score += 0.10
        
        if snapshot.get("requested_remedies"):
            score += 0.10
        
        return min(score, 1.0)

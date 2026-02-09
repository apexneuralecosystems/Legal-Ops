"""
Case Structuring Agent - Extracts legal entities and creates matter snapshot.
"""
from agents.base_agent import BaseAgent
from typing import Dict, Any, List, Optional
import json
import re
from services.llm_service import get_llm_service
import re
import logging
from datetime import datetime

logger = logging.getLogger(__name__)


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
        
        logger.info(f"CaseStructuring: Processing {len(parallel_texts)} text segments for matter {matter_id}")
        
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
        
        logger.info(f"CaseStructuring: Combined text length - EN: {len(full_text_en)} chars, MS: {len(full_text_ms)} chars")
        
        if len(full_text_en) > 0:
            logger.info(f"CaseStructuring: Text preview (first 500 chars): {full_text_en[:500]}")
        
        # Use LLM to extract structured information
        # INCREASED LIMIT: 500,000 chars approx 150+ pages to handle multiple docs
        extraction_prompt = self._create_extraction_prompt(full_text_en, full_text_ms)
        
        logger.info(f"CaseStructuring: Calling LLM for extraction...")
        response_text = await self.llm.generate(extraction_prompt)
        
        logger.info("\n" + "-"*40)
        logger.info("CASE STRUCTURING - AI EXTRACTION PREVIEW")
        logger.info(f"Length: {len(response_text)} chars")
        logger.info("-" * 20)
        logger.info(response_text[:1000] if len(response_text) > 1000 else response_text)
        logger.info("-" * 40 + "\n")
        
        extracted_data = self._parse_llm_response(response_text)
        logger.info(f"CaseStructuring: Extracted data: {extracted_data}")
        
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
            "key_dates": self._process_key_dates(extracted_data.get("key_dates", [])),
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
        return f"""You are a Malaysian legal AI assistant. Your task is to extract structured information from the following legal documents with HIGH ACCURACY and DETAIL.

Current Date: {datetime.utcnow().strftime('%Y-%m-%d')}

INSTRUCTIONS:
1. Analyze ALL provided text from all documents.
2. Extract DETAILED legal issues. Do not summarize into one line if there are distinct points.
3. Look specifically for "triable issues", "grounds for defense", "grounds for stay of execution", and procedural irregularities.
4. Extract the specific "Prayers" or "Relief Sought" (word for word if possible).
5. Identify all parties and their roles accurately.

English Text (Combined):
{text_en[:500000]}

Malay Text (Combined):
{text_ms[:500000]}

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
            "type": "future_deadline" or "hearing_date" or "contract_date" or "filing_date",
            "date": "YYYY-MM-DD",
            "description": "Short description of the event"
        }}
    ],
    "issues": [
        {{
            "id": "ISS-1",
            "text_en": "Detailed legal issue in English (e.g., 'Whether the Defences of D1 and D2 raise any triable issue to resist Summary Judgment')",
            "text_ms": "Detailed legal issue in Malay",
            "legal_basis": "Statutory or common law authority (e.g., 'Order 14 Rules of Court 2012')",
            "grounds": "Factual basis for this issue from the document",
            "confidence": 0.0-1.0
        }}
    ],
    "requested_remedies": [
        {{
            "text": "Specific prayer or relief sought (e.g., 'Damages in the sum of RM50,000')",
            "legal_basis": "Authority for this remedy",
            "amount": "Numerical value if mentioned",
            "confidence": 0.0-1.0
        }}
    ]
}}

Return ONLY the JSON object, no additional text."""

    def _process_key_dates(self, key_dates: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Sort and accurately categorize key dates."""
        if not key_dates:
            return []
            
        today = datetime.utcnow()
        processed = []
        
        for item in key_dates:
            date_str = item.get("date", "")
            if not date_str or date_str == "Unknown":
                continue
                
            try:
                # Standardize date string and parse
                # Handle YYYY-MM-DD
                dt = datetime.strptime(date_str[:10], "%Y-%m-%d")
                
                # Re-categorize type based on current date
                original_type = item.get("type", "").lower()
                
                if dt > today:
                    if "hearing" in original_type:
                        new_type = "hearing_date"
                    else:
                        new_type = "future_deadline"
                else:
                    if original_type in ["filing_date", "contract_date"]:
                        new_type = original_type
                    else:
                        new_type = "past_milestone"
                
                processed.append({
                    "date": date_str,
                    "type": new_type,
                    "description": item.get("description", ""),
                    "_dt": dt # Internal field for sorting
                })
            except Exception as e:
                logger.warning(f"Could not parse date '{date_str}': {e}")
                # Keep it as is if unparseable, but mark it
                processed.append(item)
                
        # Sort chronologically
        processed.sort(key=lambda x: x.get("_dt", datetime.max))
        
        # Remove internal field
        for p in processed:
            if "_dt" in p:
                del p["_dt"]
                
        return processed
    
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

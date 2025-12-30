"""
Issue & Prayer Planner Agent - Proposes causes of action and prayers.
"""
from agents.base_agent import BaseAgent
from typing import Dict, Any, List
from services.llm_service import get_llm_service
import json
import re
import asyncio


class IssuePlannerAgent(BaseAgent):
    """
    From matter snapshot, propose causes of action and prayers for cause papers.
    
    Inputs:
    - matter_snapshot: structured case information
    - legal_knowledge_config: embeddings/citation limit
    - jurisdiction: Peninsular Malaysia or East Malaysia
    
    Outputs:
    - issues: array of legal theories with precedents
    - suggested_prayers: mapped to templates
    """
    
    def __init__(self):
        super().__init__(agent_id="IssuePlanner")
        self.llm = get_llm_service()
    
    async def process(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process issue planning request.
        
        Args:
            inputs: {
                "matter_snapshot": Dict,
                "jurisdiction": str,
                "citation_limit": int (default 10)
            }
            
        Returns:
            {
                "issues": List[Dict],
                "suggested_prayers": List[Dict]
            }
        """
        await self.validate_input(inputs, ["matter_snapshot"])
        
        matter = inputs["matter_snapshot"]
        jurisdiction = inputs.get("jurisdiction", "Peninsular Malaysia")
        citation_limit = inputs.get("citation_limit", 10)
        
        # Create prompt for issue identification
        prompt = self._create_issue_prompt(matter, jurisdiction)
        
        try:
            response_text = await self.llm.generate(prompt)
            result = self._parse_llm_response(response_text)
            
            issues = result.get("issues", [])
            prayers = result.get("prayers", [])
            
            # Enhance with precedents (mock for now)
            precedent_tasks = [
                self._find_precedents_async(
                    issue.get("legal_basis", ""),
                    limit=min(3, citation_limit)
                ) for issue in issues
            ]
            precedents_results = await asyncio.gather(*precedent_tasks)
            for issue, precedents in zip(issues, precedents_results):
                issue["precedents"] = precedents
            
            confidence = self._calculate_confidence(issues, prayers)
            
        except Exception as e:
            print(f"Issue planning error: {e}")
            issues = self._fallback_issues(matter)
            prayers = self._fallback_prayers(matter)
            confidence = 0.5
        
        return self.format_output(
            data={
                "issues": issues,
                "suggested_prayers": prayers,
                "total_issues": len(issues),
                "total_prayers": len(prayers)
            },
            confidence=confidence,
            human_review_required=confidence < 0.7
        )
    
    def _create_issue_prompt(self, matter: Dict[str, Any], jurisdiction: str) -> str:
        """Create prompt for LLM to identify legal issues."""
        
        case_type = matter.get("case_type", "general")
        parties = matter.get("parties", [])
        issues_text = matter.get("issues", [])
        
        parties_str = "\n".join([
            f"- {p['role'].upper()}: {p['name']}"
            for p in parties
        ])
        
        issues_str = "\n".join([
            f"- {issue.get('text_en', '')}"
            for issue in issues_text
        ])
        
        return f"""You are a Malaysian legal expert. Analyze this case and identify causes of action and prayers.

CASE INFORMATION:
Type: {case_type}
Jurisdiction: {jurisdiction}
Court: {matter.get('court', 'Unknown')}

PARTIES:
{parties_str}

IDENTIFIED ISSUES:
{issues_str}

TASK:
Identify legal causes of action and suggest prayers. Return JSON:

{{
  "issues": [
    {{
      "id": "ISS-01",
      "title": "Breach of contract - non-payment",
      "legal_basis": ["Contract Act 1950 s.40", "Common law"],
      "theory": "primary" or "alternative",
      "confidence": 0.0-1.0,
      "likely_evidence_required": ["Contract document", "Payment records"],
      "template_id": "TPL-PRAYER-MONEY"
    }}
  ],
  "prayers": [
    {{
      "text_en": "Judgment for the sum of RM X",
      "text_ms": "Penghakiman untuk jumlah RM X",
      "template_id": "TPL-PRAYER-MONEY",
      "priority": "primary" or "alternative",
      "confidence": 0.0-1.0
    }}
  ]
}}

Return ONLY valid JSON."""
    
    def _parse_llm_response(self, response_text: str) -> Dict[str, Any]:
        """Parse LLM response and extract JSON."""
        try:
            json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
            if json_match:
                return json.loads(json_match.group())
            else:
                return json.loads(response_text)
        except json.JSONDecodeError:
            return {"issues": [], "prayers": []}
    
    async def _find_precedents_async(self, legal_basis: str, limit: int = 3) -> List[Dict[str, Any]]:
        """
        Find relevant precedents using LLM asynchronously.
        Generates contextually relevant Malaysian case citations.
        """
        if not legal_basis:
            return []
        
        prompt = f"""You are a Malaysian legal research expert. Generate {limit} relevant Malaysian case precedents for the following legal basis:

Legal Basis: {legal_basis}

Return a JSON array of precedents. Each precedent must have:
- citation: A realistic Malaysian case citation format (e.g., "[2019] 2 MLJ 345")
- court: The court (Federal Court, Court of Appeal, High Court)
- relevance: A score from 0.80 to 0.98
- summary: A brief 10-word summary of the principle

Return ONLY valid JSON array, no explanation. Example:
[{{"citation": "[2019] 2 MLJ 345", "court": "Court of Appeal", "relevance": 0.92, "summary": "Contract interpretation using objective approach"}}]"""

        try:
            result_text = await self.llm.generate(prompt)
            result_text = result_text.strip()
            
            # Parse JSON
            import re
            json_match = re.search(r'\[.*\]', result_text, re.DOTALL)
            if json_match:
                precedents = json.loads(json_match.group())
                return precedents[:limit]
            else:
                return []
        except Exception as e:
            print(f"Precedent search error: {e}")
            return []

    def _find_precedents(self, legal_basis: str, limit: int = 3) -> List[Dict[str, Any]]:
        """
        Find relevant precedents using LLM.
        Generates contextually relevant Malaysian case citations.
        """
        if not legal_basis:
            return []
        
        prompt = f"""You are a Malaysian legal research expert. Generate {limit} relevant Malaysian case precedents for the following legal basis:

Legal Basis: {legal_basis}

Return a JSON array of precedents. Each precedent must have:
- citation: A realistic Malaysian case citation format (e.g., "[2019] 2 MLJ 345")
- court: The court (Federal Court, Court of Appeal, High Court)
- relevance: A score from 0.80 to 0.98
- summary: A brief 10-word summary of the principle

Return ONLY valid JSON array, no explanation. Example:
[{{"citation": "[2019] 2 MLJ 345", "court": "Court of Appeal", "relevance": 0.92, "summary": "Contract interpretation using objective approach"}}]"""

        try:
            result_text = self.llm.generate_sync(prompt)
            result_text = result_text.strip()
            
            # Parse JSON
            import re
            json_match = re.search(r'\[.*\]', result_text, re.DOTALL)
            if json_match:
                precedents = json.loads(json_match.group())
                return precedents[:limit]
            else:
                return []
        except Exception as e:
            print(f"Precedent search error: {e}")
            return []
    
    def _fallback_issues(self, matter: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate basic issues based on matter type with clear placeholders."""
        case_type = matter.get("case_type", "general").lower()
        
        # First check if matter already has issues extracted
        existing_issues = matter.get("issues", [])
        if existing_issues:
            return [{
                "id": f"ISS-{i+1:02d}",
                "title": issue.get("text_en", issue.get("title", "[Issue to be defined]")),
                "legal_basis": ["[Undang-undang berkaitan / Applicable law]"],
                "theory": "primary" if i == 0 else "alternative",
                "confidence": 0.6,
                "likely_evidence_required": ["[Bukti yang diperlukan / Evidence required]"],
                "template_id": "TPL-PRAYER-GENERAL",
                "precedents": []
            } for i, issue in enumerate(existing_issues)]
        
        # Generate appropriate issue template based on case type
        if "contract" in case_type:
            return [{
                "id": "ISS-01",
                "title": "[Pelanggaran Kontrak / Breach of Contract]",
                "legal_basis": ["Contract Act 1950 s.40", "Akta Kontrak 1950"],
                "theory": "primary",
                "confidence": 0.6,
                "likely_evidence_required": ["[Dokumen kontrak / Contract document]", "[Rekod pembayaran / Payment records]"],
                "template_id": "TPL-PRAYER-MONEY",
                "precedents": []
            }]
        elif "tort" in case_type:
            return [{
                "id": "ISS-01",
                "title": "[Kecuaian / Negligence]",
                "legal_basis": ["Common law - Donoghue v Stevenson"],
                "theory": "primary",
                "confidence": 0.6,
                "likely_evidence_required": ["[Bukti kecederaan / Evidence of injury]"],
                "template_id": "TPL-PRAYER-DAMAGES",
                "precedents": []
            }]
        
        return [{
            "id": "ISS-01",
            "title": "[SILA NYATAKAN ISU / Please Specify Issue]",
            "legal_basis": ["[Undang-undang berkaitan / Applicable law]"],
            "theory": "primary",
            "confidence": 0.5,
            "likely_evidence_required": ["[Bukti yang diperlukan / Evidence required]"],
            "template_id": "TPL-PRAYER-GENERAL",
            "precedents": []
        }]
    
    def _fallback_prayers(self, matter: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate basic prayers with clear placeholders."""
        return [
            {
                "text_en": "[Judgment for the sum of RM ______]",
                "text_ms": "[Penghakiman untuk jumlah RM ______]",
                "template_id": "TPL-PRAYER-MONEY",
                "priority": "primary",
                "confidence": 0.6
            },
            {
                "text_en": "Interest at [__]% per annum",
                "text_ms": "Faedah pada kadar [__]% setahun",
                "template_id": "TPL-PRAYER-INTEREST",
                "priority": "primary",
                "confidence": 0.7
            },
            {
                "text_en": "Costs and such further relief as the Court deems fit",
                "text_ms": "Kos dan apa-apa relief lain yang Mahkamah fikirkan sesuai",
                "template_id": "TPL-PRAYER-COSTS",
                "priority": "alternative",
                "confidence": 0.8
            }
        ]
    
    def _calculate_confidence(self, issues: List[Dict], prayers: List[Dict]) -> float:
        """Calculate overall confidence based on completeness."""
        score = 0.0
        
        if issues:
            score += 0.4
            # Check if issues have legal basis
            if all(issue.get("legal_basis") for issue in issues):
                score += 0.2
        
        if prayers:
            score += 0.3
            # Check if prayers are mapped to templates
            if all(prayer.get("template_id") for prayer in prayers):
                score += 0.1
        
        return min(score, 1.0)

"""
Argument Builder Agent - Draft bilingual issue memos.
"""
from agents.base_agent import BaseAgent
from typing import Dict, Any, List
from services.llm_service import get_llm_service


class ArgumentBuilderAgent(BaseAgent):
    """
    Draft bilingual issue memo that lawyers can import into submissions.
    
    Inputs:
    - issues: list of legal issues
    - cases: relevant cases from research agent
    - matter_snapshot: case context
    
    Outputs:
    - issue_memo_en: English analysis
    - issue_memo_ms: Malay authoritative wording
    - suggested_wording: for submissions
    """
    
    def __init__(self):
        super().__init__(agent_id="ArgumentBuilder")
        self.llm = get_llm_service()
    
    async def process(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process argument building request.
        
        Args:
            inputs: {
                "issues": List[Dict],
                "cases": List[Dict],
                "matter_snapshot": Dict,
                "query": str (optional)
            }
            
        Returns:
            {
                "issue_memo_en": str,
                "issue_memo_ms": str,
                "suggested_wording": List[Dict]
            }
        """
        await self.validate_input(inputs, ["cases"])
        
        issues = inputs.get("issues")
        cases = inputs.get("cases")
        matter = inputs.get("matter_snapshot", {})
        query = inputs.get("query")
        
        # Ensure issues and cases are lists
        if cases is None:
            cases = []
            
        # If no issues provided but we have a query, auto-generate them
        if not issues and query:
            issues = await self._generate_issues_from_query(query, cases)
        elif issues is None:
            issues = []
        
        # Build argument for each issue
        arguments = []
        
        for issue in issues:
            arg = await self._build_argument_for_issue(issue, cases, matter)
            arguments.append(arg)
        
        # Compile into memo
        memo_en = self._compile_memo_en(arguments, matter)
        memo_ms = self._compile_memo_ms(arguments, matter)
        
        # Extract suggested wording
        suggested_wording = self._extract_suggested_wording(arguments)
        
        return self.format_output(
            data={
                "issue_memo_en": memo_en,
                "issue_memo_ms": memo_ms,
                "suggested_wording": suggested_wording,
                "total_issues": len(arguments)
            },
            confidence=0.82
        )

    async def _generate_issues_from_query(self, query: str, cases: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Generate legal issues from search query and cases."""
        prompt = f"""Identify 3 distinct legal issues based on this search query and relevant cases.

QUERY: {query}

CASES:
{self._format_cases_for_prompt(cases[:3])}

Return ONLY a JSON list of objects with 'title' and 'legal_basis' fields.
Example:
[
  {{"title": "Issue description", "legal_basis": ["Contract Law", "Section 56"]}}
]"""
        try:
            response = await self.llm.generate(prompt)
            # Simple parsing - in production, use a more robust parser or structured output
            import json
            import re
            
            # extract json block if present
            match = re.search(r'\[.*\]', response, re.DOTALL)
            if match:
                json_str = match.group(0)
                return json.loads(json_str)
            else:
                # Fallback if no valid JSON found
                return [{"title": f"Legal implications of {query}", "legal_basis": ["General Principles"]}]
        except Exception as e:
            return [{"title": f"Legal issue regarding {query}", "legal_basis": ["General Principles"]}]

    async def _build_argument_for_issue(
        self,
        issue: Dict[str, Any],
        cases: List[Dict[str, Any]],
        matter: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Build argument for a single issue."""
        
        # Filter relevant cases for this issue
        relevant_cases = [
            c for c in cases
            if any(area in c.get("subject_areas", []) for area in issue.get("legal_basis", []))
        ][:3]
        
        # If no specific matches, use top cases
        if not relevant_cases:
            relevant_cases = cases[:3]
        
        # Create prompt for argument
        prompt = f"""Draft a legal argument for this issue:

ISSUE: {issue.get('title', '')}
LEGAL BASIS: {', '.join(issue.get('legal_basis', []))}

RELEVANT CASES:
{self._format_cases_for_prompt(relevant_cases)}

Write a concise legal argument (2-3 paragraphs) with inline citations."""
        
        try:
            analysis = await self.llm.generate(prompt)
        except:
            analysis = f"Analysis for {issue.get('title', 'issue')} pending."
        
        # Get Malay translation of analysis (mock for now or use translation service)
        # In a real system, we'd call the TranslationAgent here
        analysis_ms = f"[Terjemahan Bahasa Melayu]: {analysis[:100]}... (Sila rujuk teks Bahasa Inggeris)"
        
        return {
            "issue_id": issue.get("id", "auto-gen"),
            "issue_title": issue.get("title"),
            "analysis_en": analysis,
            "analysis_ms": analysis_ms,
            "cases_cited": [c["citation"] for c in relevant_cases],
            "suggested_wording_en": f"It is submitted that {issue.get('title', 'the claim')} is supported by the authorities.",
            "suggested_wording_ms": f"Adalah dihujahkan bahawa {issue.get('title', '')} disokong oleh autoriti-autoriti tersebut."
        }
    
    def _format_cases_for_prompt(self, cases: List[Dict[str, Any]]) -> str:
        """Format cases for LLM prompt."""
        formatted = []
        for case in cases:
            formatted.append(
                f"- {case['citation']}: {case.get('headnote_en', '')[:200]}"
            )
        return "\n".join(formatted)
    
    def _compile_memo_en(self, arguments: List[Dict[str, Any]], matter: Dict[str, Any]) -> str:
        """Compile English issue memo."""
        
        memo = f"""LEGAL ISSUE MEMO

Matter: {matter.get('title', 'Untitled')}
Date: {matter.get('created_at', 'N/A')}

"""
        
        for i, arg in enumerate(arguments, 1):
            memo += f"""
## Issue {i}: {arg['issue_title']}

{arg['analysis_en']}

**Cases Cited**: {', '.join(arg['cases_cited'])}

**Suggested Submission Wording**: {arg['suggested_wording_en']}

---
"""
        
        return memo
    
    def _compile_memo_ms(self, arguments: List[Dict[str, Any]], matter: Dict[str, Any]) -> str:
        """Compile Malay issue memo."""
        
        memo = f"""MEMO ISU UNDANG-UNDANG

Perkara: {matter.get('title', 'Tanpa Tajuk')}
Tarikh: {matter.get('created_at', 'T/A')}

"""
        
        for i, arg in enumerate(arguments, 1):
            memo += f"""
## Isu {i}: {arg['issue_title']}

{arg['analysis_ms']}

**Kes Dirujuk**: {', '.join(arg['cases_cited'])}

**Cadangan Perkataan Hujahan**: {arg['suggested_wording_ms']}

---
"""
        
        return memo
    
    def _extract_suggested_wording(self, arguments: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Extract suggested wording for submissions."""
        
        wording = []
        
        for arg in arguments:
            wording.append({
                "issue_id": arg.get("issue_id"),
                "wording_en": arg["suggested_wording_en"],
                "wording_ms": arg["suggested_wording_ms"],
                "binding_authorities": [
                    c for c in arg["cases_cited"] if "MLJ" in c or "CLJ" in c
                ],
                "persuasive_authorities": [
                    c for c in arg["cases_cited"] if "MLJ" not in c and "CLJ" not in c
                ]
            })
        
        return wording


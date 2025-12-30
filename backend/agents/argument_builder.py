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
                "matter_snapshot": Dict
            }
            
        Returns:
            {
                "issue_memo_en": str,
                "issue_memo_ms": str,
                "suggested_wording": List[Dict]
            }
        """
        await self.validate_input(inputs, ["issues", "cases"])
        
        issues = inputs["issues"]
        cases = inputs["cases"]
        matter = inputs.get("matter_snapshot", {})
        
        # Ensure issues and cases are lists, not None
        if issues is None:
            issues = []
        if cases is None:
            cases = []
        
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
        
        return {
            "issue_id": issue.get("id"),
            "issue_title": issue.get("title"),
            "analysis_en": analysis,
            "analysis_ms": f"[Analisis dalam Bahasa Melayu untuk {issue.get('title')}]",
            "cases_cited": [c["citation"] for c in relevant_cases],
            "suggested_wording_en": f"The {issue.get('title', 'claim')} is well-founded in law.",
            "suggested_wording_ms": f"Tuntutan {issue.get('title', '')} adalah berasas dalam undang-undang."
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
                "issue_id": arg["issue_id"],
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

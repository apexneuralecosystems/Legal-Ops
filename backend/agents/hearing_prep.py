"""
Hearing Prep & Live Assistance Agent - Prepare hearing bundles and scripts.
"""
from agents.base_agent import BaseAgent
from typing import Dict, Any, List
from services.llm_service import get_llm_service


class HearingPrepAgent(BaseAgent):
    """
    Produce hearing bundle, bilingual scripts, and dynamic Q&A suggestions.
    Uses Gemini LLM for generating contextual content.
    
    Inputs:
    - matter_snapshot: case information
    - pleadings: list of pleadings
    - cases: relevant authorities
    - issues: legal issues
    
    Outputs:
    - hearing_bundle: tabbed structure
    - oral_submission_script_ms: Malay script with English notes
    - if_judge_asks: FAQs with answers and citations
    """
    
    def __init__(self):
        super().__init__(agent_id="HearingPrep")
        self.llm = get_llm_service()
    
    async def process(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process hearing preparation.
        
        Args:
            inputs: {
                "matter_snapshot": Dict,
                "pleadings": List[Dict],
                "cases": List[Dict],
                "issues": List[Dict]
            }
            
        Returns:
            {
                "hearing_bundle": Dict,
                "oral_script_ms": str,
                "oral_script_en_notes": str,
                "if_judge_asks": List[Dict]
            }
        """
        await self.validate_input(inputs, ["matter_snapshot"])
        
        matter = inputs["matter_snapshot"]
        pleadings = inputs.get("pleadings", [])
        cases = inputs.get("cases", [])
        issues = inputs.get("issues", [])
        
        # Ensure all lists are actually lists, not None
        if pleadings is None:
            pleadings = []
        if cases is None:
            cases = []
        if issues is None:
            issues = []
        
        # Create hearing bundle
        bundle = self._create_hearing_bundle(matter, pleadings, cases)
        
        # Run LLM generations in parallel
        # import asyncio  <-- moved to top level or assumed available, but good to keep if local import needed
        import asyncio
        oral_script_task = self._create_oral_script(matter, issues, cases)
        faqs_task = self._create_judge_faqs(matter, issues, cases)
        
        # Wait for both tasks to complete
        (oral_script_ms, oral_script_en), faqs = await asyncio.gather(
            oral_script_task,
            faqs_task
        )
        
        return self.format_output(
            data={
                "hearing_bundle": bundle,
                "oral_script_ms": oral_script_ms,
                "oral_script_en_notes": oral_script_en,
                "if_judge_asks": faqs,
                "total_faqs": len(faqs)
            },
            confidence=0.85
        )
    
    def _create_hearing_bundle(
        self,
        matter: Dict[str, Any],
        pleadings: List[Dict],
        cases: List[Dict]
    ) -> Dict[str, Any]:
        """Create tabbed hearing bundle structure."""
        
        tabs = []
        
        # Tab 1: Pleadings
        tabs.append({
            "tab": "1",
            "section": "Pleadings",
            "items": [
                {
                    "description": p.get("pleading_type", "Pleading"),
                    "language": "Malay (with English translation)",
                    "pages": "TBD"
                }
                for p in pleadings
            ]
        })
        
        # Tab 2: Submissions
        tabs.append({
            "tab": "2",
            "section": "Written Submissions",
            "items": [
                {
                    "description": "Plaintiff's Submissions",
                    "language": "Malay",
                    "pages": "TBD"
                }
            ]
        })
        
        # Tab 3: Authorities
        # Safe filtering with None checks
        binding_cases = [c for c in cases if c.get("weight") == "binding" or c.get("binding") == True]
        persuasive_cases = [c for c in cases if c.get("weight") == "persuasive" or (c.get("binding") == False and c not in binding_cases)]
        
        authority_items = []
        for i, case in enumerate(binding_cases, 1):
            authority_items.append({
                "description": f"Authority {i}: {case.get('citation', 'N/A')} (Binding)",
                "summary": (case.get("headnote_en") or "")[:100],
                "pages": "TBD"
            })
        
        for i, case in enumerate(persuasive_cases, len(binding_cases) + 1):
            authority_items.append({
                "description": f"Authority {i}: {case.get('citation', 'N/A')} (Persuasive)",
                "summary": (case.get("headnote_en") or "")[:100],
                "pages": "TBD"
            })
        
        tabs.append({
            "tab": "3",
            "section": "Bundle of Authorities",
            "items": authority_items
        })
        
        # Tab 4: Translations
        tabs.append({
            "tab": "4",
            "section": "Certified Translations",
            "items": [
                {
                    "description": "Translation of key documents",
                    "language": "English (certified)",
                    "pages": "TBD"
                }
            ]
        })
        
        return {
            "bundle_name": f"Hearing Bundle - {matter.get('title', 'Matter')}",
            "tabs": tabs,
            "total_tabs": len(tabs)
        }
    
    async def _create_oral_script(
        self,
        matter: Dict[str, Any],
        issues: List[Dict],
        cases: List[Dict]
    ) -> tuple:
        """Create bilingual oral submission script using LLM."""
        
        # Build case context for LLM
        case_title = matter.get('title', 'Legal Matter')
        case_type = matter.get('case_type', 'civil')
        parties = matter.get('parties', [])
        
        # Format parties for prompt
        plaintiff = next((p.get('name', 'Plaintiff') for p in parties if p.get('role') == 'plaintiff'), 'Plaintif')
        defendant = next((p.get('name', 'Defendant') for p in parties if p.get('role') == 'defendant'), 'Defendan')
        
        # Format issues for prompt
        issues_text = ""
        for i, issue in enumerate(issues, 1):
            issues_text += f"{i}. {issue.get('title', 'Legal Issue')}\n"
        
        # Format cases for prompt
        cases_text = ""
        for case in cases[:3]:  # Limit to top 3 cases
            cases_text += f"- {case.get('citation', 'N/A')}: {case.get('headnote_en', '')[:100]}\n"
        
        # Generate Malay script with LLM
        ms_prompt = f"""Generate a formal oral submission script in Bahasa Malaysia for a Malaysian court hearing.

Case Title: {case_title}
Case Type: {case_type}
Plaintif: {plaintiff}
Defendan: {defendant}

Legal Issues:
{issues_text if issues_text else 'General contract dispute'}

Relevant Authorities:
{cases_text if cases_text else 'No specific authorities cited'}

Generate a professional oral submission script in formal Bahasa Malaysia that:
1. Opens with "Yang Arif" greeting
2. States the case briefly
3. Addresses each legal issue
4. Cites relevant authorities
5. Ends with prayer for relief

Use formal legal Malay terminology. Output ONLY the script text, no explanations."""

        # Generate English companion notes
        en_prompt = f"""Generate English companion notes for a Malay oral submission.
        
Case Title: {case_title}
Case Type: {case_type}

Legal Issues:
{issues_text if issues_text else 'General contract dispute'}

Relevant Authorities:
{cases_text if cases_text else 'No specific authorities cited'}

Generate professional English speaking notes that allow a lawyer to follow the Malay submission.
Focus on:
1. Key legal points in English
2. Summaries of the arguments
3. Translation of key Malay legal terms used

Output ONLY the notes text."""

        # Run generations in parallel
        try:
            import asyncio
            results = await asyncio.gather(
                self.llm.generate(ms_prompt),
                self.llm.generate(en_prompt),
                return_exceptions=True
            )
            
            script_ms = results[0] if isinstance(results[0], str) else ""
            script_en = results[1] if isinstance(results[1], str) else ""
            
            if isinstance(results[0], Exception):
                print(f"Error generating MS script: {results[0]}")
                
            if isinstance(results[1], Exception):
                print(f"Error generating EN script: {results[1]}")

            return script_ms, script_en
            
        except Exception as e:
            print(f"Error in oral script generation: {e}")
            return "", ""
    
    async def _create_judge_faqs(
        self,
        matter: Dict[str, Any],
        issues: List[Dict],
        cases: List[Dict]
    ) -> List[Dict[str, Any]]:
        """Create FAQ for potential judge questions using LLM."""
        
        case_title = matter.get('title', 'Legal Matter')
        case_type = matter.get('case_type', 'civil')
        parties = matter.get('parties', [])
        
        # Format context for LLM
        plaintiff = next((p.get('name', 'Plaintiff') for p in parties if p.get('role') == 'plaintiff'), 'Plaintif')
        
        issues_text = "\n".join([f"- {issue.get('title', '')}" for issue in issues])
        
        # Get real case citations from matter's research/arguments
        real_cases = []
        
        # Check if matter has research results or arguments with cases
        if 'research_results' in matter and matter['research_results']:
            research_cases = matter['research_results'].get('cases', [])
            real_cases.extend(research_cases[:5])  # Top 5 most relevant
        
        # Also check arguments field
        if 'arguments' in matter and matter['arguments']:
            for arg in matter.get('arguments', []):
                if 'supporting_cases' in arg:
                    real_cases.extend(arg['supporting_cases'][:2])
        
        # Use provided cases if available, otherwise fall back to  matter cases
        if cases and len(cases) > 0:
            cases_text = "\n".join([
                f"- {case.get('citation', case.get('case_name', 'Unknown'))} - {case.get('summary', ''  )[:100]}"
                for case in cases[:5]
            ])
        elif real_cases:
            cases_text = "\n".join([
                f"- {case.get('citation', case.get('case_name', 'Unknown'))} - {case.get('summary', '')[:100]}"
                for case in real_cases[:5]
            ])
        else:
            # Get cases from database for this jurisdiction/matter type
            cases_text = f"Malaysian {matter.get('case_type', 'civil')} case law (general principles)"
        
        prompt = f"""You are a Malaysian legal expert preparing for a court hearing. Generate 5 potential questions a judge might ask and prepare bilingual answers.

Case: {case_title}
Type: {case_type}
Plaintiff: {plaintiff}

Legal Issues:
{issues_text if issues_text else 'General civil dispute'}

Relevant Case Authorities:
{cases_text}

Generate a JSON array with 5 FAQs. Each FAQ must have:
- question: The judge's question in English
- answer_ms: Professional answer in formal Bahasa Malaysia (start with "Yang Arif, ...")
- answer_en: Professional answer in formal English (start with "Your Honour, ...")
- authority: Cite a SPECIFIC Malaysian case from the authorities above, or a relevant statute
- confidence: 0.75-0.95

IMPORTANT: Use the actual case citations provided above in your authorities. Format: "[Case Name] [Year] [Court]"

Return ONLY valid JSON array. Example format:
[{{"question": "Why is this court the appropriate forum?", "answer_ms": "Yang Arif, ...", "answer_en": "Your Honour, ...", "authority": "Actual case citation from above", "confidence": 0.85}}]"""

        result_text = await self.llm.generate(prompt)
        result_text = result_text.strip()
        
        # Parse JSON
        import re
        import json
        try:
            json_match = re.search(r'\[.*\]', result_text, re.DOTALL)
            if json_match:
                faqs = json.loads(json_match.group())
                return faqs[:5]
        except Exception as e:
            # Fallback for parsing error
            print(f"Error parsing FAQs JSON: {e}")
            pass
        
        return []


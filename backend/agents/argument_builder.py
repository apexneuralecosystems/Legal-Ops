"""
Argument Builder Agent - Draft bilingual issue memos.
"""
from agents.base_agent import BaseAgent
from typing import Dict, Any, List
from services.llm_service import get_llm_service
import logging
import asyncio
import json

logger = logging.getLogger(__name__)


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
        Process argument building request with Knowledge Base enhancement.
        
        Args:
            inputs: {
                "issues": List[Dict],
                "cases": List[Dict],
                "matter_snapshot": Dict,
                "query": str (optional),
                "db_session": Session (optional - for KB queries),
                "matter_id": str (optional - for KB comparison)
            }
            
        Returns:
            {
                "issue_memo_en": str,
                "issue_memo_ms": str,
                "suggested_wording": List[Dict],
                "kb_insights": Dict (Phase 2)
            }
        """
        await self.validate_input(inputs, ["cases"])
        
        issues = inputs.get("issues")
        cases = inputs.get("cases")
        matter = inputs.get("matter_snapshot", {})
        query = inputs.get("query")
        db_session = inputs.get("db_session")
        matter_id = inputs.get("matter_id") or matter.get("id")
        
        # Ensure issues and cases are lists
        if cases is None:
            cases = []
            
        # If no issues provided but we have a query, auto-generate them
        if not issues and query:
            issues = await self._generate_issues_from_query(query, cases)
        elif issues is None:
            issues = []
        
        # ⭐ PHASE 2: Query Knowledge Base for strategic insights
        kb_data = {}
        if db_session and matter_id:
            try:
                from services.kb_enrichment_service import get_kb_enrichment_service
                kb_service = get_kb_enrichment_service()
                
                logger.info(f"📚 Querying Knowledge Base for matter: {matter_id}")
                kb_data = await kb_service.enrich_argument_data(
                    matter_id=matter_id,
                    user_selected_cases=cases,
                    issues=issues,
                    db=db_session
                )
                
                if kb_data.get("kb_available"):
                    logger.info(f"✅ KB insights available: {kb_data.get('similar_matters_count', 0)} similar matters")
                    
                    # Merge KB cases with user-selected cases (if any)
                    additional_kb_cases = kb_data.get("additional_cases", [])
                    if additional_kb_cases:
                        logger.info(f"📎 Adding {len(additional_kb_cases)} cases from knowledge base")
                        cases = cases + additional_kb_cases
                else:
                    logger.info("ℹ️ KB insights not available (no similar matters or general research)")
                    
            except Exception as e:
                logger.warning(f"⚠️ KB enrichment failed: {e}. Continuing without KB insights.")
                kb_data = {"kb_available": False, "error": str(e)}
        else:
            logger.info("ℹ️ Skipping KB enrichment (no db_session or matter_id)")
        
        # Build argument for each issue (with KB context if available)
        arguments = []
        
        for issue in issues:
            arg = await self._build_argument_for_issue(
                issue, 
                cases, 
                matter,
                kb_insights=kb_data.get("insights", {}),
                db_session=db_session
            )
            arguments.append(arg)
        
        # Compile into memo (with KB insights section if available)
        memo_en = self._compile_memo_en(arguments, matter, kb_data=kb_data)
        memo_ms = self._compile_memo_ms(arguments, matter, kb_data=kb_data)
        
        # Extract suggested wording
        suggested_wording = self._extract_suggested_wording(arguments)
        
        return self.format_output(
            data={
                "issue_memo_en": memo_en,
                "issue_memo_ms": memo_ms,
                "suggested_wording": suggested_wording,
                "total_issues": len(arguments),
                "kb_insights": kb_data,  # ⭐ NEW: Include KB data in response
                "kb_available": kb_data.get("kb_available", False),
                "similar_matters_count": kb_data.get("similar_matters_count", 0)
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
        matter: Dict[str, Any],
        kb_insights: Dict[str, Any] = None,
        db_session = None
    ) -> Dict[str, Any]:
        """Build argument for a single issue using doctrinal research format with FULL JUDGMENTS and KB insights."""
        
        if kb_insights is None:
            kb_insights = {}
        
        # Filter relevant cases for this issue
        relevant_cases = [
            c for c in cases
            if any(area in c.get("subject_areas", []) for area in issue.get("legal_basis", []))
        ][:10]
        
        if not relevant_cases:
            relevant_cases = cases[:10]
        
        # ⭐ OPTION 3 DETECTION: Check if judgments already prefetched during search
        already_fetched_cases = [c for c in relevant_cases if c.get("full_judgment_fetched")]
        if already_fetched_cases:
            logger.info(f"⚡ Option 3 SUCCESS: {len(already_fetched_cases)}/{len(relevant_cases)} judgments already available from search!")
        
        # Check which cases still need fetching (Option 3 should make this list empty/small)
        cases_needing_fetch = [c for c in relevant_cases if not c.get("full_judgment_fetched") and c.get("link")]
        
        if cases_needing_fetch:
            logger.info(f"🔍 Checking memory cache for {len(cases_needing_fetch)} cases...")
            
            # ⭐ OPTIMIZATION: Check memory cache first (from background fetch)
            from services.background_judgment_fetcher import BackgroundJudgmentFetcher
            
            still_need_fetch = []
            cache_hit_count = 0
            
            for case in cases_needing_fetch:
                case_link = case.get("link")
                cached_judgment = await BackgroundJudgmentFetcher.get_cached(case_link)
                
                if cached_judgment and cached_judgment.get("success"):
                    # Use cached judgment - populate case immediately
                    case["full_judgment"] = cached_judgment.get("full_text", "")
                    case["judgment_word_count"] = cached_judgment.get("word_count", 0)
                    case["judgment_headnotes"] = cached_judgment.get("headnotes", "")
                    case["judgment_facts"] = cached_judgment.get("facts", "")
                    case["judgment_issues"] = cached_judgment.get("issues_text", "")
                    case["judgment_reasoning"] = cached_judgment.get("reasoning", "")
                    case["judgment_judges"] = cached_judgment.get("judges", [])
                    case["judgment_sections"] = cached_judgment.get("sections", [])
                    case["full_judgment_fetched"] = True
                    case["from_cache"] = True
                    cache_hit_count += 1
                    logger.info(f"⚡ Memory cache HIT: {case.get('title', 'Unknown')[:50]} ({cached_judgment.get('word_count', 0):,} words)")
                else:
                    still_need_fetch.append(case)
            
            logger.info(f"📊 Cache performance: {cache_hit_count}/{len(cases_needing_fetch)} hits ({cache_hit_count/len(cases_needing_fetch)*100:.0f}%)")
            
            # Only fetch cases not in memory cache
            if still_need_fetch:
                logger.info(f"🌐 Fetching {len(still_need_fetch)} judgments from Lexis...")
                scraper = None
                try:
                    from services.lexis_scraper import LexisScraper
                    # Phase 3: Pass db_session to enable caching
                    scraper = LexisScraper(use_pool=False, db_session=db_session)
                    await scraper.start_robot()
                    
                    # Fetch full judgments
                    enriched = await scraper.fetch_multiple_judgments(still_need_fetch)
                    
                    # Update the relevant_cases list with enriched data
                    for i, case in enumerate(relevant_cases):
                        for enriched_case in enriched:
                            if case.get("link") == enriched_case.get("link"):
                                relevant_cases[i] = enriched_case
                                break
                    
                    logger.info(f"✅ Full judgments fetched successfully")
                except Exception as e:
                    logger.warning(f"⚠️ Could not fetch full judgments: {e}. Using summaries as fallback.")
                finally:
                    # Always close browser, even on error
                    if scraper:
                        try:
                            await scraper.close_robot()
                        except Exception as close_err:
                            logger.debug(f"Error closing browser: {close_err}")
            else:
                logger.info(f"✅ All judgments available from memory cache - no fetching needed!")
        else:
            logger.info(f"ℹ️ Using existing data (full judgments or summaries)")
        
        # STEP 1: Generate structured JSON data first (WITH FULL JUDGMENTS IF AVAILABLE)
        logger.info(f"🔬 Using doctrinal format with {'FULL JUDGMENTS' if any(c.get('full_judgment') for c in relevant_cases) else 'SUMMARIES'}")
        
        # DEEP DIVE PROMPT: Designed to generate 3-4 pages of content per issue
        json_prompt = f"""You are a senior Malaysian legal researcher preparing a comprehensive doctrinal memorandum for court submission.

**CRITICAL GROUNDING RULES:**
1. Use ONLY information from the provided FULL JUDGMENT texts below. 0% hallucination tolerance.
2. Quote verbatim from the judgment using quotation marks. Include paragraph numbers [Para X] where visible.
3. Your analysis must be EXHAUSTIVE and DETAILED. This is for a 10-12 page legal memorandum, NOT a summary.

---
**ISSUE UNDER ANALYSIS:**
{issue.get('title', '')}

**LEGAL BASIS:**
{', '.join(issue.get('legal_basis', []))}

---
**PRIMARY SOURCE DOCUMENTS (FULL COURT JUDGMENTS):**
{self._format_cases_with_full_judgments(relevant_cases)}

---
**REQUIRED OUTPUT (JSON FORMAT):**
Generate a JSON object with EXHAUSTIVE DETAIL for each section. Your goal is 1500-2000 words of analysis per case.

{{
  "issue_framing": {{
    "main_issue": "A comprehensive statement of the legal issue in 2-3 sentences, including statutory basis and key doctrinal questions.",
    "sub_issues": ["Sub-issue 1 with full context", "Sub-issue 2 with full context", "Sub-issue 3 if applicable"]
  }},
  "case_analysis": [
    {{
      "no": 1,
      "case_name": "Full official case name",
      "citation": "[Year] MLJU/MLJ/CLJ XXX",
      "court": "Federal Court / Court of Appeal / High Court",
      "judges": "Name(s) of presiding judge(s) if available",
      "facts": "COMPREHENSIVE FACTUAL NARRATIVE (Minimum 400 words). Include: (1) Parties and their relationship, (2) Chronological sequence of events, (3) Key contractual terms or statutory provisions at issue, (4) The specific conduct alleged as breach/wrong, (5) Procedural history. Quote directly from the judgment where possible.",
      "issues": "The EXACT legal questions framed by the court (2-3 sentences). Quote the court's own framing if available.",
      "excerpt": "EXTENDED RATIO DECIDENDI (Minimum 200 words). Include the judge's key legal reasoning, the rule of law applied, and the holding. Use VERBATIM QUOTES with [Para X] citations where possible.",
      "remarks": "STRATEGIC ANALYTICAL COMMENTARY (Minimum 300 words). Include: (1) How this case applies to the current matter, (2) Distinctions or similarities with the client's facts, (3) Strength of authority (binding/persuasive), (4) Potential counter-arguments and how this case addresses them."
    }}
  ],
  "doctrinal_synthesis": {{
    "settled_principles": ["Principle 1 with full explanation (2-3 sentences)", "Principle 2 with full explanation", "Principle 3"],
    "distinctions": {{
      "key_distinction_1": "Full explanation of the doctrinal distinction and its significance (3-4 sentences)",
      "key_distinction_2": "Full explanation"
    }},
    "doctrinal_development": "A paragraph (5-7 sentences) on how the law has developed in this area, including any landmark cases and recent trends."
  }},
  "application": {{
    "legal_characterization": "A full paragraph (5-7 sentences) characterizing the client's situation in light of the analyzed cases.",
    "available_remedies": ["Remedy 1 with explanation", "Remedy 2 with explanation"],
    "barred_remedies": ["Remedy 1 with explanation of why barred"],
    "strategic_recommendations": ["Recommendation 1", "Recommendation 2"],
    "conclusion": "A comprehensive conclusion (3-5 sentences) summarizing the legal position."
  }},
  "public_importance": {{
    "novel_aspects": "Full explanation of any novel legal issues (3-4 sentences).",
    "appellate_value": "Assessment of appellate prospects (3-4 sentences).",
    "significance": "Broader legal or commercial significance (3-4 sentences)."
  }}
}}

**FINAL INSTRUCTION:** Return ONLY valid JSON. Include ALL cases provided above in the case_analysis array. Be EXHAUSTIVE. This memorandum will be reviewed by a senior partner and submitted to court."""
        
        try:
            json_response = await self.llm.generate(json_prompt, max_tokens=16000)
            
            # Extract JSON from response
            import json
            import re
            match = re.search(r'\{.*\}', json_response, re.DOTALL)
            if match:
                data = json.loads(match.group(0))
                
                # ⭐ PHASE 3: Self-Reflect / Verification Step
                # Verify generated analysis against source text (Headnotes/Facts)
                logger.info("🧐 Running Self-Reflect verification on case analysis...")
                data = await self._verify_analysis(data, relevant_cases)
                
                # STEP 2: Convert structured JSON to formatted markdown
                analysis = self._format_doctrinal_analysis(data)
            else:
                raise ValueError("No JSON found in response")
                
        except Exception as e:
            logger.warning(f"JSON generation failed: {e}, trying direct markdown")
            # Fallback to simpler format
            analysis = await self._generate_simple_analysis(issue, relevant_cases, matter)
        
        # Get Malay translation
        translation_prompt = f"""Translate to formal Bahasa Melayu (maintain all markdown tables and structure):

{analysis}

Return ONLY the Malay translation."""
        
        try:
            analysis_ms = await self.llm.generate(translation_prompt, max_tokens=16000)
        except Exception:
            analysis_ms = f"[Terjemahan diperlukan / Translation required]"
        
        # Calculate metadata about full judgments usage
        cases_with_full_judgment = [c for c in relevant_cases if c.get('full_judgment_fetched')]
        total_judgment_words = sum(c.get('judgment_word_count', 0) for c in cases_with_full_judgment)
        
        return {
            "issue_id": issue.get("id", "auto-gen"),
            "issue_title": issue.get("title"),
            "analysis_en": analysis,
            "analysis_ms": analysis_ms,
            "cases_cited": [c.get("citation", "Unknown") for c in relevant_cases],
            "suggested_wording_en": f"It is respectfully submitted that {issue.get('title', 'the issue')} is governed by established doctrinal principles as analyzed above.",
            "suggested_wording_ms": f"Adalah dengan hormatnya dihujahkan bahawa {issue.get('title', 'isu tersebut')} dikawal oleh prinsip-prinsip doktrin yang telah ditetapkan seperti dianalisis di atas.",
            "used_full_judgments": len(cases_with_full_judgment) > 0,
            "full_judgment_count": len(cases_with_full_judgment),
            "total_judgment_words": total_judgment_words
        }
    
    def _format_doctrinal_analysis(self, data: Dict[str, Any]) -> str:
        """Convert structured JSON data to formatted markdown with table."""
        
        # Build markdown output
        output = "## PART A — ISSUE FRAMING\n\n"
        output += f"{data.get('issue_framing', {}).get('main_issue', 'Issue not specified')}\n\n"
        
        sub_issues = data.get('issue_framing', {}).get('sub_issues', [])
        if sub_issues:
            output += "**Sub-Issues:**\n"
            for i, sub in enumerate(sub_issues, 1):
                output += f"{i}. {sub}\n"
            output += "\n"
        
        # Build table for Part B
        output += "## PART B — DOCTRINAL CASE LAW ANALYSIS\n\n"
        output += "| No. | Authority | Facts | Issues | Excerpt | Remarks |\n"
        output += "|-----|-----------|-------|--------|---------|----------|\n"
        
        cases = data.get('case_analysis', [])
        for case in cases:
            # Format authority with line breaks
            authority = f"**{case.get('case_name', 'Unknown')}**<br>{case.get('citation', '')}<br>{case.get('court', '')}"
            
            # Sanitize content for markdown table cells (no raw newlines, escape pipes)
            def sanitize_cell(text):
                if not text: return ""
                # Replace newlines with <br> to keep table grid intact
                text = text.replace('\n', '<br>')
                # Escape pipes to avoid breaking table structure
                text = text.replace('|', '\\|')
                return text.strip()

            # DEEP DIVE: No truncation - allow full exhaustive content
            facts = sanitize_cell(case.get('facts', ''))
            issues = sanitize_cell(case.get('issues', ''))
            excerpt = f"\"{sanitize_cell(case.get('excerpt', ''))}\"" if case.get('excerpt') else ''
            remarks = sanitize_cell(case.get('remarks', ''))
            
            output += f"| {case.get('no', '')} | {authority} | {facts} | {issues} | {excerpt} | {remarks} |\n"
        
        output += "\n## PART C — DOCTRINAL SYNTHESIS\n\n"
        synthesis = data.get('doctrinal_synthesis', {})
        output += "**Settled Legal Principles:**\n"
        for i, principle in enumerate(synthesis.get('settled_principles', []), 1):
            output += f"{i}. {principle}\n"
        
        output += "\n**Doctrinal Distinctions:**\n"
        distinctions = synthesis.get('distinctions', {})
        for key, value in distinctions.items():
            output += f"- {key.replace('_', ' ').title()}: {value}\n"
        
        if synthesis.get('doctrinal_development'):
            output += f"\n**Historical Development:**\n{synthesis.get('doctrinal_development')}\n"
        
        output += "\n## PART D — APPLICATION TO THE PRESENT QUERY\n\n"
        application = data.get('application', {})
        output += f"**Legal Characterization:**\n{application.get('legal_characterization', 'Not specified')}\n\n"
        output += f"**Available Remedies:**\n"
        for remedy in application.get('available_remedies', []):
            output += f"- {remedy}\n"
        output += f"\n**Barred Remedies:**\n"
        for remedy in application.get('barred_remedies', []):
            output += f"- {remedy}\n"
        
        # NEW: Strategic Recommendations (from Deep Dive prompt)
        strategic_recs = application.get('strategic_recommendations', [])
        if strategic_recs:
            output += f"\n**Strategic Recommendations:**\n"
            for rec in strategic_recs:
                output += f"- {rec}\n"
        
        output += f"\n**Conclusion:**\n{application.get('conclusion', '')}\n"
        
        output += "\n## PART E — PUBLIC IMPORTANCE / LITIGATION VALUE\n\n"
        importance = data.get('public_importance', {})
        if importance.get('novel_aspects'):
            output += f"**Novel Aspects:** {importance.get('novel_aspects')}\n\n"
        if importance.get('appellate_value'):
            output += f"**Appellate Value:** {importance.get('appellate_value')}\n\n"
        if importance.get('significance'):
            output += f"**Significance:** {importance.get('significance')}\n"
        
        return output
    
    async def _generate_simple_analysis(self, issue: Dict, cases: List, matter: Dict) -> str:
        """Fallback simple analysis if JSON parsing fails."""
        prompt = f"""Analyze this legal issue with proper table format:

ISSUE: {issue.get('title')}
CASES: {', '.join([c.get('citation', '') for c in cases[:3]])}

Create analysis with this structure:
## PART A — ISSUE FRAMING
[2-3 paragraphs]

## PART B — CASE LAW TABLE
| No. | Authority | Facts | Issues | Excerpt | Remarks |
|-----|-----------|-------|--------|---------|---------|
[Fill in rows for each case]

## PART C — SYNTHESIS
[Principles and distinctions]

## PART D — APPLICATION
[Application to facts]

## PART E — IMPORTANCE
[If applicable]"""
        
        return await self.llm.generate(prompt, max_tokens=6000)
    
    
    async def _verify_analysis(self, data: Dict[str, Any], sources: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Verify generated case analysis against source text to prevent hallucinations."""
        
        cases_analysis = data.get("case_analysis", [])
        if not cases_analysis:
            return data
            
        async def verify_single_case(case_data):
            # Find matching source case
            source = next((s for s in sources if s.get("citation") == case_data.get("citation") or s.get("title") == case_data.get("case_name")), None)
            
            if not source:
                return case_data # Cannot verify without source
                
            # Prepare verification context
            verification_text = source.get("judgment_headnotes") or source.get("summary") or source.get("full_judgment", "")[:3000]
            if not verification_text:
                return case_data
                
            prompt = f"""Verify the accuracy of this generated case analysis against the source text.
            
            SOURCE TEXT (HEADNOTES/SUMMARY):
            {verification_text[:4000]}
            
            GENERATED ANALYSIS:
            Facts: {case_data.get('facts')}
            Ratio: {case_data.get('excerpt')}
            
            TASK:
            1. Check if the Facts in the generated analysis are supported by the Source Text.
            2. Check if the Ratio is accurate.
            
            If the analysis is ACCURATE, return generic string "PASS".
            If there are hallucinations or errors, return the CORRECTED JSON object for this case (fields: no, case_name, citation, court, facts, issues, excerpt, remarks).
            """
            
            try:
                response = await self.llm.generate(prompt, max_tokens=1000, temperature=0.3)
                if "PASS" in response:
                    return case_data
                
                # Try to parse corrected JSON
                import re
                match = re.search(r'\{.*\}', response, re.DOTALL)
                if match:
                    corrected = json.loads(match.group(0))
                    # Merge to preserve fields not returned
                    merged = {**case_data, **corrected}
                    return merged
            except Exception as e:
                logger.warning(f"Verification failed for {case_data.get('citation')}: {e}")
                
            return case_data

        # Run verification in parallel
        tasks = [verify_single_case(c) for c in cases_analysis]
        verified_cases = await asyncio.gather(*tasks)
        
        # Update data with verified cases
        data["case_analysis"] = verified_cases
        return data

    def _format_cases_for_doctrinal_prompt(self, cases: List[Dict[str, Any]]) -> str:
        """Format cases comprehensively for doctrinal research."""
        formatted = []
        for i, case in enumerate(cases, 1):
            case_text = f"""{i}. {case.get('citation', 'Unknown Citation')}
   Court: {case.get('court', 'Not specified')}
   Facts: {case.get('headnote_en', case.get('summary', 'No summary available'))[:400]}
   Legal Areas: {', '.join(case.get('subject_areas', ['General']))}
"""
            formatted.append(case_text)
        return "\n".join(formatted)
    
    def _format_cases_with_full_judgments(self, cases: List[Dict[str, Any]]) -> str:
        """
        Format cases WITH full judgment text for comprehensive doctrinal analysis.
        If full judgment not available, falls back to summary.
        """
        formatted = []
        for i, case in enumerate(cases, 1):
            citation = case.get('citation', 'Unknown Citation')
            court = case.get('court', 'Not specified')
            
            # Check if we have full judgment
            full_judgment = case.get('full_judgment', '')
            has_full_judgment = bool(full_judgment and len(full_judgment) > 500)
            
            if has_full_judgment:
                word_count = case.get('judgment_word_count', len(full_judgment.split()))
                
                # Include structured sections if available
                headnotes = case.get('judgment_headnotes', '')
                facts = case.get('judgment_facts', '')
                reasoning = case.get('judgment_reasoning', '')
                
                case_text = f"""
═══════════════════════════════════════════════════
CASE {i}: {citation} - {court}
Word Count: {word_count:,} words (COMPLETE JUDGMENT)
═══════════════════════════════════════════════════

"""
                
                if headnotes:
                    case_text += f"""HEADNOTES:
{headnotes[:2000]}

"""
                
                if facts:
                    case_text += f"""FACTS (Extracted):
{facts[:3000]}

"""
                
                if reasoning:
                    case_text += f"""JUDGE'S REASONING (Extracted):
{reasoning[:10000]}

"""
                else:
                    # Use first portion of full judgment
                    case_text += f"""FULL JUDGMENT TEXT:
{full_judgment[:15000]}
[...judgment continues for {word_count:,} total words]

"""
                
                case_text += "═══════════════════════════════════════════════════\n"
                
            else:
                # Fallback to summary if full judgment not available
                summary = case.get('headnote_en', case.get('summary', 'No summary available'))
                case_text = f"""
Case {i}: {citation} - {court}
Summary: {summary[:500]}
[Note: Full judgment not available, using summary only]

"""
            
            formatted.append(case_text)
        
        return "\n".join(formatted)
    
    def _format_cases_for_prompt(self, cases: List[Dict[str, Any]]) -> str:
        """Format cases for LLM prompt."""
        formatted = []
        for case in cases:
            formatted.append(
                f"- {case['citation']}: {case.get('headnote_en', '')[:200]}"
            )
        return "\n".join(formatted)
    
    def _compile_memo_en(self, arguments: List[Dict[str, Any]], matter: Dict[str, Any], kb_data: Dict[str, Any] = None) -> str:
        """Compile English doctrinal research memo with KB insights."""
        
        if kb_data is None:
            kb_data = {}
        
        # Check if any arguments used full judgments
        full_judgment_count = sum(1 for arg in arguments if arg.get('used_full_judgments', False))
        total_words = sum(arg.get('total_judgment_words', 0) for arg in arguments)
        
        memo = f"""# DOCTRINAL LEGAL RESEARCH MEMORANDUM

**Matter:** {matter.get('title', 'Untitled')}  
**Date:** {matter.get('created_at', 'N/A')}  
**Researcher:** Senior Appellate Legal Research Team  
**Format:** Doctrinal Case-Law Driven Analysis
"""
        
        if full_judgment_count > 0:
            memo += f"""
**🎯 Research Quality:** ENHANCED - Analyzed {full_judgment_count} complete court judgments ({total_words:,} words)
"""
        
        # ⭐ PHASE 2: Add KB insights indicator
        if kb_data.get("kb_available"):
            similar_count = kb_data.get("similar_matters_count", 0)
            memo += f"""
**📚 Knowledge Base:** ACTIVE - {similar_count} similar historical matters analyzed for strategic insights
"""
        
        memo += "\n---\n\n"
        
        # ⭐ PHASE 2: Include KB insights section BEFORE issues
        if kb_data.get("kb_available"):
            from services.kb_enrichment_service import get_kb_enrichment_service
            kb_service = get_kb_enrichment_service()
            kb_section = kb_service.format_kb_insights_for_memo(kb_data)
            memo += kb_section
        
        # Original issues analysis
        for i, arg in enumerate(arguments, 1):
            memo += f"""
# ISSUE {i}: {arg['issue_title']}

{arg['analysis_en']}

---

**Total Cases Analyzed:** {len(arg['cases_cited'])}  
**Cases Cited:** {', '.join(arg['cases_cited'][:5])}{'...' if len(arg['cases_cited']) > 5 else ''}

**Suggested Counsel Wording:**  
{arg['suggested_wording_en']}

---

"""
        
        memo += f"""
## OVERALL RESEARCH SUMMARY

- **Total Issues Analyzed:** {len(arguments)}
- **Total Authorities Reviewed:** {sum(len(arg['cases_cited']) for arg in arguments)}
- **Primary Jurisdiction:** Malaysian Law
- **Comparative Jurisdictions:** UK, Canada, Commonwealth
"""
        
        if full_judgment_count > 0:
            memo += f"""
- **✨ Full Judgments Analyzed:** {full_judgment_count} complete court decisions
- **📝 Total Judgment Content:** {total_words:,} words from primary sources
"""
        
        if kb_data.get("kb_available"):
            similar_count = kb_data.get("similar_matters_count", 0)
            memo += f"""
- **📚 Knowledge Base Insights:** {similar_count} similar historical matters analyzed
- **🎯 Strategic Enhancement:** Outcome predictions and risk analysis included
"""
        
        memo += """
---

*This memorandum follows doctrinal legal research methodology suitable for court filings, legal opinions, and appellate submissions.*
"""
        
        return memo
    
    def _compile_memo_ms(self, arguments: List[Dict[str, Any]], matter: Dict[str, Any], kb_data: Dict[str, Any] = None) -> str:
        """Compile Malay issue memo with KB insights."""
        
        if kb_data is None:
            kb_data = {}
        
        memo = f"""MEMO ISU UNDANG-UNDANG

Perkara: {matter.get('title', 'Tanpa Tajuk')}
Tarikh: {matter.get('created_at', 'T/A')}
"""
        
        # KB insights indicator
        if kb_data.get("kb_available"):
            similar_count = kb_data.get("similar_matters_count", 0)
            memo += f"""
**📚 Pangkalan Pengetahuan:** {similar_count} kes sejarah yang serupa dianalisis

---
"""
        
        memo += "\n"
        
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


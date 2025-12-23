"""
Consistency & Translation QA Agent - Verifies alignment between Malay and English pleadings.
"""
from agents.base_agent import BaseAgent
from typing import Dict, Any, List
import re


class ConsistencyQAAgent(BaseAgent):
    """
    Perform segment-by-segment alignment check and flag discrepancies.
    
    Checks:
    - No missing paragraphs
    - Defined terms match exactly
    - Dates/sums match
    - Citations identical
    
    Inputs:
    - pleading_ms: Malay pleading text
    - pleading_en: English pleading text
    - parallel_translations: original parallel pairs from translation agent
    
    Outputs:
    - consistency_report: list of issues with severity
    - block_for_human: true if high severity issues found
    """
    
    def __init__(self):
        super().__init__(agent_id="ConsistencyQA")
    
    async def process(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process consistency QA.
        
        Args:
            inputs: {
                "pleading_ms": str,
                "pleading_en": str,
                "aligned_pairs": List[Dict] (optional)
            }
            
        Returns:
            {
                "consistency_report": List[Dict],
                "block_for_human": bool,
                "passed_checks": int,
                "failed_checks": int
            }
        """
        await self.validate_input(inputs, ["pleading_ms", "pleading_en"])
        
        pleading_ms = inputs["pleading_ms"]
        pleading_en = inputs["pleading_en"]
        aligned_pairs = inputs.get("aligned_pairs", [])
        
        issues = []
        
        # Check 1: Missing paragraphs
        missing_para_issues = self._check_missing_paragraphs(pleading_ms, pleading_en)
        issues.extend(missing_para_issues)
        
        # Check 2: Defined terms consistency
        term_issues = self._check_defined_terms(pleading_ms, pleading_en)
        issues.extend(term_issues)
        
        # Check 3: Dates and sums matching
        number_issues = self._check_numbers_and_dates(pleading_ms, pleading_en)
        issues.extend(number_issues)
        
        # Check 4: Citations matching
        citation_issues = self._check_citations(pleading_ms, pleading_en)
        issues.extend(citation_issues)
        
        # Check 5: Paragraph alignment (if aligned_pairs provided)
        if aligned_pairs:
            alignment_issues = self._check_alignment_quality(aligned_pairs)
            issues.extend(alignment_issues)
        
        # Categorize by severity
        high_severity = [i for i in issues if i.get("severity") == "high"]
        medium_severity = [i for i in issues if i.get("severity") == "medium"]
        low_severity = [i for i in issues if i.get("severity") == "low"]
        
        block_for_human = len(high_severity) > 0
        
        passed_checks = 5 - len(set(i.get("check_type") for i in issues))
        failed_checks = len(set(i.get("check_type") for i in issues))
        
        return self.format_output(
            data={
                "consistency_report": {
                    "all_issues": issues,
                    "high_severity": high_severity,
                    "medium_severity": medium_severity,
                    "low_severity": low_severity,
                    "total_issues": len(issues)
                },
                "block_for_human": block_for_human,
                "passed_checks": passed_checks,
                "failed_checks": failed_checks,
                "fix_suggestions": self._generate_fix_suggestions(issues)
            },
            confidence=0.92,
            human_review_required=block_for_human
        )
    
    def _check_missing_paragraphs(self, ms_text: str, en_text: str) -> List[Dict[str, Any]]:
        """Check for missing paragraphs between versions."""
        
        ms_para_nums = set(re.findall(r'^(\d+)\.', ms_text, re.MULTILINE))
        en_para_nums = set(re.findall(r'^(\d+)\.', en_text, re.MULTILINE))
        
        issues = []
        
        missing_in_en = ms_para_nums - en_para_nums
        missing_in_ms = en_para_nums - ms_para_nums
        
        if missing_in_en:
            issues.append({
                "check_type": "missing_paragraphs",
                "severity": "high",
                "description": f"Paragraphs {', '.join(sorted(missing_in_en))} present in Malay but missing in English",
                "affected_paragraphs": list(missing_in_en)
            })
        
        if missing_in_ms:
            issues.append({
                "check_type": "missing_paragraphs",
                "severity": "high",
                "description": f"Paragraphs {', '.join(sorted(missing_in_ms))} present in English but missing in Malay",
                "affected_paragraphs": list(missing_in_ms)
            })
        
        return issues
    
    def _check_defined_terms(self, ms_text: str, en_text: str) -> List[Dict[str, Any]]:
        """Check that defined terms are consistent."""
        
        issues = []
        
        # Check PLAINTIF/PLAINTIFF
        ms_plaintif_count = len(re.findall(r'\bPLAINTIF\b', ms_text))
        en_plaintiff_count = len(re.findall(r'\bPLAINTIFF\b', en_text))
        
        if ms_plaintif_count != en_plaintiff_count:
            issues.append({
                "check_type": "defined_terms",
                "severity": "medium",
                "description": f"PLAINTIF appears {ms_plaintif_count} times in Malay but PLAINTIFF appears {en_plaintiff_count} times in English",
                "term": "PLAINTIFF/PLAINTIF"
            })
        
        # Check DEFENDAN/DEFENDANT
        ms_defendan_count = len(re.findall(r'\bDEFENDAN\b', ms_text))
        en_defendant_count = len(re.findall(r'\bDEFENDANT\b', en_text))
        
        if ms_defendan_count != en_defendant_count:
            issues.append({
                "check_type": "defined_terms",
                "severity": "medium",
                "description": f"DEFENDAN appears {ms_defendan_count} times in Malay but DEFENDANT appears {en_defendant_count} times in English",
                "term": "DEFENDANT/DEFENDAN"
            })
        
        return issues
    
    def _check_numbers_and_dates(self, ms_text: str, en_text: str) -> List[Dict[str, Any]]:
        """Check that numbers and dates match exactly."""
        
        issues = []
        
        # Extract all numbers
        ms_numbers = re.findall(r'\b\d+(?:[.,]\d+)*\b', ms_text)
        en_numbers = re.findall(r'\b\d+(?:[.,]\d+)*\b', en_text)
        
        # Normalize (remove commas)
        ms_numbers_norm = [n.replace(',', '') for n in ms_numbers]
        en_numbers_norm = [n.replace(',', '') for n in en_numbers]
        
        ms_set = set(ms_numbers_norm)
        en_set = set(en_numbers_norm)
        
        missing_in_en = ms_set - en_set
        missing_in_ms = en_set - ms_set
        
        if missing_in_en:
            issues.append({
                "check_type": "numbers_dates",
                "severity": "high",
                "description": f"Numbers {', '.join(sorted(missing_in_en))} in Malay not found in English",
                "missing_numbers": list(missing_in_en)
            })
        
        if missing_in_ms:
            issues.append({
                "check_type": "numbers_dates",
                "severity": "high",
                "description": f"Numbers {', '.join(sorted(missing_in_ms))} in English not found in Malay",
                "missing_numbers": list(missing_in_ms)
            })
        
        # Check date formats
        ms_dates = re.findall(r'\d{1,2}[/-]\d{1,2}[/-]\d{4}', ms_text)
        en_dates = re.findall(r'\d{1,2}[/-]\d{1,2}[/-]\d{4}', en_text)
        
        if len(ms_dates) != len(en_dates):
            issues.append({
                "check_type": "numbers_dates",
                "severity": "medium",
                "description": f"Date count mismatch: {len(ms_dates)} in Malay, {len(en_dates)} in English",
                "ms_dates": ms_dates,
                "en_dates": en_dates
            })
        
        return issues
    
    def _check_citations(self, ms_text: str, en_text: str) -> List[Dict[str, Any]]:
        """Check that legal citations are identical."""
        
        issues = []
        
        # Extract citations (e.g., [2019] 2 MLJ 345)
        citation_pattern = r'\[\d{4}\]\s+\d+\s+[A-Z]+\s+\d+'
        
        ms_citations = re.findall(citation_pattern, ms_text)
        en_citations = re.findall(citation_pattern, en_text)
        
        ms_set = set(ms_citations)
        en_set = set(en_citations)
        
        if ms_set != en_set:
            missing_in_en = ms_set - en_set
            missing_in_ms = en_set - ms_set
            
            if missing_in_en or missing_in_ms:
                issues.append({
                    "check_type": "citations",
                    "severity": "high",
                    "description": "Citation mismatch between Malay and English versions",
                    "ms_citations": list(ms_set),
                    "en_citations": list(en_set)
                })
        
        return issues
    
    def _check_alignment_quality(self, aligned_pairs: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Check quality of paragraph alignment."""
        
        issues = []
        
        for pair in aligned_pairs:
            alignment_score = pair.get("alignment_score", 1.0)
            
            if alignment_score < 0.6:
                issues.append({
                    "check_type": "alignment_quality",
                    "severity": "high",
                    "description": f"Paragraph {pair.get('para_num')} has very low alignment score",
                    "para_num": pair.get("para_num"),
                    "alignment_score": alignment_score
                })
            elif alignment_score < 0.8:
                issues.append({
                    "check_type": "alignment_quality",
                    "severity": "medium",
                    "description": f"Paragraph {pair.get('para_num')} has low alignment score",
                    "para_num": pair.get("para_num"),
                    "alignment_score": alignment_score
                })
        
        return issues
    
    def _generate_fix_suggestions(self, issues: List[Dict[str, Any]]) -> List[str]:
        """Generate actionable fix suggestions based on issues found."""
        
        suggestions = []
        
        issue_types = set(i.get("check_type") for i in issues)
        
        if "missing_paragraphs" in issue_types:
            suggestions.append("Review paragraph numbering in both versions and ensure all paragraphs are translated")
        
        if "defined_terms" in issue_types:
            suggestions.append("Verify all defined terms (PLAINTIFF/PLAINTIF, DEFENDANT/DEFENDAN) are used consistently")
        
        if "numbers_dates" in issue_types:
            suggestions.append("Cross-check all numerical values and dates between Malay and English versions")
        
        if "citations" in issue_types:
            suggestions.append("Ensure all legal citations are identical in both versions")
        
        if "alignment_quality" in issue_types:
            suggestions.append("Review paragraphs with low alignment scores for potential meaning divergence")
        
        return suggestions

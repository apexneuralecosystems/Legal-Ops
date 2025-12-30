"""
English Companion Draft Agent - Produces English mirror of Malay pleading.
"""
from agents.base_agent import BaseAgent
from typing import Dict, Any, List
from services.llm_service import get_llm_service
import re


class EnglishCompanionAgent(BaseAgent):
    """
    Produce English mirror of Malay pleading for internal review.
    Preserve meaning and legal effect, flag divergences.
    
    Inputs:
    - pleading_ms_text: Malay pleading text
    - paragraph_map: mapping of paragraphs to sources
    
    Outputs:
    - pleading_en_text: English version
    - aligned_pairs: bilingual paragraph pairs
    - divergence_flags: paragraphs where meaning may differ
    """
    
    def __init__(self):
        super().__init__(agent_id="EnglishCompanion")
        self.llm = get_llm_service()
    
    async def process(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process English companion drafting.
        
        Args:
            inputs: {
                "pleading_ms_text": str,
                "paragraph_map": List[Dict],
                "matter_snapshot": Dict (optional)
            }
            
        Returns:
            {
                "pleading_en_text": str,
                "aligned_pairs": List[Dict],
                "divergence_flags": List[Dict]
            }
        """
        await self.validate_input(inputs, ["pleading_ms_text"])
        
        pleading_ms = inputs["pleading_ms_text"]
        paragraph_map = inputs.get("paragraph_map", [])
        matter = inputs.get("matter_snapshot", {})
        
        # Create translation prompt
        prompt = self._create_translation_prompt(pleading_ms, matter)
        
        # Call LLM with error handling
        try:
            pleading_en = await self.llm.generate(prompt)
        except Exception as e:
            print(f"Error in English companion LLM generation: {e}")
            pleading_en = f"[Drafting Error: {str(e)}]"
        
        # Post-process to ensure legal formatting
        pleading_en = self._apply_legal_formatting(pleading_en, matter)
        
        # Create aligned pairs
        aligned_pairs = self._create_aligned_pairs(pleading_ms, pleading_en)
        
        # Detect divergences
        divergence_flags = self._detect_divergences(aligned_pairs)
        
        confidence = 0.88
        
        return self.format_output(
            data={
                "pleading_en_text": pleading_en,
                "aligned_pairs": aligned_pairs,
                "divergence_flags": divergence_flags,
                "total_paragraphs": len(aligned_pairs)
            },
            confidence=confidence,
            human_review_required=len(divergence_flags) > 0
        )
    
    def _create_translation_prompt(self, pleading_ms: str, matter: Dict[str, Any]) -> str:
        """Create prompt for LLM to translate Malay pleading to English."""
        
        return f"""You are a Malaysian legal translator. Translate this Malay pleading to English.

REQUIREMENTS:
1. Preserve legal meaning and effect exactly
2. Use formal legal English register
3. Keep defined terms in UPPERCASE (PLAINTIFF, DEFENDANT)
4. Maintain paragraph numbering
5. Preserve all dates, amounts, and citations exactly
6. Use standard English legal terminology

MALAY PLEADING:
{pleading_ms}

Translate to English, maintaining the exact structure and legal effect:"""
    
    def _apply_legal_formatting(self, text: str, matter: Dict[str, Any]) -> str:
        """Apply formal legal formatting to the English draft."""
        
        # Ensure defined terms are uppercase
        text = re.sub(r'\bplaintiff\b', 'PLAINTIFF', text, flags=re.IGNORECASE)
        text = re.sub(r'\bdefendant\b', 'DEFENDANT', text, flags=re.IGNORECASE)
        
        # Add header if not present
        if not text.strip().startswith("IN THE HIGH COURT"):
            header = f"""IN THE {matter.get('court', 'HIGH COURT').upper()}

{matter.get('title', 'CASE TITLE')}

STATEMENT OF CLAIM

"""
            text = header + text
        
        return text
    
    def _create_aligned_pairs(
        self,
        pleading_ms: str,
        pleading_en: str
    ) -> List[Dict[str, Any]]:
        """Create paragraph-level alignment between Malay and English."""
        
        # Extract numbered paragraphs from both versions
        ms_paras = re.findall(r'(\d+)\.\s+([^\n]+(?:\n(?!\d+\.)[^\n]+)*)', pleading_ms)
        en_paras = re.findall(r'(\d+)\.\s+([^\n]+(?:\n(?!\d+\.)[^\n]+)*)', pleading_en)
        
        aligned_pairs = []
        
        # Align by paragraph number
        for (ms_num, ms_text), (en_num, en_text) in zip(ms_paras, en_paras):
            if ms_num == en_num:
                aligned_pairs.append({
                    "para_num": ms_num,
                    "text_ms": ms_text.strip(),
                    "text_en": en_text.strip(),
                    "alignment_score": self._calculate_alignment(ms_text, en_text)
                })
        
        return aligned_pairs
    
    def _calculate_alignment(self, ms_text: str, en_text: str) -> float:
        """Calculate alignment score between Malay and English paragraphs."""
        
        # Extract numbers from both texts
        ms_numbers = set(re.findall(r'\d+', ms_text))
        en_numbers = set(re.findall(r'\d+', en_text))
        
        # Numbers must match exactly
        if ms_numbers != en_numbers:
            return 0.6
        
        # Length ratio
        ms_words = len(ms_text.split())
        en_words = len(en_text.split())
        
        if ms_words == 0 or en_words == 0:
            return 0.5
        
        length_ratio = min(ms_words, en_words) / max(ms_words, en_words)
        
        return round((length_ratio * 0.7) + 0.3, 2)
    
    def _detect_divergences(self, aligned_pairs: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Detect paragraphs where Malay and English may diverge in meaning."""
        
        divergences = []
        
        for pair in aligned_pairs:
            alignment_score = pair.get("alignment_score", 1.0)
            
            # Flag if alignment score is low
            if alignment_score < 0.7:
                divergences.append({
                    "para_num": pair["para_num"],
                    "reason": "Low alignment score - possible meaning divergence",
                    "alignment_score": alignment_score,
                    "severity": "high" if alignment_score < 0.5 else "medium"
                })
            
            # Check for missing numbers
            ms_numbers = set(re.findall(r'\d+', pair["text_ms"]))
            en_numbers = set(re.findall(r'\d+', pair["text_en"]))
            
            if ms_numbers != en_numbers:
                divergences.append({
                    "para_num": pair["para_num"],
                    "reason": "Number mismatch between Malay and English",
                    "ms_numbers": list(ms_numbers),
                    "en_numbers": list(en_numbers),
                    "severity": "high"
                })
        
        return divergences
    


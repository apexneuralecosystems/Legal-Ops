"""
Malay Drafting Agent - Generates formal legal Malay pleadings.
"""
from agents.base_agent import BaseAgent
from typing import Dict, Any, List
from services.llm_service import get_llm_service
import re


class MalayDraftingAgent(BaseAgent):
    """
    Drafts pleadings in Malay using templates and facts.
    
    Inputs:
    - matter_snapshot: structured case information
    - template_id: pleading template to use
    - issues_selected: list of issues to include
    - prayers_selected: list of prayers to include
    
    Outputs:
    - pleading_ms_text: full Malay pleading
    - paragraph_map: mapping of paragraphs to source segments
    """
    
    def __init__(self):
        super().__init__(agent_id="MalayDrafting")
        self.llm = get_llm_service()
    
    async def process(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process Malay drafting request.
        
        Args:
            inputs: {
                "matter_snapshot": Dict,
                "template_id": str,
                "issues_selected": List[Dict],
                "prayers_selected": List[Dict]
            }
            
        Returns:
            {
                "pleading_ms_text": str,
                "paragraph_map": List[Dict],
                "confidence": float
            }
        """
        await self.validate_input(inputs, ["matter_snapshot"])
        
        matter = inputs["matter_snapshot"]
        template_id = inputs.get("template_id", "TPL-HighCourt-MS-v2")
        issues = inputs.get("issues_selected", [])
        prayers = inputs.get("prayers_selected", [])
        language = inputs.get("language", "ms")  # Default to Malay
        
        # Create drafting prompt based on language
        if language == "en" or "EN" in template_id:
            # Generate English pleading directly
            prompt = self._create_drafting_prompt(matter, template_id, issues, prayers, language="en")
        else:
            # Generate Malay pleading
            prompt = self._create_drafting_prompt(matter, template_id, issues, prayers, language="ms")
        
        # Call LLM directly - with error handling
        try:
            pleading_text = await self.llm.generate(prompt)
        except Exception as e:
            print(f"Error in Malay drafting LLM generation: {e}")
            # Return partial error result instead of 500
            return {
                "status": "partial_error",
                "data": {
                    "pleading_ms_text": f"Error generating draft: {str(e)}. Please retry or edit manually.",
                    "paragraph_map": [],
                    "confidence": 0.0
                },
                "metadata": self.create_metadata(),
                "human_review_required": True
            }
        
        # Post-process to ensure formal legal register
        pleading_text = self._apply_legal_formatting(pleading_text, matter)
        
        # Create paragraph map
        paragraph_map = self._create_paragraph_map(pleading_text, matter)
        
        confidence = 0.92
        
        return self.format_output(
            data={
                "pleading_ms_text": pleading_text,
                "paragraph_map": paragraph_map,
                "confidence": confidence
            },
            confidence=confidence,
            human_review_required=confidence < 0.8
        )
    
    def _create_drafting_prompt(
        self,
        matter: Dict[str, Any],
        template_id: str,
        issues: List[Dict],
        prayers: List[Dict],
        language: str = "ms"
    ) -> str:
        """Create prompt for LLM drafting in specified language."""
        
        parties_str = "\n".join([
            f"- {p['role'].upper()}: {p['name']}"
            for p in matter.get("parties", [])
        ])
        
        issues_str = "\n".join([
            f"{i+1}. {issue.get('text_ms', issue.get('text_en', ''))}"
            for i, issue in enumerate(issues)
        ])
        
        prayers_str = "\n".join([
            f"{i+1}. {prayer.get('text', '')}"
            for i, prayer in enumerate(prayers)
        ])
        
        return f"""Anda adalah peguam Malaysia yang mahir. Draf satu pernyataan tuntutan (Statement of Claim) dalam Bahasa Melayu formal untuk kes berikut:

MAKLUMAT KES:
Tajuk: {matter.get('title', 'Kes Tidak Dinamakan')}
Mahkamah: {matter.get('court', 'Mahkamah Tinggi Malaya')}
Jenis Kes: {matter.get('case_type', 'am')}

PIHAK-PIHAK:
{parties_str}

ISU-ISU UNDANG-UNDANG:
{issues_str}

REMEDI YANG DIMINTA:
{prayers_str}

ARAHAN:
1. Gunakan format formal Bahasa Melayu undang-undang Malaysia
2. Gunakan istilah yang betul: PLAINTIF, DEFENDAN (huruf besar)
3. Nombor perenggan dengan angka Arab (1., 2., 3., dll.)
4. Pastikan semua tarikh dan nombor tepat seperti dalam maklumat kes
5. Gunakan struktur standard: Pengenalan → Fakta → Pelanggaran → Remedi → Doa
6. Gunakan bahasa formal seperti "Tertuduh", "Plaintif dengan hormatnya menyatakan"

Draf pernyataan tuntutan lengkap dalam Bahasa Melayu:"""
    
    def _apply_legal_formatting(self, text: str, matter: Dict[str, Any]) -> str:
        """Apply formal legal formatting to the draft."""
        
        # Ensure defined terms are uppercase
        text = re.sub(r'\bplaintif\b', 'PLAINTIF', text, flags=re.IGNORECASE)
        text = re.sub(r'\bdefendan\b', 'DEFENDAN', text, flags=re.IGNORECASE)
        
        # Add header if not present
        if not text.strip().startswith("DALAM MAHKAMAH"):
            header = f"""DALAM MAHKAMAH {matter.get('court', 'TINGGI MALAYA').upper()}

{matter.get('title', 'KES TIDAK DINAMAKAN')}

PERNYATAAN TUNTUTAN

"""
            text = header + text
        
        return text
    
    def _create_paragraph_map(
        self,
        pleading_text: str,
        matter: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Create mapping of paragraphs to source references."""
        
        paragraph_map = []
        
        # Split into numbered paragraphs
        paragraphs = re.findall(r'(\d+)\.\s+([^\n]+(?:\n(?!\d+\.)[^\n]+)*)', pleading_text)
        
        for para_num, para_text in paragraphs:
            paragraph_map.append({
                "para_id": f"p{para_num}",
                "text": para_text.strip(),
                "source_refs": [
                    {
                        "doc_id": "matter_snapshot",
                        "segment_id": None
                    }
                ],
                "confidence": 0.9
            })
        
        return paragraph_map
    


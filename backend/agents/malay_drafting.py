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
        
        # Handle issues text based on language preference
        issues_str = ""
        for i, issue in enumerate(issues):
            text = ""
            if language == "en":
                text = issue.get('text_en', issue.get('text_ms', issue.get('title', '')))
            else:
                text = issue.get('text_ms', issue.get('text_en', issue.get('title', '')))
            issues_str += f"{i+1}. {text}\n"
        
        # Handle prayers text based on language preference
        prayers_str = ""
        for i, prayer in enumerate(prayers):
            text = ""
            if language == "en":
                text = prayer.get('text_en', prayer.get('text_ms', prayer.get('text', '')))
            else:
                text = prayer.get('text_ms', prayer.get('text_en', prayer.get('text', '')))
            prayers_str += f"{i+1}. {text}\n"
        
        if language == "en":
            return f"""You are an expert Malaysian lawyer. Draft a Statement of Claim in formal legal English for the following case:

CASE INFORMATION:
Title: {matter.get('title', 'Unnamed Case')}
Court: {matter.get('court', 'High Court of Malaya')}
Case Type: {matter.get('case_type', 'general')}

PARTIES:
{parties_str}

LEGAL ISSUES:
{issues_str}

PRAYERS (REMEDIES SOUGHT):
{prayers_str}

INSTRUCTIONS:
1. Use formal Malaysian legal English format
2. Use correct terms: PLAINTIFF, DEFENDANT (uppercase)
3. Number paragraphs with Arabic numerals (1., 2., 3., etc.)
4. Ensure all dates and numbers are accurate as per case info
5. Use standard structure: Introduction → Facts → Breach → Remedy → Prayer
6. Use formal language like "The Plaintiff humbly submits", "WHEREFORE the Plaintiff prays"

Draft the complete Statement of Claim in English:"""
        else:
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
        text = re.sub(r'\bplaintiff\b', 'PLAINTIFF', text, flags=re.IGNORECASE)
        text = re.sub(r'\bdefendant\b', 'DEFENDANT', text, flags=re.IGNORECASE)
        
        # Check language based on content (simple heuristic)
        is_english = "statement of claim" in text.lower() or "plaintiff" in text.lower()
        
        # Add header if not present
        if not text.strip().upper().startswith("IN THE") and not text.strip().upper().startswith("DALAM"):
            
            if is_english:
                court_default = 'HIGH COURT OF MALAYA'
                title_default = 'UNNAMED CASE'
            else:
                court_default = 'TINGGI MALAYA'
                title_default = 'KES TIDAK DINAMAKAN'
                
            court_name = matter.get('court', court_default).upper()
            
            # If court name is Malay but we drafting in English, try to translate common terms (simple heuristic)
            if is_english and "TINGGI" in court_name:
                court_name = court_name.replace("MAHKAMAH", "COURT").replace("TINGGI", "HIGH").replace("MALAYA", "OF MALAYA")
                
            title = matter.get('title', title_default)
            
            if is_english:
                header = f"""IN THE {court_name}

{title}

STATEMENT OF CLAIM

"""
            else:
                header = f"""DALAM MAHKAMAH {court_name}

{title}

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
    


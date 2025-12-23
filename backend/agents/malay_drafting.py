"""
Malay Drafting Agent - Generates formal legal Malay pleadings.
"""
from agents.base_agent import BaseAgent
from typing import Dict, Any, List
import google.generativeai as genai
from config import settings
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
        genai.configure(api_key=settings.GEMINI_API_KEY)
        self.model = genai.GenerativeModel(settings.GEMINI_MODEL)
    
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
        
        # Create drafting prompt
        prompt = self._create_drafting_prompt(matter, template_id, issues, prayers)
        
        try:
            response = await self.model.generate_content_async(prompt)
            pleading_text = response.text
            
            # Post-process to ensure formal legal register
            pleading_text = self._apply_legal_formatting(pleading_text, matter)
            
            # Create paragraph map
            paragraph_map = self._create_paragraph_map(pleading_text, matter)
            
            confidence = 0.92
            
        except Exception as e:
            print(f"Drafting error: {e}")
            pleading_text = self._generate_fallback_pleading(matter, issues, prayers)
            paragraph_map = []
            confidence = 0.5
        
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
        prayers: List[Dict]
    ) -> str:
        """Create prompt for LLM drafting."""
        
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
    
    def _generate_fallback_pleading(
        self,
        matter: Dict[str, Any],
        issues: List[Dict],
        prayers: List[Dict]
    ) -> str:
        """Generate basic fallback pleading with clear placeholders for human input."""
        
        parties = matter.get("parties", [])
        plaintiff = next((p for p in parties if p["role"] == "plaintiff"), {"name": "[NAMA PLAINTIF]"})
        defendant = next((p for p in parties if p["role"] == "defendant"), {"name": "[NAMA DEFENDAN]"})
        
        # Get plaintiff and defendant names, clean up placeholder brackets if present
        plaintiff_name = plaintiff.get("name", "[NAMA PLAINTIF]")
        defendant_name = defendant.get("name", "[NAMA DEFENDAN]")
        
        # Build issues section
        issues_text = ""
        for i, issue in enumerate(issues, 3):
            issue_title = issue.get("title", issue.get("text_ms", "[Isu undang-undang]"))
            issues_text += f"""
{i}. **Isu: {issue_title}**
   [Butiran fakta-fakta kes akan dimasukkan di sini. Berdasarkan maklumat yang diberikan, fakta-fakta adalah tidak lengkap. Oleh itu, perenggan ini dibiarkan kosong dan perlu diisi dengan fakta-fakta yang relevan dengan kes.]
"""
        
        # Build prayers section
        prayers_text = ""
        for i, prayer in enumerate(prayers, 1):
            prayer_ms = prayer.get("text_ms", prayer.get("text", "[Relief yang dipohon]"))
            prayers_text += f"   ({chr(96+i)}) {prayer_ms}\n"
        
        if not prayers_text:
            prayers_text = """   (a) [Penghakiman untuk jumlah RM ______ ]
   (b) [Faedah pada kadar ____% setahun]
   (c) Kos dan apa-apa relief lain yang Mahkamah fikirkan sesuai"""

        return f"""**DALAM MAHKAMAH {matter.get('court', 'TINGGI MALAYA').upper()}**

**PERMOHONAN NO: [Ruang untuk diisi oleh Pendaftar Mahkamah]**

**ANTARA**

**PLAINTIF**

**DAN**

**DEFENDAN**

**PERNYATAAN TUNTUTAN**

1.  **Pengenalan**

    PLAINTIF dengan hormatnya menyatakan perkara-perkara berikut kepada Mahkamah Yang Mulia ini:

    1.1 PLAINTIF ialah pihak yang memulakan prosiding.
    
    1.2 DEFENDAN ialah pihak yang didakwa telah melakukan atau tidak melakukan penyerahan kepada pemegang serah hak.

2.  **Fakta-Fakta**

    2.1 [Butiran fakta-fakta kes akan dimasukkan di sini. Berdasarkan maklumat yang diberikan, fakta-fakta adalah tidak lengkap. Oleh itu, perenggan ini dibiarkan kosong dan perlu diisi dengan fakta-fakta yang relevan dengan kes.]
{issues_text}
**DOA**

Dengan yang demikian, PLAINTIF memohon Mahkamah Yang Mulia ini memberikan:

{prayers_text}

Bertarikh pada [TARIKH] ini.

______________________
Peguam Cara bagi PLAINTIF
"""

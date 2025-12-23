"""
Template & Compliance Agent - Chooses correct pleading template and ensures language compliance.
"""
from agents.base_agent import BaseAgent
from typing import Dict, Any, List


class TemplateComplianceAgent(BaseAgent):
    """
    Choose correct pleading template based on court level and geography.
    Ensure language compliance (Malay for West Malaysia, English for East Malaysia).
    
    Inputs:
    - jurisdiction: Peninsular Malaysia or East Malaysia
    - matter_type: contract, tort, criminal, etc.
    - court: High Court, Sessions Court, etc.
    
    Outputs:
    - template: {primary_language, sections_order, mandatory_clauses, citation_format}
    """
    
    def __init__(self):
        super().__init__(agent_id="TemplateCompliance")
        
        # Template registry
        self.templates = {
            "TPL-HighCourt-MS-v2": {
                "name": "High Court Malay Statement of Claim",
                "court_level": "High Court",
                "jurisdiction": "Peninsular Malaysia",
                "primary_language": "ms",
                "sections_order": [
                    "header",
                    "parties",
                    "facts",
                    "breach",
                    "damages",
                    "prayers",
                    "signature"
                ],
                "mandatory_clauses": [
                    "court_jurisdiction",
                    "party_identification",
                    "cause_of_action",
                    "prayers"
                ],
                "citation_format": "malaysian",
                "requires_translation_affidavit": True
            },
            "TPL-HighCourt-EN-v2": {
                "name": "High Court English Statement of Claim",
                "court_level": "High Court",
                "jurisdiction": "East Malaysia",
                "primary_language": "en",
                "sections_order": [
                    "header",
                    "parties",
                    "facts",
                    "breach",
                    "damages",
                    "prayers",
                    "signature"
                ],
                "mandatory_clauses": [
                    "court_jurisdiction",
                    "party_identification",
                    "cause_of_action",
                    "prayers"
                ],
                "citation_format": "malaysian",
                "requires_translation_affidavit": False
            },
            "TPL-SessionsCourt-MS-v1": {
                "name": "Sessions Court Malay Statement of Claim",
                "court_level": "Sessions Court",
                "jurisdiction": "Peninsular Malaysia",
                "primary_language": "ms",
                "sections_order": [
                    "header",
                    "parties",
                    "facts",
                    "prayers",
                    "signature"
                ],
                "mandatory_clauses": [
                    "party_identification",
                    "cause_of_action",
                    "prayers"
                ],
                "citation_format": "malaysian",
                "requires_translation_affidavit": True
            }
        }
    
    async def process(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process template selection and compliance check.
        
        Args:
            inputs: {
                "jurisdiction": str,
                "matter_type": str,
                "court": str,
                "override_language": str (optional)
            }
            
        Returns:
            {
                "template": Dict,
                "template_id": str,
                "compliance_warnings": List[str],
                "redlines_needed": bool
            }
        """
        await self.validate_input(inputs, ["jurisdiction", "court"])
        
        jurisdiction = inputs["jurisdiction"]
        court = inputs["court"]
        matter_type = inputs.get("matter_type", "general")
        override_language = inputs.get("override_language")
        
        # Select appropriate template
        template_id = self._select_template(jurisdiction, court, matter_type)
        template = self.templates.get(template_id, self.templates["TPL-HighCourt-MS-v2"])
        
        # Check language compliance
        compliance_warnings = []
        redlines_needed = False
        
        # West Malaysia High Court requires Malay
        if "Peninsular" in jurisdiction and "High Court" in court:
            if override_language and override_language != "ms":
                compliance_warnings.append(
                    "West Malaysia High Court requires Malay as primary filing language. "
                    "English excerpts must be accompanied by certified translation affidavit."
                )
                redlines_needed = True
        
        # East Malaysia allows English
        if "East" in jurisdiction and override_language == "ms":
            compliance_warnings.append(
                "East Malaysia courts allow English filings. Consider using English template for efficiency."
            )
        
        # Check mandatory clauses
        if not template.get("mandatory_clauses"):
            compliance_warnings.append("Template missing mandatory clause definitions")
        
        return self.format_output(
            data={
                "template_id": template_id,
                "template": template,
                "compliance_warnings": compliance_warnings,
                "redlines_needed": redlines_needed,
                "template_snippets": self._get_template_snippets(template_id)
            },
            confidence=0.95,
            human_review_required=len(compliance_warnings) > 0
        )
    
    def _select_template(self, jurisdiction: str, court: str, matter_type: str) -> str:
        """Select appropriate template based on jurisdiction and court."""
        
        # High Court templates
        if "High Court" in court:
            if "Peninsular" in jurisdiction or "West" in jurisdiction:
                return "TPL-HighCourt-MS-v2"
            else:
                return "TPL-HighCourt-EN-v2"
        
        # Sessions Court templates
        elif "Sessions Court" in court:
            return "TPL-SessionsCourt-MS-v1"
        
        # Default to High Court Malay
        return "TPL-HighCourt-MS-v2"
    
    def _get_template_snippets(self, template_id: str) -> Dict[str, str]:
        """Get template snippets for each section."""
        
        snippets = {
            "header": """DALAM MAHKAMAH TINGGI MALAYA
DI [LOKASI]

KES SIVIL NO: [NOMBOR]

ANTARA

[NAMA PLAINTIF] ... PLAINTIF

DAN

[NAMA DEFENDAN] ... DEFENDAN

PERNYATAAN TUNTUTAN""",
            
            "parties": """1. PLAINTIF ialah [nama dan alamat].

2. DEFENDAN ialah [nama dan alamat].""",
            
            "facts": """3. Pada atau sekitar [tarikh], PLAINTIF dan DEFENDAN telah membuat perjanjian [butiran perjanjian].

4. Mengikut terma-terma perjanjian tersebut, DEFENDAN bersetuju untuk [obligasi].""",
            
            "breach": """5. DEFENDAN telah melanggar perjanjian tersebut dengan [butiran pelanggaran].

6. Akibat daripada pelanggaran tersebut, PLAINTIF telah mengalami kerugian.""",
            
            "prayers": """MAKA PLAINTIF memohon:

a) Penghakiman terhadap DEFENDAN untuk jumlah [RM X];
b) Faedah mengikut kadar yang difikirkan adil oleh Mahkamah;
c) Kos;
d) Relief lain yang difikirkan adil oleh Mahkamah.

Bertarikh pada [tarikh] ini.

______________________
Peguam Cara bagi PLAINTIF"""
        }
        
        return snippets

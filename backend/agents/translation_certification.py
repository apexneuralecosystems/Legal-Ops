"""
Translation Certification Agent - Create working translations and certification checklist.
"""
from agents.base_agent import BaseAgent
from typing import Dict, Any, List
from datetime import datetime


class TranslationCertificationAgent(BaseAgent):
    """
    Create working translations and certification checklist for human certified translator.
    
    Inputs:
    - source_documents: list of documents needing certification
    - target_language: en or ms
    
    Outputs:
    - working_translation: target language version
    - certification_checklist: reminders for translator
    - affidavit_draft: template with placeholders
    """
    
    def __init__(self):
        super().__init__(agent_id="TranslationCertification")
    
    async def process(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process translation certification request.
        
        Args:
            inputs: {
                "source_documents": List[Dict],
                "target_language": str,
                "translator_name": str (optional),
                "translator_qualifications": str (optional)
            }
            
        Returns:
            {
                "working_translation": str,
                "certification_checklist": List[str],
                "affidavit_draft": str
            }
        """
        await self.validate_input(inputs, ["source_documents", "target_language"])
        
        source_docs = inputs["source_documents"]
        target_lang = inputs["target_language"]
        translator_name = inputs.get("translator_name", "[TRANSLATOR NAME]")
        translator_quals = inputs.get("translator_qualifications", "[QUALIFICATIONS]")
        
        # Create working translation summary
        working_translation = self._create_working_translation(source_docs, target_lang)
        
        # Generate certification checklist
        checklist = self._create_certification_checklist(source_docs, target_lang)
        
        # Draft affidavit
        affidavit = self._create_affidavit_draft(
            source_docs,
            target_lang,
            translator_name,
            translator_quals
        )
        
        return self.format_output(
            data={
                "working_translation": working_translation,
                "certification_checklist": checklist,
                "affidavit_draft": affidavit,
                "total_documents": len(source_docs)
            },
            confidence=0.90
        )
    
    def _create_working_translation(
        self,
        source_docs: List[Dict[str, Any]],
        target_lang: str
    ) -> str:
        """Create working translation summary."""
        
        translation = f"""WORKING TRANSLATION SUMMARY
Target Language: {target_lang.upper()}
Date: {datetime.utcnow().strftime('%Y-%m-%d')}

"""
        
        for i, doc in enumerate(source_docs, 1):
            translation += f"""
Document {i}: {doc.get('filename', 'Unknown')}
Source Language: {doc.get('doc_lang_hint', 'unknown')}
Pages: {doc.get('estimated_pages', 'N/A')}

[Working translation provided by AI - requires certified translator review]

---
"""
        
        return translation
    
    def _create_certification_checklist(
        self,
        source_docs: List[Dict[str, Any]],
        target_lang: str
    ) -> List[str]:
        """Generate certification checklist for translator."""
        
        checklist = [
            "Verify translator qualifications (sworn translator or equivalent)",
            "Confirm source documents match originals exactly",
            "Review AI working translation for accuracy",
            "Correct any errors or mistranslations",
            "Ensure legal terminology is accurate",
            "Preserve formatting and structure",
            "Verify all numbers, dates, and names are identical",
            "Check defined terms are consistent",
            "Sign and date the certified translation",
            "Prepare translator's affidavit",
            "Attach copies of translator's credentials",
            "File with court as required"
        ]
        
        # Add document-specific items
        for doc in source_docs:
            # Use 'or' to handle None values that slip through .get()
            ocr_conf = doc.get("ocr_confidence") or 1.0
            if ocr_conf < 0.8:
                checklist.append(
                    f"⚠️ Document '{doc.get('filename')}' has low OCR confidence - verify against original"
                )
        
        return checklist
    
    def _create_affidavit_draft(
        self,
        source_docs: List[Dict[str, Any]],
        target_lang: str,
        translator_name: str,
        translator_quals: str
    ) -> str:
        """Create affidavit draft template."""
        
        doc_list = "\n".join([
            f"{i}. {doc.get('filename', 'Document')} ({doc.get('doc_lang_hint', 'unknown')} → {target_lang})"
            for i, doc in enumerate(source_docs, 1)
        ])
        
        affidavit = f"""AFFIDAVIT OF TRANSLATOR

IN THE [COURT NAME]

[CASE TITLE]

AFFIDAVIT OF {translator_name}

I, {translator_name}, of [ADDRESS], do solemnly and sincerely declare as follows:

1. I am a [sworn translator / certified translator] duly qualified to translate documents from [SOURCE LANGUAGE] to [TARGET LANGUAGE].

2. My qualifications are as follows:
   {translator_quals}

3. I have translated the following documents in this matter:
   {doc_list}

4. I certify that the translations attached hereto marked as Exhibits [A, B, C...] are true and accurate translations of the original documents to the best of my knowledge and ability.

5. The translations have been prepared in accordance with professional translation standards and legal requirements.

6. I have preserved the meaning, intent, and legal effect of the original documents in the translations.

7. All numerical values, dates, names, and citations in the translations match the original documents exactly.

8. I make this affidavit conscientiously believing it to be true and in accordance with the Statutory Declarations Act 1960.

DECLARED at [LOCATION]  )
this [DAY] day of [MONTH] [YEAR]  )

                                    )
                                    )  ______________________
Before me,                          )  {translator_name}
                                    )  [IC No: ____________]


______________________
Commissioner for Oaths
"""
        
        return affidavit

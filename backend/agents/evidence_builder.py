"""
Evidence Packet Builder & Versioning Agent - Build index and evidence bundles.
"""
from agents.base_agent import BaseAgent
from typing import Dict, Any, List
from datetime import datetime


class EvidenceBuilderAgent(BaseAgent):
    """
    Build index, version history, translator affidavits, and evidence bundle for court.
    
    Inputs:
    - matter_id: matter identifier
    - documents: list of documents
    - pleadings: list of pleadings
    - translations: list of certified translations
    
    Outputs:
    - evidence_packet: PDF assembly plan
    - index_json: mapping originals → translations → affidavits
    - version_history: array of changes
    """
    
    def __init__(self):
        super().__init__(agent_id="EvidenceBuilder")
    
    async def process(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process evidence packet building.
        
        Args:
            inputs: {
                "matter_id": str,
                "documents": List[Dict],
                "pleadings": List[Dict],
                "translations": List[Dict] (optional),
                "affidavits": List[Dict] (optional)
            }
            
        Returns:
            {
                "evidence_packet": Dict,
                "index_json": Dict,
                "version_history": List[Dict]
            }
        """
        await self.validate_input(inputs, ["matter_id", "documents"])
        
        matter_id = inputs["matter_id"]
        documents = inputs["documents"]
        pleadings = inputs.get("pleadings", [])
        translations = inputs.get("translations", [])
        affidavits = inputs.get("affidavits", [])
        
        # Build index
        index = self._build_index(matter_id, documents, pleadings, translations, affidavits)
        
        # Create PDF assembly plan
        packet = self._create_packet_plan(index)
        
        # Generate version history
        version_history = self._create_version_history(matter_id, documents, pleadings)
        
        return self.format_output(
            data={
                "evidence_packet": packet,
                "index_json": index,
                "version_history": version_history,
                "total_items": len(index.get("items", []))
            },
            confidence=0.88
        )
    
    def _build_index(
        self,
        matter_id: str,
        documents: List[Dict],
        pleadings: List[Dict],
        translations: List[Dict],
        affidavits: List[Dict]
    ) -> Dict[str, Any]:
        """Build comprehensive index mapping all evidence."""
        
        items = []
        
        # Add pleadings
        for i, pleading in enumerate(pleadings, 1):
            items.append({
                "tab": f"A{i}",
                "type": "pleading",
                "description": f"{pleading.get('pleading_type', 'Pleading')} (Malay)",
                "file_id": pleading.get("id"),
                "language": "ms",
                "has_translation": bool(pleading.get("pleading_en_text")),
                "translation_tab": f"A{i}(EN)" if pleading.get("pleading_en_text") else None
            })
        
        # Add documents
        for i, doc in enumerate(documents, 1):
            # Find related translation (safe matching)
            translation = next(
                (t for t in translations if isinstance(t, dict) and t.get("source_doc_id") == doc.get("id")),
                None
            )
            
            # Find related affidavit (safe matching)
            affidavit = next(
                (a for a in affidavits if isinstance(a, dict) and a.get("doc_id") == doc.get("id")),
                None
            )
            
            items.append({
                "tab": f"B{i}",
                "type": "document",
                "description": doc.get("filename", "Document"),
                "file_id": doc.get("id"),
                "language": doc.get("doc_lang_hint", "unknown"),
                "has_translation": translation is not None,
                "translation_tab": f"B{i}(T)" if translation else None,
                "has_affidavit": affidavit is not None,
                "affidavit_tab": f"B{i}(A)" if affidavit else None
            })
        
        return {
            "matter_id": matter_id,
            "created_at": datetime.utcnow().isoformat(),
            "items": items,
            "total_tabs": len(items)
        }
    
    def _create_packet_plan(self, index: Dict[str, Any]) -> Dict[str, Any]:
        """Create PDF assembly plan for court bundle."""
        
        sections = []
        
        # Section 1: Pleadings
        pleading_items = [item for item in index["items"] if item["type"] == "pleading"]
        if pleading_items:
            sections.append({
                "section_name": "Pleadings",
                "tabs": [item["tab"] for item in pleading_items],
                "page_start": 1,
                "page_end": len(pleading_items) * 10  # Estimate 10 pages per pleading
            })
        
        # Section 2: Documents
        doc_items = [item for item in index["items"] if item["type"] == "document"]
        if doc_items:
            sections.append({
                "section_name": "Documents",
                "tabs": [item["tab"] for item in doc_items],
                "page_start": sections[-1]["page_end"] + 1 if sections else 1,
                "page_end": sections[-1]["page_end"] + len(doc_items) * 5 if sections else len(doc_items) * 5
            })
        
        # Section 3: Translations
        translation_items = [item for item in index["items"] if item.get("has_translation")]
        if translation_items:
            sections.append({
                "section_name": "Certified Translations",
                "tabs": [item["translation_tab"] for item in translation_items if item.get("translation_tab")],
                "page_start": sections[-1]["page_end"] + 1 if sections else 1,
                "page_end": sections[-1]["page_end"] + len(translation_items) * 5 if sections else len(translation_items) * 5
            })
        
        # Section 4: Affidavits
        affidavit_items = [item for item in index["items"] if item.get("has_affidavit")]
        if affidavit_items:
            sections.append({
                "section_name": "Translator Affidavits",
                "tabs": [item["affidavit_tab"] for item in affidavit_items if item.get("affidavit_tab")],
                "page_start": sections[-1]["page_end"] + 1 if sections else 1,
                "page_end": sections[-1]["page_end"] + len(affidavit_items) * 3 if sections else len(affidavit_items) * 3
            })
        
        return {
            "bundle_name": f"Evidence Bundle - {index['matter_id']}",
            "sections": sections,
            "total_estimated_pages": sections[-1]["page_end"] if sections else 0,
            "assembly_instructions": [
                "Print all documents single-sided on A4 paper",
                "Insert tab dividers at each section",
                "Number pages consecutively",
                "Bind with treasury tags or ring binder",
                "Prepare cover page with case details"
            ]
        }
    
    def _create_version_history(
        self,
        matter_id: str,
        documents: List[Dict],
        pleadings: List[Dict]
    ) -> List[Dict[str, Any]]:
        """Generate version history for audit trail."""
        
        history = []
        
        # Document collection events
        for doc in documents:
            history.append({
                "timestamp": doc.get("created_at", datetime.utcnow().isoformat()),
                "event_type": "document_added",
                "entity_id": doc.get("id"),
                "description": f"Document '{doc.get('filename')}' added to matter",
                "agent": "DocumentCollector"
            })
        
        # Pleading creation events
        for pleading in pleadings:
            history.append({
                "timestamp": pleading.get("created_at", datetime.utcnow().isoformat()),
                "event_type": "pleading_created",
                "entity_id": pleading.get("id"),
                "description": f"Pleading '{pleading.get('pleading_type')}' version {pleading.get('version', 1)} created",
                "agent": "MalayDrafting"
            })
        
        # Sort by timestamp
        history.sort(key=lambda x: x["timestamp"])
        
        return history

"""
Document Collector Agent - Gathers documents from multiple sources.
"""
from agents.base_agent import BaseAgent
from typing import Dict, Any, List
import hashlib
import os
from datetime import datetime
import aiofiles
import json


class DocumentCollectorAgent(BaseAgent):
    """
    Collects documents from various sources and produces normalized document manifest.
    
    Inputs:
    - connector_type: gmail/outlook/upload/whatsapp_export/dms
    - files: list of file objects or paths
    - metadata: envelope metadata (sender, date, subject, etc.)
    
    Outputs:
    - document_manifest: JSON with normalized document list
    - stored documents with IDs
    """
    
    def __init__(self):
        super().__init__(agent_id="DocumentCollector")
        self.supported_connectors = ["gmail", "outlook", "upload", "whatsapp_export", "dms"]
    
    async def process(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process document collection request.
        
        Args:
            inputs: {
                "connector_type": str,
                "files": List[Dict],  # [{filename, content, mime_type}]
                "metadata": Dict,  # source-specific metadata
                "matter_id": str
            }
            
        Returns:
            {
                "document_manifest": List[Dict],
                "total_documents": int,
                "duplicates_found": int
            }
        """
        await self.validate_input(inputs, ["connector_type", "files", "matter_id"])
        
        connector_type = inputs["connector_type"]
        files = inputs["files"]
        metadata = inputs.get("metadata", {})
        matter_id = inputs["matter_id"]
        
        if connector_type not in self.supported_connectors:
            raise ValueError(f"Unsupported connector type: {connector_type}")
        
        documents = []
        seen_hashes = {}
        duplicates_count = 0
        
        for file_data in files:
            doc_info = await self._process_single_file(
                file_data,
                connector_type,
                metadata,
                matter_id,
                seen_hashes
            )
            
            if doc_info["is_duplicate"]:
                duplicates_count += 1
            
            documents.append(doc_info)
        
        return self.format_output(
            data={
                "document_manifest": documents,
                "total_documents": len(documents),
                "duplicates_found": duplicates_count
            },
            confidence=0.95
        )
    
    async def _process_single_file(
        self,
        file_data: Dict[str, Any],
        connector_type: str,
        metadata: Dict,
        matter_id: str,
        seen_hashes: Dict[str, str]
    ) -> Dict[str, Any]:
        """Process a single file and create document record."""
        
        filename = file_data.get("filename", "unknown")
        content = file_data.get("content", b"")
        mime_type = file_data.get("mime_type", "application/octet-stream")
        
        # Calculate file hash for deduplication
        file_hash = hashlib.sha256(content).hexdigest()
        
        # Check for duplicates
        is_duplicate = file_hash in seen_hashes
        duplicate_of = seen_hashes.get(file_hash)
        
        if not is_duplicate:
            seen_hashes[file_hash] = f"DOC-{datetime.utcnow().strftime('%Y%m%d')}-{file_hash[:8]}"
        
        # Determine if OCR is needed
        ocr_needed = mime_type in [
            "application/pdf",
            "image/png",
            "image/jpeg",
            "image/tiff"
        ]
        
        # Extract language hint from filename or metadata
        doc_lang_hint = self._detect_language_hint(filename, metadata)
        
        # Create document record
        doc_id = seen_hashes[file_hash]
        
        doc_info = {
            "doc_id": doc_id,
            "matter_id": matter_id,
            "source": connector_type,
            "filename": filename,
            "mime_type": mime_type,
            "received_utc": metadata.get("received_date", datetime.utcnow().isoformat()),
            "size_bytes": len(content),
            "file_hash": file_hash,
            "is_duplicate": is_duplicate,
            "duplicate_of": duplicate_of,
            "ocr_needed": ocr_needed,
            "doc_lang_hint": doc_lang_hint,
            "confidence": 0.86 if ocr_needed else 0.95,
            "file_content": content
        }
        
        # Add source-specific metadata
        if connector_type in ["gmail", "outlook"]:
            doc_info["sender"] = metadata.get("sender")
            doc_info["subject"] = metadata.get("subject")
            doc_info["recipients"] = metadata.get("recipients", [])
        
        return doc_info
    
    def _detect_language_hint(self, filename: str, metadata: Dict) -> str:
        """
        Detect language hint from filename or metadata.
        
        Returns: "ms", "en", "mixed", or "unknown"
        """
        filename_lower = filename.lower()
        
        # Check for language indicators in filename
        if any(word in filename_lower for word in ["malay", "bahasa", "ms_"]):
            return "ms"
        elif any(word in filename_lower for word in ["english", "en_"]):
            return "en"
        
        if "language" in metadata and isinstance(metadata["language"], str):
            lang = metadata["language"].lower()
            if "malay" in lang or "ms" in lang:
                return "ms"
            elif "english" in lang or "en" in lang:
                return "en"
        
        return "unknown"
    
    async def process_whatsapp_export(self, export_file: str) -> List[Dict[str, Any]]:
        """
        Parse WhatsApp export and split into message-level items.
        
        Args:
            export_file: Path to WhatsApp export text file
            
        Returns:
            List of message documents
        """
        messages = []
        
        async with aiofiles.open(export_file, 'r', encoding='utf-8') as f:
            content = await f.read()
        
        # Simple WhatsApp message parser
        # Format: [DD/MM/YYYY, HH:MM:SS] Sender: Message
        lines = content.split('\n')
        
        for line in lines:
            if not line.strip():
                continue
            
            # Parse timestamp and sender
            if line.startswith('['):
                try:
                    timestamp_end = line.index(']')
                    timestamp_str = line[1:timestamp_end]
                    
                    rest = line[timestamp_end + 1:].strip()
                    if ':' in rest:
                        sender, message = rest.split(':', 1)
                        
                        messages.append({
                            "timestamp": timestamp_str,
                            "sender": sender.strip(),
                            "message": message.strip(),
                            "source": "whatsapp_export"
                        })
                except (ValueError, IndexError):
                    continue
        
        return messages

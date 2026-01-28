"""
OCR Post-Processing Service for Legal Documents
================================================
Handles:
- Header/footer detection and removal
- Noise filtering (serial numbers, stamps)
- Metadata extraction (case numbers, court, parties)
- Legal-aware sentence splitting
- Token-controlled chunking for RAG
"""
import re
import logging
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass, field
from difflib import SequenceMatcher

logger = logging.getLogger(__name__)


# ============================================
# LEGAL ABBREVIATIONS (do not split on period)
# ============================================
LEGAL_ABBREVIATIONS = {
    # Titles
    'dr', 'mr', 'mrs', 'ms', 'prof', 'hon', 'rev',
    # Numbers
    'no', 'nos', 'ref', 'tel', 'fax',
    # Legal
    'vs', 'v', 'ss', 'art', 'para', 'pp', 'eg', 'ie', 'etc',
    'j', 'jj', 'c', 'l', 'r', 's', 'p', 'q',  # Judge, Justice, etc.
    # Malaysian
    'bhd', 'sdn', 'sek', 'enr', 'plt',
    # Company
    'inc', 'ltd', 'co', 'corp', 'llc',
}

# ============================================
# NOISE PATTERNS (to be removed)
# ============================================
NOISE_PATTERNS = [
    # Page numbers
    r'^\s*\d{1,3}\s*$',
    r'^Page\s+\d+\s+of\s+\d+\s*$',
    r'^\s*-\s*\d+\s*-\s*$',
    r'^m/s\s+\d+\s*$',
    
    # Stamp artifacts
    r'FILED\s+.*?(?:AM|PM)',
    r'(?:RECEIVED|CERTIFIED|SEALED).*?\d{4}',
    
    # Watermarks
    r'^CONFIDENTIAL\s*$',
    r'^DRAFT\s*(?:COPY)?\s*$',
    r'^DO\s+NOT\s+COPY\s*$',
    
    # Reference lines (keep for metadata, remove from body)
    r'^(?:Ruj\.|Ref\.?)\s*:',
]


@dataclass
class LegalMetadata:
    """Extracted metadata from legal documents."""
    case_number: Optional[str] = None
    court: Optional[str] = None
    parties: List[str] = field(default_factory=list)
    filing_date: Optional[str] = None
    judge: Optional[str] = None
    document_type: Optional[str] = None
    section_refs: List[str] = field(default_factory=list)
    acts_cited: List[str] = field(default_factory=list)


@dataclass 
class TextChunk:
    """A token-controlled text chunk for RAG."""
    text: str
    token_count: int
    source_page_start: int
    source_page_end: int
    chunk_type: str = "paragraph"
    section_ref: Optional[str] = None
    is_embeddable: bool = True


class OCRPostProcessor:
    """Post-processing service for legal OCR output."""
    
    def __init__(self, target_tokens: int = 600, max_tokens: int = 800, overlap_tokens: int = 100):
        self.target_tokens = target_tokens
        self.max_tokens = max_tokens
        self.overlap_tokens = overlap_tokens
        self._encoder = None
    
    def _get_encoder(self):
        """Lazy load tiktoken encoder."""
        if self._encoder is None:
            try:
                import tiktoken
                self._encoder = tiktoken.encoding_for_model("gpt-4")
            except Exception:
                logger.warning("tiktoken not available, using word-based estimation")
                self._encoder = None
        return self._encoder
    
    def count_tokens(self, text: str) -> int:
        """Count tokens in text."""
        encoder = self._get_encoder()
        if encoder:
            return len(encoder.encode(text))
        # Fallback: rough word-based estimate (1 token ≈ 0.75 words)
        return int(len(text.split()) * 1.33)
    
    # ============================================
    # HEADER/FOOTER DETECTION
    # ============================================
    
    def detect_headers_footers(
        self, 
        pages: List[Dict[str, Any]], 
        similarity_threshold: float = 0.75,
        min_occurrences: int = 3
    ) -> Dict[str, List[str]]:
        """
        Detect repeating headers and footers by comparing first/last blocks across pages.
        
        Args:
            pages: List of page dicts with 'text' or 'blocks' keys
            similarity_threshold: How similar text must be to count as repeating
            min_occurrences: Minimum pages pattern must appear on
        
        Returns:
            Dict with 'headers' and 'footers' pattern lists
        """
        if len(pages) < min_occurrences:
            return {"headers": [], "footers": []}
        
        # Extract first ~200 chars from each page (likely header area)
        first_blocks = []
        last_blocks = []
        
        for page in pages:
            text = page.get('text', '') or page.get('raw_text', '')
            if text:
                lines = text.strip().split('\n')
                # First 3 lines (header area)
                header_text = '\n'.join(lines[:3])[:300]
                first_blocks.append(header_text)
                # Last 3 lines (footer area)
                footer_text = '\n'.join(lines[-3:])[:300]
                last_blocks.append(footer_text)
        
        def find_repeating(text_list: List[str]) -> List[str]:
            patterns = []
            for text in text_list:
                if not text.strip():
                    continue
                matches = sum(
                    1 for other in text_list
                    if SequenceMatcher(None, text, other).ratio() > similarity_threshold
                )
                if matches >= min_occurrences:
                    if text not in patterns:
                        patterns.append(text)
            return patterns
        
        return {
            "headers": find_repeating(first_blocks),
            "footers": find_repeating(last_blocks)
        }
    
    def remove_headers_footers(self, text: str, patterns: Dict[str, List[str]]) -> str:
        """Remove detected header/footer patterns from text."""
        cleaned = text
        
        for header in patterns.get("headers", []):
            if len(header) > 10:
                # Check if text starts similarly
                if SequenceMatcher(None, cleaned[:len(header)+50], header).ratio() > 0.6:
                    # Find where header ends and remove
                    lines = cleaned.split('\n')
                    header_lines = header.count('\n') + 1
                    cleaned = '\n'.join(lines[header_lines:])
        
        for footer in patterns.get("footers", []):
            if len(footer) > 10:
                # Check if text ends similarly
                if SequenceMatcher(None, cleaned[-(len(footer)+50):], footer).ratio() > 0.6:
                    lines = cleaned.split('\n')
                    footer_lines = footer.count('\n') + 1
                    cleaned = '\n'.join(lines[:-footer_lines])
        
        return cleaned.strip()
    
    # ============================================
    # NOISE FILTERING
    # ============================================
    
    def remove_noise(self, text: str) -> str:
        """Remove OCR noise from legal documents."""
        lines = text.split('\n')
        cleaned_lines = []
        
        for line in lines:
            line_stripped = line.strip()
            
            # Skip empty lines
            if not line_stripped:
                cleaned_lines.append('')
                continue
            
            # Check against noise patterns
            is_noise = any(
                re.match(pattern, line_stripped, re.IGNORECASE)
                for pattern in NOISE_PATTERNS
            )
            
            if not is_noise:
                cleaned_lines.append(line)
        
        # Remove excessive blank lines
        result = '\n'.join(cleaned_lines)
        result = re.sub(r'\n{3,}', '\n\n', result)
        
        return result.strip()
    
    # ============================================
    # METADATA EXTRACTION
    # ============================================
    
    def extract_metadata(self, text: str) -> LegalMetadata:
        """Extract legal metadata from OCR text."""
        metadata = LegalMetadata()
        
        # Limit search to first 3000 chars for performance
        search_text = text[:3000]
        
        # Case number patterns (Malaysian format)
        case_patterns = [
            r'(?:Case\s*No|No\.\s*Kes|Suit\s*No|Guaman\s*No)\.?\s*[:.]?\s*([\w\-/\(\)]+)',
            r'((?:WA|BA|DA|MT|S|JR|CA|PA)[-\s]?\d+[-\s]?\d*[-\s]?\d*[-/]\d{2,4})',
            r'(\d{2,4}[-/]\d+[-/]\d{2,4})',
        ]
        for pattern in case_patterns:
            match = re.search(pattern, search_text, re.IGNORECASE)
            if match:
                metadata.case_number = match.group(1).strip() if match.lastindex else match.group(0).strip()
                break
        
        # Court name
        court_patterns = [
            (r'HIGH\s+COURT.*?(?:AT|DI)\s+(\w+(?:\s+\w+)?)', 'High Court'),
            (r'MAHKAMAH\s+TINGGI.*?(?:AT|DI)\s+(\w+(?:\s+\w+)?)', 'High Court'),
            (r'COURT\s+OF\s+APPEAL', 'Court of Appeal'),
            (r'MAHKAMAH\s+RAYUAN', 'Court of Appeal'),
            (r'FEDERAL\s+COURT', 'Federal Court'),
            (r'MAHKAMAH\s+PERSEKUTUAN', 'Federal Court'),
            (r'SESSIONS?\s+COURT', 'Sessions Court'),
            (r'MAHKAMAH\s+SESYEN', 'Sessions Court'),
            (r'MAGISTRATE.?S?\s+COURT', 'Magistrate Court'),
        ]
        for pattern, court_type in court_patterns:
            match = re.search(pattern, search_text, re.IGNORECASE)
            if match:
                if match.lastindex:
                    metadata.court = f"{court_type} at {match.group(1).title()}"
                else:
                    metadata.court = court_type
                break
        
        # Parties (v. or vs or versus)
        party_match = re.search(
            r'^\s*(.*?)\s+(?:v\.?|vs\.?|versus|lawan)\s+(.*)$',
            search_text,
            re.IGNORECASE | re.MULTILINE
        )
        if party_match:
            plaintiff = party_match.group(1).strip()[:150]
            defendant = party_match.group(2).strip()[:150]
            # Clean up
            plaintiff = re.sub(r'\s+', ' ', plaintiff)
            defendant = re.sub(r'\s+', ' ', defendant).split('\n')[0]
            metadata.parties = [plaintiff, defendant]
        
        # Date patterns
        date_match = re.search(
            r'\b(\d{1,2})\s+(Jan(?:uary)?|Feb(?:ruary)?|Mar(?:ch)?|Apr(?:il)?|May|Jun(?:e)?|Jul(?:y)?|Aug(?:ust)?|Sep(?:tember)?|Oct(?:ober)?|Nov(?:ember)?|Dec(?:ember)?)\s+(\d{4})\b',
            search_text,
            re.IGNORECASE
        )
        if date_match:
            metadata.filing_date = date_match.group(0)
        
        # Section references
        section_matches = re.findall(r'[Ss](?:ection|\.)\s*(\d+(?:\([a-z0-9]+\))*)', text)
        metadata.section_refs = list(set(section_matches[:20]))  # Limit to 20
        
        # Acts cited
        act_matches = re.findall(r'([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*\s+Act\s+\d{4})', text)
        metadata.acts_cited = list(set(act_matches[:20]))  # Limit to 20
        
        return metadata
    
    # ============================================
    # LEGAL-AWARE SENTENCE SPLITTING
    # ============================================
    
    def split_sentences_legal(self, text: str) -> List[str]:
        """
        Split text into sentences with legal-document awareness.
        Handles citations, section refs, and abbreviations.
        """
        # Step 1: Protect citations like [2024] 1 MLJ 123
        protected = re.sub(
            r'\[(\d{4})\]\s*\d+\s*[A-Z]+\s*\d+',
            lambda m: m.group(0).replace('.', '〈DOT〉'),
            text
        )
        
        # Step 2: Protect section numbers like S.30(1)(a)
        protected = re.sub(
            r'([Ss])\.(\d+)',
            r'\1〈DOT〉\2',
            protected
        )
        
        # Step 3: Protect abbreviations
        for abbr in LEGAL_ABBREVIATIONS:
            # Match abbreviation followed by period and space
            protected = re.sub(
                rf'\b({abbr})\.(?=\s)',
                rf'\1〈DOT〉',
                protected,
                flags=re.IGNORECASE
            )
        
        # Step 4: Protect decimal numbers
        protected = re.sub(r'(\d)\.(\d)', r'\1〈DOT〉\2', protected)
        
        # Step 5: Split on sentence-ending punctuation followed by space and capital
        sentences = re.split(r'(?<=[.!?])\s+(?=[A-Z\[\(])', protected)
        
        # Step 6: Restore protected periods
        sentences = [s.replace('〈DOT〉', '.').strip() for s in sentences]
        
        return [s for s in sentences if s.strip()]
    
    # ============================================
    # TOKEN-CONTROLLED CHUNKING
    # ============================================
    
    def chunk_text(
        self,
        text: str,
        page_number: int = 1
    ) -> List[TextChunk]:
        """
        Create token-controlled chunks from text.
        
        Args:
            text: Cleaned text to chunk
            page_number: Source page number for traceability
        
        Returns:
            List of TextChunk objects
        """
        if not text.strip():
            return []
        
        # First, split into paragraphs
        paragraphs = re.split(r'\n{2,}', text)
        
        chunks = []
        current_sentences = []
        current_tokens = 0
        
        for para in paragraphs:
            para = para.strip()
            if not para:
                continue
            
            # Check if paragraph is a heading
            is_heading = (
                len(para) < 100 and
                (para.isupper() or re.match(r'^(?:GROUND|ISSUE|SECTION|PART)\s+\d+', para, re.IGNORECASE))
            )
            
            # Split paragraph into sentences
            sentences = self.split_sentences_legal(para)
            
            for sentence in sentences:
                sentence_tokens = self.count_tokens(sentence)
                
                # If single sentence exceeds max, force split
                if sentence_tokens > self.max_tokens:
                    # Save current if exists
                    if current_sentences:
                        chunk_text = ' '.join(current_sentences)
                        chunks.append(TextChunk(
                            text=chunk_text,
                            token_count=current_tokens,
                            source_page_start=page_number,
                            source_page_end=page_number,
                            chunk_type="paragraph"
                        ))
                        current_sentences = []
                        current_tokens = 0
                    
                    # Split long sentence by clauses
                    clauses = re.split(r'[;,]\s+', sentence)
                    for clause in clauses:
                        chunks.append(TextChunk(
                            text=clause,
                            token_count=self.count_tokens(clause),
                            source_page_start=page_number,
                            source_page_end=page_number,
                            chunk_type="clause"
                        ))
                    continue
                
                # If adding this sentence exceeds target, save current chunk
                if current_tokens + sentence_tokens > self.target_tokens and current_tokens > 100:
                    chunk_text = ' '.join(current_sentences)
                    chunks.append(TextChunk(
                        text=chunk_text,
                        token_count=current_tokens,
                        source_page_start=page_number,
                        source_page_end=page_number,
                        chunk_type="heading" if is_heading else "paragraph"
                    ))
                    
                    # Keep last few sentences for overlap
                    overlap_sentences = []
                    overlap_tokens = 0
                    for s in reversed(current_sentences):
                        s_tokens = self.count_tokens(s)
                        if overlap_tokens + s_tokens <= self.overlap_tokens:
                            overlap_sentences.insert(0, s)
                            overlap_tokens += s_tokens
                        else:
                            break
                    
                    current_sentences = overlap_sentences
                    current_tokens = overlap_tokens
                
                current_sentences.append(sentence)
                current_tokens += sentence_tokens
        
        # Add final chunk
        if current_sentences:
            chunk_text = ' '.join(current_sentences)
            chunks.append(TextChunk(
                text=chunk_text,
                token_count=current_tokens,
                source_page_start=page_number,
                source_page_end=page_number,
                chunk_type="paragraph"
            ))
        
        return chunks
    
    # ============================================
    # FULL PROCESSING PIPELINE
    # ============================================
    
    def process_document_pages(
        self,
        pages: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Process all pages of a document through the full pipeline.
        
        Args:
            pages: List of page dicts with 'page_number' and 'raw_text'
        
        Returns:
            Dict with 'pages' (cleaned), 'chunks', 'metadata'
        """
        # Step 1: Detect headers/footers across all pages
        patterns = self.detect_headers_footers(pages)
        logger.info(f"Detected {len(patterns['headers'])} headers, {len(patterns['footers'])} footers")
        
        # Step 2: Process each page
        processed_pages = []
        all_chunks = []
        combined_text = ""
        
        for page in pages:
            page_num = page.get('page_number', 1)
            raw_text = page.get('raw_text', '') or page.get('text', '')
            
            # Remove headers/footers
            cleaned = self.remove_headers_footers(raw_text, patterns)
            
            # Remove noise
            cleaned = self.remove_noise(cleaned)
            
            # Create chunks from this page
            page_chunks = self.chunk_text(cleaned, page_num)
            
            processed_pages.append({
                'page_number': page_num,
                'raw_text': raw_text,
                'cleaned_text': cleaned,
                'word_count': len(cleaned.split()),
                'char_count': len(cleaned),
                'detected_headers': patterns['headers'] if page_num == 1 else [],
                'detected_footers': patterns['footers'] if page_num == len(pages) else [],
            })
            
            all_chunks.extend(page_chunks)
            combined_text += cleaned + "\n\n"
        
        # Step 3: Extract metadata from combined text
        metadata = self.extract_metadata(combined_text)
        
        # Step 4: Assign chunk sequences
        for i, chunk in enumerate(all_chunks):
            chunk.chunk_sequence = i + 1
        
        return {
            'pages': processed_pages,
            'chunks': [
                {
                    'chunk_sequence': c.chunk_sequence if hasattr(c, 'chunk_sequence') else i+1,
                    'chunk_text': c.text,
                    'token_count': c.token_count,
                    'source_page_start': c.source_page_start,
                    'source_page_end': c.source_page_end,
                    'chunk_type': c.chunk_type,
                    'is_embeddable': c.is_embeddable,
                }
                for i, c in enumerate(all_chunks)
            ],
            'metadata': {
                'case_number': metadata.case_number,
                'court': metadata.court,
                'parties': metadata.parties,
                'filing_date': metadata.filing_date,
                'section_refs': metadata.section_refs[:10],
                'acts_cited': metadata.acts_cited[:10],
            },
            'patterns_detected': patterns,
        }


# Global instance
_ocr_post_processor = None


def get_ocr_post_processor() -> OCRPostProcessor:
    """Get the global OCR post-processor instance."""
    global _ocr_post_processor
    if _ocr_post_processor is None:
        _ocr_post_processor = OCRPostProcessor()
    return _ocr_post_processor


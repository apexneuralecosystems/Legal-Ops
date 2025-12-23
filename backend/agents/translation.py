"""
Translation Agent - Provides high-quality NMT Malay ↔ English translation using Gemini.
"""
from agents.base_agent import BaseAgent
from typing import Dict, Any, List
import google.generativeai as genai
from config import settings
import re


class TranslationAgent(BaseAgent):
    """
    Provide high-quality NMT Malay ↔ English translation using Google Gemini.
    Preserve legal terms and provide both literal and idiomatic translations.
    
    Inputs:
    - segments: list of text segments with language tags
    - target_language: 'en' or 'ms'
    - translation_mode: 'literal' or 'idiomatic' or 'both'
    
    Outputs:
    - parallel: array of {src, src_lang, tgt_literal, tgt_idiom, alignment_score}
    """
    
    def __init__(self):
        super().__init__(agent_id="Translation")
        genai.configure(api_key=settings.GEMINI_API_KEY)
        self.model = genai.GenerativeModel(settings.GEMINI_MODEL)
        
        # Legal terms to preserve
        self.legal_terms = {
            'ms': ['plaintif', 'defendan', 'mahkamah', 'perbicaraan', 'penghakiman'],
            'en': ['plaintiff', 'defendant', 'court', 'trial', 'judgment']
        }
    
    async def process(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process translation request.
        
        Args:
            inputs: {
                "segments": List[Dict],
                "target_language": str,
                "translation_mode": str (default: 'both')
            }
            
        Returns:
            {
                "parallel": List[Dict],
                "total_segments": int
            }
        """
        await self.validate_input(inputs, ["segments"])
        
        segments = inputs["segments"]
        target_lang = inputs.get("target_language", "en")
        mode = inputs.get("translation_mode", "both")
        
        parallel_texts = []
        
        for segment in segments:
            src_text = segment.get("text", "")
            src_lang = segment.get("lang", "unknown")
            
            # Skip if already in target language
            if src_lang == target_lang:
                parallel_texts.append({
                    "src": src_text,
                    "src_lang": src_lang,
                    "tgt_literal": src_text,
                    "tgt_idiom": src_text,
                    "alignment_score": 1.0,
                    "human_review": False
                })
                continue
            
            # Translate using Gemini
            try:
                if mode == 'both':
                    literal = await self._translate_gemini(src_text, src_lang, target_lang, 'literal')
                    idiomatic = await self._translate_gemini(src_text, src_lang, target_lang, 'idiomatic')
                elif mode == 'literal':
                    literal = await self._translate_gemini(src_text, src_lang, target_lang, 'literal')
                    idiomatic = literal
                else:
                    idiomatic = await self._translate_gemini(src_text, src_lang, target_lang, 'idiomatic')
                    literal = idiomatic
                
                # Calculate alignment score
                alignment_score = self._calculate_alignment(src_text, literal)
                
                # Flag for human review if confidence is low
                human_review = alignment_score < 0.7
                
                parallel_texts.append({
                    "src": src_text,
                    "src_lang": src_lang,
                    "tgt_literal": literal,
                    "tgt_idiom": idiomatic,
                    "alignment_score": alignment_score,
                    "human_review": human_review
                })
                
            except Exception as e:
                print(f"Translation error for segment: {e}")
                parallel_texts.append({
                    "src": src_text,
                    "src_lang": src_lang,
                    "tgt_literal": "[Translation failed]",
                    "tgt_idiom": "[Translation failed]",
                    "alignment_score": 0.0,
                    "human_review": True
                })
        
        return self.format_output(
            data={
                "parallel": parallel_texts,
                "total_segments": len(parallel_texts)
            },
            confidence=0.88
        )
    
    async def _translate_gemini(
        self,
        text: str,
        src_lang: str,
        tgt_lang: str,
        mode: str
    ) -> str:
        """Translate text using Google Gemini."""
        
        # Map language codes to full names
        lang_names = {
            'ms': 'Malay',
            'en': 'English'
        }
        
        src_name = lang_names.get(src_lang, src_lang)
        tgt_name = lang_names.get(tgt_lang, tgt_lang)
        
        if mode == 'literal':
            prompt = f"""Translate the following {src_name} legal text to {tgt_name}. 
Provide a LITERAL, word-for-word translation that preserves the exact legal meaning.
Preserve legal terms like PLAINTIF, DEFENDAN, MAHKAMAH in their original form.
Keep all numbers, dates, and citations exactly as they appear.

Text to translate:
{text}

Provide ONLY the translation, no explanations:"""
        else:
            prompt = f"""Translate the following {src_name} legal text to {tgt_name}.
Provide a natural, IDIOMATIC translation that reads fluently in {tgt_name} while preserving legal meaning.
Preserve legal terms like PLAINTIF, DEFENDAN, MAHKAMAH in their original form.
Keep all numbers, dates, and citations exactly as they appear.

Text to translate:
{text}

Provide ONLY the translation, no explanations:"""
        
        try:
            response = self.model.generate_content(prompt)
            translation = response.text.strip()
            
            # Clean up any explanatory text
            translation = re.sub(r'^(Translation:|Literal:|Idiomatic:)\s*', '', translation, flags=re.IGNORECASE)
            
            return translation
            
        except Exception as e:
            print(f"Gemini translation error: {e}")
            return f"[Translation error: {str(e)}]"
    
    def _calculate_alignment(self, src: str, tgt: str) -> float:
        """Calculate alignment score between source and target."""
        
        # Extract numbers from both texts
        src_numbers = set(re.findall(r'\d+', src))
        tgt_numbers = set(re.findall(r'\d+', tgt))
        
        # Numbers must match exactly
        if src_numbers != tgt_numbers:
            return 0.6
        
        # Calculate length ratio
        src_words = len(src.split())
        tgt_words = len(tgt.split())
        
        if src_words == 0 or tgt_words == 0:
            return 0.5
        
        length_ratio = min(src_words, tgt_words) / max(src_words, tgt_words)
        
        # Malay-English typically has 0.8-1.2 ratio
        if 0.7 <= length_ratio <= 1.3:
            base_score = 0.9
        elif 0.5 <= length_ratio <= 1.5:
            base_score = 0.8
        else:
            base_score = 0.7
        
        # Bonus for number preservation
        if src_numbers == tgt_numbers and len(src_numbers) > 0:
            base_score += 0.05
        
        return round(min(base_score, 1.0), 2)

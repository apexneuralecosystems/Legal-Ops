"""
Devil's Advocate Agent - Advanced Cross-Examination.

This agent provides senior litigation partner-level analysis
that automatically challenges the user's legal position.

Output Components:
1. Contractual Defenses Table
2. Evidentiary Gaps
3. Cross-Examination Questions
4. Strategic Recommendations
5. Opposing Strategy Prediction
"""

import logging
from typing import Dict, Any, List, Optional
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage
from config import settings

logger = logging.getLogger(__name__)


DEVILS_ADVOCATE_PROMPT = """You are a senior litigation partner with 25 years of experience in Malaysian courts.

You have been provided with a legal analysis. Your job is to CHALLENGE this position as if you were opposing counsel and advising the client on vulnerabilities.

You MUST provide ALL 5 components below in your response:

## 🔴 1. CONTRACTUAL DEFENSES TABLE
| Defense | Case Law Against You | Your Vulnerability |
|---------|---------------------|-------------------|
[List each potential defense the opposing party could raise, cite a Malaysian case that supports their defense, and rate vulnerability as HIGH/MEDIUM/LOW]

## 🔴 2. EVIDENTIARY GAPS I WOULD EXPLOIT
❌ **Gap 1**: [What critical document is missing?]
> [Cite a Malaysian case where this gap was fatal]

❌ **Gap 2**: [What testimony is uncorroborated?]
> [Explain how opposing counsel would exploit this]

❌ **Gap 3**: [What assumption is unproven?]
> [Describe the risk if this is challenged at trial]

## 🔴 3. CROSS-EXAMINATION QUESTIONS I WOULD ASK
Write 3-5 specific questions designed to create doubt or contradiction:
1. *"[Exact question in quotation marks targeting a weakness]"*
2. *"[Another question that challenges credibility or facts]"*
3. *"[A question about timeline or documentation gaps]"*

## 🔴 4. STRATEGIC RECOMMENDATIONS
| Issue | Action Required | Priority |
|-------|-----------------|----------|
| [Issue 1] | [Specific action] | 🔴 HIGH |
| [Issue 2] | [Specific action] | 🟡 MEDIUM |
| [Issue 3] | [Specific action] | 🟢 LOW |

## 🔴 5. OPPOSING COUNSEL'S LIKELY STRATEGY
Based on my analysis:
1. **Interlocutory Applications**: [What motions will they file?]
2. **Defense Theory**: [What is their main argument?]
3. **Key Cases They'll Cite**: [List 2-3 Malaysian cases they'll rely on]
4. **Settlement Pressure Points**: [Where will they try to force settlement?]

REMEMBER: You are not helping the user win - you are stress-testing their case like the toughest opposing counsel would.
Be specific. Use real Malaysian case citations where possible. Be brutally honest about weaknesses.
"""


class DevilsAdvocateAgent:
    """
    Automatic cross-examination agent.
    Runs after every substantive legal response.
    """
    
    def __init__(self):
        self.llm = None
        self._init_llm()
    
    def _init_llm(self):
        """Initialize the LLM for devil's advocate analysis."""
        try:
            self.llm = ChatOpenAI(
                model=settings.OPENROUTER_MODEL or "openai/gpt-4o",
                openai_api_key=settings.OPENROUTER_API_KEY,
                openai_api_base="https://openrouter.ai/api/v1",
                temperature=0.4,  # Slightly higher for creative challenges
                max_tokens=3000,
            )
            logger.info("DevilsAdvocateAgent initialized")
        except Exception as e:
            logger.error(f"Failed to initialize DevilsAdvocateAgent: {e}")
            self.llm = None
    
    async def analyze(
        self,
        legal_position: str,
        case_context: str = None,
        document_summary: str = None
    ) -> Dict[str, Any]:
        """
        Generate devil's advocate analysis.
        
        Args:
            legal_position: The initial legal analysis/argument to challenge
            case_context: Brief description of the case
            document_summary: Summary of uploaded documents
        
        Returns:
            Dict with 'challenge' (full analysis) and 'components' (parsed sections)
        """
        if not self.llm:
            return {
                "challenge": "[Devil's Advocate agent not initialized]",
                "components": {}
            }
        
        # Build the analysis request
        user_content = f"""
## CASE CONTEXT
{case_context or "Not provided"}

## DOCUMENT SUMMARY
{document_summary or "Not provided"}

## LEGAL POSITION TO CHALLENGE
{legal_position}

---
Now provide your 5-component Devil's Advocate analysis.
"""
        
        messages = [
            SystemMessage(content=DEVILS_ADVOCATE_PROMPT),
            HumanMessage(content=user_content)
        ]
        
        try:
            response = await self.llm.ainvoke(messages)
            challenge_text = response.content
            
            # Parse components (basic extraction)
            components = self._parse_components(challenge_text)
            
            return {
                "challenge": challenge_text,
                "components": components
            }
            
        except Exception as e:
            logger.error(f"DevilsAdvocateAgent.analyze error: {e}")
            return {
                "challenge": f"[Analysis failed: {str(e)}]",
                "components": {}
            }
    
    def _parse_components(self, text: str) -> Dict[str, str]:
        """Extract individual components from the analysis."""
        components = {}
        
        markers = [
            ("defenses", "CONTRACTUAL DEFENSES TABLE"),
            ("evidentiary_gaps", "EVIDENTIARY GAPS"),
            ("cross_examination", "CROSS-EXAMINATION QUESTIONS"),
            ("recommendations", "STRATEGIC RECOMMENDATIONS"),
            ("opposing_strategy", "OPPOSING COUNSEL'S LIKELY STRATEGY"),
        ]
        
        for key, marker in markers:
            start_idx = text.find(marker)
            if start_idx != -1:
                # Find next marker or end
                next_idx = len(text)
                for _, next_marker in markers:
                    if next_marker != marker:
                        idx = text.find(next_marker, start_idx + len(marker))
                        if idx != -1 and idx < next_idx:
                            next_idx = idx
                
                components[key] = text[start_idx:next_idx].strip()
        
        return components


# ============================================
# GLOBAL INSTANCE
# ============================================

_devils_advocate_agent = None

def get_devils_advocate_agent() -> DevilsAdvocateAgent:
    """Get or create the global DevilsAdvocateAgent instance."""
    global _devils_advocate_agent
    if _devils_advocate_agent is None:
        _devils_advocate_agent = DevilsAdvocateAgent()
    return _devils_advocate_agent

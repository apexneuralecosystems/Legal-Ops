"""
Case Strength Predictor Agent - Analyzes case strength using AI.
Provides win probability, risks, strengths, and improvement suggestions.
"""
import google.generativeai as genai
from typing import Dict, Any
from config import settings
from agents.base_agent import BaseAgent
import json
import logging

logger = logging.getLogger(__name__)


class CaseStrengthAgent(BaseAgent):
    """
    AI-powered case strength analyzer that predicts outcomes
    and identifies strengths/weaknesses.
    """
    
    def __init__(self):
        super().__init__(agent_id="CaseStrength")
        genai.configure(api_key=settings.GEMINI_API_KEY)
        self.model = genai.GenerativeModel(settings.GEMINI_MODEL)
    
    async def process(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analyze case strength based on matter data.
        
        Input:
            matter: Matter snapshot with title, issues, parties, etc.
            documents: List of documents
            risk_scores: Existing risk assessment
            
        Output:
            win_probability: 0-100 percentage
            risks: List of identified weaknesses
            strengths: List of identified advantages
            suggestions: List of improvement recommendations
            overall_assessment: Brief summary
        """
        logger.info("Starting case strength analysis")
        
        matter = input_data.get("matter", {})
        documents = input_data.get("documents", [])
        risk_scores = input_data.get("risk_scores", {})
        
        # Build context for AI
        context = self._build_context(matter, documents, risk_scores)
        
        # Analyze with Gemini
        try:
            analysis = await self._analyze_with_ai(context)
            
            logger.info(f"Case strength analysis complete: {analysis.get('win_probability')}% probability")
            
            return {
                "status": "success",
                "data": analysis
            }
            
        except Exception as e:
            logger.error(f"Error in case strength analysis: {str(e)}")
            return {
                "status": "error",
                "error": str(e),
                "data": self._get_fallback_analysis(matter, risk_scores)
            }
    
    def _build_context(self, matter: Dict, documents: list, risk_scores: Dict) -> str:
        """Build context string for AI analysis."""
        context = f"""
CASE INFORMATION
================
Title: {matter.get('title', 'Unknown')}
Type: {matter.get('matter_type', 'Unknown')}
Court: {matter.get('court', 'Unknown')}
Jurisdiction: {matter.get('jurisdiction', 'Malaysia')}
Status: {matter.get('status', 'Unknown')}

PARTIES
=======
{self._format_parties(matter.get('parties', []))}

ISSUES
======
{self._format_list(matter.get('issues', []))}

REQUESTED REMEDIES
==================
{self._format_list(matter.get('requested_remedies', []))}

RISK ASSESSMENT
===============
Jurisdictional Complexity: {risk_scores.get('jurisdictional_complexity', 'N/A')}/10
Language Complexity: {risk_scores.get('language_complexity', 'N/A')}/10
Volume Risk: {risk_scores.get('volume_risk', 'N/A')}/10
Time Pressure: {risk_scores.get('time_pressure', 'N/A')}/10
Composite Score: {risk_scores.get('composite_score', 'N/A')}/10

DOCUMENTS
=========
Total Documents: {len(documents)}
"""
        return context
    
    def _format_parties(self, parties: list) -> str:
        if not parties:
            return "No parties identified"
        result = []
        for party in parties:
            if isinstance(party, dict):
                result.append(f"- {party.get('name', 'Unknown')} ({party.get('role', 'Unknown')})")
            else:
                result.append(f"- {party}")
        return "\n".join(result) if result else "No parties identified"
    
    def _format_list(self, items: list) -> str:
        if not items:
            return "None identified"
        result = []
        for item in items:
            if isinstance(item, dict):
                result.append(f"- {item.get('description', str(item))}")
            else:
                result.append(f"- {item}")
        return "\n".join(result) if result else "None identified"
    
    async def _analyze_with_ai(self, context: str) -> Dict:
        """Use Gemini to analyze case strength."""
        prompt = f"""You are a senior Malaysian legal analyst. Analyze the following case and provide a strength assessment.

{context}

Provide your analysis in the following JSON format (respond ONLY with valid JSON, no markdown):
{{
    "win_probability": <number 0-100>,
    "confidence_level": "<high|medium|low>",
    "risks": [
        {{"risk": "<risk description>", "severity": "<high|medium|low>", "mitigation": "<suggested mitigation>"}}
    ],
    "strengths": [
        {{"strength": "<strength description>", "impact": "<high|medium|low>"}}
    ],
    "suggestions": [
        {{"action": "<specific action to take>", "priority": "<high|medium|low>", "reason": "<why this helps>"}}
    ],
    "overall_assessment": "<2-3 sentence summary of case prospects>",
    "key_factors": [
        "<factor 1>",
        "<factor 2>",
        "<factor 3>"
    ]
}}

Consider Malaysian legal standards, evidence strength, procedural compliance, and precedent support.
If information is limited, make reasonable assessments based on available data.
"""

        response = self.model.generate_content(prompt)
        response_text = response.text.strip()
        
        # Clean up response if it has markdown code blocks
        if response_text.startswith("```"):
            response_text = response_text.split("```")[1]
            if response_text.startswith("json"):
                response_text = response_text[4:]
        if response_text.endswith("```"):
            response_text = response_text[:-3]
        
        return json.loads(response_text.strip())
    
    def _get_fallback_analysis(self, matter: Dict, risk_scores: Dict) -> Dict:
        """Provide fallback analysis if AI fails."""
        composite = risk_scores.get('composite_score', 5)
        
        # Estimate probability based on risk score (inverted)
        probability = max(20, min(80, int(100 - (composite * 8))))
        
        return {
            "win_probability": probability,
            "confidence_level": "low",
            "risks": [
                {"risk": "Limited case information available", "severity": "medium", "mitigation": "Gather more documentation"},
                {"risk": f"Risk score is {composite}/10", "severity": "medium" if composite < 7 else "high", "mitigation": "Address high-risk areas"}
            ],
            "strengths": [
                {"strength": "Case has been properly filed", "impact": "medium"},
                {"strength": "Documents are organized", "impact": "low"}
            ],
            "suggestions": [
                {"action": "Complete document collection", "priority": "high", "reason": "More evidence improves assessment accuracy"},
                {"action": "Review case with senior counsel", "priority": "medium", "reason": "Expert review can identify additional factors"}
            ],
            "overall_assessment": "This is a preliminary assessment based on limited information. More detailed analysis requires additional case documentation.",
            "key_factors": [
                "Evidence completeness",
                "Legal precedent support",
                "Procedural compliance"
            ]
        }


# Singleton instance
_case_strength_agent = None

def get_case_strength_agent() -> CaseStrengthAgent:
    global _case_strength_agent
    if _case_strength_agent is None:
        _case_strength_agent = CaseStrengthAgent()
    return _case_strength_agent

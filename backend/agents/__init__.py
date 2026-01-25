"""
Agents package initialization with lazy loading.
This prevents the entire application from crashing if a single dependency 
for an agent (like playwright or pytesseract) is missing.
"""
import importlib
from typing import Any

# Mapping of class names to their module names
AGENT_MODULE_MAP = {
    "BaseAgent": "base_agent",
    "DocumentCollectorAgent": "document_collector",
    "OCRLanguageAgent": "ocr_language",
    "TranslationAgent": "translation",
    "CaseStructuringAgent": "case_structuring",
    "RiskScoringAgent": "risk_scoring",
    "MalayDraftingAgent": "malay_drafting",
    "IssuePlannerAgent": "issue_planner",
    "TemplateComplianceAgent": "template_compliance",
    "EnglishCompanionAgent": "english_companion",
    "ConsistencyQAAgent": "consistency_qa",
    "ResearchAgent": "research",
    "ArgumentBuilderAgent": "argument_builder",
    "TranslationCertificationAgent": "translation_certification",
    "EvidenceBuilderAgent": "evidence_builder",
    "HearingPrepAgent": "hearing_prep",
}

def __getattr__(name: str) -> Any:
    """Lazy-load agents when they are accessed."""
    if name in AGENT_MODULE_MAP:
        module_name = AGENT_MODULE_MAP[name]
        try:
            module = importlib.import_module(f"agents.{module_name}")
            return getattr(module, name)
        except Exception as e:
            # Fallback or re-raise with better context if needed
            # For now, we let the individual agent handle its own missing dependencies
            # but we ensure the module itself can be imported.
            raise ImportError(f"Could not import {name} from agents.{module_name}: {e}")
    
    raise AttributeError(f"module {__name__} has no attribute {name}")

# For IDE support and __all__
__all__ = list(AGENT_MODULE_MAP.keys())

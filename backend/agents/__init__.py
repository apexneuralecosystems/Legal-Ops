"""
Agents package initialization.
"""
from agents.base_agent import BaseAgent
from agents.document_collector import DocumentCollectorAgent
from agents.ocr_language import OCRLanguageAgent
from agents.translation import TranslationAgent
from agents.case_structuring import CaseStructuringAgent
from agents.risk_scoring import RiskScoringAgent
from agents.malay_drafting import MalayDraftingAgent
from agents.issue_planner import IssuePlannerAgent
from agents.template_compliance import TemplateComplianceAgent
from agents.english_companion import EnglishCompanionAgent
from agents.consistency_qa import ConsistencyQAAgent
from agents.research import ResearchAgent
from agents.argument_builder import ArgumentBuilderAgent
from agents.translation_certification import TranslationCertificationAgent
from agents.evidence_builder import EvidenceBuilderAgent
from agents.hearing_prep import HearingPrepAgent

__all__ = [
    "BaseAgent",
    "DocumentCollectorAgent",
    "OCRLanguageAgent",
    "TranslationAgent",
    "CaseStructuringAgent",
    "RiskScoringAgent",
    "MalayDraftingAgent",
    "IssuePlannerAgent",
    "TemplateComplianceAgent",
    "EnglishCompanionAgent",
    "ConsistencyQAAgent",
    "ResearchAgent",
    "ArgumentBuilderAgent",
    "TranslationCertificationAgent",
    "EvidenceBuilderAgent",
    "HearingPrepAgent",
]

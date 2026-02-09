"""
SQLAlchemy models package.
"""
from .matter import Matter
from .document import Document
from .segment import Segment
from .pleading import Pleading
from .research import ResearchCase
from .audit import AuditLog
from .auth import User
from .usage import UserUsage
from .ocr_models import OCRDocument, OCRPage, OCRChunk, OCRProcessingLog
from .chat import ChatMessage, CaseLearning
from .case_intelligence import CaseEntity, CaseRelationship
from .case_insights import CaseInsight, CaseMetric
from .cross_case_learning import CasePattern, CaseOutcome, CaseSimilarity

__all__ = [
    "Matter",
    "Document",
    "Segment",
    "Pleading",
    "ResearchCase",
    "AuditLog",
    "User",
    "UserUsage",
    "OCRDocument",
    "OCRPage",
    "OCRChunk",
    "OCRProcessingLog",
    "ChatMessage",
    "CaseLearning",
    "CaseEntity",
    "CaseRelationship",
    "CaseInsight",
    "CaseMetric",
    "CasePattern",
    "CaseOutcome",
    "CaseSimilarity",
]

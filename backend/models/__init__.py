"""
SQLAlchemy models package.
"""
from models.matter import Matter
from models.document import Document
from models.segment import Segment
from models.pleading import Pleading
from models.research import ResearchCase
from models.audit import AuditLog
from models.auth import User
from models.usage import UserUsage
from models.ocr_models import OCRDocument, OCRPage, OCRChunk, OCRProcessingLog
from models.chat import ChatMessage, CaseLearning
from models.case_intelligence import CaseEntity, CaseRelationship
from models.case_insights import CaseInsight, CaseMetric
from models.cross_case_learning import CasePattern, CaseOutcome, CaseSimilarity

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

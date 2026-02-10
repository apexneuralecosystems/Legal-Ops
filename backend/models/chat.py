"""Chat message model for conversation memory"""
from sqlalchemy import Column, String, Text, Boolean, DateTime, Integer, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
from database import Base


class ChatMessage(Base):
    __tablename__ = "chat_messages"

    id = Column(String(36), primary_key=True)
    matter_id = Column(String(36), ForeignKey("matters.id", ondelete="CASCADE"), nullable=False, index=True)
    conversation_id = Column(String(36), nullable=False, index=True)  # Groups related messages
    user_id = Column(String(36), nullable=True)
    
    # Message content
    role = Column(String(20), nullable=False)  # 'user' or 'assistant'
    message = Column(Text, nullable=False)
    
    # Metadata about the response
    method = Column(String(50), nullable=True)  # 'long_context_full_text', 'rag', etc.
    context_used = Column(Text, nullable=True)  # JSON list of document names
    confidence = Column(String(20), nullable=True)  # 'high', 'medium', 'low'
    
    # User feedback
    helpful = Column(Boolean, nullable=True)  # Thumbs up/down
    user_correction = Column(Text, nullable=True)  # If user provides correction
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    
    # Relationships
    matter = relationship("Matter", backref="chat_messages")


class CaseLearning(Base):
    """Store learnings from user corrections for future use"""
    __tablename__ = "case_learnings"
    
    id = Column(String(36), primary_key=True)
    matter_id = Column(String(36), ForeignKey("matters.id", ondelete="CASCADE"), nullable=False, index=True)
    
    learning_type = Column(String(50), nullable=False)  # 'correction', 'clarification', 'new_fact'
    original_text = Column(Text, nullable=True)
    corrected_text = Column(Text, nullable=False)
    importance = Column(Integer, default=3)  # 1-5 scale, higher = more important
    
    # Source tracking
    source_message_id = Column(String(36), ForeignKey("chat_messages.id", ondelete="SET NULL"), nullable=True)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    applied_count = Column(Integer, default=0)  # How many times this learning was used
    
    # Relationships
    matter = relationship("Matter", backref="learnings")

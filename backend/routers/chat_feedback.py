"""Feedback endpoint for chat messages"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from database import get_sync_db as get_db
from models.chat import ChatMessage, CaseLearning
from pydantic import BaseModel
from typing import Optional
from uuid import uuid4
from datetime import datetime
import logging

router = APIRouter()
logger = logging.getLogger(__name__)


class FeedbackRequest(BaseModel):
    message_id: str
    helpful: bool
    correction: Optional[str] = None
    importance: Optional[int] = 3  # 1-5 scale


@router.post("/chat/feedback")
async def submit_chat_feedback(
    feedback: FeedbackRequest,
    db: Session = Depends(get_db)
):
    """
    Submit feedback on a chat message.
    
    - helpful: True = thumbs up, False = thumbs down
    - correction: Optional text correction from user
    - importance: How important is this correction (1-5, default 3)
    """
    try:
        # Find the message
        message = db.query(ChatMessage).filter(
            ChatMessage.id == feedback.message_id
        ).first()
        
        if not message:
            raise HTTPException(status_code=404, detail="Message not found")
        
        # Update message feedback
        message.helpful = feedback.helpful
        if feedback.correction:
            message.user_correction = feedback.correction
        
        # If user provided correction, create a case learning
        if feedback.correction and not feedback.helpful:
            learning = CaseLearning(
                id=str(uuid4()),
                matter_id=message.matter_id,
                learning_type="correction",
                original_text=message.message[:500],  # Store first 500 chars
                corrected_text=feedback.correction,
                importance=feedback.importance or 3,
                source_message_id=message.id,
                created_at=datetime.utcnow()
            )
            db.add(learning)
            logger.info(f"Created case learning from correction for matter {message.matter_id}")
        
        db.commit()
        
        return {
            "success": True,
            "message": "Feedback recorded",
            "learning_created": feedback.correction is not None and not feedback.helpful
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error submitting feedback: {e}")
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/chat/history/{conversation_id}")
async def get_conversation_history(
    conversation_id: str,
    limit: int = 50,
    db: Session = Depends(get_db)
):
    """Get full conversation history"""
    try:
        messages = db.query(ChatMessage).filter(
            ChatMessage.conversation_id == conversation_id
        ).order_by(ChatMessage.created_at).limit(limit).all()
        
        return {
            "conversation_id": conversation_id,
            "total_messages": len(messages),
            "messages": [
                {
                    "id": msg.id,
                    "role": msg.role,
                    "message": msg.message,
                    "method": msg.method,
                    "confidence": msg.confidence,
                    "helpful": msg.helpful,
                    "created_at": msg.created_at.isoformat()
                }
                for msg in messages
            ]
        }
    except Exception as e:
        logger.error(f"Error fetching conversation history: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/learnings/{matter_id}")
async def get_case_learnings(
    matter_id: str,
    db: Session = Depends(get_db)
):
    """Get all learnings/corrections for a case"""
    try:
        learnings = db.query(CaseLearning).filter(
            CaseLearning.matter_id == matter_id
        ).order_by(CaseLearning.importance.desc(), CaseLearning.created_at.desc()).all()
        
        return {
            "matter_id": matter_id,
            "total_learnings": len(learnings),
            "learnings": [
                {
                    "id": l.id,
                    "type": l.learning_type,
                    "corrected_text": l.corrected_text,
                    "importance": l.importance,
                    "applied_count": l.applied_count,
                    "created_at": l.created_at.isoformat()
                }
                for l in learnings
            ]
        }
    except Exception as e:
        logger.error(f"Error fetching case learnings: {e}")
        raise HTTPException(status_code=500, detail=str(e))

"""
AI Tasks API router - Endpoints for real-time AI task status.
"""
from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session
from database import get_sync_db as get_db
from models import Matter
from typing import List, Dict, Any
from datetime import datetime, timedelta
import logging

router = APIRouter()
logger = logging.getLogger(__name__)



@router.get("/tasks", response_model=Dict[str, Any])
def get_ai_tasks(
    request: Request,
    limit: int = 10,
    db: Session = Depends(get_db)
):

    """
    Get real-time AI task status based on active matters.
    
    Returns tasks from matters that are currently being processed,
    with status inferred from matter workflow state.
    """
    # Get recently updated matters (active workflows)
    recent_cutoff = datetime.utcnow() - timedelta(hours=24)
    
    matters = db.query(Matter).filter(
        Matter.updated_at >= recent_cutoff
    ).order_by(Matter.updated_at.desc()).limit(limit).all()
    
    tasks = []
    
    for matter in matters:
        # Generate tasks based on matter status
        status = matter.status or "intake"
        matter_id = matter.id
        title = matter.title or f"Matter {matter_id[:8]}..."
        
        # Count documents for this matter
        from models import Document
        doc_count = db.query(Document).filter(Document.matter_id == matter_id).count()
        
        if status == "intake":
            # Intake workflow tasks
            tasks.extend([
                {
                    "id": f"task-{matter_id}-ocr",
                    "matter_id": matter_id,
                    "agent": "OCRLanguageAgent",
                    "type": "OCR Processing",
                    "status": "completed" if doc_count > 0 else "in_progress",
                    "description": f"Processing documents for {title}",
                    "progress": 100 if doc_count > 0 else 50,
                    "started_at": matter.created_at.isoformat() if matter.created_at else None,
                },
                {
                    "id": f"task-{matter_id}-translate",
                    "matter_id": matter_id,
                    "agent": "TranslationAgent", 
                    "type": "Translation",
                    "status": "completed" if doc_count > 0 else "in_progress",
                    "description": f"Translating documents for {title}",
                    "progress": 100 if doc_count > 0 else 30,
                    "started_at": matter.created_at.isoformat() if matter.created_at else None,
                },
                {
                    "id": f"task-{matter_id}-structure",
                    "matter_id": matter_id,
                    "agent": "CaseStructuringAgent",
                    "type": "Case Structuring",
                    "status": "completed" if matter.parties else "pending",
                    "description": f"Structuring case details for {title}",
                    "progress": 100 if matter.parties else 0,
                    "started_at": matter.created_at.isoformat() if matter.created_at else None,
                },
            ])
        
        elif status == "drafting":
            tasks.append({
                "id": f"task-{matter_id}-draft",
                "matter_id": matter_id,
                "agent": "MalayDraftingAgent",
                "type": "Pleading Draft",
                "status": "in_progress",
                "description": f"Drafting pleadings for {title}",
                "progress": 60,
                "started_at": matter.updated_at.isoformat() if matter.updated_at else None,
            })
        
        elif status == "research":
            tasks.append({
                "id": f"task-{matter_id}-research",
                "matter_id": matter_id,
                "agent": "ResearchAgent",
                "type": "Legal Research",
                "status": "in_progress",
                "description": f"Researching cases for {title}",
                "progress": 45,
                "started_at": matter.updated_at.isoformat() if matter.updated_at else None,
            })
        
        elif status in ["evidence", "hearing"]:
            tasks.append({
                "id": f"task-{matter_id}-evidence",
                "matter_id": matter_id,
                "agent": "EvidenceBuilderAgent",
                "type": "Evidence Bundle",
                "status": "in_progress",
                "description": f"Preparing evidence for {title}",
                "progress": 70,
                "started_at": matter.updated_at.isoformat() if matter.updated_at else None,
            })
    
    # Sort by status (in_progress first, then pending, then completed)
    status_order = {"in_progress": 0, "pending": 1, "completed": 2}
    tasks.sort(key=lambda x: status_order.get(x["status"], 3))
    
    return {
        "tasks": tasks[:limit],
        "total": len(tasks),
        "last_updated": datetime.utcnow().isoformat()
    }


@router.get("/tasks/{task_id}", response_model=Dict[str, Any])
def get_task_detail(task_id: str, db: Session = Depends(get_db)):

    """
    Get detailed status of a specific AI task.
    """
    # Parse matter_id from task_id
    parts = task_id.split("-")
    if len(parts) < 3:
        return {"error": "Invalid task ID format", "task_id": task_id}
    
    matter_id = parts[1]
    
    matter = db.query(Matter).filter(Matter.id == matter_id).first()
    if not matter:
        return {"error": "Matter not found", "task_id": task_id}
    
    return {
        "task_id": task_id,
        "matter_id": matter_id,
        "matter_title": matter.title,
        "status": matter.status,
        "created_at": matter.created_at.isoformat() if matter.created_at else None,
        "updated_at": matter.updated_at.isoformat() if matter.updated_at else None,
    }

"""
Matters API router - Endpoints for matter management and workflows.
"""
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any
from pydantic import BaseModel
from database import get_sync_db as get_db
from models import Matter, Document
from models.pleading import Pleading
from models.segment import Segment
from orchestrator import OrchestrationController
from config import settings
from jose import JWTError, jwt
from utils.sync_usage_tracker import SyncUsageTracker
import json
import logging

router = APIRouter()
controller = OrchestrationController()
security = HTTPBearer()

# Sync version of auth dependency for backward compatibility
def get_current_user_sync(
    credentials: HTTPAuthorizationCredentials = Depends(security),
) -> Dict[str, Any]:
    """
    Sync version of get_current_user for existing sync endpoints.
    """
    token = credentials.credentials
    
    try:
        payload = jwt.decode(
            token,
            settings.SECRET_KEY,
            algorithms=[settings.ALGORITHM]
        )
        user_id = payload.get("sub")
        email = payload.get("email")
        
        if user_id is None:
            raise HTTPException(
                status_code=401,
                detail="Invalid authentication credentials",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        return {"user_id": user_id, "email": email}
        
    except JWTError:
        raise HTTPException(
            status_code=401,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )


# Pydantic schemas
class MatterResponse(BaseModel):
    matter_id: str
    title: str
    status: str
    court: Optional[str]
    jurisdiction: Optional[str]
    primary_language: str
    human_review_required: bool
    
    class Config:
        from_attributes = True


class IntakeRequest(BaseModel):
    connector_type: str
    metadata: dict = {}


class DraftingRequest(BaseModel):
    template_id: str = "TPL-HighCourt-MS-v2"
    issues_selected: List[dict] = []
    prayers_selected: List[dict] = []


@router.post("/intake", response_model=dict)
async def start_intake_workflow(
    files: List[UploadFile] = File(None),
    connector_type: str = Form("upload"),
    metadata: str = Form("{}"),
    db: Session = Depends(get_db),
    current_user: Dict[str, Any] = Depends(get_current_user_sync)
):
    print(f"DEBUG: Received intake request. Files: {len(files) if files else 0}, Connector: {connector_type}")
    """
    Start the intake workflow to process uploaded documents.
    
    Workflow: Document Collection → OCR → Translation → Case Structuring → Risk Scoring
    
    Args:
        files: Optional list of files to upload (can be empty for manual matter creation)
        connector_type: Type of connector (upload, email, etc.)
        metadata: JSON string with additional metadata
    
    Returns:
        Matter snapshot with risk scores
        
    Raises:
        402 Payment Required: If user has exhausted free uses and needs to subscribe
    """
    
    # Check usage limits - will raise 402 if payment required
    user_id = current_user["user_id"]
    usage_result = SyncUsageTracker.require_usage_or_payment(user_id, "intake", db)
    
    # Parse metadata
    try:
        metadata_dict = json.loads(metadata)
    except:
        metadata_dict = {}
    
    # Create matter record
    matter = Matter(
        title="New Matter - Processing",
        matter_type="general",
        status="intake",
        created_by=user_id  # Use authenticated user ID
    )
    db.add(matter)
    db.commit()
    db.refresh(matter)
    
    # Prepare file data (handle empty/None files list)
    file_data = []
    if files:
        for file in files:
            content = await file.read()
            file_data.append({
                "filename": file.filename,
                "content": content,
                "mime_type": file.content_type or "application/octet-stream"
            })
    
    # Run intake workflow
    logger = logging.getLogger(__name__)
    logger.info(f"Starting intake workflow for matter {matter.id} with {len(file_data)} files")
    
    try:
        result = await controller.run_intake_workflow(
            files=file_data,
            connector_type=connector_type,
            metadata=metadata_dict,
            matter_id=matter.id
        )
        
        workflow_status = result.get('workflow_status')
        logger.info(f"Intake workflow completed with status: {workflow_status}")
        
        if workflow_status == "failed":
            error_msg = result.get('error', 'Unknown error')
            logger.error(f"Workflow failed: {error_msg}")
            matter.status = "failed"
            matter.title = f"Failed - {matter.title}"
            db.commit()
            
            return {
                "status": "error",
                "message": f"Intake workflow failed: {error_msg}",
                "matter_id": matter.id,
                "error_details": error_msg
            }
    except Exception as e:
        logger.error(f"Exception during intake workflow: {str(e)}", exc_info=True)
        matter.status = "failed"
        matter.title = f"Error - {matter.title}"
        db.commit()
        
        return {
            "status": "error",
            "message": f"Intake workflow exception: {str(e)}",
            "matter_id": matter.id,
            "error_details": str(e)
        }
    
    logger.info(f"Intake workflow result: {result.get('workflow_status')}")
    
    # Update matter with results
    if result.get("workflow_status") == "completed":
        matter_snapshot = result.get("matter_snapshot", {})
        risk_scores = result.get("risk_scores", {})
        
        matter.title = matter_snapshot.get("title") or matter.title
        matter.matter_type = matter_snapshot.get("case_type", "general")
        matter.court = matter_snapshot.get("court")
        matter.jurisdiction = matter_snapshot.get("jurisdiction")
        matter.primary_language = matter_snapshot.get("primary_language", "ms")
        matter.parties = matter_snapshot.get("parties", [])
        matter.key_dates = matter_snapshot.get("key_dates", [])
        matter.issues = matter_snapshot.get("issues", [])
        matter.requested_remedies = matter_snapshot.get("requested_remedies", [])
        matter.volume_estimate = matter_snapshot.get("volume_estimate")
        matter.estimated_pages = matter_snapshot.get("estimated_pages")
        
        # Risk scores
        matter.jurisdictional_complexity = risk_scores.get("jurisdictional_complexity")
        matter.language_complexity = risk_scores.get("language_complexity")
        matter.volume_risk = risk_scores.get("volume_risk")
        matter.time_pressure = risk_scores.get("time_pressure")
        matter.composite_score = risk_scores.get("composite_score")
        matter.risk_rationale = risk_scores.get("rationale", [])
        matter.human_review_required = risk_scores.get("human_review_required", False)
        
        matter.status = "structured"
        
        # Save documents to database
        document_manifest = result.get("document_manifest", [])
        logger.info(f"Saving {len(document_manifest)} documents to database")
        
        for doc_data in document_manifest:
            try:
                # Check if document already exists
                existing_doc = db.query(Document).filter(Document.file_hash == doc_data.get("file_hash")).first()
                
                if not existing_doc:
                    new_doc = Document(
                        id=doc_data.get("doc_id"),
                        matter_id=matter.id,
                        filename=doc_data.get("filename"),
                        mime_type=doc_data.get("mime_type"),
                        file_size=doc_data.get("size_bytes"),
                        file_hash=doc_data.get("file_hash"),
                        file_path=f"uploads/{doc_data.get('filename')}", # Placeholder for local storage
                        source="system",
                        ocr_completed=True
                    )
                    db.add(new_doc)
                    logger.info(f"Saved document {new_doc.id}: {new_doc.filename}")
                else:
                    logger.info(f"Document {doc_data.get('filename')} already exists")
            except Exception as e:
                logger.error(f"Failed to save document {doc_data.get('filename')}: {e}")
        
        db.commit()
    
    def sanitize_for_json(obj):
        """Recursively remove bytes and non-serializable objects."""
        if isinstance(obj, bytes):
            return "<binary_data_removed>"
        elif isinstance(obj, dict):
            return {k: sanitize_for_json(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [sanitize_for_json(i) for i in obj]
        else:
            return obj

    # Sanitize result before returning
    cleaned_result = sanitize_for_json(result)
    
    return {
        "status": "success",
        "matter_id": matter.id,
        "workflow_result": cleaned_result
    }


@router.get("/", response_model=List[MatterResponse])
async def list_matters(
    skip: int = 0,
    limit: int = 50,
    status: Optional[str] = None,
    db: Session = Depends(get_db)
    # Temporarily removed for testing
    # current_user: Dict[str, Any] = Depends(get_current_user_sync)
):
    """
    List all matters with optional filtering.
    
    Args:
        skip: Number of records to skip
        limit: Maximum number of records to return
        status: Filter by status (intake, structured, drafting, ready, filed)
    """
    query = db.query(Matter)
    
    if status:
        query = query.filter(Matter.status == status)
    
    matters = query.offset(skip).limit(limit).all()
    
    return [MatterResponse.from_orm(m) for m in matters]


@router.get("/{matter_id}", response_model=dict)
async def get_matter(matter_id: str, db: Session = Depends(get_db)):
    # Auth temporarily removed for testing
    """
    Get detailed matter information including snapshot and risk scores.
    """
    matter = db.query(Matter).filter(Matter.id == matter_id).first()
    
    if not matter:
        raise HTTPException(status_code=404, detail="Matter not found")
    
    return matter.to_dict()


@router.delete("/{matter_id}", response_model=dict)
async def delete_matter(matter_id: str, db: Session = Depends(get_db)):
    # Auth temporarily removed for testing
    """
    Delete a matter and all associated documents, segments, and pleadings.
    """
    matter = db.query(Matter).filter(Matter.id == matter_id).first()
    
    if not matter:
        raise HTTPException(status_code=404, detail="Matter not found")
    
    try:
        # Delete associated pleadings
        db.query(Pleading).filter(Pleading.matter_id == matter_id).delete()
        
        # Delete associated documents (segments are cascade deleted via relationship)
        db.query(Document).filter(Document.matter_id == matter_id).delete()
        
        # Delete the matter
        db.delete(matter)
        db.commit()
        
        return {
            "status": "success",
            "message": f"Matter {matter_id} and all associated data deleted successfully"
        }
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to delete matter: {str(e)}")


@router.post("/{matter_id}/draft", response_model=dict)
async def start_drafting_workflow(
    matter_id: str,
    request: DraftingRequest,
    db: Session = Depends(get_db),
    current_user: Dict[str, Any] = Depends(get_current_user_sync)
):
    """
    Start the drafting workflow for a matter.
    
    Workflow: Issue Planning → Template Selection → Malay Drafting → English Companion → QA
    
    Returns:
        Pleading with Malay and English versions
    """
    matter = db.query(Matter).filter(Matter.id == matter_id).first()
    
    if not matter:
        raise HTTPException(status_code=404, detail="Matter not found")
    
    # Prepare matter snapshot
    matter_snapshot = matter.to_dict()
    
    # Run drafting workflow
    result = await controller.run_drafting_workflow(
        matter_snapshot=matter_snapshot,
        template_id=request.template_id,
        issues_selected=request.issues_selected,
        prayers_selected=request.prayers_selected
    )
    
    # Save pleading to database
    if result.get("workflow_status") == "completed":
        
        pleading_data = result.get("pleading_ms", {})
        
        pleading = Pleading(
            matter_id=matter_id,
            pleading_type="statement_of_claim",
            template_id=request.template_id,
            pleading_ms_text=pleading_data.get("pleading_ms_text"),
            pleading_ms_confidence=pleading_data.get("confidence"),
            paragraph_map=pleading_data.get("paragraph_map", []),
            issues_used=request.issues_selected,
            prayers_used=request.prayers_selected,
            status="draft",
            created_by="system"
        )
        
        db.add(pleading)
        matter.status = "drafting"
        db.commit()
        db.refresh(pleading)
        
        result["pleading_id"] = pleading.id
    
    return {
        "status": "success",
        "matter_id": matter_id,
        "workflow_result": result
    }


@router.get("/{matter_id}/documents", response_model=List[dict])
async def get_matter_documents(matter_id: str, db: Session = Depends(get_db)):
    """
    Get all documents for a matter.
    """
    documents = db.query(Document).filter(Document.matter_id == matter_id).all()
    
    return [doc.to_dict() for doc in documents]


@router.get("/{matter_id}/parallel-view", response_model=dict)
async def get_parallel_view(matter_id: str, db: Session = Depends(get_db)):
    """
    Get parallel text view (Malay ↔ English segments) for a matter.
    """
    
    # Get all documents for this matter
    documents = db.query(Document).filter(Document.matter_id == matter_id).all()
    doc_ids = [doc.id for doc in documents]
    
    # Get all segments
    segments = db.query(Segment).filter(Segment.document_id.in_(doc_ids)).all()
    
    # Group by document
    parallel_data = {}
    for segment in segments:
        if segment.document_id not in parallel_data:
            parallel_data[segment.document_id] = []
        
        parallel_data[segment.document_id].append(segment.to_dict())
    
    return {
        "matter_id": matter_id,
        "parallel_segments": parallel_data
    }


# Evidence Workflow Endpoints

class CertifyTranslationRequest(BaseModel):
    document_id: str


@router.post("/{matter_id}/certify-translation", response_model=dict)
async def certify_translation(
    matter_id: str,
    request: CertifyTranslationRequest,
    db: Session = Depends(get_db)
):
    """
    Generate translation certification for a document.
    
    Args:
        matter_id: Matter ID
        request: Request containing document_id
        
    Returns:
        Translation certification document
    """
    
    matter = db.query(Matter).filter(Matter.id == matter_id).first()
    
    if not matter:
        raise HTTPException(status_code=404, detail="Matter not found")
    
    # Get document
    document = db.query(Document).filter(Document.id == request.document_id).first()
    
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")
    
    # Run translation certification via evidence workflow
    result = await controller.run_evidence_workflow(
        matter_id=matter_id,
        documents=[document.to_dict()]
    )
    
    if result.get("workflow_status") == "completed":
        return {
            "status": "success",
            "matter_id": matter_id,
            "translation_cert": result.get("translation_cert", {})
        }
    else:
        return {
            "status": "error",
            "message": result.get("error", "Translation certification failed")
        }


class EvidencePacketRequest(BaseModel):
    documents: List[dict]


@router.post("/{matter_id}/build-evidence-packet", response_model=dict)
async def build_evidence_packet(
    matter_id: str,
    request: EvidencePacketRequest,
    db: Session = Depends(get_db)
):
    """
    Build evidence packet from selected documents.
    
    Args:
        matter_id: Matter ID
        request: Request containing list of documents
        
    Returns:
        Evidence packet with organized documents
    """
    documents = request.documents
    
    matter = db.query(Matter).filter(Matter.id == matter_id).first()
    
    if not matter:
        raise HTTPException(status_code=404, detail="Matter not found")
    
    # Run evidence workflow
    logger = logging.getLogger(__name__)
    logger.info(f"Building evidence packet for matter {matter_id} with {len(documents)} documents")
    
    result = None
    try:
        result = await controller.run_evidence_workflow(
            matter_id=matter_id,
            documents=documents
        )
    except Exception as e:
        logger.error(f"Evidence workflow exception: {e}", exc_info=True)
        return {
            "status": "error",
            "message": f"Evidence workflow failed: {str(e)}"
        }
    
    if not result:
        logger.error("Evidence workflow returned None")
        return {
            "status": "error",
            "message": "Evidence workflow failed to return result"
        }
    
    logger.info(f"Evidence workflow result: {result.get('workflow_status')}")
    
    if result.get("workflow_status") == "completed":
        return {
            "status": "success",
            "matter_id": matter_id,
            "evidence_packet": result.get("evidence_packet", {})
        }
    else:
        return {
            "status": "error",
            "message": result.get("error", "Evidence packet building failed")
        }


@router.post("/{matter_id}/prepare-hearing", response_model=dict)
async def prepare_hearing(matter_id: str, db: Session = Depends(get_db)):
    """
    Prepare hearing bundle for a matter.
    
    Args:
        matter_id: Matter ID
        
    Returns:
        Hearing bundle with all required documents
    """
    
    matter = db.query(Matter).filter(Matter.id == matter_id).first()
    
    if not matter:
        raise HTTPException(status_code=404, detail="Matter not found")
    
    # Get all documents for this matter
    documents = db.query(Document).filter(Document.matter_id == matter_id).all()
    
    # Run evidence workflow
    result = await controller.run_evidence_workflow(
        matter_id=matter_id,
        documents=[doc.to_dict() for doc in documents]
    )
    
    if result.get("workflow_status") == "completed":
        return {
            "status": "success",
            "matter_id": matter_id,
            "hearing_bundle": result.get("hearing_bundle", {})
        }
    else:
        return {
            "status": "error",
            "message": result.get("error", "Hearing preparation failed")
        }


@router.get("/{matter_id}/hearing-bundle", response_model=dict)
async def get_hearing_bundle(matter_id: str, db: Session = Depends(get_db)):
    """
    Retrieve prepared hearing bundle for a matter.
    
    Args:
        matter_id: Matter ID
        
    Returns:
        Previously prepared hearing bundle
    """
    
    matter = db.query(Matter).filter(Matter.id == matter_id).first()
    
    if not matter:
        raise HTTPException(status_code=404, detail="Matter not found")
    
    # For now, return the matter snapshot
    # In production, this would retrieve stored hearing bundle
    return {
        "status": "success",
        "matter_id": matter_id,
        "hearing_bundle": {
            "matter_snapshot": matter.to_dict(),
            "documents_count": db.query(Document).filter(Document.matter_id == matter_id).count(),
            "status": "ready"
        }
    }


@router.post("/{matter_id}/analyze-strength", response_model=dict)
async def analyze_case_strength(matter_id: str, db: Session = Depends(get_db)):
    """
    Analyze case strength using AI.
    
    Returns:
        - win_probability: 0-100%
        - risks: Identified weaknesses
        - strengths: Identified advantages
        - suggestions: Improvement recommendations
    """
    matter = db.query(Matter).filter(Matter.id == matter_id).first()
    
    if not matter:
        raise HTTPException(status_code=404, detail="Matter not found")
    
    # Get documents for the matter
    documents = db.query(Document).filter(Document.matter_id == matter_id).all()
    doc_list = [doc.to_dict() for doc in documents]
    
    # Prepare risk scores
    risk_scores = {
        "jurisdictional_complexity": matter.jurisdictional_complexity,
        "language_complexity": matter.language_complexity,
        "volume_risk": matter.volume_risk,
        "time_pressure": matter.time_pressure,
        "composite_score": matter.composite_score
    }
    
    # Use the Case Strength Agent
    from agents.case_strength import get_case_strength_agent
    agent = get_case_strength_agent()
    
    result = await agent.process({
        "matter": matter.to_dict(),
        "documents": doc_list,
        "risk_scores": risk_scores
    })
    
    if result.get("status") == "success":
        return {
            "status": "success",
            "matter_id": matter_id,
            "analysis": result.get("data")
        }
    else:
        return {
            "status": "partial",
            "matter_id": matter_id,
            "analysis": result.get("data"),
            "warning": result.get("error")
        }

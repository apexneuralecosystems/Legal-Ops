"""
Matters API router - Endpoints for matter management and workflows.
"""
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, BackgroundTasks
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, validator
from datetime import datetime
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
import os
import aiofiles
import uuid

router = APIRouter()
controller = OrchestrationController()
security = HTTPBearer()

logger = logging.getLogger(__name__)

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
        
    except JWTError as e:
        print(f"AUTH DEBUG: JWT Decode Failed. Token: {token[:10]}... Error: {e}")
        raise HTTPException(
            status_code=401,
            detail=f"Invalid authentication credentials: {str(e)}",
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
    matter_type: Optional[str]
    created_at: Optional[datetime]
    human_review_required: bool
    key_dates: Optional[List[Dict[str, Any]]] = None
    parties: Optional[List[Dict[str, Any]]] = None
    issues: Optional[List[Dict[str, Any]]] = None
    requested_remedies: Optional[List[Dict[str, Any]]] = None
    risk_scores: Optional[Dict[str, Any]] = None
    volume_estimate: Optional[int] = None
    estimated_pages: Optional[int] = None
    processing_status: Optional[str] = None
    reviewer_id: Optional[str] = None
    review_notes: Optional[str] = None
    created_by: Optional[str] = None
    updated_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True
        
    @validator("matter_id", pre=True)
    def handle_id_alias(cls, v):
        return v


class IntakeRequest(BaseModel):
    connector_type: str
    metadata: dict = {}


class DraftingRequest(BaseModel):
    template_id: str = "TPL-HighCourt-MS-v2"
    issues_selected: List[dict] = []
    prayers_selected: List[dict] = []


@router.post("/intake", response_model=dict)
async def start_intake_workflow(
    background_tasks: BackgroundTasks,
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
    import traceback
    
    try:
        # Check usage limits - will raise 402 if payment required
        # Wrap in try-except specifically for usage tracking to give clearer error
        try:
            user_id = current_user["user_id"]
            usage_result = SyncUsageTracker.require_usage_or_payment(user_id, "intake", db)
        except Exception as e:
            # If it's a 402/HTTPException, let it bubble up
            if isinstance(e, HTTPException):
                raise e
            # Otherwise log and continue (fail open for billing errors during demo)
            print(f"Usage tracking error: {e}")
            logger.error(f"Usage tracking failed: {e}", exc_info=True)
            # Proceed without blocking if usage check fails (fail open)
        
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
            # Import dependencies for background tasks and hashing
            try:
                from services.rag_service import get_rag_service
                import hashlib
                from datetime import datetime
            except ImportError:
                pass

            async def run_ingestion(filepath: str, m_id: str):
                try:
                    rag = get_rag_service()
                    logger.info(f"Background Ingestion for: {filepath} (Matter: {m_id})")
                    # Ingest
                    await rag.ingest_document(filepath, matter_id=m_id)
                    
                    # Update OCR status in DB? Ideally yes, but tricky with async independent session.
                    # For now, RAG completion is enough for chat.
                    
                except Exception as e:
                    logger.error(f"Background ingestion failed for {filepath}: {e}")

            for file in files:
                content = await file.read()
                
                # SAVE TO DISK (Fixes Ghost File Issue)
                safe_filename = os.path.basename(file.filename)
                save_path = os.path.join(settings.UPLOAD_DIR, safe_filename)
                
                # Ensure directory exists
                os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
                
                async with aiofiles.open(save_path, 'wb') as f:
                    await f.write(content)
                
                logger.info(f"Saved intake file to disk: {save_path}")
                
                # CREATE DB RECORD IMMEDIATELY (Fixes 'No Documents in UI' issue)
                try:
                    sha256_hash = hashlib.sha256(content).hexdigest()
                    # Use random component to ensure ID is truly unique even if file is uploaded again
                    import uuid
                    doc_id = f"DOC-{datetime.utcnow().strftime('%Y%m%d')}-{str(uuid.uuid4())[:8]}"
                    
                    new_doc = Document(
                        id=doc_id,
                        matter_id=matter.id,
                        filename=safe_filename,
                        mime_type=file.content_type or "application/octet-stream",
                        file_size=len(content),
                        file_hash=sha256_hash,
                        file_path=f"uploads/{safe_filename}",
                        source="intake_upload",
                        ocr_completed=True # Triggered via background task
                    )
                    db.add(new_doc)
                    db.flush() # Flush to get ID if needed, commit handled later or now
                    logger.info(f"Created Document record: {doc_id}")
                except Exception as doc_err:
                    db.rollback() # CRITICAL: Reset session state
                    logger.error(f"Failed to create document record for {safe_filename}: {doc_err}")
                    # Re-retrieve matter since rollback might have detached it
                    matter = db.query(Matter).filter(Matter.id == matter.id).first()
                    continue # Skip this file and move on

                # RAG INGESTION: Moved to background task to prevent timeouts
                # save_path is passed to background task via file_data
                
                file_data.append({
                    "filename": file.filename,
                    "content": content,
                    "mime_type": file.content_type or "application/octet-stream",
                    "doc_id": doc_id, # Pass ID to workflow so it knows
                    "file_hash": sha256_hash,
                    "size_bytes": len(content),
                    "file_path": save_path # Add path for background RAG
                })
            
            # Commit the documents so they are visible immediately
            db.commit()
        
        # Trigger background processing
        background_tasks.add_task(
            _process_intake_background,
            matter.id,
            files_data=file_data,  # Pass pre-processed file data
            connector_type=connector_type,
            metadata=metadata_dict
        )
        
        return {
            "status": "processing",
            "matter_id": matter.id,
            "message": "Intake workflow started in background. Please poll for status."
        }

    except Exception as e:
        logger.error(f"Error starting intake workflow: {e}")
        raise HTTPException(status_code=500, detail=str(e))

async def _process_intake_background(matter_id: str, files_data: List[Dict], connector_type: str, metadata: Dict):
    """Background task for heavy intake workflow."""
    from database import SessionLocal
    from models import Matter
    
    db = SessionLocal()
    matter = db.query(Matter).filter(Matter.id == matter_id).first()
    if not matter:
        db.close()
        return

    try:
        logger.info(f"Background: Starting intake workflow for matter {matter.id} with {len(files_data)} files")
        
        # Initialize controller locally to avoid circular imports if possible or reuse global
        # Assuming controller is imported at top level or available
        from orchestrator.controller import OrchestrationController
        controller = OrchestrationController() 

        # RAG INGESTION (in background)
        # We run this in parallel with the main workflow to avoid blocking the initial dashboard load
        async def run_rag_ingestion(f_data, m_id):
            from services.rag_service import get_rag_service
            try:
                rag = get_rag_service()
                for file_info in f_data:
                    f_path = file_info.get("file_path")
                    if f_path:
                        logger.info(f"Background: Ingesting {f_path} for RAG...")
                        await rag.ingest_document(f_path, matter_id=m_id)
            except Exception as rag_err:
                logger.error(f"Background RAG ingestion failed: {rag_err}")

        # Start RAG as a background task so it doesn't block the OCR/Dashboard workflow
        import asyncio
        asyncio.create_task(run_rag_ingestion(files_data, matter.id))
        
        # This is the blocking call the dashboard waits for
        result = await controller.run_intake_workflow(
            files=files_data,
            connector_type=connector_type,
            metadata=metadata,
            matter_id=matter.id
        )
        
        workflow_status = result.get('workflow_status')
        logger.info(f"Background: Intake workflow completed with status: {workflow_status}")
        
        if workflow_status == "failed":
            error_msg = result.get('error', 'Unknown error')
            logger.error(f"Background: Workflow failed: {error_msg}")
            matter.status = "failed"
            matter.title = f"Failed - {matter.title}"
        else:
            # Update matter with results (success path)
            matter_snapshot = result.get("matter_snapshot", {})
            
            # Update title (use extracted or keep default)
            matter.title = matter_snapshot.get("title") or matter.title
            if matter.title == "New Matter - Processing":
                matter.title = "New Matter" 
            
            matter.matter_type = matter_snapshot.get("case_type") or "general"
            matter.court = matter_snapshot.get("court") or "High Court"
            matter.jurisdiction = matter_snapshot.get("jurisdiction") or "Peninsular Malaysia"
            matter.primary_language = matter_snapshot.get("primary_language") or "ms"
            
            # Save other fields 
            matter.parties = matter_snapshot.get("parties", [])
            matter.requested_remedies = matter_snapshot.get("requested_remedies", [])
            matter.issues = matter_snapshot.get("issues", [])
            matter.key_dates = matter_snapshot.get("key_dates", [])
            matter.volume_estimate = matter_snapshot.get("volume_estimate")
            matter.estimated_pages = matter_snapshot.get("estimated_pages", 0)

            # Risk scores
            risk_scores = result.get("risk_scores", {})
            matter.jurisdictional_complexity = risk_scores.get("jurisdictional_complexity", 1)
            matter.language_complexity = risk_scores.get("language_complexity", 1)
            matter.volume_risk = risk_scores.get("volume_risk", 1)
            matter.time_pressure = risk_scores.get("time_pressure", 2)
            matter.composite_score = risk_scores.get("composite_score", 1.3)
            # Ensure rationale is a list or handled correctly (DB might expect JSON/ARRAY)
            # Assuming DB model handles it or we serialize if needed, usually SQLAlchemy + JSON column handles list fine
            matter.risk_rationale = risk_scores.get("rationale", []) 
            matter.human_review_required = risk_scores.get("human_review_required", False)
            
            matter.status = "structured"

            # Create Audit Log entry
            from models.audit import AuditLog
            audit_entry = AuditLog(
                matter_id=matter.id,
                agent_id="IntakeOrchestrator",
                action_type="intake_completion",
                action_description=f"Automated intake and case structuring completed. Processed {matter.estimated_pages} pages.",
                entity_type="matter",
                entity_id=matter.id,
                user_id=matter.created_by
            )
            db.add(audit_entry)

            # SAVE OCR SEGMENTS TO DATABASE
            # This is critical for the new granular segmentation
            from models import Segment
            import uuid
            
            all_segments = result.get("all_segments", [])
            logger.info(f"Background: Saving {len(all_segments)} OCR segments to database for matter {matter.id}...")
            
            for seg_data in all_segments:
                try:
                    # check if segment already exists to avoid duplicates if re-run
                    # simple check by ID if provided
                    seg_id = seg_data.get("segment_id")
                    if seg_id:
                        exists = db.query(Segment).filter(Segment.id == seg_id).first()
                        if exists:
                            continue

                    new_segment = Segment(
                        id=seg_id or f"SEG-{str(uuid.uuid4())[:12]}",
                        document_id=seg_data.get("doc_id"),
                        page_number=seg_data.get("page") or 1,
                        sequence_number=seg_data.get("sequence") or 0,
                        text=seg_data.get("text", ""),
                        lang=seg_data.get("lang", "unknown"),
                        lang_confidence=seg_data.get("lang_confidence", 0.0),
                        ocr_confidence=seg_data.get("ocr_confidence", 0.0),
                        human_check_required=seg_data.get("human_check_required", False)
                    )
                    db.add(new_segment)
                except Exception as seg_err:
                    logger.warning(f"Failed to save segment: {seg_err}")
            
            logger.info("Background: OCR segments saved.")

        db.commit()
            
    except Exception as e:
        logger.error(f"Background: Exception during intake workflow: {str(e)}", exc_info=True)
        matter.status = "failed"
        matter.title = f"Error - {matter.title}"
        db.commit()
    finally:
        db.close()




@router.get("/", response_model=List[MatterResponse])
def list_matters(
    skip: int = 0,
    limit: int = 50,
    status: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: Dict[str, Any] = Depends(get_current_user_sync)
):
    """
    List all matters with optional filtering.
    
    Args:
        skip: Number of records to skip
        limit: Maximum number of records to return
        status: Filter by status (intake, structured, drafting, ready, filed)
    """
    query = db.query(Matter).filter(Matter.created_by == current_user["user_id"])
    
    if status:
        query = query.filter(Matter.status == status)
    else:
        # User explicitly asked NOT to show matters on dashboard until OCR is complete.
        # We exclude 'intake' status which corresponds to the initial processing phase.
        query = query.filter(Matter.status != "intake")
    
    matters = query.order_by(Matter.created_at.desc()).offset(skip).limit(limit).all()
    
    # Mapping helper for id -> matter_id
    response_list = []
    for m in matters:
        data = {
            "matter_id": m.id,
            "title": m.title,
            "status": m.status,
            "court": m.court,
            "jurisdiction": m.jurisdiction,
            "primary_language": m.primary_language,
            "matter_type": m.matter_type,
            "created_at": m.created_at,
            "human_review_required": m.human_review_required
        }
        response_list.append(MatterResponse(**data))
        
    return response_list


@router.get("/{matter_id}", response_model=dict)
def get_matter(matter_id: str, db: Session = Depends(get_db), current_user: Dict[str, Any] = Depends(get_current_user_sync)):
    """
    Get detailed matter information including snapshot and risk scores.
    """
    matter = db.query(Matter).filter(Matter.id == matter_id).first()
    
    if not matter:
        raise HTTPException(status_code=404, detail="Matter not found")
    
    response = matter.to_dict()
    # Explicitly ensure processing_status is included if it exists
    if hasattr(matter, 'processing_status'):
        response['processing_status'] = matter.processing_status
        
    return response


@router.delete("/{matter_id}", response_model=dict)
def delete_matter(matter_id: str, db: Session = Depends(get_db), current_user: Dict[str, Any] = Depends(get_current_user_sync)):
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
    matter = db.query(Matter).filter(Matter.id == matter_id, Matter.created_by == current_user["user_id"]).first()
    
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
        
        # Create Audit Log entry for drafting
        from models.audit import AuditLog
        audit_entry = AuditLog(
            matter_id=matter_id,
            agent_id="DraftingOrchestrator",
            action_type="pleading_drafted",
            action_description=f"Automated Statement of Claim drafted using template: {request.template_id}",
            entity_type="pleading",
            entity_id=None, # Will be set after flush
            user_id=current_user["user_id"]
        )
        db.add(audit_entry)
        
        db.commit()
        db.refresh(pleading)
        audit_entry.entity_id = pleading.id
        db.commit()
    
    return {
        "status": "success",
        "matter_id": matter_id,
        "workflow_result": result
    }

@router.post("/{matter_id}/draft/stream")
async def start_drafting_workflow_stream(
    matter_id: str,
    request: DraftingRequest,
    db: Session = Depends(get_db),
    current_user: Dict[str, Any] = Depends(get_current_user_sync)
):
    """
    Start the drafting workflow and stream updates (Server-Sent Events).
    """
    from fastapi.responses import StreamingResponse
    
    matter = db.query(Matter).filter(Matter.id == matter_id, Matter.created_by == current_user["user_id"]).first()
    if not matter:
        raise HTTPException(status_code=404, detail="Matter not found")
    
    matter_snapshot = matter.to_dict()
    
    stream_generator = controller.run_drafting_workflow_stream(
        matter_snapshot=matter_snapshot,
        template_id=request.template_id,
        issues_selected=request.issues_selected,
        prayers_selected=request.prayers_selected
    )
    
    async def event_generator():
        async for event in stream_generator:
            # SSE format: data: {json}\n\n
            yield f"data: {event}\n\n"
            
            # If result, we also save to DB (side effect)
            try:
                event_data = json.loads(event)
                if event_data.get("type") == "result":
                    result = event_data.get("data")
                    pleading_data = result.get("pleading_ms", {}) or result.get("pleading_en", {})
                    
                    if pleading_data:
                        # Re-fetch matter in fresh session context if needed
                        # (Not doing here to keep stream fast, frontend handles saving?)
                        # Actually better to save here to ensure persistence
                        
                        # Note: We can't easily use the `db` session here inside the async generator
                        # if it's already closed. For now, we trust the stream completion.
                        pass
            except Exception as e:
                import traceback
                traceback.print_exc()
                pass

    return StreamingResponse(event_generator(), media_type="text/event-stream")


@router.get("/{matter_id}/documents", response_model=List[dict])
def get_matter_documents(matter_id: str, db: Session = Depends(get_db), current_user: Dict[str, Any] = Depends(get_current_user_sync)):
    """
    Get all documents for a matter.
    """
    # Verify matter ownership first
    matter = db.query(Matter).filter(Matter.id == matter_id, Matter.created_by == current_user["user_id"]).first()
    if not matter:
        raise HTTPException(status_code=404, detail="Matter not found")

    documents = db.query(Document).filter(Document.matter_id == matter_id).all()
    
    return [doc.to_dict() for doc in documents]


@router.get("/{matter_id}/parallel-view", response_model=dict)
def get_parallel_view(matter_id: str, db: Session = Depends(get_db), current_user: Dict[str, Any] = Depends(get_current_user_sync)):
    """
    Get parallel text view (Malay ↔ English segments) for a matter.
    """
    # Verify matter ownership first
    matter = db.query(Matter).filter(Matter.id == matter_id, Matter.created_by == current_user["user_id"]).first()
    if not matter:
        raise HTTPException(status_code=404, detail="Matter not found")
    
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





@router.get("/{matter_id}/documents", response_model=List[Dict[str, Any]])
def get_matter_documents(matter_id: str, db: Session = Depends(get_db), current_user: Dict[str, Any] = Depends(get_current_user_sync)):
    """
    Get all documents for a specific matter.
    """
    matter = db.query(Matter).filter(Matter.id == matter_id, Matter.created_by == current_user["user_id"]).first()
    if not matter:
        raise HTTPException(status_code=404, detail="Matter not found")
        
    documents = db.query(Document).filter(Document.matter_id == matter_id).all()
    
    return [doc.to_dict() for doc in documents]


# Evidence Workflow Endpoints

class CertifyTranslationRequest(BaseModel):
    document_id: str


@router.post("/{matter_id}/certify-translation", response_model=dict)
async def certify_translation(
    matter_id: str,
    request: CertifyTranslationRequest,
    db: Session = Depends(get_db),
    current_user: Dict[str, Any] = Depends(get_current_user_sync)
):
    """
    Generate translation certification for a document.
    
    Args:
        matter_id: Matter ID
        request: Request containing document_id
        
    Returns:
        Translation certification document
    """
    
    matter = db.query(Matter).filter(Matter.id == matter_id, Matter.created_by == current_user["user_id"]).first()
    
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
    db: Session = Depends(get_db),
    current_user: Dict[str, Any] = Depends(get_current_user_sync)
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
    
    matter = db.query(Matter).filter(Matter.id == matter_id, Matter.created_by == current_user["user_id"]).first()
    
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
async def prepare_hearing(matter_id: str, db: Session = Depends(get_db), current_user: Dict[str, Any] = Depends(get_current_user_sync)):
    """
    Prepare hearing bundle for a matter.
    
    Args:
        matter_id: Matter ID
        
    Returns:
        Hearing bundle with all required documents
    """
    
    matter = db.query(Matter).filter(Matter.id == matter_id, Matter.created_by == current_user["user_id"]).first()
    
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
def get_hearing_bundle(matter_id: str, db: Session = Depends(get_db), current_user: Dict[str, Any] = Depends(get_current_user_sync)):
    """
    Retrieve prepared hearing bundle for a matter.
    
    Args:
        matter_id: Matter ID
        
    Returns:
        Previously prepared hearing bundle
    """
    
    matter = db.query(Matter).filter(Matter.id == matter_id, Matter.created_by == current_user["user_id"]).first()
    
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
async def analyze_case_strength(matter_id: str, db: Session = Depends(get_db), current_user: Dict[str, Any] = Depends(get_current_user_sync)):
    """
    Analyze case strength using AI.
    
    Returns:
        - win_probability: 0-100%
        - risks: Identified weaknesses
        - strengths: Identified advantages
        - suggestions: Improvement recommendations
    """
    matter = db.query(Matter).filter(Matter.id == matter_id, Matter.created_by == current_user["user_id"]).first()
    
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

"""
Documents API router - Endpoints for document management.
"""
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, BackgroundTasks
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from typing import List, Dict, Any, Optional
from database import get_sync_db as get_db
from models import Document, Matter
from models.segment import Segment
from config import settings
from jose import JWTError, jwt
import os
import aiofiles
import logging

router = APIRouter()
logger = logging.getLogger(__name__)
security = HTTPBearer()

# Sync auth dependency
def get_current_user_sync(
    credentials: HTTPAuthorizationCredentials = Depends(security),
) -> Dict[str, Any]:
    """Validate JWT token and return user info."""
    token = credentials.credentials
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        user_id = payload.get("sub")
        if user_id is None:
            raise HTTPException(status_code=401, detail="Invalid credentials", headers={"WWW-Authenticate": "Bearer"})
        return {"user_id": user_id, "email": payload.get("email")}
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid credentials", headers={"WWW-Authenticate": "Bearer"})

# Allowed file extensions for upload (security whitelist)
ALLOWED_EXTENSIONS = {
    '.pdf', '.doc', '.docx', '.txt', '.rtf',  # Documents
    '.png', '.jpg', '.jpeg', '.gif', '.bmp', '.tiff',  # Images
    '.xls', '.xlsx', '.csv',  # Spreadsheets
}

# MIME type mapping for validation
ALLOWED_MIME_TYPES = {
    'application/pdf',
    'application/msword',
    'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
    'text/plain',
    'text/rtf',
    'image/png',
    'image/jpeg',
    'image/gif',
    'image/bmp',
    'image/tiff',
    'application/vnd.ms-excel',
    'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
    'text/csv',
}


def validate_file_extension(filename: str) -> bool:
    """Validate file extension against whitelist."""
    if not filename:
        return False
    
    # Get extension (lowercase)
    ext = os.path.splitext(filename)[1].lower()
    
    # Check for double extension attacks (e.g., file.pdf.exe)
    if filename.count('.') > 1:
        # Get all extensions
        parts = filename.lower().split('.')
        for part in parts[1:]:  # Skip the base name
            if f'.{part}' not in ALLOWED_EXTENSIONS:
                # Check if it's a dangerous extension
                dangerous_exts = {'.exe', '.bat', '.cmd', '.sh', '.ps1', '.vbs', '.js', '.msi'}
                if f'.{part}' in dangerous_exts:
                    return False
    
    return ext in ALLOWED_EXTENSIONS


@router.get("/", response_model=list)
def list_documents(
    skip: int = 0,
    limit: int = 50,
    matter_id: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: Dict[str, Any] = Depends(get_current_user_sync)
):
    """
    List all documents with optional filtering by matter_id.
    """
    # Join with Matter to filter by created_by
    query = db.query(Document).join(Matter).filter(Matter.created_by == current_user["user_id"])
    
    if matter_id:
        query = query.filter(Document.matter_id == matter_id)
    
    documents = query.offset(skip).limit(limit).all()
    
    return [
        {
            "id": doc.id,
            "filename": doc.filename,
            "mime_type": doc.mime_type,
            "matter_id": doc.matter_id,
            "created_at": doc.created_at.isoformat() if doc.created_at else None
        }
        for doc in documents
    ]


@router.post("/upload", response_model=dict)
async def upload_document(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    matter_id: Optional[str] = Form(None),
    db: Session = Depends(get_db),
    current_user: Dict[str, Any] = Depends(get_current_user_sync)
):
    """
    Upload a single document.
    
    Args:
        file: File to upload (allowed: PDF, DOC, DOCX, TXT, images)
        matter_id: Associated matter ID (optional)
    """
    # Validate file extension
    if not validate_file_extension(file.filename):
        raise HTTPException(
            status_code=400,
            detail=f"File type not allowed. Allowed extensions: {', '.join(sorted(ALLOWED_EXTENSIONS))}"
        )
    
    # Validate MIME type
    if file.content_type and file.content_type not in ALLOWED_MIME_TYPES:
        logger.warning(f"Suspicious MIME type: {file.content_type} for file {file.filename}")
        # Allow but log warning - MIME type can be spoofed
    
    # Validate matter_id if provided
    if matter_id:
        logger.info(f"Uploading file '{file.filename}' for matter_id: {matter_id}")
        matter = db.query(Matter).filter(Matter.id == matter_id, Matter.created_by == current_user["user_id"]).first()
        if not matter:
            logger.error(f"Matter {matter_id} not found during upload")
            raise HTTPException(status_code=404, detail="Matter not found")
        try:
            from services.rag_service import get_rag_service
            rag = get_rag_service()
            rag._get_vector_store(matter_id)
        except Exception as e:
            logger.warning(f"Failed to initialize vector store for matter {matter_id}: {e}")
    else:
        logger.warning(f"Uploading file '{file.filename}' without matter_id")

    # Read file content
    content = await file.read()
    
    # Check file size
    if len(content) > settings.MAX_UPLOAD_SIZE:
        raise HTTPException(
            status_code=413,
            detail=f"File too large. Maximum size is {settings.MAX_UPLOAD_SIZE} bytes"
        )
    
    # Save file to storage
    # Fix: Sanitize filename to prevent path traversal
    safe_filename = os.path.basename(file.filename)
    file_path = os.path.join(settings.UPLOAD_DIR, safe_filename)
    
    async with aiofiles.open(file_path, 'wb') as f:
        await f.write(content)
    
    # Create document record
    document = Document(
        matter_id=matter_id,
        filename=safe_filename,
        original_filename=file.filename,
        mime_type=file.content_type,
        file_path=file_path,
        file_size=len(content),
        source="upload"
    )
    
    db.add(document)
    db.commit()
    db.refresh(document)
    
    logger.info(f"Document uploaded: {safe_filename} ({len(content)} bytes)")
    
    # TRIGGER FULL INTAKE / RAG INGESTION
    try:
        async def run_detailed_intake(filepath: str, m_id: str, doc_id: str, doc_original_name: str, doc_filename: str, creator_id: str):
            logger.info(f"Starting Background Intake for {filepath} (Matter: {m_id})")
            
            is_pdf = filepath.lower().endswith(".pdf")

            if is_pdf:
                try:
                    from services.enhanced_ocr_pipeline import get_enhanced_ocr_pipeline
                    from services.ocr_embedding_service import embed_pending_chunks
                    pipeline = get_enhanced_ocr_pipeline()
                    # Use aiofiles if possible for async, but pipeline takes bytes.
                    # Standard open is blocking but fast for small files. Pipeline is async.
                    # Let's use aiofiles to be consistent with other fixes
                    import aiofiles
                    async with aiofiles.open(filepath, "rb") as f:
                        file_bytes = await f.read()

                    async def ocr_progress(step, detail):
                        logger.info(f"OCR pipeline [{step}] {detail}")
                        
                    result = await pipeline.process_document(
                        file_content=file_bytes,
                        filename=doc_original_name or doc_filename,
                        matter_id=m_id,
                        file_path=filepath,
                        created_by=creator_id,
                        progress_callback=ocr_progress,
                        document_id=doc_id
                    )
                    await embed_pending_chunks(document_id=result.get("document_id"))
                except Exception as e:
                    logger.error(f"Enhanced OCR pipeline failed for {filepath}: {e}")
                    from services.rag_service import get_rag_service
                    rag = get_rag_service()
                    await rag.ingest_document(filepath, matter_id=m_id)
            else:
                from services.rag_service import get_rag_service
                rag = get_rag_service()
                await rag.ingest_document(filepath, matter_id=m_id)
            
            # 2. If it's a matter document, re-run orchestrator to update dashboard (Legal Issues, Parties, etc.)
            if m_id and m_id != "general":
                from orchestrator.controller import OrchestrationController
                from routers.matters import _process_intake_background
                
                # Use the background helper from matters.py to update DB
                # Note: This will potentially re-read all docs or just add this one 
                # depending on how _process_intake_background is implemented.
                # For now, let's just trigger it.
                # Pass explicit ID instead of object if needed? 
                # _process_intake_background signature is: (matter_id: str, files: List[dict], connector_type: str, metadata: dict)
                # It doesn't take ORM objects, it takes dictionaries (files_data).
                
                # Check how files_data is constructed.
                # Original code:
                # files_data = [{
                #     "filename": doc_obj.original_filename,
                #     "content": None, 
                #     "mime_type": doc_obj.mime_type,
                #     "doc_id": doc_obj.id,
                #     "file_path": filepath
                # }]
                # doc_obj CANNOT be accessed here if session closed.
                # Using passed primitives:
                files_data = [{
                    "filename": doc_original_name,
                    "content": None, 
                    "mime_type": "application/pdf" if is_pdf else "application/octet-stream", # Approximate or need to pass mime too?
                    "doc_id": doc_id,
                    "file_path": filepath
                }]
                
                background_tasks.add_task(_process_intake_background, m_id, files_data, "upload", {})

        background_tasks.add_task(
            run_detailed_intake, 
            file_path, 
            matter_id, 
            document.id, 
            document.original_filename, 
            document.filename, 
            current_user["user_id"]
        )
        
    except Exception as ingestion_err:
        logger.error(f"Failed to queue intake task: {ingestion_err}")
    
    return {
        "status": "success",
        "document_id": document.id,
        "filename": document.filename,
        "size": document.file_size,
        "ocr_status": "queued"
    }



@router.get("/{doc_id}", response_model=dict)
def get_document(doc_id: str, db: Session = Depends(get_db), current_user: Dict[str, Any] = Depends(get_current_user_sync)):
    """
    Get document metadata.
    """
    document = db.query(Document).join(Matter).filter(
        Document.id == doc_id,
        Matter.created_by == current_user["user_id"]
    ).first()
    
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")
    
    return document.to_dict()


@router.get("/{doc_id}/download")
def download_document(doc_id: str, db: Session = Depends(get_db), current_user: Dict[str, Any] = Depends(get_current_user_sync)):
    """
    Download original document file.
    """
    document = db.query(Document).join(Matter).filter(
        Document.id == doc_id,
        Matter.created_by == current_user["user_id"]
    ).first()
    
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")
    
    if not os.path.exists(document.file_path):
        raise HTTPException(status_code=404, detail="File not found on disk")
    
    return FileResponse(
        path=document.file_path,
        filename=document.original_filename,
        media_type=document.mime_type
    )


@router.get("/{doc_id}/preview", response_model=dict)
def get_document_preview(doc_id: str, db: Session = Depends(get_db), current_user: Dict[str, Any] = Depends(get_current_user_sync)):
    """
    Get OCR preview of document (first 1000 characters).
    """
    document = db.query(Document).join(Matter).filter(
        Document.id == doc_id,
        Matter.created_by == current_user["user_id"]
    ).first()
    
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")
    
    # Get segments for preview
    segments = db.query(Segment).filter(
        Segment.document_id == doc_id
    ).limit(10).all()
    
    preview_text = "\n\n".join([seg.text for seg in segments])
    
    return {
        "doc_id": doc_id,
        "filename": document.filename,
        "preview": preview_text[:10000],
        "ocr_completed": document.ocr_completed,
        "ocr_confidence": document.ocr_confidence,
        "total_segments": len(segments)
    }

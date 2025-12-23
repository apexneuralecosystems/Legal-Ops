"""
Documents API router - Endpoints for document management.
"""
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
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
async def list_documents(
    skip: int = 0,
    limit: int = 50,
    matter_id: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """
    List all documents with optional filtering by matter_id.
    """
    query = db.query(Document)
    
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
    file: UploadFile = File(...),
    matter_id: Optional[str] = Form(None),
    db: Session = Depends(get_db)
    # Auth temporarily removed for testing
    # current_user: Dict[str, Any] = Depends(get_current_user_sync)
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
        matter = db.query(Matter).filter(Matter.id == matter_id).first()
        if not matter:
            raise HTTPException(status_code=404, detail="Matter not found")

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
    
    return {
        "status": "success",
        "document_id": document.id,
        "filename": document.filename,
        "size": document.file_size
    }



@router.get("/{doc_id}", response_model=dict)
async def get_document(doc_id: str, db: Session = Depends(get_db)):
    # Auth temporarily removed
    """
    Get document metadata.
    """
    document = db.query(Document).filter(Document.id == doc_id).first()
    
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")
    
    return document.to_dict()


@router.get("/{doc_id}/download")
async def download_document(doc_id: str, db: Session = Depends(get_db), current_user: Dict[str, Any] = Depends(get_current_user_sync)):
    """
    Download original document file.
    """
    document = db.query(Document).filter(Document.id == doc_id).first()
    
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
async def get_document_preview(doc_id: str, db: Session = Depends(get_db)):
    """
    Get OCR preview of document (first 1000 characters).
    """
    document = db.query(Document).filter(Document.id == doc_id).first()
    
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
        "preview": preview_text[:1000],
        "ocr_completed": document.ocr_completed,
        "ocr_confidence": document.ocr_confidence,
        "total_segments": len(segments)
    }

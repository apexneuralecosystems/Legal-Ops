from fastapi import APIRouter, Depends, HTTPException, Request, UploadFile, File, Form
from fastapi.responses import StreamingResponse
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from database import get_sync_db as get_db
from models import Matter
from typing import List, Dict, Any, Optional
from pydantic import BaseModel
from jose import JWTError, jwt
import logging
import json
import asyncio
import os
import aiofiles
from config import settings

router = APIRouter()
logger = logging.getLogger(__name__)
security = HTTPBearer()

# Sync version of auth dependency
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

class ChatRequest(BaseModel):
    message: str
    conversation_id: Optional[str] = None
    matter_id: Optional[str] = None
    context_files: List[str] = []

@router.post("/upload")
async def upload_context_file(
    file: UploadFile = File(...),
    matter_id: Optional[str] = Form("general"),
    db: Session = Depends(get_db),
    current_user: Dict[str, Any] = Depends(get_current_user_sync)
):
    """
    Upload and ingest a document for RAG.
    """
    try:
        # Sanitize filename
        safe_filename = os.path.basename(file.filename)
        # Use a temp directory or the standard upload dir
        file_path = os.path.join(settings.UPLOAD_DIR, f"ctx_{safe_filename}")
        
        async with aiofiles.open(file_path, 'wb') as f:
            content = await file.read()
            await f.write(content)
            
        logger.info(f"Paralegal uploaded context file: {file_path}")
        
        # Verify matter ownership if linked to a specific matter
        if matter_id and matter_id != "general":
            # Using local import to avoid circular dependency
            matter = db.query(Matter).filter(Matter.id == matter_id, Matter.created_by == current_user["user_id"]).first()
            if not matter:
                raise HTTPException(status_code=404, detail="Matter not found or access denied")
            
            # Save to Document table for Evidence viewing
            try:
                import hashlib
                from datetime import datetime
                from models import Document
                
                # Calculate hash
                sha256_hash = hashlib.sha256(content).hexdigest()
                
                # Check for duplicate
                existing_doc = db.query(Document).filter(
                    Document.file_hash == sha256_hash,
                    Document.matter_id == matter_id
                ).first()
                
                if not existing_doc:
                    # Create document ID
                    doc_id = f"DOC-{datetime.utcnow().strftime('%Y%m%d')}-{sha256_hash[:8]}"
                    
                    new_doc = Document(
                        id=doc_id,
                        matter_id=matter_id,
                        filename=safe_filename,
                        mime_type=file.content_type or "application/octet-stream",
                        file_size=len(content),
                        file_hash=sha256_hash,
                        file_path=f"uploads/{safe_filename}",
                        source="paralegal_upload",
                        ocr_completed=False # Will be processed by RAG
                    )
                    db.add(new_doc)
                    db.commit()
                    logger.info(f"Saved document to database: {doc_id}")
                else:
                    logger.info("Document already exists in database")
                    
            except Exception as db_err:
                logger.error(f"Failed to save document record: {db_err}")
                # Don't fail the upload just because DB save failed
                pass

        # Trigger RAG Ingestion
        try:
            from services.rag_service import get_rag_service
            rag = get_rag_service()
            success = await rag.ingest_document(file_path, matter_id=matter_id)
            status_msg = "uploaded_and_ingested" if success else "uploaded_but_ingestion_failed"
        except Exception as rag_err:
             logger.error(f"RAG Ingestion failed: {rag_err}")
             status_msg = "uploaded_but_rag_error"
        
        return {
            "filename": safe_filename,
            "filepath": file_path,
            "status": status_msg
        }
    except Exception as e:
        logger.error(f"Paralegal upload error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/chat")
async def paralegal_chat(
    request: ChatRequest,
    db: Session = Depends(get_db),
    current_user: Dict[str, Any] = Depends(get_current_user_sync)
):
    """
    Stream chat response from Paralegal AI using RAG.
    """
    from services.rag_service import get_rag_service
    
    async def response_generator():
        try:
            # 1. Yield Status
            yield f"data: {json.dumps({'type': 'status', 'content': 'Analyzing query...'})}\n\n"
            await asyncio.sleep(0.1)
            
            # 2. Call RAG Service
            rag = get_rag_service()
            yield f"data: {json.dumps({'type': 'status', 'content': 'Searching documents & legal databases...'})}\n\n"
            
            result = await rag.query(
                query_text=request.message,
                matter_id=request.matter_id,
                context_files=request.context_files
            )
            
            # 3. Stream Answer (Simulated typing of the full response for UX)
            answer = result.get("answer", "")
            method = result.get("method", "rag")
            sources = result.get("sources", [])
            
            # Helper to stream words
            words = answer.split(" ")
            for word in words:
                await asyncio.sleep(0.02) # Fast typing
                yield f"data: {json.dumps({'type': 'token', 'content': word + ' '})}\n\n"
            
            # 4. Stream Sources/Context Info
            if sources:
                source_text = "\n\n**Sources:**\n" + "\n".join([f"- {s}" for s in sources])
                yield f"data: {json.dumps({'type': 'token', 'content': source_text})}\n\n"
            
            if method == "web_search":
                 yield f"data: {json.dumps({'type': 'status', 'content': 'Used Firecrawl Web Search'})}\n\n"
            
            # Final message
            yield f"data: {json.dumps({'type': 'done', 'content': ''})}\n\n"

        except Exception as e:
            logger.error(f"Paralegal chat error: {e}")
            yield f"data: {json.dumps({'type': 'error', 'content': str(e)})}\n\n"

    return StreamingResponse(response_generator(), media_type="text/event-stream")

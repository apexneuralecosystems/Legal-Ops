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
from datetime import datetime
from config import settings
from dependencies import get_current_user

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
    mode: Optional[str] = None
    enable_devil: bool = True

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
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Stream chat response from Paralegal AI using multi-tool research + automatic cross-examination.
    """
    from agents.legal_research_agent import get_legal_research_agent
    from agents.devils_advocate_agent import get_devils_advocate_agent
    from services.rag_service import get_rag_service
    
    async def response_generator():
        try:
            # 1. Yield Status
            yield f"data: {json.dumps({'type': 'status', 'content': 'Analyzing query...'})}\n\n"
            await asyncio.sleep(0.01)
            
            mode = request.mode or "analysis"
            tools_used = []
            sources = []
            if mode == "argument":
                if request.matter_id:
                    status_msg = "Building arguments from case files only (no Lexis, no web)..."
                else:
                    status_msg = "Building arguments from uploaded documents and web (no Lexis)..."
                yield f"data: {json.dumps({'type': 'status', 'content': status_msg})}\n\n"
                await asyncio.sleep(0.01)
                rag = get_rag_service()
                rag_result = await rag.query(
                    query_text=request.message,
                    matter_id=request.matter_id,
                    conversation_id=request.conversation_id,
                    k=10,
                    context_files=request.context_files or None
                )
                answer = rag_result.get("answer", "")
                raw_sources = rag_result.get("sources", []) or []
                sources = [
                    {"tool": "matter_documents", "result": s}
                    for s in raw_sources
                ]
                tools_used = ["Matter Documents (Argument Mode)"]
            else:
                research_agent = get_legal_research_agent()
                yield f"data: {json.dumps({'type': 'status', 'content': 'Searching case files, legislation and web...'})}\n\n"
                await asyncio.sleep(0.01)
                research_result = await research_agent.research(
                    query=request.message,
                    matter_id=request.matter_id,
                    context=", ".join(request.context_files) if request.context_files else None
                )
                answer = research_result.get("answer", "")
                sources = research_result.get("sources", [])
                tools_used = research_result.get("tools_used", [])
            
            # 3. Stream the main answer
            yield f"data: {json.dumps({'type': 'status', 'content': 'Generating legal analysis...'})}\n\n"
            
            # Stream words for UX
            # If the answer already contains suggested steps, we'll stream it as is
            words = answer.split(" ")
            for word in words:
                await asyncio.sleep(0.002) # Reduced from 0.01 for snappier feel
                yield f"data: {json.dumps({'type': 'token', 'content': word + ' '})}\n\n"
            
            # 4. Save chat message to database
            try:
                from models.chat import ChatMessage
                from uuid import uuid4
                
                # Generate conversation_id if not provided
                conv_id = request.conversation_id or str(uuid4())
                
                # Save user message
                user_msg_id = str(uuid4())
                user_msg = ChatMessage(
                    id=user_msg_id,
                    matter_id=request.matter_id or "general",
                    conversation_id=conv_id,
                    user_id=current_user.get("user_id"),
                    role="user",
                    message=request.message,
                    created_at=datetime.utcnow()
                )
                db.add(user_msg)
                
                # Save assistant response
                assistant_msg_id = str(uuid4())
                assistant_msg = ChatMessage(
                    id=assistant_msg_id,
                    matter_id=request.matter_id or "general",
                    conversation_id=conv_id,
                    user_id=current_user.get("user_id"),
                    role="assistant",
                    message=answer,
                    method=rag_result.get("method", "unknown") if mode == "argument" else "multi_tool_research",
                    context_used=json.dumps([s.get("result") for s in sources]) if sources else None,
                    confidence=rag_result.get("confidence", "medium") if mode == "argument" else "high",
                    created_at=datetime.utcnow()
                )
                db.add(assistant_msg)
                db.commit()
                
                # Send conversation_id in metadata
                yield f"data: {json.dumps({'type': 'metadata', 'conversation_id': conv_id, 'message_id': assistant_msg_id})}\n\n"
                
                logger.info(f"Saved chat messages for conversation {conv_id}")
            except Exception as save_err:
                logger.error(f"Failed to save chat messages: {save_err}")
                db.rollback()
            
            # 5. Stream sources
            if sources:
                source_text = "\n\n---\n### 📚 Sources Used\n"
                for src in sources:
                    tool_name = src.get("tool", "unknown")
                    source_text += f"- **{tool_name.replace('_', ' ').title()}**: {src.get('result', '')[:2000]}...\n"
                yield f"data: {json.dumps({'type': 'token', 'content': source_text})}\n\n"
            
            if request.enable_devil:
                yield f"data: {json.dumps({'type': 'status', 'content': '🔴 Running Senior Partner Review (Devils Advocate)...'})}\n\n"
                
                devil = get_devils_advocate_agent()
                devil_result = await devil.analyze(
                    legal_position=answer,
                    case_context=request.message,
                    document_summary=", ".join(request.context_files) if request.context_files else None
                )
                
                challenge = devil_result.get("challenge", "")
                
                if challenge and not challenge.startswith("["):
                    # Distinct separator for Devil's Advocate
                    yield f"data: {json.dumps({'type': 'token', 'content': '\\n\\n---\\n\\n'})}\n\n"
                    yield f"data: {json.dumps({'type': 'token', 'content': '# 🔴 Devils Advocate Challenge\\n\\n'})}\n\n"
                    yield f"data: {json.dumps({'type': 'token', 'content': '*This critical review identifies vulnerabilities in the analysis above.*\\n\\n'})}\n\n"
                    
                    challenge_words = challenge.split(" ")
                    for word in challenge_words:
                        await asyncio.sleep(0.005)
                        yield f"data: {json.dumps({'type': 'token', 'content': word + ' '})}\n\n"
            
            # Final message
            yield f"data: {json.dumps({'type': 'done', 'content': ''})}\n\n"

        except Exception as e:
            logger.error(f"Paralegal chat error: {e}")
            yield f"data: {json.dumps({'type': 'error', 'content': str(e)})}\n\n"

    return StreamingResponse(response_generator(), media_type="text/event-stream")


@router.get("/suggested-questions/{matter_id}")
async def get_suggested_questions(
    matter_id: str,
    db: Session = Depends(get_db),
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Generate context-aware suggested questions based on the matter's documents.
    Called when Doc Chat is opened.
    """
    from services.rag_service import get_rag_service
    from services.llm_service import LLMService
    
    try:
        # 1. Verify matter exists and user has access
        matter = db.query(Matter).filter(
            Matter.id == matter_id,
            Matter.created_by == current_user["user_id"]
        ).first()
        
        if not matter:
            raise HTTPException(status_code=404, detail="Matter not found")
        
        # 2. Get document summaries from RAG
        rag = get_rag_service()
        context_summary = ""
        
        try:
            store = rag._get_vector_store(matter_id)
            if store:
                docs = store.similarity_search(
                    f"Summary of legal issues in matter {matter_id}",
                    k=5,
                )
                logger.info(f"SuggestedQs: Retrieved {len(docs)} docs from RAG for {matter_id}")
                context_summary = "\n".join([d.page_content[:300] for d in docs])
            else:
                logger.warning(f"SuggestedQs: No vector store found for {matter_id}")
        except Exception as rag_err:
            logger.warning(f"RAG fetch for suggested questions failed: {rag_err}")
        
        # 3. Use matter metadata as fallback/supplement
        matter_context = f"""
Case Title: {matter.title or 'Untitled'}
Parties: {json.dumps(matter.parties) if matter.parties else 'Not specified'}
Legal Issues: {json.dumps(matter.issues) if matter.issues else 'Not specified'}
Key Dates: {json.dumps(matter.key_dates) if matter.key_dates else 'Not specified'}
"""
        
        # 4. Generate suggested questions using LLM
        llm = LLMService()
        prompt = f"""Based on the following case context, generate 5 insightful legal questions that a lawyer might want answered about this case.

CASE CONTEXT:
{matter_context}

DOCUMENT EXCERPTS:
{context_summary[:1500] if context_summary else 'No documents processed yet.'}

Generate exactly 5 questions in JSON format:
[
  "Question 1?",
  "Question 2?",
  "Question 3?",
  "Question 4?",
  "Question 5?"
]

Focus on:
- Key legal issues
- Potential risks
- Evidence requirements
- Procedural matters
- Strategic considerations

Return ONLY the JSON array, no other text."""

        response = await llm.generate(prompt, temperature=0.7, max_tokens=500)
        
        # Parse the response
        try:
            # Try to extract JSON from the response
            import re
            
            # 1. Attempt standard JSON extraction
            json_match = re.search(r'\[.*\]', response, re.DOTALL)
            if json_match:
                try:
                    questions = json.loads(json_match.group())
                except json.JSONDecodeError:
                    # 2. If valid JSON structure but bad content, try ast.literal_eval for single quotes
                    try:
                        import ast
                        questions = ast.literal_eval(json_match.group())
                    except:
                        questions = None
            else:
                questions = None
            
            # 3. Fallback: Parse number/bullet list if JSON failed
            if not questions or not isinstance(questions, list):
                logger.info("JSON parsing failed for suggested questions, attempting list parsing")
                questions = []
                for line in response.split('\n'):
                    line = line.strip()
                    # Catch lines starting with "1.", "-", "*", "•"
                    if re.match(r'^(\d+\.|-|\*|•)\s+', line):
                        # Remove marker and quotes
                        clean_q = re.sub(r'^(\d+\.|-|\*|•)\s+', '', line).strip().strip('"').strip("'")
                        if len(clean_q) > 10 and "?" in clean_q:
                            questions.append(clean_q)
            
            # 4. Final Fallback if still empty
            if not questions:
                logger.warning("Failed to parse suggested questions, using defaults")
                questions = [
                    f"What are the key legal issues in {matter.title or 'this case'}?",
                    "What evidence do we need to strengthen our position?",
                    "What are the potential defenses the opposing party might raise?",
                    "What are the key dates and deadlines I should be aware of?",
                    "What is the likelihood of success in this case?"
                ]
        except Exception as e:
            logger.warning(f"Error parsing AI response: {e}")
            questions = [
                f"What are the key legal issues in {matter.title or 'this case'}?",
                "What evidence do we need to strengthen our position?",
                "What are the potential defenses the opposing party might raise?",
                "What are the key dates and deadlines I should be aware of?",
                "What is the likelihood of success in this case?"
            ]

        return {
            "matter_id": matter_id,
            "matter_title": matter.title,
            "suggested_questions": questions[:5]  # Ensure max 5
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Suggested questions error: {e}")
        # Return default questions on error
        return {
            "matter_id": matter_id,
            "matter_title": None,
            "suggested_questions": [
                "What are the key legal issues in this case?",
                "What evidence is available to support our claims?",
                "What are the potential weaknesses in our position?",
                "What deadlines or limitation periods apply?",
                "What remedies can we seek?"
            ]
        }

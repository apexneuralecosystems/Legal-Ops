import os
import logging
from typing import List, Dict, Any, Optional
from uuid import uuid4

# Config
from config import settings

logger = logging.getLogger(__name__)


def _try_import_ocr_chunks():
    """Try to import OCR chunk models, return None if not available."""
    try:
        from models.ocr_models import OCRChunk, OCRDocument
        return OCRChunk, OCRDocument
    except ImportError:
        return None, None

class RAGService:
    """
    Service for RAG (Retrieval-Augmented Generation) operations.
    Handles document ingestion, vector storage, and hybrid retrieval.
    """
    
    def __init__(self):
        self.persist_directory = os.path.join(settings.BASE_DIR, "data", "chroma_db")
        self._embedding_function = None
        self._vector_store = None
        self._vector_stores = {}
        self._firecrawl = None
        
        # Initialize lazily
        self._init_resources()

    def _init_resources(self):
        """Initialize embeddings and vector store using OpenRouter or OpenAI."""
        try:
            # Lazy imports to prevent crashes if dependencies are missing
            try:
                from langchain_chroma import Chroma
                chroma_available = True
            except ImportError as e:
                logger.error(f"RAG dependencies missing: {e}. Install chromadb, langchain-chroma, etc.")
                chroma_available = False
            
            from langchain_openai import OpenAIEmbeddings
            
            # Try OpenRouter first (uses OpenAI-compatible API)
            api_key = settings.OPENROUTER_API_KEY or settings.OPENAI_API_KEY
            
            if not api_key:
                logger.warning("No API key set (OPENROUTER_API_KEY or OPENAI_API_KEY). RAG capabilities limited.")
                return
            
            # Use OpenRouter's embedding endpoint if using OpenRouter key
            if settings.OPENROUTER_API_KEY and not settings.OPENAI_API_KEY:
                # OpenRouter is OpenAI-compatible, use its base URL
                # Note: valid models on OpenRouter for embeddings might differ
                # Trying standard openai/text-embedding-3-small and handling errors
                self._embedding_function = OpenAIEmbeddings(
                    api_key=settings.OPENROUTER_API_KEY,
                    base_url="https://openrouter.ai/api/v1",
                    model="openai/text-embedding-3-small",
                    check_embedding_ctx_length=False  # Disable length check to avoid extra calls
                )
                logger.info("RAG: Using OpenRouter for embeddings (openai/text-embedding-3-small)")
            else:
                self._embedding_function = OpenAIEmbeddings(
                    api_key=settings.OPENAI_API_KEY,
                    model="text-embedding-3-small"
                )
                logger.info("RAG: Using OpenAI for embeddings")
            
            if chroma_available:
                self._vector_store = Chroma(
                    collection_name="legal_ops_rag",
                    embedding_function=self._embedding_function,
                    persist_directory=self.persist_directory
                )
                logger.info("RAG: Vector store initialized successfully (global collection)")
            else:
                logger.warning("RAG: ChromaDB not available. Vector store features will be limited.")
            
            # Optional: Firecrawl for web scraping
            if settings.FIRECRAWL_API_KEY:
                try:
                    from firecrawl import FirecrawlApp
                    self._firecrawl = FirecrawlApp(api_key=settings.FIRECRAWL_API_KEY)
                except ImportError:
                    pass
                
        except ImportError as e:
            logger.error(f"RAG dependencies missing: {e}. Install chromadb, langchain-chroma, etc.")
        except Exception as e:
            logger.error(f"Failed to initialize RAG resources: {e}")

    def _get_vector_store(self, matter_id: Optional[str] = None):
        """
        Get or create a Chroma collection for the given matter.
        If matter_id is None, return the global collection.
        """
        if not self._embedding_function:
            return None
        
        if matter_id:
            key = matter_id
            collection_name = f"legal_ops_matter_{matter_id}"
        else:
            key = "__global__"
            if self._vector_store:
                return self._vector_store
            collection_name = "legal_ops_rag"
        
        if key in self._vector_stores:
            return self._vector_stores[key]
        
        try:
            from langchain_chroma import Chroma
            store = Chroma(
                collection_name=collection_name,
                embedding_function=self._embedding_function,
                persist_directory=self.persist_directory
            )
            self._vector_stores[key] = store
            logger.info(f"RAG: Vector store initialized for key={key}, collection={collection_name}")
            return store
        except Exception as e:
            logger.error(f"Failed to initialize vector store for {matter_id}: {e}")
            return None

    async def ingest_document(self, file_path: str, matter_id: str = "general") -> bool:
        """
        Ingest a PDF document into the vector store.
        """
        store = self._get_vector_store(matter_id)
        if not store:
            logger.error("Vector store not initialized.")
            return False

        try:
            from langchain_text_splitters import RecursiveCharacterTextSplitter
            from langchain_community.document_loaders import PyPDFLoader
            
            logger.info(f"Ingesting document: {file_path}")
            
            # 1. Load PDF
            loader = PyPDFLoader(file_path)
            raw_docs = loader.load()
            
            # 2. Split into chunks
            text_splitter = RecursiveCharacterTextSplitter(
                chunk_size=1000,
                chunk_overlap=200,
                length_function=len,
            )
            chunks = text_splitter.split_documents(raw_docs)
            
            # 3. Add Metadata
            for chunk in chunks:
                chunk.metadata["matter_id"] = matter_id
                chunk.metadata["source"] = os.path.basename(file_path)
                
            # 4. Store in Chroma (matter-scoped collection)
            if chunks:
                store.add_documents(documents=chunks)
                logger.info(f"Successfully ingested {len(chunks)} chunks from {file_path} into matter collection '{matter_id}'")
            else:
                logger.warning(f"No text chunks found in {file_path}. Skipping vector storage.")
            
            return True
            
        except Exception as e:
            logger.error(f"Ingestion failed for {file_path}: {e}")
            return False

    async def query(self, query_text: str, matter_id: Optional[str] = None, conversation_id: Optional[str] = None, k: int = 5, context_files: Optional[List[str]] = None) -> Dict[str, Any]:
        """
        Retrieve context and generate an answer.
        
        Args:
            query_text: The user's question
            matter_id: Optional matter ID to filter documents
            conversation_id: Optional conversation ID for memory
            k: Number of documents to retrieve
            context_files: Optional list of file paths to include as context
        
        Returns:
            Dict containing 'answer', 'sources', 'confidence', 'method' (rag/web)
        """
        # Read uploaded file content if provided
        file_context = ""
        sources = []
        if context_files:
            for file_path in context_files:
                try:
                    
                    if os.path.exists(file_path):
                        filename = os.path.basename(file_path)
                        content = ""
                        
                        # Try to read text content
                        if file_path.lower().endswith('.pdf'):
                            # Use Vision API for PDF extraction (handles scanned PDFs too)
                            try:
                                from services.llm_service import get_llm_service
                                llm = get_llm_service()
                                
                                logger.info(f"Extracting PDF via Vision API: {filename}")
                                content = await llm.extract_pdf_content(file_path)
                                logger.info(f"PDF Vision extraction complete: {len(content)} chars")
                                
                            except Exception as vision_err:
                                logger.error(f"PDF Vision extraction failed: {vision_err}")
                                # Fallback: try reading as binary and extracting plaintext
                                try:
                                    with open(file_path, 'rb') as f:
                                        raw = f.read()
                                    # Try to find text between common PDF markers
                                    import re
                                    text_parts = re.findall(rb'\((.*?)\)', raw)
                                    content = " ".join([t.decode('utf-8', errors='ignore') for t in text_parts[:100]])
                                except:
                                    content = "[PDF could not be read. Please copy-paste the relevant text.]"
                            
                            if content and len(content.strip()) > 50:
                                file_context += f"\n\n--- Document: {filename} ---\n{content[:15000]}\n"
                                sources.append(filename)
                            else:
                                file_context += f"\n\n--- Document: {filename} ---\n[Content extraction limited. Please copy-paste the relevant text.]\n"
                                sources.append(filename)
                        else:
                            # Plain text files, docx, etc
                            if file_path.lower().endswith('.docx'):
                                try:
                                    from docx import Document as DocxDocument
                                    doc = DocxDocument(file_path)
                                    content = "\n".join([p.text for p in doc.paragraphs])
                                except:
                                    content = "[DOCX extraction failed]"
                            else:
                                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                                    content = f.read()[:15000]
                            
                            file_context += f"\n\n--- Document: {filename} ---\n{content[:15000]}\n"
                            sources.append(filename)
                except Exception as e:
                    logger.error(f"Error reading context file {file_path}: {e}")
        
        # LOAD CONVERSATION HISTORY for context
        conversation_context = ""
        if matter_id and conversation_id:
            try:
                from database import SessionLocal
                from models.chat import ChatMessage, CaseLearning
                
                db = SessionLocal()
                
                # Get last 10 messages (5 exchanges)
                recent_msgs = db.query(ChatMessage).filter(
                    ChatMessage.matter_id == matter_id,
                    ChatMessage.conversation_id == conversation_id
                ).order_by(ChatMessage.created_at.desc()).limit(10).all()
                
                if recent_msgs:
                    conversation_context = "\n\n=== CONVERSATION HISTORY ===\n"
                    for msg in reversed(recent_msgs):
                        conversation_context += f"{msg.role.upper()}: {msg.message}\n"
                    conversation_context += "=== END HISTORY ===\n\n"
                    logger.info(f"Loaded {len(recent_msgs)} messages from conversation history")
                
                # Load important case learnings/corrections
                learnings = db.query(CaseLearning).filter(
                    CaseLearning.matter_id == matter_id,
                    CaseLearning.importance >= 3
                ).order_by(CaseLearning.importance.desc()).limit(5).all()
                
                if learnings:
                    conversation_context += "\n=== IMPORTANT CLARIFICATIONS (from previous corrections) ===\n"
                    for learning in learnings:
                        conversation_context += f"• {learning.corrected_text}\n"
                        # Increment usage counter
                        learning.applied_count += 1
                    conversation_context += "=== END CLARIFICATIONS ===\n\n"
                    logger.info(f"Applied {len(learnings)} case learnings")
                    db.commit()
                
                db.close()
            except Exception as conv_err:
                logger.warning(f"Failed to load conversation history: {conv_err}")
        
        # LOAD KNOWLEDGE GRAPH for instant structured answers
        knowledge_graph_context = ""
        if matter_id:
            try:
                from database import SessionLocal
                from models.case_intelligence import CaseEntity, CaseRelationship
                
                db = SessionLocal()
                
                # Check if knowledge graph exists
                entity_count = db.query(CaseEntity).filter(
                    CaseEntity.matter_id == matter_id
                ).count()
                
                if entity_count > 0:
                    # Classify query intent
                    intent = await self._classify_query_intent(query_text)
                    
                    # Load relevant entities based on intent
                    relevant_entities = []
                    
                    if intent in ["party_query", "all_parties"]:
                        relevant_entities = db.query(CaseEntity).filter(
                            CaseEntity.matter_id == matter_id,
                            CaseEntity.entity_type == 'party'
                        ).all()
                    elif intent in ["claim_query", "amount_query"]:
                        relevant_entities = db.query(CaseEntity).filter(
                            CaseEntity.matter_id == matter_id,
                            CaseEntity.entity_type == 'claim'
                        ).all()
                    elif intent == "defense_query":
                        relevant_entities = db.query(CaseEntity).filter(
                            CaseEntity.matter_id == matter_id,
                            CaseEntity.entity_type == 'defense'
                        ).all()
                    elif intent == "timeline_query":
                        relevant_entities = db.query(CaseEntity).filter(
                            CaseEntity.matter_id == matter_id,
                            CaseEntity.entity_type == 'date'
                        ).all()
                    elif intent == "issue_query":
                        relevant_entities = db.query(CaseEntity).filter(
                            CaseEntity.matter_id == matter_id,
                            CaseEntity.entity_type == 'issue'
                        ).all()
                    else:
                        relevant_entities = db.query(CaseEntity).filter(
                            CaseEntity.matter_id == matter_id
                        ).order_by(CaseEntity.confidence.desc()).limit(20).all()
                    
                    if relevant_entities:
                        knowledge_graph_context = "\n\n=== CASE KNOWLEDGE GRAPH ===\n"
                        by_type = {}
                        for entity in relevant_entities:
                            if entity.entity_type not in by_type:
                                by_type[entity.entity_type] = []
                            by_type[entity.entity_type].append(entity)
                        
                        for entity_type, entities in by_type.items():
                            knowledge_graph_context += f"\n{entity_type.upper()}S:\n"
                            for entity in entities:
                                knowledge_graph_context += f"  • {entity.entity_name}"
                                if entity.entity_value and isinstance(entity.entity_value, dict):
                                    key_info = []
                                    for k, v in entity.entity_value.items():
                                        if k in ['role', 'amount', 'date', 'claim_type', 'defense_type']:
                                            key_info.append(f"{k}: {v}")
                                    if key_info:
                                        knowledge_graph_context += f" ({', '.join(key_info)})"
                                knowledge_graph_context += "\n"
                        
                        knowledge_graph_context += "=== END KNOWLEDGE GRAPH ===\n\n"
                        logger.info(f"Loaded knowledge graph: {len(relevant_entities)} entities, intent: {intent}")
                
                db.close()
            except Exception as kg_err:
                logger.warning(f"Failed to load knowledge graph: {kg_err}")
        
        # Skip the early embedding check - we'll use Long Context Strategy for matter queries
        # if not self._embedding_function:
        #     # Fallback only used if we have no matter_id AND no embeddings
        #     pass

        try:
            # 1. Retrieve from Vector Store OR Long Context Loading
            filter_dict = {"matter_id": matter_id} if matter_id else None
            
            context_text = ""
            sources = []
            method = "rag"
            
            # LONG CONTEXT STRATEGY (Full Accuracy)
            # If matter_id is provided, we try to load ALL text first to ensure NO TRUNCATION
            if matter_id:
                logger.info(f"DEBUG: RAG query for matter_id: '{matter_id}'")
                
                # Fetch all documents for this matter to get full text
                try:
                    from database import SessionLocal
                    from models import Document
                    from models.segment import Segment
                    
                    db = SessionLocal()
                    
                    # PREFERRED STRATEGY: Read from OCRChunks (Enhanced Pipeline)
                    OCRChunk, OCRDocument = _try_import_ocr_chunks()
                    full_context_accumulated = ""
                    total_chars = 0
                    
                    if OCRChunk and OCRDocument:
                        try:
                            chunks = db.query(OCRChunk).join(OCRDocument).filter(
                                OCRDocument.matter_id == matter_id,
                                OCRChunk.is_embeddable == True
                            ).order_by(OCRDocument.id, OCRChunk.chunk_sequence).all()
                            
                            if chunks:
                                logger.info(f"Found {len(chunks)} chunks in ocr_chunks table for matter '{matter_id}'")
                                current_doc_id = None
                                
                                for chunk in chunks:
                                    if chunk.document_id != current_doc_id:
                                        doc = db.query(OCRDocument).filter(OCRDocument.id == chunk.document_id).first()
                                        doc_filename = doc.filename if doc else "Unknown Document"
                                        full_context_accumulated += f"\n\n--- Document: {doc_filename} ---\n"
                                        current_doc_id = chunk.document_id
                                        sources.append(doc_filename)
                                    
                                    full_context_accumulated += chunk.chunk_text + "\n"
                                    total_chars += len(chunk.chunk_text)
                        except Exception as chunk_err:
                            logger.warning(f"ocr_chunks query failed: {chunk_err}")

                    # FALLBACK STRATEGY: Read from legacy OCR Segments
                    if total_chars == 0:
                        from models.segment import Segment
                        from models import Document as LegacyDocument
                        
                        segments = db.query(Segment).join(LegacyDocument).filter(
                            LegacyDocument.matter_id == matter_id
                        ).order_by(LegacyDocument.id, Segment.page_number, Segment.sequence_number).all()
                        
                        if segments:
                            logger.info(f"Found {len(segments)} legacy segments for matter '{matter_id}'")
                            current_doc_id = None
                            
                            for seg in segments:
                                if seg.document_id != current_doc_id:
                                    doc_filename = seg.document.filename if seg.document else "Unknown Document"
                                    full_context_accumulated += f"\n\n--- Document: {doc_filename} ---\n"
                                    current_doc_id = seg.document_id
                                    sources.append(doc_filename)
                                
                                full_context_accumulated += seg.text + "\n"
                                total_chars += len(seg.text)
                    
                    # FINAL FALLBACK: File system read
                    if total_chars == 0:
                        logger.warning("No OCR data found in DB. Falling back to File System read.")
                        from models import Document
                        docs = db.query(Document).filter(Document.matter_id == matter_id).all()
                        
                        for doc in docs:
                            file_path = doc.file_path
                            if not os.path.isabs(file_path):
                                file_path = os.path.join(settings.BASE_DIR, file_path)
                                
                            doc_text = ""
                            if os.path.exists(file_path):
                                try:
                                    if file_path.lower().endswith('.pdf'):
                                        import fitz
                                        with fitz.open(file_path) as pdf_doc:
                                            for page in pdf_doc:
                                                doc_text += page.get_text() + "\n"
                                    else:
                                        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                                            doc_text = f.read()
                                except Exception as read_err:
                                    logger.warning(f"Failed to read doc {doc.filename}: {read_err}")
                            
                            if doc_text:
                                full_context_accumulated += f"\n\n--- Document: {doc.filename} ---\n{doc_text}\n"
                                total_chars += len(doc_text)
                                sources.append(doc.filename)
                    
                    db.close()
                    
                    # If total text is within reasonable context limit (e.g., 700k chars for 1M context model)
                    # We use it directly. This guarantees NO LOSS of information.
                    if total_chars > 0 and total_chars < 700000:
                        # Prepend knowledge graph, then conversation context, then document context
                        context_text = knowledge_graph_context + conversation_context + full_context_accumulated
                        method = "long_context_full_text"
                        logger.info(f"Long Context: Successfully loaded {total_chars} chars. Bypassing RAG chunks.")
                    else:
                        logger.info(f"Long Context: Text too large ({total_chars} chars) or empty. Falling back to High-K RAG.")
                        method = "rag" 
                        sources = [] # Reset sources to rely on RAG
                except Exception as long_ctx_err:
                    logger.error(f"Long Context loading failed: {long_ctx_err}. Falling back to RAG.")
                    method = "rag"
            
            
            # Fallback to Standard RAG if Long Context didn't work or wasn't applicable
            if method == "rag":
                # Check if vector store is available
                if not self._embedding_function:
                    logger.warning("RAG mode requested but embeddings not available. Using direct LLM with file context.")
                    method = "direct_llm_with_context"
                else:
                    # Get docs with scores (distance)
                    # Increase K for better coverage if we are in strict mode
                    k_val = k
                    if matter_id:
                         k_val = 20 # Retrieve more chunks for specific matters

                    store = self._get_vector_store(matter_id if matter_id else None)
                    if not store:
                        logger.warning("Vector store not initialized. Using direct LLM with file context.")
                        method = "direct_llm_with_context"
                    else:
                        results = store.similarity_search_with_score(
                            query_text, 
                            k=k_val,
                            filter=filter_dict
                        )
                
                        best_score = results[0][1] if results else 1.0
                        
                        # STRICT MODE: DISABLE WEB SEARCH FALLBACK for specific matters
                        # Only use web search if it's a "general" query (no matter_id)
                        if (not results or best_score > 0.45) and not matter_id: 
                            logger.info(f"Low confidence ({best_score:.3f}). Triggering Firecrawl web search.")
                            
                            if self._firecrawl:
                                method = "web_search"
                                # Firecrawl search
                                try:
                                    web_results = self._firecrawl.search(query_text, params={"limit": 3})
                                    if isinstance(web_results, list): 
                                         for res in web_results: 
                                             content = res.get('markdown', '') or res.get('content', '') or res.get('text', '')
                                             url = res.get('url', 'web')
                                             context_text += f"\nSource [{url}]:\n{content[:1000]}\n"
                                             sources.append(url)
                                except Exception as fe:
                                    logger.error(f"Firecrawl search failed: {fe}")
                                    method = "rag_low_confidence"
                        
                        if method == "rag" or method == "rag_low_confidence":
                            # Build context from chunks
                            for doc, score in results:
                                context_text += f"\nSource [{doc.metadata.get('source')}]:\n{doc.page_content}\n"
                                sources.append(doc.metadata.get('source'))

            # 2. Generate Answer
            from services.llm_service import get_llm_service
            llm = get_llm_service()
            
            # STRICT PROMPT FOR MATTER CHAT
            if matter_id:
                system_prompt = f"""You are an advanced AI Paralegal assistant for a Malaysian legal matter.

INSTRUCTIONS:
1. Answer the user's question based on the provided Document Context below
2. You may analyze, synthesize, and draw reasonable legal conclusions from the documents
3. Always cite which document(s) you're referencing (e.g., "According to the Grounds of Judgment...")  
4. If specific facts are not mentioned in the documents, state that clearly
5. You may apply general Malaysian legal principles to interpret the documents

Context:
{context_text}
"""
            else:
                # Original general prompt
                system_prompt = f"""You are an advanced AI Paralegal using Retrieval-Augmented Generation.
Answer the user's question based strictly on the provided context.
If the context contains the answer, cite the source.
If the context does not contain the answer, state that you don't know based on the documents.

Context:
{context_text}
"""
            
            user_prompt = f"Question: {query_text}"
            
            full_prompt = f"{system_prompt}\n\n{user_prompt}"
            
            # Using a larger model for long context if available (assuming LLM service handles this based on prompt length or config)
            answer = await llm.generate(full_prompt)
            
            return {
                "answer": answer,
                "sources": list(set(sources)), # Dedupe
                "confidence": "high",
                "method": method
            }

        except Exception as e:
            logger.error(f"RAG Query failed: {e}", exc_info=True)
            return {"answer": "An error occurred during research.", "error": str(e)}
    
    async def _classify_query_intent(self, query_text: str) -> str:
        """Classify query intent for knowledge graph routing"""
        
        query_lower = query_text.lower()
        
        # Party queries
        if any(word in query_lower for word in ['who', 'parties', 'plaintiff', 'defendant', 'claimant', 'respondent']):
            return "party_query"
        
        # Claim/amount queries
        if any(word in query_lower for word in ['claim', 'amount', 'money', 'rm', 'sum', 'damages']):
            return "claim_query"
        
        # Defense queries
        if any(word in query_lower for word in ['defense', 'defence', 'defend', 'counterclaim']):
            return "defense_query"
        
        # Timeline/date queries
        if any(word in query_lower for word in ['when', 'date', 'timeline', 'filed', 'deadline']):
            return "timeline_query"
        
        # Issue queries
        if any(word in query_lower for word in ['issue', 'law', 'statute', 'act', 'legal']):
            return "issue_query"
        
        return "general"

# Global Instance
_rag_service = None

def get_rag_service() -> RAGService:
    global _rag_service
    if _rag_service is None:
        _rag_service = RAGService()
    return _rag_service

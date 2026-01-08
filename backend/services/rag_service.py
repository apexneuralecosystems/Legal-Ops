import os
import logging
from typing import List, Dict, Any, Optional
from uuid import uuid4

# Config
from config import settings

logger = logging.getLogger(__name__)

class RAGService:
    """
    Service for RAG (Retrieval-Augmented Generation) operations.
    Handles document ingestion, vector storage, and hybrid retrieval.
    """
    
    def __init__(self):
        self.persist_directory = os.path.join(settings.BASE_DIR, "data", "chroma_db")
        self._embedding_function = None
        self._vector_store = None
        self._firecrawl = None
        
        # Initialize lazily
        self._init_resources()

    def _init_resources(self):
        """Initialize embeddings and vector store using OpenRouter or OpenAI."""
        try:
            # Lazy imports to prevent crashes if dependencies are missing
            from langchain_chroma import Chroma
            from langchain_openai import OpenAIEmbeddings
            
            # Try OpenRouter first (uses OpenAI-compatible API)
            api_key = settings.OPENROUTER_API_KEY or settings.OPENAI_API_KEY
            
            if not api_key:
                logger.warning("No API key set (OPENROUTER_API_KEY or OPENAI_API_KEY). RAG capabilities limited.")
                return
            
            # Use OpenRouter's embedding endpoint if using OpenRouter key
            if settings.OPENROUTER_API_KEY and not settings.OPENAI_API_KEY:
                # OpenRouter is OpenAI-compatible, use its base URL
                self._embedding_function = OpenAIEmbeddings(
                    api_key=settings.OPENROUTER_API_KEY,
                    base_url="https://openrouter.ai/api/v1",
                    model="openai/text-embedding-3-small"  # OpenRouter's embedding model
                )
                logger.info("RAG: Using OpenRouter for embeddings")
            else:
                self._embedding_function = OpenAIEmbeddings(
                    api_key=settings.OPENAI_API_KEY,
                    model="text-embedding-3-small"
                )
                logger.info("RAG: Using OpenAI for embeddings")
            
            self._vector_store = Chroma(
                collection_name="legal_ops_rag",
                embedding_function=self._embedding_function,
                persist_directory=self.persist_directory
            )
            logger.info("RAG: Vector store initialized successfully")
            
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

    async def ingest_document(self, file_path: str, matter_id: str = "general") -> bool:
        """
        Ingest a PDF document into the vector store.
        """
        if not self._vector_store:
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
                
            # 4. Store in Chroma
            # Chroma handles batching internally usually, but we can do it explicitly if needed
            self._vector_store.add_documents(documents=chunks)
            
            logger.info(f"Successfully ingested {len(chunks)} chunks from {file_path}")
            return True
            
        except Exception as e:
            logger.error(f"Ingestion failed for {file_path}: {e}")
            return False

    async def query(self, query_text: str, matter_id: Optional[str] = None, k: int = 5, context_files: Optional[List[str]] = None) -> Dict[str, Any]:
        """
        Retrieve context and generate an answer.
        
        Args:
            query_text: The user's question
            matter_id: Optional matter ID to filter documents
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
                    import os
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
        
        if not self._vector_store:
            # Fallback to direct LLM query when RAG not available
            logger.warning("Vector store not initialized. Using direct LLM fallback.")
            try:
                from services.llm_service import get_llm_service
                llm = get_llm_service()
                
                system_prompt = """You are an AI Paralegal assistant. Answer the user's legal question to the best of your ability.
If the user has provided documents, analyze their content carefully before answering.
If you don't know the answer, say so honestly. Always provide general legal information, not specific legal advice."""
                
                # Include file context if available
                if file_context:
                    user_prompt = f"Document Context:{file_context}\n\nQuestion: {query_text}"
                else:
                    user_prompt = f"Question: {query_text}"
                
                answer = await llm.generate(f"{system_prompt}\n\n{user_prompt}")
                return {
                    "answer": answer,
                    "sources": sources,
                    "confidence": "medium",
                    "method": "direct_llm"
                }
            except Exception as llm_err:
                logger.error(f"Direct LLM fallback failed: {llm_err}")
                return {"answer": f"RAG system not initialized and LLM fallback failed: {llm_err}", "sources": []}

        try:
            # 1. Retrieve from Vector Store
            filter_dict = {"matter_id": matter_id} if matter_id else None
            
            # Get docs with scores (distance)
            results = self._vector_store.similarity_search_with_score(
                query_text, 
                k=k,
                filter=filter_dict
            )
            
            # specific threshold for "low confidence"
            # Cosine distance: 0 is identical, 1 is opposite. Lower is better.
            # OpenAI embeddings usually range 0.0-0.5 for relevant stuff.
            # Let's say if best score > 0.5, we try web search.
            best_score = results[0][1] if results else 1.0
            
            context_text = ""
            sources = []
            method = "rag"
            
            if not results or best_score > 0.45: # Threshold for fallback
                logger.info(f"Low confidence ({best_score:.3f}). Triggering Firecrawl web search.")
                
                if self._firecrawl:
                    method = "web_search"
                    # Firecrawl search
                    try:
                        web_results = self._firecrawl.search(query_text, params={"limit": 3})
                        # Assume web_results is a list of objects or dicts
                        if isinstance(web_results, list): # Check firecrawl-py response structure
                             for res in web_results: # This might need adjustment based on actual lib output
                                 # Standardize
                                 content = res.get('markdown', '') or res.get('content', '') or res.get('text', '')
                                 url = res.get('url', 'web')
                                 context_text += f"\nSource [{url}]:\n{content[:1000]}\n"
                                 sources.append(url)
                    except Exception as fe:
                        logger.error(f"Firecrawl search failed: {fe}")
                        # Fallback to whatever rag we had
                        method = "rag_low_confidence"
            
            if method == "rag" or method == "rag_low_confidence":
                # Build context from chunks
                for doc, score in results:
                    context_text += f"\nSource [{doc.metadata.get('source')}]:\n{doc.page_content}\n"
                    sources.append(doc.metadata.get('source'))

            # 2. Generate Answer
            # We construct a prompt and call the LLM
            from services.llm_service import get_llm_service
            llm = get_llm_service()
            
            system_prompt = f"""You are an advanced AI Paralegal using Retrieval-Augmented Generation.
Answer the user's question based strictly on the provided context.
If the context contains the answer, cite the source.
If the context does not contain the answer, state that you don't know based on the documents.

Context:
{context_text}
"""
            user_prompt = f"Question: {query_text}"
            
            full_prompt = f"{system_prompt}\n\n{user_prompt}"
            
            answer = await llm.generate(full_prompt)
            
            return {
                "answer": answer,
                "sources": list(set(sources)), # Dedupe
                "confidence": "high" if method == "rag" else "low",
                "method": method
            }

        except Exception as e:
            logger.error(f"RAG Query failed: {e}")
            return {"answer": "An error occurred during research.", "error": str(e)}

# Global Instance
_rag_service = None

def get_rag_service() -> RAGService:
    global _rag_service
    if _rag_service is None:
        _rag_service = RAGService()
    return _rag_service

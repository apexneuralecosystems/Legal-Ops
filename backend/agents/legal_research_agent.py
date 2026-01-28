"""
Legal Research Agent with Tool Calling.

This agent orchestrates multiple research tools to provide comprehensive
legal answers backed by Malaysian case law and legislation.

Tools:
- search_uploaded_docs: Query the local RAG vector store
- search_lexis: Search Lexis Advance Malaysia for case law
- search_clj: Search CLJ database (to be implemented)
- search_legislation: Query Malaysian legislation database
"""

import logging
import asyncio
from typing import Dict, Any, List, Optional
from langchain_core.tools import tool
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
from langchain_openai import ChatOpenAI
from config import settings

logger = logging.getLogger(__name__)


# ============================================
# TOOL DEFINITIONS
# ============================================

@tool
async def search_uploaded_docs(query: str, matter_id: str = None) -> str:
    """
    Search the uploaded documents for relevant legal content.
    Use this to find information from the user's case files, contracts, and evidence.
    
    Args:
        query: The search query
        matter_id: Optional matter ID to filter results
    
    Returns:
        Relevant text chunks from uploaded documents with citations.
    """
    try:
        from services.rag_service import get_rag_service
        rag = get_rag_service()
        
        if not rag._vector_store:
            return "[No documents indexed. Please upload documents first.]"
        
        # Direct similarity search
        docs = rag._vector_store.similarity_search(query, k=5)
        
        if not docs:
            return "[No relevant content found in uploaded documents.]"
        
        results = []
        for i, doc in enumerate(docs, 1):
            source = doc.metadata.get("source", "Unknown")
            page = doc.metadata.get("page", "?")
            results.append(f"**[Doc {i}: {source}, Page {page}]**\n{doc.page_content[:500]}...")
        
        return "\n\n".join(results)
        
    except Exception as e:
        logger.error(f"search_uploaded_docs error: {e}")
        return f"[Error searching documents: {str(e)}]"


@tool
async def search_lexis(query: str, country: str = "Malaysia") -> str:
    """
    Search Lexis Advance Malaysia for case law and legal precedents.
    Use this to find Malaysian court decisions relevant to the legal issue.
    
    Args:
        query: Legal search query (e.g., "breach of contract time of essence")
        country: Country filter (default: Malaysia)
    
    Returns:
        List of relevant cases with citations and summaries.
    """
    try:
        from services.lexis_scraper import LexisScraper
        
        scraper = LexisScraper()
        await scraper.start_robot()
        
        try:
            results = await scraper.search(query, country=country)
            
            if not results or len(results) == 0:
                return "[No cases found in Lexis for this query.]"
            
            formatted = []
            for i, case in enumerate(results[:5], 1):  # Top 5 results
                title = case.get("title", "Unknown Case")
                citation = case.get("citation", "No citation")
                summary = case.get("summary", "")[:300]
                formatted.append(f"**{i}. {title}**\n*{citation}*\n{summary}...")
            
            return "\n\n".join(formatted)
            
        finally:
            await scraper.close_robot()
            
    except Exception as e:
        logger.error(f"search_lexis error: {e}")
        return f"[Lexis search failed: {str(e)}. Will rely on other sources.]"


@tool
async def search_legislation(query: str, act_name: str = None) -> str:
    """
    Search Malaysian legislation and statutes from AGC (Attorney General's Chambers).
    Use this to find relevant sections of Malaysian Acts and Ordinances.
    
    Args:
        query: Search query (e.g., "limitation period contract")
        act_name: Optional specific Act name (e.g., "Contracts Act 1950")
    
    Returns:
        Relevant statutory provisions with section numbers.
    """
    try:
        from services.agc_legislation_scraper import get_agc_scraper
        
        scraper = get_agc_scraper()
        results = await scraper.search(query, act_name=act_name)
        
        if not results:
            return "[No relevant Malaysian legislation found for this query.]"
        
        formatted = []
        for i, result in enumerate(results[:5], 1):
            act_name_str = result.get("act_name", "Unknown Act")
            act_no = result.get("act_no", "")
            sections = result.get("sections", [])
            
            section_text = "\n".join(f"  - {s}" for s in sections) if sections else "  - See full Act"
            formatted.append(f"**{i}. {act_name_str}** ({act_no})\n{section_text}")
        
        return "## Malaysian Legislation\n\n" + "\n\n".join(formatted)
        
    except Exception as e:
        logger.error(f"search_legislation error: {e}")
        return f"[Legislation search failed: {str(e)}]"





# ============================================
# LEGAL RESEARCH AGENT CLASS
# ============================================

class LegalResearchAgent:
    """
    Multi-tool agent for comprehensive legal research.
    Automatically selects appropriate tools based on query.
    """
    
    def __init__(self):
        self.tools = [search_uploaded_docs, search_lexis, search_legislation]
        self.llm = None
        self._init_llm()
    
    def _init_llm(self):
        """Initialize the LLM with tool binding."""
        try:
            # Use OpenRouter for the agent
            self.llm = ChatOpenAI(
                model=settings.OPENROUTER_MODEL or "openai/gpt-4o",
                openai_api_key=settings.OPENROUTER_API_KEY,
                openai_api_base="https://openrouter.ai/api/v1",
                temperature=0.3,
                max_tokens=4000,
            )
            
            # Bind tools to the model
            self.llm_with_tools = self.llm.bind_tools(self.tools)
            
            logger.info("LegalResearchAgent initialized with tools")
            
        except Exception as e:
            logger.error(f"Failed to initialize LegalResearchAgent LLM: {e}")
            self.llm = None
    
    async def research(
        self, 
        query: str, 
        matter_id: str = None,
        context: str = None
    ) -> Dict[str, Any]:
        """
        Execute multi-tool legal research.
        
        Args:
            query: The user's legal question
            matter_id: Optional matter ID for document filtering
            context: Optional additional context
        
        Returns:
            Dict with 'answer', 'sources', 'tools_used'
        """
        if not self.llm:
            return {
                "answer": "[Research agent not initialized. Check API keys.]",
                "sources": [],
                "tools_used": []
            }
        
        # System prompt for legal research
        system_prompt = """You are a Malaysian legal research assistant with access to REAL legal databases.
        
Your task is to answer legal questions using the available tools:
1. search_uploaded_docs - Find information in the user's uploaded case files (REAL documents)
2. search_lexis - Search Lexis Advance Malaysia for case law (REAL database via UM Library)
3. search_legislation - Search Malaysian Acts from AGC Laws of Malaysia (REAL legislation)

ALWAYS:
- Search uploaded documents first to understand the case context
- Search Lexis for authoritative Malaysian case law. If Lexis fails or returns no results, do NOT use backup sources or make up cases.
- Cite EVERY legal claim with case name, year, and official citation from the search results.
- Format case citations as: Case Name [Year] Volume Report Page (e.g., Wong Kek Wei v Ho Weng Meng [2023] 1 CLJ 145)

IMPORTANT: Only cite cases that were returned by the Lexis search tool. If Lexis search failed or returns "[Lexis search failed...]", you MUST include this warning at the VERY TOP of your answer: 
"> [!WARNING]
> Lexis Advance search was unavailable for this query. The following citations are based on general historical knowledge and MUST be verified on Lexis."

After gathering information, synthesize a comprehensive legal answer with proper Malaysian law citations."""

        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=f"Legal Question: {query}\n\nMatter ID: {matter_id or 'General'}\n\nAdditional Context: {context or 'None'}")
        ]
        
        tools_used = []
        sources = []
        
        # Max 5 turns of tool usage
        for turn in range(5):
            try:
                # Call LLM with tool binding
                response = await self.llm_with_tools.ainvoke(messages)
                
                # Check if tools were requested
                if not hasattr(response, 'tool_calls') or not response.tool_calls:
                    # Final answer received
                    return {
                        "answer": response.content,
                        "sources": sources,
                        "tools_used": tools_used
                    }
                
                # Add AI message with tool calls to history
                messages.append(response)
                
                # Handle each tool call
                for tool_call in response.tool_calls:
                    tool_name = tool_call['name']
                    tool_args = tool_call['args']
                    tool_id = tool_call['id']
                    
                    if tool_name not in tools_used:
                        tools_used.append(tool_name)
                    
                    # Execute the tool
                    logger.info(f"Executing tool: {tool_name} (Turn {turn+1})")
                    
                    if tool_name == "search_uploaded_docs":
                        result = await search_uploaded_docs.ainvoke({
                            "query": tool_args.get("query", query),
                            "matter_id": tool_args.get("matter_id", matter_id)
                        })
                    elif tool_name == "search_lexis":
                        result = await search_lexis.ainvoke({
                            "query": tool_args.get("query", query),
                            "country": tool_args.get("country", "Malaysia")
                        })
                    elif tool_name == "search_legislation":
                        result = await search_legislation.ainvoke({
                            "query": tool_args.get("query", query),
                            "act_name": tool_args.get("act_name")
                        })
                    else:
                        result = f"[Unknown tool: {tool_name}]"
                    
                    sources.append({
                        "tool": tool_name,
                        "result": result[:500] if len(result) > 500 else result
                    })
                    
                    # Add tool result to messages with tool_call_id
                    from langchain_core.messages import ToolMessage
                    messages.append(ToolMessage(
                        content=result,
                        tool_call_id=tool_id
                    ))
                    
            except Exception as e:
                logger.error(f"Error in turns loop: {e}")
                break
        
        # If we exit loop without returning, get one last answer
        final_response = await self.llm.ainvoke(messages)
        return {
            "answer": final_response.content,
            "sources": sources,
            "tools_used": tools_used
        }



# ============================================
# GLOBAL INSTANCE
# ============================================

_legal_research_agent = None

def get_legal_research_agent() -> LegalResearchAgent:
    """Get or create the global LegalResearchAgent instance."""
    global _legal_research_agent
    if _legal_research_agent is None:
        _legal_research_agent = LegalResearchAgent()
    return _legal_research_agent

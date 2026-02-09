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
        
        # Use RAG service's query method which has Long Context Strategy
        # This bypasses vector store and loads all documents directly from DB
        result = await rag.query(
            query_text=query,
            matter_id=matter_id,
            k=10
        )
        
        answer = result.get("answer", "")
        sources = result.get("sources", [])
        method = result.get("method", "unknown")
        
        if not answer or answer == "I cannot find this information in the case files.":
            return "[No documents found for this matter. Please ensure documents are uploaded and OCR processed.]"
        
        # Format response with sources
        response = f"{answer}\n\n**Sources**: {', '.join(sources) if sources else 'Case documents'}"
        return response
        
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
                link = case.get("link", "#")
                summary = case.get("summary", "")[:300]
                formatted.append(f"**{i}. {title}**\n*{citation}*\n[Link]({link})\n{summary}...")
            
            return "\n\n".join(formatted)
            
        finally:
            await scraper.close_robot()
            
    except Exception as e:
        logger.error(f"search_lexis error: {e}")
        return f"[Lexis search failed: {str(e)}. Will rely on other sources.]"


@tool
async def search_legislation(query: str, act_name: Any = None) -> str:
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
        
        # Sanitize act_name input from LLM
        if act_name and not isinstance(act_name, str):
            try:
                act_name = str(act_name)
            except:
                act_name = None
        
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


@tool
async def search_web(query: str) -> str:
    """
    Perform a High-Quality Web Search using Exa.ai (Neural Search) or Firecrawl.
    Best for finding the latest 2024-2025 legal updates, guidelines, and news.
    
    Args:
        query: The search query string
        
    Returns:
        Formatted search results with source URLs and published dates.
    """
    errors = []
    
    def log_to_file(msg):
        try:
            with open("last_search_error.txt", "a") as f:
                f.write(f"{msg}\n")
        except: pass

    log_to_file("Starting search_web call...")
    try:
        import os

        exa_key = os.getenv("EXA_API_KEY") or settings.EXA_API_KEY
        websearch_key = os.getenv("WEBSEARCH_API_KEY") or settings.WEBSEARCH_API_KEY

        # 1. Try Exa.ai (Primary)
        if exa_key:
            try:
                from exa_py import Exa
                exa = Exa(exa_key)
                
                # FORCE Malaysian context for Exa
                search_query = f"Malaysia law: {query}" if "malaysia" not in query.lower() else query
                
                # Use neural search (implicit in search_and_contents)
                response = exa.search_and_contents(
                    search_query,
                    num_results=4,
                    text=True,
                    highlights=True
                )
                
                if response.results:
                    formatted = []
                    for i, res in enumerate(response.results, 1):
                        title = res.title or "Untitled"
                        url = res.url
                        date = res.published_date or "Unknown Date"
                        text_content = res.highlights[0] if res.highlights else (res.text[:500] if res.text else "")
                        formatted.append(f"**{i}. {title}** ({date})\n{url}\n{text_content}...")
                    return f"**Web Search Results (via Exa):**\n\n" + "\n\n".join(formatted)
            except Exception as e:
                err_msg = f"Exa failed: {str(e)}"
                logger.error(err_msg)
                log_to_file(err_msg)
                errors.append(err_msg)

        # 2. Try WebSearch.ai (Fallback)
        if websearch_key:
            try:
                import requests
                import json
                
                url = "https://api.websearchapi.ai/ai-search"
                headers = {
                    "Content-Type": "application/json",
                    "Authorization": f"Bearer {websearch_key}"
                }
                payload = {
                    "query": query,
                    "maxResults": 5,
                    "includeContent": False,
                    "country": "MY",
                    "language": "en"
                }
                
                response = requests.post(url, headers=headers, json=payload, timeout=10)
                if response.status_code == 200:
                    results = response.json()
                    formatted = []
                    for i, res in enumerate(results.get("data", []), 1):
                        title = res.get("title", "Untitled")
                        url = res.get("url", "")
                        snippet = res.get("snippet", "")
                        formatted.append(f"**{i}. {title}**\n{url}\n{snippet}")
                    
                    if formatted:
                        return f"**Web Search Results (via WebSearch.ai):**\n\n" + "\n\n".join(formatted)
                else:
                    msg = f"WebSearch.ai status {response.status_code}: {response.text[:100]}"
                    log_to_file(msg)
                    errors.append(msg)
            except Exception as e:
                err_msg = f"WebSearch.ai failed: {str(e)}"
                logger.error(err_msg)
                log_to_file(err_msg)
                errors.append(err_msg)

        # 3. Try Firecrawl (Fallback)
        firecrawl_key = os.getenv("FIRECRAWL_API_KEY") or settings.FIRECRAWL_API_KEY
        if firecrawl_key:
            try:
                from firecrawl import FirecrawlApp
                app = FirecrawlApp(api_key=firecrawl_key)
                
                # FORCE Malaysian context for Firecrawl
                fc_query = f"Find information about {query} specifically in Malaysia jurisdiction/law."
                
                # Use 'agent' mode for complex research
                response = app.agent(
                    prompt=fc_query,
                    model="spark-1-mini"
                )
                
                # Firecrawl response structure varies, assuming .data or markdown return
                content = response.data if hasattr(response, 'data') else str(response)
                
                return f"**Web Search Results (via Firecrawl):**\n\n{content}"
            except Exception as e:
                err_msg = f"Firecrawl failed: {str(e)}"
                logger.error(err_msg)
                log_to_file(err_msg)
                errors.append(err_msg)

        final_err = f"[No web search results found. All search providers failed. Errors: {'; '.join(errors)}]"
        log_to_file(final_err)
        return final_err


    except ImportError:
        return "[Web search unavailable: APIs/Libraries missing (exa_py/firecrawl).]"
    except Exception as e:
        logger.error(f"search_web error: {e}")
        return f"[Web search failed: {str(e)}]"
# ============================================
# LEGAL RESEARCH AGENT CLASS
# ============================================

class LegalResearchAgent:
    """
    Multi-tool agent for comprehensive legal research.
    Automatically selects appropriate tools based on query.
    """
    
    def __init__(self):
        self.tools = [search_uploaded_docs, search_lexis, search_legislation, search_web]
        self.llm = None
        self._init_llm()
    
    def _init_llm(self):
        try:
            # Use OpenRouter for reasoning capabilities
            self.llm = ChatOpenAI(
                model=settings.OPENROUTER_MODEL or "openai/gpt-4o",
                openai_api_key=settings.OPENROUTER_API_KEY,
                openai_api_base="https://openrouter.ai/api/v1",
                temperature=0.3,
                max_tokens=4000,
            )
            self.llm_with_tools = self.llm.bind_tools(self.tools)
            logger.info("LegalResearchAgent initialized with tools: Docs, Lexis, Legislation, Web")
            
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
        system_prompt = """You are a Senior Malaysian Legal Research Assistant (Advocate & Solicitor standard).

**YOUR CORE OBJECTIVE:**
Provide comprehensive, strictly cited, and strategically sound legal analysis. You must act as a high-level paralegal or junior associate assisting a senior counsel.

**AVAILABLE TOOLS & PROTOCOLS:**
1. `search_uploaded_docs`: **MANDATORY FIRST STEP** if `matter_id` is present.
   - Extract facts, dates, and evidence from the Case Files.
   - Quote relevant clauses from contracts or statements from affidavits.
   
2. `search_legislation`: **PRIMARY AUTHORITY** for statutory law.
   - Search for specific Acts (e.g., "Contracts Act 1950", "Companies Act 2016").
   - Citations must include specific Section numbers (e.g., "Section 56(1) of the Contracts Act 1950").

3. `search_lexis`: **PRIMARY AUTHORITY** for Case Law.
   - Use this to find binding precedents and High Court/Appeal Court decisions.
   - You MUST citation the case name and report reference clearly.

4. `search_web`: **SUPPLEMENTARY AUTHORITY** & Updates.
   - Use for: Recent case law (2024-2025), current guidelines, and fact-checking.
   - **CRITICAL:** Use this to find the *latest* legal developments up to the current year.

**ANALYSIS FRAMEWORK (IRAC METHOD):**
Your response must follow this structured approach:

1.  **ISSUE Definition**: Clearly state the legal question(s) based on the user's query and case facts.
2.  **LAW (Rule)**:
    - Cite specific Statutory Provisions (Sections/Acts).
    - Cite Case Law Precedents using `search_lexis` findings.
    - **CRITICAL**: When citing a case, you MUST formatting it as: **[[Case Name]]** [Year] Volume Journal Page.
3.  **APPLICATION**: 
    - Apply the Law strictly to the facts found in the Uploaded Docs.
    - Highlight strengths and weaknesses of the position.
4.  **CONCLUSION**: Provide a direct, actionable summary holding.

**CITATION RULES:**
- Every legal claim MUST support be backed by a source (Doc Name, Act Name, or Case Citation).
- Do not hallucinate laws. If you cannot find a specific provision, state that you are searching for it.

**INTERACTION STYLE:**
- Professional, objective, and authoritative.
- Use Markdown to format statute names in **bold** and case names in *italics*.

**FINAL OUTPUT REQUIRMENT:**
At the very end of your response, after the conclusion, provide exactly **3 Suggested Follow-up Questions** strictly formatted as:
### Suggested Next Steps
- [Question 1]
- [Question 2]
- [Question 3]
"""

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
                
                # 1. Create a List of coroutines for parallel execution
                tool_tasks = []
                tool_call_ids = []
                
                for tool_call in response.tool_calls:
                    tool_name = tool_call['name']
                    tool_args = tool_call['args']
                    tool_id = tool_call['id']
                    
                    if tool_name not in tools_used:
                        tools_used.append(tool_name)
                    
                    logger.info(f"Preparing tool: {tool_name} (Turn {turn+1})")
                    tool_call_ids.append(tool_id)
                    
                    if tool_name == "search_uploaded_docs":
                        tool_tasks.append(search_uploaded_docs.ainvoke({
                            "query": tool_args.get("query", query),
                            "matter_id": tool_args.get("matter_id", matter_id)
                        }))
                    elif tool_name == "search_legislation":
                        tool_tasks.append(search_legislation.ainvoke({
                            "query": tool_args.get("query", query),
                            "act_name": tool_args.get("act_name")
                        }))
                    elif tool_name == "search_web":
                        tool_tasks.append(search_web.ainvoke({
                            "query": tool_args.get("query", query)
                        }))
                    else:
                        tool_tasks.append(asyncio.sleep(0, result=f"[Unknown tool: {tool_name}]"))

                # 2. Execute all tool calls in parallel
                tool_results = await asyncio.gather(*tool_tasks, return_exceptions=True)
                
                # 3. Add to history
                from langchain_core.messages import ToolMessage
                for tool_id, result, tool_call in zip(tool_call_ids, tool_results, response.tool_calls):
                    tool_name = tool_call['name']
                    
                    # Handle exceptions from individual tool failures
                    if isinstance(result, Exception):
                        error_msg = f"Error executing {tool_name}: {str(result)}"
                        logger.error(error_msg)
                        result = error_msg
                    
                    sources.append({
                        "tool": tool_name,
                        "result": result[:500] if isinstance(result, str) and len(result) > 500 else str(result)
                    })
                    
                    messages.append(ToolMessage(
                        content=str(result),
                        tool_call_id=tool_id
                    ))
                    
            except Exception as e:
                logger.error(f"Error in parallel turns loop: {e}")
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

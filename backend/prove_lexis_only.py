"""
Dedicated verification script to prove Lexis-only research.
"""
import asyncio
import sys
import json
import io
from datetime import datetime

# Force UTF-8 encoding for terminal output
try:
    if hasattr(sys.stdout, 'reconfigure'):
        sys.stdout.reconfigure(encoding='utf-8')
except:
    pass

sys.path.insert(0, ".")

async def prove_lexis_only():
    print("=" * 80)
    print("PROOF OF LEXIS-ONLY RESEARCH AGENT")
    print(f"Timestamp: {datetime.now().isoformat()}")
    print("=" * 80)
    
    from agents.legal_research_agent import get_legal_research_agent
    agent = get_legal_research_agent()
    
    # 1. State the tools configured in the agent
    print(f"\n[STEP 1] Verifying Agent Configuration...")
    print(f"Configured Tools: {[t.name for t in agent.tools]}")
    
    # 2. Run a query
    MATTER_ID = "MAT-20260127-8f80f57e"
    QUERY = "Find Malaysian cases on Lexis Advance about breach of settlement agreements and summarize the top 2 results."
    
    print(f"\n[STEP 2] Running Research Agent...")
    print(f"Query: {QUERY}")
    
    result = await agent.research(query=QUERY, matter_id=MATTER_ID)
    
    # 3. Show Results
    print("\n" + "-" * 40)
    print("STEP 3: EXECUTION EVIDENCE")
    print("-" * 40)
    print(f"Tools Actually Used: {result.get('tools_used', [])}")
    
    print("\n[FINAL ANSWER SAMPLE]")
    print("=" * 60)
    print(result.get('answer', '')[:1000] + "...")
    print("=" * 60)
    
    print("\n[SOURCES BREAKDOWN]")
    for i, source in enumerate(result.get('sources', []), 1):
        print(f"{i}. Tool: {source['tool']} | Result Fragment: {source['result'][:100]}...")

if __name__ == "__main__":
    asyncio.run(prove_lexis_only())

"""
Streamlined Legal Research Agent Test for Answer Evaluation.
"""
import asyncio
import sys
import json
sys.path.insert(0, ".")

async def evaluate_research():
    from agents.legal_research_agent import get_legal_research_agent
    from config import settings
    
    # Force credentials check
    print(f"Using email: anmita132@gmail.com")
    
    MATTER_ID = "MAT-20260127-8f80f57e"
    agent = get_legal_research_agent()
    
    query = "What are the key legal issues in this case and what Malaysian case law supports our position?"
    context = "Matter: Sena Traffic Systems Sdn. Bhd. v. AR-Rifqi Sdn. Bhd. Dispute over traffic system contract."
    
    print("Running research...")
    try:
        result = await agent.research(
            query=query,
            matter_id=MATTER_ID,
            context=context
        )
        
        # Save results to a clean file
        with open("research_evaluation.json", "w", encoding="utf-8") as f:
            json.dump(result, f, indent=2)
            
        print("\n=== RESEARCH COMPLETED ===")
        print(f"Tools Used: {result.get('tools_used', [])}")
        print("\nAnswer Snippet:")
        print(result.get("answer", "No answer")[:500] + "...")
        
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    asyncio.run(evaluate_research())

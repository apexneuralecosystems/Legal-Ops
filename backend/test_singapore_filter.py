"""
Test script to verify Singapore filter is working
"""
import asyncio
import sys
import os

if sys.platform == 'win32':
    asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from services.lexis_scraper import LexisScraper

async def test_filter():
    print("="*60)
    print("TESTING SINGAPORE FILTER")
    print("="*60)
    
    scraper = LexisScraper()
    
    print("\n[TEST 1] Searching with Singapore filter...")
    results = await scraper.search("banking", "Singapore")
    
    print(f"\nResults found: {len(results)}")
    if results:
        print("\n[First Result]")
        print(f"Title: {results[0].get('title', 'N/A')}")
        print(f"Citation: {results[0].get('citation', 'N/A')}")
        print(f"Link: {results[0].get('link', 'N/A')}")
        print(f"Relevance: {results[0].get('relevance_score', 'N/A')}")

if __name__ == "__main__":
    asyncio.run(test_filter())

"""
Test script to verify Lexis link extraction
"""
import asyncio
import sys
import os

if sys.platform == 'win32':
    asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from services.lexis_scraper import LexisScraper

async def test_link_extraction():
    print("="*60)
    print("TESTING LEXIS LINK EXTRACTION")
    print("="*60)
    
    scraper = LexisScraper(use_pool=False)
    results_log = []

    try:
        # Test 1: Generic Search
        print("\n[TEST 1] Searching for 'breach of contract'...")
        results = await scraper.search("breach of contract")
        results_log.append(f"Test 1 Check: Found {len(results)} results")
        
        if results:
            for idx, res in enumerate(results[:5]): # Show first 5
                 log_msg = f"Result {idx+1}: {res.get('title')} | Link: {res.get('link')}"
                 print(log_msg)
                 results_log.append(log_msg)
            
            res = results[0]
            if "/document" in res.get('link', '') or "pddocfullpath" in res.get('link', ''):
                results_log.append("✅ Test 1 PASS: Deep link extracted")
            else:
                results_log.append("⚠️ Test 1 WARNING: Not a document link")
                # FORCE FAIL TO SEE HTML
                # print("DEBUG HTML LENGTH: " + str(len(res.get('debug_html', ''))))

        # Test 2: Specific Citation (User Case)
        print("\n[TEST 2] Searching for specific citation '[2026] MLJU 151'...")
        results_citation = await scraper.search("[2026] MLJU 151")
        results_log.append(f"Test 2 Check: Found {len(results_citation)} results")

        if results_citation:
            res = results_citation[0]
            log_msg = f"Result 2 Link: {res.get('link', 'N/A')}"
            print(log_msg)
            results_log.append(log_msg)
            
            if "/document" in res.get('link', '') or "pddocfullpath" in res.get('link', ''):
                results_log.append("✅ Test 2 PASS: Deep link extracted for citation")
            else:
                results_log.append("⚠️ Test 2 WARNING: Not a document link")
    
    except Exception as e:
        print(f"❌ TEST FAILED: {e}")
        results_log.append(f"❌ TEST FAILED: {e}")
    finally:
        # Write results to file
        with open("test_results_manual.txt", "w", encoding="utf-8") as f:
            f.write("\n".join(results_log))
        print("Results written to test_results_manual.txt")

if __name__ == "__main__":
    asyncio.run(test_link_extraction())

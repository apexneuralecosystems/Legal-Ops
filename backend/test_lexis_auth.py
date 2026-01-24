"""
Quick test script for Lexis Advance authentication flow.
Run this to verify the fix works.
"""
import asyncio
import sys
import os

# CRITICAL: Set Windows event loop policy BEFORE any async operations
if sys.platform == 'win32':
    asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from services.lexis_scraper import LexisScraper

import time

async def test_auth():
    start_time = time.time()
    print("=" * 60)

    print("LEXIS ADVANCE AUTHENTICATION TEST")
    print("=" * 60)
    
    scraper = LexisScraper()
    
    print(f"\n[CONFIG]")
    print(f"  Username: {scraper.username}")
    print(f"  Headless: {scraper.headless}")
    print(f"  Entry Point: {scraper.UM_LIBRARY_PORTAL_URL}")
    
    print("\n[STARTING TEST]")
    print("This will open a browser and attempt full authentication flow:")
    print("  1. UM Library Portal")
    print("  2. Click Lexis Advance link")
    print("  3. CAS Login (with service= parameter)")
    print("  4. Redirect to Lexis")
    print("  5. Verify dashboard")
    print()
    
    try:
        # Just test a simple search
        results = await scraper.search("bankin", "Malaysia")
        
        end_time = time.time()
        duration = end_time - start_time
        
        print("\n" + "=" * 60)
        print(f"SUCCESS! Completed in {duration:.2f} seconds")
        print("=" * 60)
        print(f"Results found: {len(results)}")
        
        # Write success file
        with open("SUCCESS.txt", "w") as f:
            f.write(f"Authentication Successful! found {len(results)} results")
        
        for i, result in enumerate(results[:3], 1):
            print(f"\n[Result {i}]")
            print(f"  Title: {result.get('title', 'N/A')[:60]}...")
            print(f"  Citation: {result.get('citation', 'N/A')}")
            
        return True
            
    except Exception as e:
        print("\n" + "=" * 60)
        print("AUTHENTICATION FAILED")
        print("=" * 60)
        print(f"Error: {e}")
        # Write failure file
        with open("FAILURE.txt", "w") as f:
            f.write(str(e))
        print("\nCheck debug_captures/ folder for screenshots and HTML dumps")
        return False
    finally:
        await scraper.close_robot()

if __name__ == "__main__":
    success = asyncio.run(test_auth())
    sys.exit(0 if success else 1)

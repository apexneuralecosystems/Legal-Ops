import requests
import json
import time

url = "http://localhost:8091/api/research/search"
payload = {
    "query": "banking",
    "filters": {"jurisdiction": "Malaysia"}
}

print(f"Testing API: {url}")
start_time = time.time()
try:
    # 90s timeout because Lexis scraping takes time
    response = requests.post(url, json=payload, timeout=90) 
    elapsed = time.time() - start_time
    print(f"Time: {elapsed:.2f}s")
    print(f"Status Code: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        print("✅ API Success!")
        cases = data.get('cases', [])
        print(f"Cases found: {len(cases)}")
        if cases:
            print(f"First Case: {cases[0].get('title')} - {cases[0].get('citation')}")
        else:
            print("No cases returned (but API worked).")
    else:
        print(f"❌ API Error: {response.text}")
        
except Exception as e:
    print(f"CRITICAL ERROR: {e}")


import urllib.request
import urllib.error
import json
import sys

# Constants
BASE_URL = "http://localhost:8091/api/matters"
MATTER_ID = "MAT-20251230-007ffb1d"  # From user report

def test_prepare_hearing():
    url = f"{BASE_URL}/{MATTER_ID}/prepare-hearing"
    print(f"[*] Sending POST request to: {url}")
    
    req = urllib.request.Request(url, method="POST")
    
    try:
        with urllib.request.urlopen(req, timeout=90) as response:
            status_code = response.getcode()
            print(f"[*] Status Code: {status_code}")
            
            body = response.read().decode('utf-8', errors='replace')
            print(f"[*] Raw Response Body: {body}")
            try:
                data = json.loads(body)
                print(f"[*] Response Body (JSON): {data}")
            except:
                print(f"[*] Response Body (Text): {body}")
                
            if status_code == 200:
                if isinstance(data, dict) and data.get("status") == "error":
                     print("[-] Backend returned logic error (200 OK but failed code)")
                else:
                     print("[+] Success!")
                return True
            else:
                print(f"[-] Unexpected status code: {status_code}")
                return False
                
    except urllib.error.HTTPError as e:
        print(f"[-] HTTP Error: {e.code} {e.reason}")
        print(f"[-] Response: {e.read().decode('utf-8')}")
        if e.code == 500:
            print("[-] Reproduced 500 Internal Server Error!")
        return False
        
    except Exception as e:
        print(f"[-] Request failed: {e}")
        return False

if __name__ == "__main__":
    test_prepare_hearing()

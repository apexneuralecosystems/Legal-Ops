
import urllib.request
import urllib.error
import json
import sys

# Constants
BASE_URL = "http://localhost:8091/api/matters"
# Use the same matter ID the user is using
MATTER_ID = "MAT-20251230-007ffb1d" 

def invoke_endpoint(name, endpoint, payload):
    url = f"{BASE_URL}/{MATTER_ID}/{endpoint}"
    print(f"\n[*] Testing {name}: {url}")
    
    headers = {'Content-Type': 'application/json'}
    data = json.dumps(payload).encode('utf-8')
    req = urllib.request.Request(url, data=data, headers=headers, method="POST")
    
    try:
        # Long timeout to allow for LLM processing
        with urllib.request.urlopen(req, timeout=90) as response:
            status_code = response.getcode()
            print(f"[*] Status Code: {status_code}")
            
            body = response.read().decode('utf-8', errors='replace')
            try:
                resp_data = json.loads(body)
                print(f"[*] Response: {json.dumps(resp_data, indent=2)[:500]}...") # Truncate log
            except:
                print(f"[*] Raw Body: {body[:500]}...")
                
            return status_code == 200
            
    except urllib.error.HTTPError as e:
        print(f"[-] HTTP Error: {e.code} {e.reason}")
        err_body = e.read().decode('utf-8', errors='replace')
        print(f"[-] Error Body: {err_body}")
        return False
    except Exception as e:
        print(f"[-] Request failed: {e}")
        return False

def test_build_evidence():
    # Payload for build-evidence-packet
    payload = {
        "documents": [
            {
                "id": "DOC-TEST-001",
                "filename": "test_doc.pdf",
                "doc_lang_hint": "en",
                "file_path": "uploads/test_doc.pdf",
                "mime_type": "application/pdf"
            }
        ]
    }
    invoke_endpoint("Build Evidence Packet", "build-evidence-packet", payload)

def test_draft():
    # Payload for draft
    payload = {
        "template_id": "TPL-HighCourt-MS-v2",
        "issues_selected": [{"id": "ISSUE-1", "title": "Breach of Contract"}],
        "prayers_selected": [{"id": "PRAYER-1", "text": "Damages"}]
    }
    invoke_endpoint("Drafting Workflow", "draft", payload)

if __name__ == "__main__":
    print(f"Targeting Matter: {MATTER_ID}")
    test_build_evidence()
    test_draft()

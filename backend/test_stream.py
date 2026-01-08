import requests
import json
import sys

# URL and Matter ID
MATTER_ID = "MAT-20251231-6e95ef90" # Use a valid matter ID from your system
URL = f"http://localhost:8091/api/matters/{MATTER_ID}/draft/stream" 

# Payload
data = {
    "template_id": "TPL-HighCourt-EN-v2",
    "issues_selected": [{"id": "ISS-01", "title": "Test Issue"}],
    "prayers_selected": [{"text_en": "Test Prayer"}]
}

print(f"Testing streaming for matter: {MATTER_ID}")
print(f"URL: {URL}")

try:
    with requests.post(URL, json=data, stream=True, timeout=120) as r:
        r.raise_for_status()
        print("Connected to stream...")
        
        for line in r.iter_lines():
            if line:
                decoded_line = line.decode('utf-8')
                if decoded_line.startswith("data: "):
                    print(f"Received Event: {decoded_line}")
                else:
                    print(f"Raw: {decoded_line}")
except Exception as e:
    print(f"Error: {e}")

"""
Debug script to test Paralegal chat endpoint directly.
"""
import asyncio
import httpx
import sys

async def test_paralegal_chat():
    """Test the paralegal chat endpoint."""
    base_url = "http://127.0.0.1:8091"
    
    # First, login to get a token
    print("1. Testing login...")
    async with httpx.AsyncClient() as client:
        try:
            login_resp = await client.post(
                f"{base_url}/api/auth/login",
                json={"email": "lawyer@firm.com", "password": "password"},  # JSON body with email
                timeout=10
            )
            print(f"   Login status: {login_resp.status_code}")
            if login_resp.status_code == 200:
                tokens = login_resp.json()
                access_token = tokens.get("access_token")
                print(f"   Got token: {access_token[:20]}...")
            else:
                print(f"   Login failed: {login_resp.text}")
                return
        except Exception as e:
            print(f"   Login error: {e}")
            import traceback
            traceback.print_exc()
            return
    
    # Now test paralegal chat
    print("\n2. Testing paralegal chat...")
    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(
                f"{base_url}/api/paralegal/chat",
                json={
                    "message": "What is a contract?",
                    "matter_id": None,
                    "context_files": []
                },
                headers={
                    "Authorization": f"Bearer {access_token}",
                    "Content-Type": "application/json"
                },
                timeout=60  # Longer timeout for LLM response
            )
            print(f"   Response status: {response.status_code}")
            print(f"   Response headers: {dict(response.headers)}")
            print(f"   Response body (first 1000 chars):\n{response.text[:1000]}")
        except Exception as e:
            print(f"   Chat error: {e}")
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_paralegal_chat())

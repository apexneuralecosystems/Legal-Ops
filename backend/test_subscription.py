"""
Test Subscription and Usage Tracking Endpoints
"""
import requests
import json
import os

BASE_URL = os.getenv("BACKEND_URL", "http://localhost:8005")

def get_auth_token():
    """Login and get authentication token"""
    response = requests.post(
        f"{BASE_URL}/api/auth/login",
        json={
            "email": "apextest123@example.com",
            "password": "TestPassword123!"
        }
    )
    
    if response.status_code == 200:
        return response.json()["access_token"]
    return None


def test_usage_status(token):
    """Test getting usage status"""
    print("\n" + "="*80)
    print("TEST 1: GET USAGE STATUS")
    print("="*80)
    
    headers = {"Authorization": f"Bearer {token}"}
    
    response = requests.get(
        f"{BASE_URL}/api/subscription/usage/status",
        headers=headers
    )
    
    print(f"\nStatus Code: {response.status_code}")
    
    if response.status_code == 200:
        print("✅ SUCCESS")
        print(json.dumps(response.json(), indent=2))
        return True
    else:
        print("❌ FAILED")
        print(response.text)
        return False


def test_check_workflow_access(token, workflow_type="intake"):
    """Test checking workflow access"""
    print("\n" + "="*80)
    print(f"TEST 2: CHECK WORKFLOW ACCESS ({workflow_type})")
    print("="*80)
    
    headers = {"Authorization": f"Bearer {token}"}
    
    response = requests.get(
        f"{BASE_URL}/api/subscription/check/{workflow_type}",
        headers=headers
    )
    
    print(f"\nStatus Code: {response.status_code}")
    
    if response.status_code == 200:
        result = response.json()
        print("✅ SUCCESS")
        print(json.dumps(result, indent=2))
        return result.get("can_access", False)
    else:
        print("❌ FAILED")
        print(response.text)
        return False


def main():
    print("\n" + "╔" + "="*78 + "╗")
    print("║" + "SUBSCRIPTION & USAGE TRACKING TEST".center(78) + "║")
    print("╚" + "="*78 + "╝")
    
    # Get token
    print("\nAuthenticating...")
    token = get_auth_token()
    
    if not token:
        print("❌ Authentication failed")
        return
    
    print(f"✓ Token: {token[:20]}...")
    
    # Test usage status endpoint
    test_usage_status(token)
    
    # Test workflow access check
    for workflow in ["intake", "drafting", "evidence", "research"]:
        test_check_workflow_access(token, workflow)
    
    print("\n" + "="*80)
    print("TESTING COMPLETE".center(80))
    print("="*80 + "\n")


if __name__ == "__main__":
    main()

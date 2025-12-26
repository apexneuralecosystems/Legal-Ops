"""
Test Payment Gate Enforcement
Verifies that workflow endpoints return 402 after free uses are exhausted.
"""
import requests
import json

BASE_URL = "http://localhost:8005"


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


def test_payment_gate(token):
    """Test that intake endpoint enforces payment gate"""
    headers = {"Authorization": f"Bearer {token}"}
    
    print("=" * 60)
    print("TESTING PAYMENT GATE ENFORCEMENT")
    print("=" * 60)
    
    # First, check current usage status
    print("\n1. Checking current usage status...")
    r = requests.get(f"{BASE_URL}/api/subscription/usage/status", headers=headers)
    if r.status_code == 200:
        usage = r.json()
        print(f"   Intake uses: {usage.get('usage', {}).get('intake', {}).get('used', 0)}")
        print(f"   Has paid: {usage.get('has_paid', False)}")
    
    # Check workflow access
    print("\n2. Checking intake workflow access...")
    r = requests.get(f"{BASE_URL}/api/subscription/check/intake", headers=headers)
    if r.status_code == 200:
        access = r.json()
        print(f"   Can access: {access.get('can_access')}")
        print(f"   Remaining: {access.get('remaining_free_uses')}")
        print(f"   Requires payment: {access.get('requires_payment')}")
    
    # Try calling the intake endpoint
    print("\n3. Calling intake endpoint...")
    r = requests.post(
        f"{BASE_URL}/api/matters/intake",
        headers=headers,
        data={"connector_type": "upload", "metadata": "{}"}
    )
    print(f"   Status: {r.status_code}")
    
    if r.status_code == 402:
        print("   Result: PAYMENT REQUIRED (as expected after free use)")
        detail = r.json().get("detail", {})
        print(f"   Message: {detail.get('message', 'N/A')}")
        print(f"   Redirect: {detail.get('redirect_url', 'N/A')}")
    elif r.status_code == 200:
        print("   Result: SUCCESS (free use consumed)")
    else:
        print(f"   Result: {r.text[:200]}")
    
    # Check usage again
    print("\n4. Checking usage after call...")
    r = requests.get(f"{BASE_URL}/api/subscription/usage/status", headers=headers)
    if r.status_code == 200:
        usage = r.json()
        print(f"   Intake uses: {usage.get('usage', {}).get('intake', {}).get('used', 0)}")
    
    # Try again - should get 402
    print("\n5. Calling intake again (should get 402)...")
    r = requests.post(
        f"{BASE_URL}/api/matters/intake",
        headers=headers,
        data={"connector_type": "upload", "metadata": "{}"}
    )
    print(f"   Status: {r.status_code}")
    
    if r.status_code == 402:
        print("   PAYMENT GATE WORKING!")
        detail = r.json().get("detail", {})
        print(f"   Message: {detail.get('message', '')}")
    else:
        print(f"   Unexpected: {r.text[:200]}")
    
    print("\n" + "=" * 60)


def main():
    print("\nAuthenticating...")
    token = get_auth_token()
    if not token:
        print("Authentication failed!")
        return
    
    print(f"Token: {token[:30]}...")
    test_payment_gate(token)


if __name__ == "__main__":
    main()

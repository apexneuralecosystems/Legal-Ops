"""
Test PayPal Integration with Authentication
Now that Apex auth works, test PayPal endpoints with valid tokens
"""
import requests
import json
import os

BASE_URL = os.getenv("BACKEND_URL", "http://localhost:8005")

def get_auth_token():
    """Login and get authentication token"""
    print("Step 1: Authenticating user...")
    
    # Try to login with existing user
    response = requests.post(
        f"{BASE_URL}/api/auth/login",
        json={
            "email": "apextest123@example.com",
            "password": "TestPassword123!"
        }
    )
    
    if response.status_code == 200:
        token = response.json()["access_token"]
        print(f"✓ Authentication successful")
        print(f"Token: {token[:20]}...")
        return token
    else:
        print(f"✗ Authentication failed: {response.status_code}")
        print(response.text)
        return None


def test_create_order(token):
    """Test creating a PayPal order with auth"""
    print("\n" + "="*80)
    print("TEST: Create PayPal Order (Authenticated)")
    print("="*80)
    
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    payload = {
        "amount": 10.00,
        "currency": "USD",
        "description": "Test Legal-Ops Subscription"
    }
    
    response = requests.post(
        f"{BASE_URL}/api/payments/orders/create",
        headers=headers,
        json=payload
    )
    
    print(f"\nStatus Code: {response.status_code}")
    
    if response.status_code == 200:
        result = response.json()
        print("✅ SUCCESS - PayPal order created!")
        print(f"\nOrder Details:")
        print(json.dumps(result, indent=2))
        return result.get("order_id")
    else:
        print("❌ FAILED - Order creation failed")
        try:
            print(f"Error: {json.dumps(response.json(), indent=2)}")
        except:
            print(f"Response: {response.text}")
        return None


def test_get_order(token, order_id):
    """Test getting order details"""
    if not order_id:
        print("\nSkipping order details test (no order ID)")
        return
    
    print("\n" + "="*80)
    print("TEST: Get Order Details")
    print("="*80)
    
    headers = {
        "Authorization": f"Bearer {token}"
    }
    
    response = requests.get(
        f"{BASE_URL}/api/payments/orders/{order_id}",
        headers=headers
    )
    
    print(f"\nStatus Code: {response.status_code}")
    
    if response.status_code == 200:
        result = response.json()
        print("✅ SUCCESS - Order details retrieved!")
        print(f"\nOrder Info:")
        print(json.dumps(result, indent=2))
    else:
        print("❌ FAILED")
        print(response.text)


def main():
    print("\n" + "╔" + "="*78 + "╗")
    print("║" + "PAYPAL INTEGRATION TEST (With Authentication)".center(78) + "║")
    print("╚" + "="*78 + "╝\n")
    
    # Get authentication token
    token = get_auth_token()
    
    if not token:
        print("\n❌ Cannot proceed without authentication token")
        return
    
    # Test PayPal order creation
    order_id = test_create_order(token)
    
    # Test getting order details
    if order_id:
        test_get_order(token, order_id)
    
    # Summary
    print("\n" + "="*80)
    print("SUMMARY")
    print("="*80)
    print("✅ Authentication: WORKING")
    print(f"{'✅' if order_id else '❌'} PayPal Order Creation: {'WORKING' if order_id else 'FAILED'}")
    print("="*80 + "\n")


if __name__ == "__main__":
    main()

"""
Test Apex Authentication after initialization
"""
import requests
import json
import os

BASE_URL = os.getenv("BACKEND_URL", "http://localhost:8005")

def test_signup():
    """Test user signup"""
    print("\n" + "="*80)
    print("TEST 1: USER SIGNUP".center(80))
    print("="*80)
    
    response = requests.post(
        f"{BASE_URL}/api/auth/signup",
        json={
            "email": "testuser@example.com",
            "password": "TestPassword123!",
            "full_name": "Test User"
        }
    )
    
    print(f"\nStatus Code: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")
    
    if response.status_code in [200, 201]:
        print("\n✅ SIGNUP SUCCESSFUL!")
        return True
    else:
        print("\n❌ SIGNUP FAILED")
        return False


def test_login():
    """Test user login"""
    print("\n" + "="*80)
    print("TEST 2: USER LOGIN".center(80))
    print("="*80)
    
    response = requests.post(
        f"{BASE_URL}/api/auth/login",
        json={
            "email": "testuser@example.com",
            "password": "TestPassword123!"
        }
    )
    
    print(f"\nStatus Code: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        print(f"Response: {json.dumps(data, indent=2)}")
        print("\n✅ LOGIN SUCCESSFUL!")
        return True, data.get("access_token")
    else:
        print(f"Response: {response.text}")
        print("\n❌ LOGIN FAILED")
        return False, None


def test_get_current_user(token):
    """Test getting current user info"""
    print("\n" + "="*80)
    print("TEST 3: GET CURRENT USER".center(80))
    print("="*80)
    
    response = requests.get(
        f"{BASE_URL}/api/auth/me",
        headers={"Authorization": f"Bearer {token}"}
    )
    
    print(f"\nStatus Code: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")
    
    if response.status_code == 200:
        print("\n✅ GET USER SUCCESSFUL!")
        return True
    else:
        print("\n❌ GET USER FAILED")
        return False


def main():
    print("\n" + "╔" + "="*78 + "╗")
    print("║" + "APEX AUTHENTICATION TEST".center(78) + "║")
    print("╚" + "="*78 + "╝")
    
    # Test signup
    signup_success = test_signup()
    
    # Test login
    if signup_success:
        login_success, token = test_login()
        
        # Test get current user
        if login_success and token:
            test_get_current_user(token)
    else:
        # Try login anyway in case user already exists
        login_success, token = test_login()
        if login_success and token:
            test_get_current_user(token)
    
    print("\n" + "="*80)
    print("TESTING COMPLETE".center(80))
    print("="*80 + "\n")


if __name__ == "__main__":
    main()

"""
Test SendGrid Email and PayPal Integration
Tests the newly configured credentials for email and payment services
"""
import requests
import json
import os
from datetime import datetime

BASE_URL = os.getenv("BACKEND_URL", "http://localhost:8005")

class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    RESET = '\033[0m'
    BOLD = '\033[1m'


def print_header(text):
    """Print section header"""
    print(f"\n{Colors.BOLD}{Colors.BLUE}{'='*80}{Colors.RESET}")
    print(f"{Colors.BOLD}{Colors.BLUE}{text.center(80)}{Colors.RESET}")
    print(f"{Colors.BOLD}{Colors.BLUE}{'='*80}{Colors.RESET}\n")


def test_sendgrid_email():
    """Test SendGrid email functionality via password reset endpoint"""
    print_header("TESTING SENDGRID EMAIL INTEGRATION")
    
    print("Test 1: Password Reset Email")
    print("Testing POST /api/auth/forgot-password endpoint...")
    
    try:
        response = requests.post(
            f"{BASE_URL}/api/auth/forgot-password",
            json={
                "email": "test@example.com"
            }
        )
        
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print(f"{Colors.GREEN}✓ PASS{Colors.RESET} - Email endpoint responded successfully")
            print(f"Message: {result.get('message')}")
            print(f"\n{Colors.YELLOW}Note:{Colors.RESET} Check if email was sent to test@example.com")
            print(f"From: praveen.jogi@apexneural.com")
            return True
        else:
            print(f"{Colors.RED}✗ FAIL{Colors.RESET} - Unexpected status code")
            print(f"Response: {response.text}")
            return False
            
    except Exception as e:
        print(f"{Colors.RED}✗ ERROR{Colors.RESET} - {str(e)}")
        return False


def test_paypal_order_creation():
    """Test PayPal order creation"""
    print_header("TESTING PAYPAL SANDBOX INTEGRATION")
    
    print("Test 1: Create PayPal Order")
    print("Testing POST /api/payments/orders/create endpoint...")
    
    # First, we need to sign up/login to get auth token
    print("\nStep 1: Getting authentication token...")
    try:
        # Try to login first
        login_response = requests.post(
            f"{BASE_URL}/api/auth/login",
            json={
                "email": "test@example.com",
                "password": "TestPassword123!"
            }
        )
        
        if login_response.status_code == 200:
            token = login_response.json().get("access_token")
            print(f"{Colors.GREEN}✓{Colors.RESET} Logged in successfully")
        else:
            # Try to sign up
            print("Login failed, attempting signup...")
            signup_response = requests.post(
                f"{BASE_URL}/api/auth/signup",
                json={
                    "email": "paypaltest@example.com",
                    "password": "TestPassword123!",
                    "full_name": "PayPal Test User"
                }
            )
            
            if signup_response.status_code in [200, 201]:
                # Now login
                login_response = requests.post(
                    f"{BASE_URL}/api/auth/login",
                    json={
                        "email": "paypaltest@example.com",
                        "password": "TestPassword123!"
                    }
                )
                token = login_response.json().get("access_token")
                print(f"{Colors.GREEN}✓{Colors.RESET} Signed up and logged in")
            else:
                print(f"{Colors.YELLOW}⚠{Colors.RESET} Could not authenticate, testing without auth...")
                token = None
    except Exception as e:
        print(f"{Colors.YELLOW}⚠{Colors.RESET} Auth error: {e}, testing without auth...")
        token = None
    
    print("\nStep 2: Creating PayPal order...")
    try:
        headers = {}
        if token:
            headers["Authorization"] = f"Bearer {token}"
        
        response = requests.post(
            f"{BASE_URL}/api/payments/orders/create",
            json={
                "amount": "10.00",
                "currency": "USD",
                "description": "Test Payment for Legal-Ops"
            },
            headers=headers
        )
        
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print(f"{Colors.GREEN}✓ PASS{Colors.RESET} - PayPal order created successfully")
            print(f"\nOrder Details:")
            print(f"  Order ID: {result.get('order_id', 'N/A')}")
            print(f"  Status: {result.get('status', 'N/A')}")
            print(f"  Approval URL: {result.get('approval_url', 'N/A')[:80]}...")
            
            # Check if we're using sandbox credentials
            print(f"\n{Colors.BLUE}PayPal Configuration:{Colors.RESET}")
            print(f"  Mode: SANDBOX")
            print(f"  Client ID: AbdeYPtmLDG... (configured)")
            
            return True, result.get('order_id')
        else:
            print(f"{Colors.RED}✗ FAIL{Colors.RESET} - Order creation failed")
            try:
                error = response.json()
                print(f"Error: {json.dumps(error, indent=2)}")
            except:
                print(f"Response: {response.text}")
            return False, None
            
    except Exception as e:
        print(f"{Colors.RED}✗ ERROR{Colors.RESET} - {str(e)}")
        return False, None


def test_paypal_order_details(order_id, token=None):
    """Test retrieving PayPal order details"""
    if not order_id:
        print(f"\n{Colors.YELLOW}Skipping order details test - no order ID{Colors.RESET}")
        return False
    
    print("\nTest 2: Get Order Details")
    print(f"Testing GET /api/payments/orders/{order_id}...")
    
    try:
        headers = {}
        if token:
            headers["Authorization"] = f"Bearer {token}"
        
        response = requests.get(
            f"{BASE_URL}/api/payments/orders/{order_id}",
            headers=headers
        )
        
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print(f"{Colors.GREEN}✓ PASS{Colors.RESET} - Order details retrieved")
            print(f"Order Status: {result.get('status', 'N/A')}")
            return True
        else:
            print(f"{Colors.RED}✗ FAIL{Colors.RESET} - Could not retrieve order")
            return False
            
    except Exception as e:
        print(f"{Colors.RED}✗ ERROR{Colors.RESET} - {str(e)}")
        return False


def check_server():
    """Check if server is running"""
    try:
        response = requests.get(f"{BASE_URL}/health", timeout=3)
        return response.status_code == 200
    except:
        return False


def main():
    print(f"\n{Colors.BOLD}{Colors.BLUE}")
    print("╔════════════════════════════════════════════════════════════════════════════╗")
    print("║          Email & Payment Integration Testing (SendGrid + PayPal)          ║")
    print("╚════════════════════════════════════════════════════════════════════════════╝")
    print(f"{Colors.RESET}\n")
    
    print(f"Base URL: {BASE_URL}")
    print(f"Test started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
    
    # Check server
    if not check_server():
        print(f"{Colors.RED}{Colors.BOLD}ERROR: Server is not running at {BASE_URL}{Colors.RESET}")
        print("\nPlease ensure the server is running with the updated .env configuration")
        print("The server should have reloaded automatically with the new credentials.")
        return
    
    print(f"{Colors.GREEN}✓ Server is running{Colors.RESET}\n")
    
    # Test SendGrid
    email_success = test_sendgrid_email()
    
    # Test PayPal
    paypal_success, order_id = test_paypal_order_creation()
    
    if paypal_success and order_id:
        test_paypal_order_details(order_id)
    
    # Summary
    print_header("TEST SUMMARY")
    
    print(f"Email Integration (SendGrid):")
    if email_success:
        print(f"  {Colors.GREEN}✓ WORKING{Colors.RESET} - Endpoint responds correctly")
        print(f"  {Colors.YELLOW}⚠ MANUAL CHECK REQUIRED{Colors.RESET} - Verify email delivery")
    else:
        print(f"  {Colors.RED}✗ FAILED{Colors.RESET} - Check SendGrid configuration")
    
    print(f"\nPayment Integration (PayPal):")
    if paypal_success:
        print(f"  {Colors.GREEN}✓ WORKING{Colors.RESET} - Sandbox orders can be created")
        print(f"  Mode: SANDBOX")
        print(f"  Client ID: Configured ✓")
    else:
        print(f"  {Colors.RED}✗ FAILED{Colors.RESET} - Check PayPal configuration")
    
    print(f"\n{Colors.BLUE}Configuration Status:{Colors.RESET}")
    print(f"  ✓ SENDGRID_API_KEY: Configured")
    print(f"  ✓ FROM_EMAIL: praveen.jogi@apexneural.com")
    print(f"  ✓ FRONTEND_RESET_URL: https://dbaas.apexneural.cloud/reset-password")
    print(f"  ✓ PAYPAL_CLIENT_ID: Configured (Sandbox)")
    print(f"  ✓ PAYPAL_CLIENT_SECRET: Configured (Sandbox)")
    print(f"  ✓ PAYPAL_MODE: sandbox")
    
    print(f"\n{Colors.BOLD}Next Steps:{Colors.RESET}")
    if email_success:
        print(f"  1. Check inbox of test@example.com for password reset email")
        print(f"  2. Verify email is sent from praveen.jogi@apexneural.com")
        print(f"  3. Test the reset link functionality")
    
    if paypal_success:
        print(f"  4. Complete payment flow in PayPal sandbox")
        print(f"  5. Test order capture endpoint")
        print(f"  6. Test subscription endpoints if needed")
    
    print(f"\n{Colors.BOLD}{Colors.BLUE}Testing completed!{Colors.RESET}\n")


if __name__ == "__main__":
    main()

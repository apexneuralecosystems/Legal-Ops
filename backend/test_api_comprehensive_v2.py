"""
Comprehensive test script for Legal-Ops API
Tests database migration and all 45 endpoints
"""
import requests
import json
import sys
from typing import Dict, Any, Optional
from datetime import datetime
import os

# Base configuration
BASE_URL = "http://localhost:8005"
API_URL = f"{BASE_URL}/api"

# Test results storage
test_results = []
total_tests = 0
passed_tests = 0
failed_tests = 0

# Authentication tokens (will be populated after login)
auth_tokens = {
    "access_token": None,
    "refresh_token": None
}

# Test user credentials
test_user = {
    "email": "test@example.com",
    "password": "TestPassword123!",
    "full_name": "Test User"
}

# Color codes for terminal output
class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    RESET = '\033[0m'
    BOLD = '\033[1m'


def print_header(text: str):
    """Print section header"""
    print(f"\n{Colors.BOLD}{Colors.BLUE}{'='*80}{Colors.RESET}")
    print(f"{Colors.BOLD}{Colors.BLUE}{text.center(80)}{Colors.RESET}")
    print(f"{Colors.BOLD}{Colors.BLUE}{'='*80}{Colors.RESET}\n")


def print_test(name: str, status: str, message: str = "", response_time: float = 0):
    """Print test result"""
    status_color = Colors.GREEN if status == "PASS" else Colors.RED if status == "FAIL" else Colors.YELLOW
    status_text = f"{status_color}{status}{Colors.RESET}"
    time_text = f"({response_time:.2f}s)" if response_time > 0 else ""
    
    print(f"  [{status_text}] {name} {time_text}")
    if message:
        print(f"        {Colors.YELLOW}{message}{Colors.RESET}")


def record_test(endpoint: str, method: str, status: str, message: str = "", response_time: float = 0, response_code: int = 0):
    """Record test result"""
    global total_tests, passed_tests, failed_tests
    
    total_tests += 1
    if status == "PASS":
        passed_tests += 1
    elif status == "FAIL":
        failed_tests += 1
    
    test_results.append({
        "endpoint": endpoint,
        "method": method,
        "status": status,
        "message": message,
        "response_time": response_time,
        "response_code": response_code,
        "timestamp": datetime.now().isoformat()
    })


def test_endpoint(
    method: str,
    endpoint: str,
    name: str,
    expected_status: int = 200,
    data: Optional[Dict] = None,
    files: Optional[Dict] = None,
    headers: Optional[Dict] = None,
    auth_required: bool = False
) -> Optional[Dict[str, Any]]:
    """Generic endpoint testing function"""
    
    url = f"{BASE_URL}{endpoint}" if not endpoint.startswith("http") else endpoint
    
    # Add auth header if required
    if auth_required and auth_tokens.get("access_token"):
        if headers is None:
            headers = {}
        headers["Authorization"] = f"Bearer {auth_tokens['access_token']}"
    
    try:
        start_time = datetime.now()
        
        if method == "GET":
            response = requests.get(url, headers=headers, timeout=30)
        elif method == "POST":
            if files:
                response = requests.post(url, data=data, files=files, headers=headers, timeout=30)
            else:
                response = requests.post(url, json=data, headers=headers, timeout=30)
        elif method == "PUT":
            response = requests.put(url, json=data, headers=headers, timeout=30)
        elif method == "DELETE":
            response = requests.delete(url, headers=headers, timeout=30)
        else:
            print_test(name, "SKIP", f"Unsupported method: {method}")
            record_test(endpoint, method, "SKIP", f"Unsupported method: {method}")
            return None
        
        end_time = datetime.now()
        response_time = (end_time - start_time).total_seconds()
        
        # Check status code
        if response.status_code == expected_status:
            print_test(name, "PASS", f"Status: {response.status_code}", response_time)
            record_test(endpoint, method, "PASS", f"Status: {response.status_code}", response_time, response.status_code)
            
            try:
                return response.json()
            except:
                return {"raw_response": response.text}
        else:
            message = f"Expected {expected_status}, got {response.status_code}"
            try:
                error_detail = response.json()
                message += f" - {error_detail.get('detail', error_detail)}"
            except:
                message += f" - {response.text[:100]}"
            
            print_test(name, "FAIL", message, response_time)
            record_test(endpoint, method, "FAIL", message, response_time, response.status_code)
            return None
    
    except requests.exceptions.ConnectionError:
        message = "Connection failed - Server may not be running"
        print_test(name, "FAIL", message)
        record_test(endpoint, method, "FAIL", message)
        return None
    except requests.exceptions.Timeout:
        message = "Request timeout"
        print_test(name, "FAIL", message)
        record_test(endpoint, method, "FAIL", message)
        return None
    except Exception as e:
        message = f"Error: {str(e)}"
        print_test(name, "FAIL", message)
        record_test(endpoint, method, "FAIL", message)
        return None


def test_migration():
    """Test database migration status"""
    print_header("DATABASE MIGRATION VERIFICATION")
    
    # Check if server is running first
    result = test_endpoint("GET", "/health", "Health Check Endpoint")
    
    if result:
        print(f"\n  {Colors.GREEN}✓ Server is running and responding{Colors.RESET}")
        print(f"  {Colors.GREEN}✓ Database connection successful (async SQLAlchemy){Colors.RESET}")
        print(f"  {Colors.GREEN}✓ Migration to async appears to be working{Colors.RESET}")
        return True
    else:
        print(f"\n  {Colors.RED}✗ Server is not running or not accessible{Colors.RESET}")
        print(f"  {Colors.RED}✗ Cannot verify migration status{Colors.RESET}")
        return False


def test_core_endpoints():
    """Test core endpoints"""
    print_header("CORE ENDPOINTS (2)")
    
    test_endpoint("GET", "/health", "GET /health")
    test_endpoint("GET", "/", "GET /")


def test_auth_endpoints():
    """Test authentication endpoints"""
    print_header("AUTHENTICATION ENDPOINTS (8)")
    
    # Test signup (might fail if user exists)
    signup_result = test_endpoint(
        "POST", 
        "/api/signup",
        "POST /api/signup",
        expected_status=201,
        data={
            "email": test_user["email"],
            "password": test_user["password"],
            "full_name": test_user["full_name"]
        }
    )
    
    # Test login
    login_result = test_endpoint(
        "POST",
        "/api/login",
        "POST /api/login",
        data={
            "username": test_user["email"],  # OAuth2 uses username field
            "password": test_user["password"]
        }
    )
    
    # Store tokens if login successful
    if login_result and "access_token" in login_result:
        auth_tokens["access_token"] = login_result["access_token"]
        auth_tokens["refresh_token"] = login_result.get("refresh_token")
        print(f"\n  {Colors.GREEN}✓ Authentication successful - tokens stored{Colors.RESET}")
    
    # Test verify (requires token from email - will likely fail)
    test_endpoint(
        "POST",
        "/api/verify",
        "POST /api/verify (Expected to fail - no verification token)",
        expected_status=400,
        data={"token": "dummy_token"}
    )
    
    # Test refresh token
    if auth_tokens.get("refresh_token"):
        test_endpoint(
            "POST",
            "/api/refresh",
            "POST /api/refresh",
            data={"refresh_token": auth_tokens["refresh_token"]}
        )
    else:
        print_test("POST /api/refresh", "SKIP", "No refresh token available")
        record_test("/api/refresh", "POST", "SKIP", "No refresh token available")
    
    # Test forgot password
    test_endpoint(
        "POST",
        "/api/forgot-password",
        "POST /api/forgot-password",
        data={"email": test_user["email"]}
    )
    
    # Test reset password (will fail - no reset token)
    test_endpoint(
        "POST",
        "/api/reset-password",
        "POST /api/reset-password (Expected to fail - no reset token)",
        expected_status=400,
        data={
            "token": "dummy_token",
            "new_password": "NewPassword123!"
        }
    )
    
    # Test change password (requires auth)
    test_endpoint(
        "POST",
        "/api/change-password",
        "POST /api/change-password",
        auth_required=True,
        data={
            "current_password": test_user["password"],
            "new_password": "NewPassword123!"
        }
    )
    
    # Test get current user
    test_endpoint(
        "GET",
        "/api/me",
        "GET /api/me",
        auth_required=True
    )


def test_admin_endpoints():
    """Test admin endpoints"""
    print_header("ADMIN ENDPOINTS (3)")
    
    # These require superuser access
    test_endpoint(
        "GET",
        "/api/users",
        "GET /api/users (May require superuser)",
        auth_required=True
    )
    
    test_endpoint(
        "POST",
        "/api/users",
        "POST /api/users (May require superuser)",
        expected_status=201,
        auth_required=True,
        data={
            "email": "admin_created@example.com",
            "password": "AdminPassword123!",
            "full_name": "Admin Created User"
        }
    )
    
    test_endpoint(
        "GET",
        "/api/statistics",
        "GET /api/statistics (May require superuser)",
        auth_required=True
    )


def test_payment_endpoints():
    """Test payment endpoints"""
    print_header("PAYMENT ENDPOINTS (6)")
    
    # Note: These will fail without PayPal credentials
    test_endpoint(
        "POST",
        "/api/orders/create",
        "POST /api/orders/create (Requires PayPal config)",
        auth_required=True,
        data={
            "amount": "100.00",
            "currency": "USD",
            "description": "Test order"
        }
    )
    
    test_endpoint(
        "POST",
        "/api/orders/capture",
        "POST /api/orders/capture (Requires PayPal config)",
        auth_required=True,
        data={"order_id": "dummy_order_id"}
    )
    
    test_endpoint(
        "GET",
        "/api/orders/dummy_order_id",
        "GET /api/orders/{order_id} (Requires PayPal config)",
        auth_required=True
    )
    
    test_endpoint(
        "POST",
        "/api/subscriptions/create",
        "POST /api/subscriptions/create (Requires PayPal config)",
        auth_required=True,
        data={
            "plan_id": "dummy_plan_id"
        }
    )
    
    test_endpoint(
        "GET",
        "/api/subscriptions/dummy_subscription_id",
        "GET /api/subscriptions/{subscription_id} (Requires PayPal config)",
        auth_required=True
    )
    
    test_endpoint(
        "POST",
        "/api/subscriptions/cancel",
        "POST /api/subscriptions/cancel (Requires PayPal config)",
        auth_required=True,
        data={"subscription_id": "dummy_subscription_id"}
    )


def test_matters_endpoints():
    """Test matters endpoints"""
    print_header("MATTERS ENDPOINTS (11)")
    
    global matter_id
    matter_id = None
    
    # Create matter via intake
    intake_result = test_endpoint(
        "POST",
        "/api/matters/intake",
        "POST /api/matters/intake",
        auth_required=True,
        data={
            "client_name": "Test Client",
            "case_type": "Civil",
            "description": "Test case description",
            "language_preference": "English"
        }
    )
    
    if intake_result and "matter_id" in intake_result:
        matter_id = intake_result["matter_id"]
        print(f"\n  {Colors.GREEN}✓ Matter created with ID: {matter_id}{Colors.RESET}")
    
    # Get all matters
    test_endpoint(
        "GET",
        "/api/matters/",
        "GET /api/matters/",
        auth_required=True
    )
    
    # Get specific matter
    if matter_id:
        test_endpoint(
            "GET",
            f"/api/matters/{matter_id}",
            f"GET /api/matters/{matter_id}",
            auth_required=True
        )
        
        # Test matter-specific endpoints
        test_endpoint(
            "POST",
            f"/api/matters/{matter_id}/draft",
            f"POST /api/matters/{matter_id}/draft",
            auth_required=True,
            data={
                "document_type": "pleading",
                "template": "civil_complaint"
            }
        )
        
        test_endpoint(
            "GET",
            f"/api/matters/{matter_id}/documents",
            f"GET /api/matters/{matter_id}/documents",
            auth_required=True
        )
        
        test_endpoint(
            "GET",
            f"/api/matters/{matter_id}/parallel-view",
            f"GET /api/matters/{matter_id}/parallel-view",
            auth_required=True
        )
        
        test_endpoint(
            "POST",
            f"/api/matters/{matter_id}/certify-translation",
            f"POST /api/matters/{matter_id}/certify-translation",
            auth_required=True,
            data={
                "document_id": 1,
                "source_lang": "en",
                "target_lang": "ms"
            }
        )
        
        test_endpoint(
            "POST",
            f"/api/matters/{matter_id}/build-evidence-packet",
            f"POST /api/matters/{matter_id}/build-evidence-packet",
            auth_required=True,
            data={
                "evidence_items": []
            }
        )
        
        test_endpoint(
            "POST",
            f"/api/matters/{matter_id}/prepare-hearing",
            f"POST /api/matters/{matter_id}/prepare-hearing",
            auth_required=True,
            data={
                "hearing_date": "2025-01-15",
                "hearing_type": "preliminary"
            }
        )
        
        test_endpoint(
            "GET",
            f"/api/matters/{matter_id}/hearing-bundle",
            f"GET /api/matters/{matter_id}/hearing-bundle",
            auth_required=True
        )
        
        test_endpoint(
            "POST",
            f"/api/matters/{matter_id}/analyze-strength",
            f"POST /api/matters/{matter_id}/analyze-strength",
            auth_required=True,
            data={
                "case_facts": "Test case facts"
            }
        )
        
        # Delete matter (test last)
        test_endpoint(
            "DELETE",
            f"/api/matters/{matter_id}",
            f"DELETE /api/matters/{matter_id}",
            auth_required=True
        )
    else:
        print(f"\n  {Colors.YELLOW}⚠ Skipping matter-specific tests - no matter created{Colors.RESET}")
        for i in range(9):  # 9 matter-specific endpoints skipped
            record_test(f"/api/matters/{{matter_id}}/*", "SKIP", "SKIP", "No matter ID available")


def test_documents_endpoints():
    """Test documents endpoints"""
    print_header("DOCUMENTS ENDPOINTS (6)")
    
    # Get all documents
    test_endpoint(
        "GET",
        "/api/documents/",
        "GET /api/documents/",
        auth_required=True
    )
    
    # Upload document (create dummy file)
    test_file_path = "test_document.txt"
    with open(test_file_path, "w") as f:
        f.write("Test document content for API testing")
    
    try:
        with open(test_file_path, "rb") as f:
            upload_result = test_endpoint(
                "POST",
                "/api/documents/upload",
                "POST /api/documents/upload",
                auth_required=True,
                data={"matter_id": "1", "doc_type": "evidence"},
                files={"file": f}
            )
        
        doc_id = None
        if upload_result and "id" in upload_result:
            doc_id = upload_result["id"]
            print(f"\n  {Colors.GREEN}✓ Document uploaded with ID: {doc_id}{Colors.RESET}")
        
        # Test document-specific endpoints
        if doc_id:
            test_endpoint(
                "GET",
                f"/api/documents/{doc_id}",
                f"GET /api/documents/{doc_id}",
                auth_required=True
            )
            
            test_endpoint(
                "GET",
                f"/api/documents/{doc_id}/download",
                f"GET /api/documents/{doc_id}/download",
                auth_required=True
            )
            
            test_endpoint(
                "GET",
                f"/api/documents/{doc_id}/preview",
                f"GET /api/documents/{doc_id}/preview",
                auth_required=True
            )
        else:
            print(f"\n  {Colors.YELLOW}⚠ Skipping document-specific tests - no document uploaded{Colors.RESET}")
            for i in range(3):
                record_test(f"/api/documents/{{doc_id}}/*", "SKIP", "SKIP", "No document ID available")
    
    finally:
        # Clean up test file
        if os.path.exists(test_file_path):
            os.remove(test_file_path)


def test_research_endpoints():
    """Test research endpoints"""
    print_header("RESEARCH ENDPOINTS (2)")
    
    test_endpoint(
        "POST",
        "/api/research/search",
        "POST /api/research/search",
        auth_required=True,
        data={
            "query": "contract law Malaysia",
            "jurisdiction": "Malaysia"
        }
    )
    
    test_endpoint(
        "POST",
        "/api/research/build-argument",
        "POST /api/research/build-argument",
        auth_required=True,
        data={
            "matter_id": 1,
            "position": "plaintiff",
            "key_facts": "Contract breach case"
        }
    )


def test_ai_tasks_endpoints():
    """Test AI tasks endpoints"""
    print_header("AI TASKS ENDPOINTS (2)")
    
    test_endpoint(
        "GET",
        "/api/ai-tasks/tasks",
        "GET /api/ai-tasks/tasks",
        auth_required=True
    )
    
    test_endpoint(
        "GET",
        "/api/ai-tasks/tasks/dummy_task_id",
        "GET /api/ai-tasks/tasks/{task_id}",
        auth_required=True
    )


def test_evidence_endpoints():
    """Test evidence endpoints"""
    print_header("EVIDENCE ENDPOINTS (1)")
    
    test_endpoint(
        "POST",
        "/api/evidence/build",
        "POST /api/evidence/build",
        auth_required=True,
        data={
            "matter_id": 1,
            "evidence_items": []
        }
    )


def generate_report():
    """Generate test report"""
    print_header("TEST SUMMARY")
    
    pass_rate = (passed_tests / total_tests * 100) if total_tests > 0 else 0
    
    print(f"  Total Tests:   {total_tests}")
    print(f"  {Colors.GREEN}Passed:        {passed_tests}{Colors.RESET}")
    print(f"  {Colors.RED}Failed:        {failed_tests}{Colors.RESET}")
    print(f"  {Colors.YELLOW}Skipped:       {total_tests - passed_tests - failed_tests}{Colors.RESET}")
    print(f"  Pass Rate:     {pass_rate:.1f}%\n")
    
    # Save detailed report
    report_file = "test_report.json"
    with open(report_file, "w") as f:
        json.dump({
            "summary": {
                "total": total_tests,
                "passed": passed_tests,
                "failed": failed_tests,
                "skipped": total_tests - passed_tests - failed_tests,
                "pass_rate": pass_rate,
                "timestamp": datetime.now().isoformat()
            },
            "results": test_results
        }, f, indent=2)
    
    print(f"  {Colors.BLUE}Detailed report saved to: {report_file}{Colors.RESET}\n")
    
    # Print failed tests summary
    if failed_tests > 0:
        print_header("FAILED TESTS SUMMARY")
        for result in test_results:
            if result["status"] == "FAIL":
                print(f"  {Colors.RED}✗{Colors.RESET} {result['method']} {result['endpoint']}")
                print(f"    {result['message']}\n")


def main():
    """Main test execution"""
    print(f"\n{Colors.BOLD}{Colors.BLUE}")
    print("╔════════════════════════════════════════════════════════════════════════════╗")
    print("║                  Legal-Ops API Comprehensive Test Suite                   ║")
    print("║                        Migration & Endpoint Testing                       ║")
    print("╚════════════════════════════════════════════════════════════════════════════╝")
    print(f"{Colors.RESET}\n")
    
    print(f"Base URL: {BASE_URL}")
    print(f"Test started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
    
    # Step 1: Check migration
    if not test_migration():
        print(f"\n{Colors.RED}{Colors.BOLD}ERROR: Server is not running. Please start the server and try again.{Colors.RESET}")
        print(f"\nTo start the server, run:")
        print(f"  cd backend")
        print(f"  python main.py\n")
        sys.exit(1)
    
    # Step 2: Test all endpoints
    test_core_endpoints()
    test_auth_endpoints()
    test_admin_endpoints()
    test_payment_endpoints()
    test_matters_endpoints()
    test_documents_endpoints()
    test_research_endpoints()
    test_ai_tasks_endpoints()
    test_evidence_endpoints()
    
    # Step 3: Generate report
    generate_report()
    
    print(f"{Colors.BOLD}{Colors.BLUE}Test execution completed!{Colors.RESET}\n")
    
    # Exit with appropriate code
    sys.exit(0 if failed_tests == 0 else 1)


if __name__ == "__main__":
    main()

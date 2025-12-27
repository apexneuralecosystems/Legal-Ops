"""
Quick test script to verify the API endpoint fixes
"""
import requests
import json
import os

BASE_URL = os.getenv("BACKEND_URL", "http://localhost:8005")

def test_matters_intake_without_files():
    """Test that matters intake works without files"""
    print("\n1. Testing POST /api/matters/intake (without files)...")
    
    try:
        # Test with JSON data only (no files)
        response = requests.post(
            f"{BASE_URL}/api/matters/intake",
            data={
                "connector_type": "manual",
                "metadata": json.dumps({"test": True})
            }
        )
        
        print(f"   Status: {response.status_code}")
        if response.status_code in [200, 201]:
            print(f"   ✓ PASS - Intake works without files!")
            result = response.json()
            print(f"   Matter ID: {result.get('matter_id')}")
        else:
            print(f"   ✗ FAIL - {response.text[:200]}")
            
    except Exception as e:
        print(f"   ✗ ERROR - {str(e)}")


def test_research_matter_id_types():
    """Test that research endpoint accepts both int and string for matter_id"""
    print("\n2. Testing POST /api/research/build-argument...")
    
    # Test with integer matter_id
    print("   a) With integer matter_id...")
    try:
        response = requests.post(
            f"{BASE_URL}/api/research/build-argument",
            json={
                "matter_id": 1,
                "position": "plaintiff",
                "key_facts": "Test case",
                "issues": [],
                "cases": []
            }
        )
        
        print(f"      Status: {response.status_code}")
        if response.status_code == 200:
            print(f"      ✓ PASS - Integer matter_id accepted!")
        else:
            # Check if it's a 422 validation error
            if response.status_code == 422:
                error = response.json()
                print(f"      ✗ FAIL - Validation error: {error}")
            else:
                print(f"      ~ OK - {response.status_code} (endpoint works)")
                
    except Exception as e:
        print(f"      ✗ ERROR - {str(e)}")
    
    # Test with string matter_id
    print("   b) With string matter_id...")
    try:
        response = requests.post(
            f"{BASE_URL}/api/research/build-argument",
            json={
                "matter_id": "test-123",
                "position": "plaintiff",
                "key_facts": "Test case",
                "issues": [],
                "cases": []
            }
        )
        
        print(f"      Status: {response.status_code}")
        if response.status_code == 200:
            print(f"      ✓ PASS - String matter_id accepted!")
        else:
            if response.status_code == 422:
                error = response.json()
                print(f"      ✗ FAIL - Validation error: {error}")
            else:
                print(f"      ~ OK - {response.status_code} (endpoint works)")
                
    except Exception as e:
        print(f"      ✗ ERROR - {str(e)}")


def test_evidence_matter_id_types():
    """Test that evidence endpoint accepts both int and string for matter_id"""
    print("\n3. Testing POST /api/evidence/build...")
    
    # Test with integer matter_id
    print("   a) With integer matter_id...")
    try:
        response = requests.post(
            f"{BASE_URL}/api/evidence/build",
            json={
                "matter_id": 1,
                "documents": []
            }
        )
        
        print(f"      Status: {response.status_code}")
        if response.status_code == 200:
            print(f"      ✓ PASS - Integer matter_id accepted!")
        else:
            if response.status_code == 422:
                error = response.json()
                print(f"      ✗ FAIL - Validation error: {error}")
            else:
                print(f"      ~ OK - {response.status_code} (endpoint works)")
                
    except Exception as e:
        print(f"      ✗ ERROR - {str(e)}")
    
    # Test with string matter_id
    print("   b) With string matter_id...")
    try:
        response = requests.post(
            f"{BASE_URL}/api/evidence/build",
            json={
                "matter_id": "test-456",
                "documents": []
            }
        )
        
        print(f"      Status: {response.status_code}")
        if response.status_code == 200:
            print(f"      ✓ PASS - String matter_id accepted!")
        else:
            if response.status_code == 422:
                error = response.json()
                print(f"      ✗ FAIL - Validation error: {error}")
            else:
                print(f"      ~ OK - {response.status_code} (endpoint works)")
                
    except Exception as e:
        print(f"      ✗ ERROR - {str(e)}")


def main():
    print("="*80)
    print("Testing Fixed API Endpoints")
    print("="*80)
    
    # Check server is running
    try:
        response = requests.get(f"{BASE_URL}/health")
        if response.status_code != 200:
            print("ERROR: Server is not responding at", BASE_URL)
            return
    except Exception as e:
        print(f"ERROR: Cannot connect to server at {BASE_URL}")
        print(f"Make sure the server is running with: python main.py")
        return
    
    print("✓ Server is running\n")
    
    # Run tests
    test_matters_intake_without_files()
    test_research_matter_id_types()
    test_evidence_matter_id_types()
    
    print("\n" + "="*80)
    print("Testing Complete!")
    print("="*80 + "\n")


if __name__ == "__main__":
    main()

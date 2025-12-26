"""
Debug Apex Client Initialization
"""
import sys
import logging
from database import get_apex_client, set_apex_client
from config import settings
from models.auth import User

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

def test_init():
    print("Testing Apex Client Initialization...")
    
    # Test 1: Try to create client directly
    print("\n[Test 1] Direct Creation:")
    try:
        from apex import Client
        print(f"DATABASE_URL: {settings.DATABASE_URL}")
        client = Client(
            database_url=settings.DATABASE_URL,
            user_model=User,
            async_mode=True
        )
        print("✓ Client created successfully")
    except Exception as e:
        print(f"✗ Client creation failed: {e}")
        import traceback
        traceback.print_exc()

    # Test 2: Try database.py helper
    print("\n[Test 2] Database Helper:")
    client = get_apex_client()
    if client:
        print("✓ get_apex_client() returned client")
    else:
        print("✗ get_apex_client() returned None")

if __name__ == "__main__":
    test_init()

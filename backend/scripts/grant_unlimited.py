
import sys
import os
from datetime import datetime

# Add parent directory to path to allow importing from backend modules
# This assumes the script is run from backend/ or backend/scripts/
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.append(parent_dir)

try:
    from database import SessionLocal
    from models.auth import User
    from models.usage import UserUsage
except ImportError as e:
    print(f"Import Error: {e}")
    print("Please run this script from the 'backend' directory using: python -m scripts.grant_unlimited")
    sys.exit(1)

def grant_unlimited_access(email: str):
    print(f"Attempting to grant unlimited access to: {email}")
    db = SessionLocal()
    try:
        # Find user
        user = db.query(User).filter(User.email == email).first()
        if not user:
            print(f"❌ User with email '{email}' not found in database.")
            return

        print(f"✅ Found user: {user.email} (ID: {user.id})")

        # Find or create usage record
        usage = db.query(UserUsage).filter(UserUsage.user_id == user.id).first()
        if not usage:
            print("⚠️ UserUsage record not found. Creating new record...")
            usage = UserUsage(user_id=user.id)
            db.add(usage)
        else:
            print(f"Found existing usage record.")

        # Grant unlimited rights
        usage.has_paid = True
        usage.subscription_status = 'active'
        usage.subscription_id = 'manual_admin_grant_production'
        usage.payment_date = datetime.utcnow()
        
        db.commit()
        print(f"🎉 SUCCESS! Granted unlimited access to {email}.")
        print("The user can now use all workflows without limits.")
        
    except Exception as e:
        print(f"❌ Error occurred: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    target_email = "anmita132@gmail.com"
    
    # Allow command line override
    if len(sys.argv) > 1:
        target_email = sys.argv[1]
        
    grant_unlimited_access(target_email)

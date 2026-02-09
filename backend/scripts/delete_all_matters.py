import sys
import os

# Ensure we can import from the backend directory
# Assume this script is run from the 'backend' directory
sys.path.append(os.getcwd())

from database import SessionLocal
from models import Matter, Document, Pleading

def delete_all_matters():
    db = SessionLocal()
    try:
        print("Starting cleanup...")
        
        # Delete Pleadings
        count_p = db.query(Pleading).delete()
        print(f"Deleted {count_p} Pleadings.")
        
        # Delete Documents
        count_d = db.query(Document).delete()
        print(f"Deleted {count_d} Documents.")
        
        # Delete Matters
        count_m = db.query(Matter).delete()
        print(f"Deleted {count_m} Matters.")
        
        db.commit()
        print("Commit successful. All specified data deleted.")
        
    except Exception as e:
        print(f"Error during deletion: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    delete_all_matters()

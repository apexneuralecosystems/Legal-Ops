"""
Script to clear all matters and associated data from the database.
"""
import sys
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent))

from database import SessionLocal
from models import Matter, Document, Segment, Pleading

def clear_all_matters():
    """Delete all matters and associated data."""
    db = SessionLocal()
    try:
        # Delete in reverse dependency order
        deleted_counts = {}
        
        # Delete pleadings first
        pleadings_deleted = db.query(Pleading).delete()
        deleted_counts['pleadings'] = pleadings_deleted
        
        # Delete segments
        segments_deleted = db.query(Segment).delete()
        deleted_counts['segments'] = segments_deleted
        
        # Delete documents
        documents_deleted = db.query(Document).delete()
        deleted_counts['documents'] = documents_deleted
        
        # Delete matters
        matters_deleted = db.query(Matter).delete()
        deleted_counts['matters'] = matters_deleted
        
        # Commit the changes
        db.commit()
        
        print("✅ Successfully cleared database:")
        print(f"   - Matters: {deleted_counts['matters']}")
        print(f"   - Documents: {deleted_counts['documents']}")
        print(f"   - Segments: {deleted_counts['segments']}")
        print(f"   - Pleadings: {deleted_counts['pleadings']}")
        
        return deleted_counts
        
    except Exception as e:
        db.rollback()
        print(f"❌ Error clearing database: {e}")
        raise
    finally:
        db.close()

if __name__ == "__main__":
    clear_all_matters()

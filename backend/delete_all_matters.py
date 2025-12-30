
from database import SessionLocal, engine
from models import Matter, Document, Pleading, Segment
from sqlalchemy import text
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def delete_all_matters():
    db = SessionLocal()
    try:
        logger.info("Starting cleanup of all matters...")
        
        # Delete in order of dependencies (child first, then parent)
        
        # 1. Delete Segments (depend on Documents)
        num_segments = db.query(Segment).delete()
        logger.info(f"Deleted {num_segments} segments")
        
        # 2. Delete Pleadings (depend on Matters)
        num_pleadings = db.query(Pleading).delete()
        logger.info(f"Deleted {num_pleadings} pleadings")
        
        # 3. Delete Documents (depend on Matters)
        num_documents = db.query(Document).delete()
        logger.info(f"Deleted {num_documents} documents")
        
        # 4. Delete Matters
        num_matters = db.query(Matter).delete()
        logger.info(f"Deleted {num_matters} matters")
        
        db.commit()
        logger.info("Successfully deleted all matters and related data.")
        
    except Exception as e:
        logger.error(f"Error deleting matters: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    delete_all_matters()

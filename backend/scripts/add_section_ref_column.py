
import sys
import os
from sqlalchemy import create_engine, text

# Add backend to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from config import settings

def migrate():
    print(f"Connecting to database: {settings.DATABASE_URL}")
    engine = create_engine(settings.DATABASE_URL)
    
    with engine.connect() as conn:
        try:
            print("Checking if column 'section_ref' exists in 'segments' table...")
            # Simple check by trying to select it (postgres specific info schema is better but this works cross-db usually)
            try:
                conn.execute(text("SELECT section_ref FROM segments LIMIT 1"))
                print("Column 'section_ref' already exists.")
            except Exception:
                print("Column 'section_ref' missing. Adding it...")
                conn.rollback() # Reset transaction after failed SELECT
                conn.execute(text("ALTER TABLE segments ADD COLUMN section_ref TEXT"))
                conn.commit()
                print("Successfully added 'section_ref' column.")
                
        except Exception as e:
            print(f"Migration failed: {e}")

if __name__ == "__main__":
    migrate()

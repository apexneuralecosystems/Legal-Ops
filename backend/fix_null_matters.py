"""
Fix existing matters with null or placeholder court/jurisdiction fields.
"""
import sys
sys.path.insert(0, '.')

from database import SessionLocal
from models import Matter

def fix_matters():
    db = SessionLocal()
    try:
        # Find ALL matters
        matters = db.query(Matter).all()
        
        print(f"Found {len(matters)} total matters")
        
        for matter in matters:
            changes = []
            print(f"\nMatter {matter.id}: {matter.title}")
            print(f"  Court: {repr(matter.court)}")
            print(f"  Jurisdiction: {repr(matter.jurisdiction)}")
            
            # Fix null or empty court
            if not matter.court or matter.court.strip() == "" or matter.court == "Not specified":
                matter.court = "High Court (to be specified)"
                changes.append("court")
            
            # Fix null or empty jurisdiction
            if not matter.jurisdiction or matter.jurisdiction.strip() == "" or matter.jurisdiction == "Not Specified":
                matter.jurisdiction = "Peninsular Malaysia"
                changes.append("jurisdiction")
            
            if matter.estimated_pages is None or matter.estimated_pages == 0:
                matter.estimated_pages = 1
                changes.append("estimated_pages")
            
            if matter.jurisdictional_complexity is None:
                matter.jurisdictional_complexity = 1
                changes.append("jurisdictional_complexity")
            if matter.language_complexity is None:
                matter.language_complexity = 1
                changes.append("language_complexity")
            if matter.volume_risk is None:
                matter.volume_risk = 1
                changes.append("volume_risk")
            if matter.time_pressure is None:
                matter.time_pressure = 2
                changes.append("time_pressure")
            if matter.composite_score is None:
                matter.composite_score = 1.3
                changes.append("composite_score")
            if matter.title == "New Matter - Processing":
                matter.title = "New Matter"
                changes.append("title")
            
            if changes:
                print(f"  -> Fixed: {', '.join(changes)}")
        
        db.commit()
        print("\nDone!")
        
    finally:
        db.close()

if __name__ == "__main__":
    fix_matters()

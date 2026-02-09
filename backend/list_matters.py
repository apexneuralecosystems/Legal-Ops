"""Debug script to list all matters and users."""
import sys
sys.path.insert(0, '.')

from database import SessionLocal
from models import Matter

db = SessionLocal()

print("=== ALL MATTERS IN DATABASE ===")
matters = db.query(Matter).all()
print(f"Total: {len(matters)}")

for m in matters:
    print(f"\nMatter ID: {m.id}")
    print(f"  Title: {m.title}")
    print(f"  Status: {m.status}")
    print(f"  Created By: {m.created_by}")
    
db.close()
print("\n=== END ===")

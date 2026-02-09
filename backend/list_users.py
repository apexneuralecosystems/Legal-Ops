"""Debug script to list users using sync connection."""
import sys
sys.path.insert(0, '.')

from database import SessionLocal
from sqlalchemy import text

db = SessionLocal()

print("=== USERS IN DATABASE ===")
try:
    result = db.execute(text("SELECT id, email FROM users"))
    users = result.fetchall()
    print(f"Total users: {len(users)}")
    for u in users:
        print(f"  ID: {u[0]}")
        print(f"  Email: {u[1]}")
        print()
except Exception as e:
    print(f"Error querying users: {e}")
    
print("\n=== MATTERS WITH CREATED_BY ===")
result2 = db.execute(text("SELECT id, title, status, created_by FROM matters"))
matters = result2.fetchall()
for m in matters:
    print(f"  Matter: {m[0]}")
    print(f"  Title: {m[1]}")
    print(f"  Status: {m[2]}")
    print(f"  Created By: {m[3]}")
    print()

db.close()

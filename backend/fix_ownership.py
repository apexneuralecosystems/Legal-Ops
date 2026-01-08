from database import get_sync_db
from models import User, Matter

db = next(get_sync_db())

# 1. Get an existing hash to reuse (avoiding import hell)
existing_user = db.query(User).first()
if not existing_user:
    print("No users found to copy hash from! Aborting.")
    exit(1)

# Correct attribute name: password_hash
known_hash = existing_user.password_hash
print(f"Using hash from user {existing_user.email}")

# 2. Get or Create Lead User (lawyer@firm.com)
email = "lawyer@firm.com"
user = db.query(User).filter(User.email == email).first()

if not user:
    print(f"User {email} not found. Creating...")
    user = User(
        email=email,
        password_hash=known_hash, # Correct attribute
        full_name="Lead Lawyer",
        is_active=True
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    print(f"Created user {user.id}")
else:
    print(f"Found user {user.id}")

# 3. Update All Matters to belong to this user
matters = db.query(Matter).all()
count = 0
for m in matters:
    if m.created_by != user.id:
        m.created_by = user.id
        count += 1

if count > 0:
    db.commit()
    print(f"Updated {count} matters to belong to {email}")
else:
    print("All matters already belong to user.")

"""
Script to reset lawyer@firm.com password to 'password' using proper hash.
"""
from database import get_sync_db
from models import User
from apex.auth import hash_password

db = next(get_sync_db())

email = "lawyer@firm.com"
new_password = "password"

user = db.query(User).filter(User.email == email).first()

if user:
    print(f"Found user: {user.id}")
    user.password_hash = hash_password(new_password)
    db.commit()
    print(f"Password reset to '{new_password}' for {email}")
else:
    print(f"User {email} not found!")

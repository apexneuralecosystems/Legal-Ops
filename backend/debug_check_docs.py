
from database import SessionLocal
from models import Document, Matter
import sys

def check_docs(matter_id):
    db = SessionLocal()
    try:
        print(f"Checking matter: {matter_id}")
        matter = db.query(Matter).filter(Matter.id == matter_id).first()
        if not matter:
            print("Matter NOT found!")
        else:
            print(f"Matter found: {matter.title}")
            
        docs = db.query(Document).filter(Document.matter_id == matter_id).all()
        print(f"Documents found: {len(docs)}")
        for d in docs:
            print(f" - {d.id}: {d.filename} (Hash: {d.file_hash})")
            
    except Exception as e:
        print(f"Error: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    check_docs("MAT-20260107-e4534573")

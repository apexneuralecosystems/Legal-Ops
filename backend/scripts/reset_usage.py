import asyncio
import sys
import os

# Add parent directory to path to import backend modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database import AsyncSessionLocal
from models.usage import UserUsage
from sqlalchemy import select

async def reset_usage():
    async with AsyncSessionLocal() as session:
        print("Connecting to database...")
        result = await session.execute(select(UserUsage))
        usages = result.scalars().all()
        
        if not usages:
            print("No usage records found.")
            return

        print(f"Found {len(usages)} usage records.")
        for usage in usages:
            print(f"Resetting usage for user {usage.user_id}")
            usage.intake_count = 0
            usage.drafting_count = 0
            usage.evidence_count = 0
            usage.research_count = 0
            # usage.has_paid = True # Optional: upgrade to premium
        
        await session.commit()
        print("Usage reset successfully.")

if __name__ == "__main__":
    asyncio.run(reset_usage())

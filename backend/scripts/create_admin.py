"""
Create an admin user.

Usage (from project root):
    docker exec projectflow-backend-1 python scripts/create_admin.py
    docker exec projectflow-backend-1 python scripts/create_admin.py --username admin --password secret --email admin@example.com
"""

import asyncio
import argparse
import sys
import os

# Make sure app package is importable when run inside the container
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from sqlalchemy import select
from app.database import AsyncSessionLocal
from app.models.user import User
from app.core.security import hash_password


async def create_admin(username: str, password: str, email: str) -> None:
    async with AsyncSessionLocal() as db:
        existing = await db.execute(select(User).where(User.username == username))
        if existing.scalar_one_or_none():
            print(f"User '{username}' already exists — skipping.")
            return

        user = User(
            username=username,
            email=email,
            hashed_password=hash_password(password),
            is_active=True,
            is_admin=True,
        )
        db.add(user)
        await db.commit()
        await db.refresh(user)
        print(f"Created admin user: {user.username} <{user.email}>")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Create an admin user")
    parser.add_argument("--username", default="admin")
    parser.add_argument("--password", default="admin123")
    parser.add_argument("--email",    default="admin@example.com")
    args = parser.parse_args()

    asyncio.run(create_admin(args.username, args.password, args.email))

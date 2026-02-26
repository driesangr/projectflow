"""
scripts/create_admin.py
=======================

Creates the first privileged user (superuser or admin) from the command line.

Usage
-----
    # From the backend directory:
    python -m scripts.create_admin

Environment variables (or .env file):
    ADMIN_USERNAME   (default: admin)
    ADMIN_EMAIL      (default: admin@example.com)
    ADMIN_PASSWORD   (required – no default)
    ADMIN_ROLE       superuser | admin  (default: superuser)
"""

import asyncio
import os
import sys

from sqlalchemy import select

# Make sure the app package is on the path when running as a script
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.security import hash_password
from app.database import AsyncSessionLocal
from app.models.user import GlobalRole, User


async def main() -> None:
    username = os.getenv("ADMIN_USERNAME", "admin")
    email    = os.getenv("ADMIN_EMAIL",    "admin@example.com")
    password = os.getenv("ADMIN_PASSWORD", "")
    role_str = os.getenv("ADMIN_ROLE",     "superuser")

    if not password:
        print("ERROR: ADMIN_PASSWORD environment variable is required.", file=sys.stderr)
        sys.exit(1)

    try:
        role = GlobalRole(role_str)
    except ValueError:
        print(f"ERROR: Unknown ADMIN_ROLE '{role_str}'. Use 'superuser' or 'admin'.", file=sys.stderr)
        sys.exit(1)

    async with AsyncSessionLocal() as db:
        existing = await db.execute(
            select(User).where(User.username == username, User.is_deleted.is_(False))
        )
        user = existing.scalar_one_or_none()

        if user:
            # Update role if already exists
            user.global_role = role
            user.is_admin    = True
            user.is_active   = True
            await db.commit()
            print(f"✓ Updated existing user '{username}' → role={role.value}")
        else:
            user = User(
                username=username,
                email=email,
                hashed_password=hash_password(password),
                global_role=role,
                is_admin=True,
                is_active=True,
                full_name="System Administrator",
            )
            db.add(user)
            await db.commit()
            print(f"✓ Created {role.value} user '{username}' ({email})")


if __name__ == "__main__":
    asyncio.run(main())

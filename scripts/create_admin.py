import asyncio
import getpass

from tortoise import Tortoise

from app.models.admin import User
from app.settings import settings
from app.utils.password import get_password_hash


async def create_admin() -> None:
    await Tortoise.init(config=settings.TORTOISE_ORM)
    try:
        username = input("Admin username: ").strip()
        email = input("Admin email (optional): ").strip() or None
        if not username or await User.filter(username=username).exists():
            raise ValueError("Username is empty or already exists")
        password = getpass.getpass("Password (at least 12 characters): ")
        if len(password) < 12 or password != getpass.getpass("Confirm password: "):
            raise ValueError("Password is too short or confirmation does not match")
        await User.create(
            username=username,
            email=email,
            password=get_password_hash(password),
            is_active=True,
            is_superuser=True,
        )
        print(f"Created administrator: {username}")
    finally:
        await Tortoise.close_connections()


if __name__ == "__main__":
    asyncio.run(create_admin())

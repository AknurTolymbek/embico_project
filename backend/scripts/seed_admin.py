"""Create the first administrator only from explicitly configured credentials."""
import asyncio
from sqlalchemy import select

from app.core.config import settings
from app.core.security import get_password_hash
from app.db.database import AsyncSessionLocal
from app.models import User, UserRole
from app.modules.users.schemas import UserCreate
from app.modules.users.service import create_user, find_by_login


async def seed_admin() -> None:
    async with AsyncSessionLocal() as db:
        if (await db.execute(select(User.id).where(User.role == UserRole.ADMIN, User.is_active.is_(True)).limit(1))).scalar_one_or_none():
            print('Администратор уже настроен.')
            return
        if not settings.FIRST_SUPERUSER_PASSWORD:
            print('Администратор не создан: задайте FIRST_SUPERUSER_PASSWORD в корневом .env.')
            return
        values = UserCreate(username=settings.FIRST_SUPERUSER_LOGIN,
                            password=settings.FIRST_SUPERUSER_PASSWORD,
                            first_name=settings.FIRST_SUPERUSER_FIRST_NAME,
                            last_name=settings.FIRST_SUPERUSER_LAST_NAME,
                            email=settings.FIRST_SUPERUSER_EMAIL, role=UserRole.ADMIN)
        # An old account may already own the configured bootstrap email.
        existing = await find_by_login(db, values.username)
        if not existing and values.email:
            existing = await find_by_login(db, values.email)
        if existing:
            existing.username = values.username
            existing.first_name = values.first_name
            existing.last_name = values.last_name
            existing.full_name = f'{values.first_name} {values.last_name}'
            existing.hashed_password = get_password_hash(values.password)
            existing.role = UserRole.ADMIN
            existing.is_active = True
        else:
            await create_user(db, values)
        await db.commit()
        print('Первый администратор создан. Пароль в лог не выводится.')


if __name__ == '__main__':
    asyncio.run(seed_admin())

"""Create the first administrator or sync its password from explicitly configured credentials."""
import asyncio

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.security import get_password_hash, verify_password
from app.db.database import AsyncSessionLocal
from app.models import UserRole
from app.modules.users.schemas import UserCreate
from app.modules.users.service import create_user, find_by_login


async def seed_admin(db: AsyncSession | None = None) -> None:
    if db is None:
        async with AsyncSessionLocal() as session:
            return await seed_admin(session)
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
        existing.role = UserRole.ADMIN
        existing.is_active = True
        password_changed = not verify_password(values.password, existing.hashed_password)
        if password_changed:
            existing.hashed_password = get_password_hash(values.password)
        await db.commit()
        print('Администратор: пароль обновлён.' if password_changed else 'Администратор: без изменений.')
    else:
        await create_user(db, values)
        await db.commit()
        print('Администратор создан.')


if __name__ == '__main__':
    asyncio.run(seed_admin())

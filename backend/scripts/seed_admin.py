"""
Скрипт для создания администратора (тестовая учётная запись).

Создаёт пользователя admin@a.a с паролем admin123.
Если пользователь уже существует — ничего не делает (идемпотентно).

Запуск (из папки backend):
    python -m scripts.seed_admin
"""
import asyncio

from sqlalchemy import select

from app.core.security import get_password_hash
from app.db.database import AsyncSessionLocal
from app.models import User  # noqa: F401 — импорт пакета регистрирует все модели
from app.models.enums import UserRole

ADMIN_EMAIL = "admin@embico.kz"
ADMIN_PASSWORD = "admin123"
ADMIN_FULL_NAME = "Администратор"


async def seed_admin() -> None:
    async with AsyncSessionLocal() as db:
        result = await db.execute(select(User).where(User.email == ADMIN_EMAIL))
        existing = result.scalar_one_or_none()

        if existing:
            print(f"Пользователь {ADMIN_EMAIL} уже существует (id={existing.id}), пропускаем.")
            return

        admin = User(
            email=ADMIN_EMAIL,
            hashed_password=get_password_hash(ADMIN_PASSWORD),
            # Отдельной роли admin пока нет — используем репродуктолога
            role=UserRole.REPRODUCTOLOGIST,
            full_name=ADMIN_FULL_NAME,
            is_active=True,
        )
        db.add(admin)
        await db.commit()
        await db.refresh(admin)

        print(f"✓ Создан пользователь {ADMIN_EMAIL} (id={admin.id})")
        print(f"  Email: {ADMIN_EMAIL} | Пароль: {ADMIN_PASSWORD}")


if __name__ == "__main__":
    asyncio.run(seed_admin())

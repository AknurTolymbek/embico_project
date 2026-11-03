"""
Базовые миксины для моделей SQLAlchemy.
Общие поля для всех моделей: timestamps, soft delete.
"""
from datetime import datetime, timezone

from sqlalchemy import DateTime, func
from sqlalchemy.orm import Mapped, mapped_column


class TimestampMixin:
    """
    Миксин для автоматического добавления created_at и updated_at.
    Используется во всех моделях для отслеживания времени создания/изменения.
    """
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )


class SoftDeleteMixin:
    """
    Миксин для soft delete (мягкое удаление).
    Вместо физического удаления записей помечаем их как удалённые.
    Важно для медицинских данных - ничего не удаляем физически.
    """
    is_deleted: Mapped[bool] = mapped_column(
        nullable=False,
        default=False,
        server_default="false",
    )
    deleted_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
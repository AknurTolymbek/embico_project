"""
Модель пользователя (User).
Пользователи системы: репродуктологи и эмбриологи.
"""
from typing import TYPE_CHECKING

from sqlalchemy import String, Enum as SQLEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.database import Base
from app.models.base import TimestampMixin
from app.models.enums import UserRole

if TYPE_CHECKING:
    from app.models.cycle import Cycle


class User(Base, TimestampMixin):
    """
    Пользователь системы EMBICO.
    Может быть репродуктологом или эмбриологом.
    """
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[UserRole] = mapped_column(SQLEnum(UserRole, values_callable=lambda e: [m.value for m in e]), nullable=False)
    full_name: Mapped[str] = mapped_column(String(255), nullable=False)
    is_active: Mapped[bool] = mapped_column(default=True, server_default="true", nullable=False)

    # Relationships
    # Циклы, где этот пользователь назначен как врач
    cycles_as_doctor: Mapped[list["Cycle"]] = relationship(
        "Cycle",
        foreign_keys="Cycle.assigned_doctor_id",
        back_populates="assigned_doctor",
    )

    # Циклы, где этот пользователь назначен как эмбриолог
    cycles_as_embryologist: Mapped[list["Cycle"]] = relationship(
        "Cycle",
        foreign_keys="Cycle.assigned_embryologist_id",
        back_populates="assigned_embryologist",
    )

    def __repr__(self) -> str:
        return f"<User(id={self.id}, email='{self.email}', role='{self.role}')>"
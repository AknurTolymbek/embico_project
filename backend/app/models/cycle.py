"""
Модель цикла ЭКО (Cycle).
Клинический цикл пациентки: от подготовки до исхода.
"""
from datetime import date
from typing import TYPE_CHECKING

from sqlalchemy import String, Date, ForeignKey, Text, Enum as SQLEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.database import Base
from app.models.base import TimestampMixin, SoftDeleteMixin
from app.models.enums import CycleStatus, CycleStage

if TYPE_CHECKING:
    from app.models.patient import Patient
    from app.models.user import User


class Cycle(Base, TimestampMixin, SoftDeleteMixin):
    """
    Цикл ЭКО.
    Один цикл = весь клинический путь от начала до исхода.
    """
    __tablename__ = "cycles"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)

    # Связь с пациенткой
    patient_id: Mapped[int] = mapped_column(
        ForeignKey("patients.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Номер цикла для данной пациентки (1, 2, 3...)
    cycle_number: Mapped[int] = mapped_column(nullable=False)

    # Даты
    start_date: Mapped[date] = mapped_column(Date, nullable=False)
    end_date: Mapped[date | None] = mapped_column(Date, nullable=True)

    # Статус и этап
    status: Mapped[CycleStatus] = mapped_column(
        SQLEnum(CycleStatus, values_callable=lambda e: [m.value for m in e]),
        nullable=False,
        default=CycleStatus.ACTIVE,
    )
    current_stage: Mapped[CycleStage] = mapped_column(
        SQLEnum(CycleStage, values_callable=lambda e: [m.value for m in e]),
        nullable=False,
        default=CycleStage.PREPARATION,
    )

    # Назначенные специалисты
    assigned_doctor_id: Mapped[int | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    assigned_embryologist_id: Mapped[int | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    # Флаг донорского цикла
    is_donor_cycle: Mapped[bool] = mapped_column(
        nullable=False,
        default=False,
        server_default="false",
    )

    # Причина отмены (обязательна при status='cancelled')
    cancellation_reason: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Заметки
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Relationships
    patient: Mapped["Patient"] = relationship(
        "Patient",
        back_populates="cycles",
    )

    assigned_doctor: Mapped["User | None"] = relationship(
        "User",
        foreign_keys=[assigned_doctor_id],
        back_populates="cycles_as_doctor",
    )

    assigned_embryologist: Mapped["User | None"] = relationship(
        "User",
        foreign_keys=[assigned_embryologist_id],
        back_populates="cycles_as_embryologist",
    )

    def __repr__(self) -> str:
        return (
            f"<Cycle(id={self.id}, patient_id={self.patient_id}, "
            f"cycle_number={self.cycle_number}, status='{self.status}')>"
        )
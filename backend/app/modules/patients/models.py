"""
Модель пациентки (Patient).
Обезличенные данные пациенток клиники ЭКО.
"""
from datetime import date
from typing import TYPE_CHECKING

from sqlalchemy import String, Date, Numeric
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.database import Base
from app.db.mixins import TimestampMixin, SoftDeleteMixin

if TYPE_CHECKING:
    from app.models.cycle import Cycle


class Patient(Base, TimestampMixin, SoftDeleteMixin):
    """
    Пациентка клиники ЭКО.
    Данные обезличены (нет ФИО).
    """
    __tablename__ = "patients"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)

    # Обезличенный медицинский номер (вместо ФИО)
    medical_record_number: Mapped[str] = mapped_column(
        String(50), unique=True, index=True, nullable=False
    )

    date_of_birth: Mapped[date] = mapped_column(Date, nullable=False)

    # Группа крови (опционально)
    blood_type: Mapped[str | None] = mapped_column(String(10), nullable=True)

    # Антропометрические данные
    height: Mapped[float | None] = mapped_column(Numeric(5, 2), nullable=True)  # в см
    weight: Mapped[float | None] = mapped_column(Numeric(5, 2), nullable=True)  # в кг

    # АМГ (антимюллеров гормон) - важный показатель овариального резерва
    amh_level: Mapped[float | None] = mapped_column(Numeric(6, 2), nullable=True)  # в нг/мл

    # Relationships
    cycles: Mapped[list["Cycle"]] = relationship(
        "Cycle",
        back_populates="patient",
        cascade="all, delete-orphan",
    )

    def __repr__(self) -> str:
        return f"<Patient(id={self.id}, mrn='{self.medical_record_number}')>"
"""Initial tables: users, patients, cycles

Revision ID: 001
Revises:
Create Date: 2024-11-03 12:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = '001'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Создаём enum типы
    op.execute("CREATE TYPE userrole AS ENUM ('reproductologist', 'embryologist')")
    op.execute("CREATE TYPE cyclestatus AS ENUM ('active', 'completed', 'cancelled')")
    op.execute("CREATE TYPE cyclestage AS ENUM ('preparation', 'stimulation', 'retrieval', 'embryology', 'transfer', 'outcome')")

    # Таблица users
    op.create_table(
        'users',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('email', sa.String(length=255), nullable=False),
        sa.Column('hashed_password', sa.String(length=255), nullable=False),
        sa.Column('role', postgresql.ENUM('reproductologist', 'embryologist', name='userrole', create_type=False), nullable=False),
        sa.Column('full_name', sa.String(length=255), nullable=False),
        sa.Column('is_active', sa.Boolean(), server_default='true', nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_users_email'), 'users', ['email'], unique=True)
    op.create_index(op.f('ix_users_id'), 'users', ['id'], unique=False)

    # Таблица patients
    op.create_table(
        'patients',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('medical_record_number', sa.String(length=50), nullable=False),
        sa.Column('date_of_birth', sa.Date(), nullable=False),
        sa.Column('blood_type', sa.String(length=10), nullable=True),
        sa.Column('height', sa.Numeric(precision=5, scale=2), nullable=True),
        sa.Column('weight', sa.Numeric(precision=5, scale=2), nullable=True),
        sa.Column('amh_level', sa.Numeric(precision=6, scale=2), nullable=True),
        sa.Column('is_deleted', sa.Boolean(), server_default='false', nullable=False),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_patients_id'), 'patients', ['id'], unique=False)
    op.create_index(op.f('ix_patients_medical_record_number'), 'patients', ['medical_record_number'], unique=True)

    # Таблица cycles
    op.create_table(
        'cycles',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('patient_id', sa.Integer(), nullable=False),
        sa.Column('cycle_number', sa.Integer(), nullable=False),
        sa.Column('start_date', sa.Date(), nullable=False),
        sa.Column('end_date', sa.Date(), nullable=True),
        sa.Column('status', postgresql.ENUM('active', 'completed', 'cancelled', name='cyclestatus', create_type=False), nullable=False),
        sa.Column('current_stage', postgresql.ENUM('preparation', 'stimulation', 'retrieval', 'embryology', 'transfer', 'outcome', name='cyclestage', create_type=False), nullable=False),
        sa.Column('assigned_doctor_id', sa.Integer(), nullable=True),
        sa.Column('assigned_embryologist_id', sa.Integer(), nullable=True),
        sa.Column('is_donor_cycle', sa.Boolean(), server_default='false', nullable=False),
        sa.Column('cancellation_reason', sa.Text(), nullable=True),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('is_deleted', sa.Boolean(), server_default='false', nullable=False),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['assigned_doctor_id'], ['users.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['assigned_embryologist_id'], ['users.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['patient_id'], ['patients.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_cycles_assigned_doctor_id'), 'cycles', ['assigned_doctor_id'], unique=False)
    op.create_index(op.f('ix_cycles_assigned_embryologist_id'), 'cycles', ['assigned_embryologist_id'], unique=False)
    op.create_index(op.f('ix_cycles_id'), 'cycles', ['id'], unique=False)
    op.create_index(op.f('ix_cycles_patient_id'), 'cycles', ['patient_id'], unique=False)


def downgrade() -> None:
    # Удаляем таблицы
    op.drop_index(op.f('ix_cycles_patient_id'), table_name='cycles')
    op.drop_index(op.f('ix_cycles_id'), table_name='cycles')
    op.drop_index(op.f('ix_cycles_assigned_embryologist_id'), table_name='cycles')
    op.drop_index(op.f('ix_cycles_assigned_doctor_id'), table_name='cycles')
    op.drop_table('cycles')

    op.drop_index(op.f('ix_patients_medical_record_number'), table_name='patients')
    op.drop_index(op.f('ix_patients_id'), table_name='patients')
    op.drop_table('patients')

    op.drop_index(op.f('ix_users_id'), table_name='users')
    op.drop_index(op.f('ix_users_email'), table_name='users')
    op.drop_table('users')

    # Удаляем enum типы
    op.execute("DROP TYPE cyclestage")
    op.execute("DROP TYPE cyclestatus")
    op.execute("DROP TYPE userrole")

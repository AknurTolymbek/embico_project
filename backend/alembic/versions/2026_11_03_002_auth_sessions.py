"""User accounts and rotating JWT refresh sessions; retain clinical data.

Revision ID: 002
Revises: 001
"""
from alembic import op
import sqlalchemy as sa

revision = '002'
down_revision = '001'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('users', sa.Column('username', sa.String(80), nullable=True))
    op.add_column('users', sa.Column('first_name', sa.String(120), nullable=True))
    op.add_column('users', sa.Column('last_name', sa.String(120), nullable=True))
    op.execute("""UPDATE users SET
        username = 'user_' || id,
        first_name = COALESCE(NULLIF(left(split_part(trim(full_name), ' ', 1), 120), ''), 'Пользователь'),
        last_name = CASE WHEN position(' ' in trim(full_name)) > 0 THEN COALESCE(NULLIF(left(trim(substring(trim(full_name) from position(' ' in trim(full_name)) + 1)), 120), ''), '—') ELSE '—' END
    """)
    op.alter_column('users', 'username', nullable=False)
    op.alter_column('users', 'first_name', nullable=False)
    op.alter_column('users', 'last_name', nullable=False)
    op.create_index('ix_users_username', 'users', ['username'], unique=True)
    op.alter_column('users', 'email', existing_type=sa.String(255), nullable=True)
    op.execute('ALTER TYPE userrole RENAME TO userrole_legacy')
    op.execute("CREATE TYPE userrole AS ENUM ('admin', 'doctor')")
    op.execute("ALTER TABLE users ALTER COLUMN role TYPE userrole USING ('doctor'::userrole)")
    op.execute('DROP TYPE userrole_legacy')
    op.create_table('auth_sessions',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('user_id', sa.Integer(), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('refresh_hash', sa.String(64), nullable=False),
        sa.Column('expires_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('revoked_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    )
    op.create_index('ix_auth_sessions_user_id', 'auth_sessions', ['user_id'])


def downgrade():
    op.drop_table('auth_sessions')
    # Email-less users receive unique local addresses to restore the old NOT NULL schema.
    op.execute("UPDATE users SET email = 'user-' || id || '@migration.invalid' WHERE email IS NULL")
    op.alter_column('users', 'email', existing_type=sa.String(255), nullable=False)
    op.execute('ALTER TYPE userrole RENAME TO userrole_auth')
    op.execute("CREATE TYPE userrole AS ENUM ('reproductologist', 'embryologist')")
    op.execute("ALTER TABLE users ALTER COLUMN role TYPE userrole USING ('reproductologist'::userrole)")
    op.execute('DROP TYPE userrole_auth')
    op.drop_index('ix_users_username', table_name='users')
    for column in ('last_name', 'first_name', 'username'):
        op.drop_column('users', column)

"""Add users and idempotency_keys tables

Revision ID: 0002
Revises: 0001
Create Date: 2025-08-14

"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '0002'
down_revision = '0001'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Create users and idempotency_keys tables and associated indexes."""
    # create users table
    op.create_table(
        'users',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('email', sa.String(length=256), nullable=False),
        sa.Column('password_hash', sa.String(length=256), nullable=False),
        sa.Column('role', sa.String(length=16), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
    )
    # indexes for users
    op.create_index(op.f('ix_users_email'), 'users', ['email'], unique=True)
    op.create_index(op.f('ix_users_role'), 'users', ['role'], unique=False)
    op.create_index(op.f('ix_users_created_at'), 'users', ['created_at'], unique=False)

    # create idempotency_keys table
    op.create_table(
        'idempotency_keys',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('key', sa.String(length=128), nullable=False),
        sa.Column('method', sa.String(length=8), nullable=False),
        sa.Column('path', sa.String(length=512), nullable=False),
        sa.Column('body_hash', sa.String(length=64), nullable=True),
        sa.Column('response_status', sa.Integer(), nullable=True),
        sa.Column(
            'response_body',
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=True,
        ),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
    )
    # indexes for idempotency_keys
    op.create_index(op.f('ix_idempotency_keys_key'), 'idempotency_keys', ['key'], unique=False)
    op.create_index(op.f('ix_idempotency_keys_method'), 'idempotency_keys', ['method'], unique=False)
    op.create_index(op.f('ix_idempotency_keys_path'), 'idempotency_keys', ['path'], unique=False)
    op.create_index('ix_idem_key_method_path', 'idempotency_keys', ['key', 'method', 'path'], unique=False)
    op.create_index(op.f('ix_idempotency_keys_created_at'), 'idempotency_keys', ['created_at'], unique=False)


def downgrade() -> None:
    """Drop users and idempotency_keys tables and associated indexes."""
    # drop indexes and tables in reverse order
    op.drop_index(op.f('ix_idempotency_keys_created_at'), table_name='idempotency_keys')
    op.drop_index('ix_idem_key_method_path', table_name='idempotency_keys')
    op.drop_index(op.f('ix_idempotency_keys_path'), table_name='idempotency_keys')
    op.drop_index(op.f('ix_idempotency_keys_method'), table_name='idempotency_keys')
    op.drop_index(op.f('ix_idempotency_keys_key'), table_name='idempotency_keys')
    op.drop_table('idempotency_keys')
    op.drop_index(op.f('ix_users_created_at'), table_name='users')
    op.drop_index(op.f('ix_users_role'), table_name='users')
    op.drop_index(op.f('ix_users_email'), table_name='users')
    op.drop_table('users')
"""add supabase_id to users

Revision ID: 015_add_supabase_id_to_users
Revises: 014_enterprise_audit
Create Date: 2026-07-16 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '015_add_supabase_id_to_users'
down_revision = '014_enterprise_audit'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('users', sa.Column('supabase_id', sa.String(length=255), nullable=True))
    op.create_index(op.f('ix_users_supabase_id'), 'users', ['supabase_id'], unique=True)


def downgrade():
    op.drop_index(op.f('ix_users_supabase_id'), table_name='users')
    op.drop_column('users', 'supabase_id')

"""add organizations and organization_members tables

Revision ID: 017_add_organizations
Revises: 016_add_organization_id_columns
Create Date: 2026-07-16 00:02:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '017_add_organizations'
down_revision = '016_add_organization_id_columns'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'organizations',
        sa.Column('id', sa.String(length=36), primary_key=True),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('slug', sa.String(length=255), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default=sa.text('true')),
    )
    op.create_index('ix_organizations_slug', 'organizations', ['slug'], unique=True)

    op.create_table(
        'organization_members',
        sa.Column('id', sa.String(length=36), primary_key=True),
        sa.Column('organization_id', sa.String(length=36), sa.ForeignKey('organizations.id'), nullable=False),
        sa.Column('user_id', sa.Integer(), sa.ForeignKey('users.id'), nullable=False),
        sa.Column('role', sa.String(length=50), nullable=False, server_default='member'),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.UniqueConstraint('organization_id', 'user_id', name='uq_organization_user'),
    )


def downgrade():
    op.drop_table('organization_members')
    op.drop_index('ix_organizations_slug', table_name='organizations')
    op.drop_table('organizations')

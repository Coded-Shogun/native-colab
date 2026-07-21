"""add organization_id columns (dual-write) to workspace-scoped tables

Revision ID: 016_add_organization_id_columns
Revises: 015_add_supabase_id_to_users
Create Date: 2026-07-16 00:01:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '016_add_organization_id_columns'
down_revision = '015_add_supabase_id_to_users'
branch_labels = None
depends_on = None

WORKSPACE_SCOPED_TABLES = [
    'projects',
    'time_entries',
    'channels',
    'folders',
    'documents',
    'meetings',
    'whiteboards',
    'teams',
    'calendars',
    'signature_requests',
    'notifications',
    'audit_logs',
    'security_events',
    'data_access_logs',
    'compliance_logs',
    'webhooks',
    'integration_connections',
    'search_indexes',
    'search_history',
    'saved_searches',
    'analytics_events',
    'reports',
    'export_jobs',
    'workspace_metrics',
]


def upgrade():
    for table in WORKSPACE_SCOPED_TABLES:
        op.add_column(table, sa.Column('organization_id', sa.String(length=36), nullable=True))


def downgrade():
    for table in WORKSPACE_SCOPED_TABLES:
        op.drop_column(table, 'organization_id')

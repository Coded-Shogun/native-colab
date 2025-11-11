"""add analytics and reporting

Revision ID: 013_add_analytics_reporting
Revises: 012_add_webhooks_integrations
Create Date: 2025-11-11 17:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '013_add_analytics_reporting'
down_revision = '012_add_webhooks_integrations'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create analytics event type enum
    op.execute("""
        CREATE TYPE analyticseventtype AS ENUM (
            'page_view', 'button_click', 'form_submit', 'search', 'file_upload', 'file_download',
            'user_login', 'user_logout', 'api_call', 'error', 'custom'
        );
    """)

    # Create report type enum
    op.execute("""
        CREATE TYPE reporttype AS ENUM (
            'user_activity', 'project_progress', 'time_tracking', 'task_completion',
            'workspace_analytics', 'custom'
        );
    """)

    # Create report status enum
    op.execute("""
        CREATE TYPE reportstatus AS ENUM ('pending', 'processing', 'completed', 'failed');
    """)

    # Create report format enum
    op.execute("""
        CREATE TYPE reportformat AS ENUM ('pdf', 'csv', 'excel', 'json');
    """)

    # Create export status enum
    op.execute("""
        CREATE TYPE exportstatus AS ENUM ('pending', 'processing', 'completed', 'failed', 'expired');
    """)

    # Create analytics_events table
    op.create_table(
        'analytics_events',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('event_type', postgresql.ENUM(name='analyticseventtype', create_type=False), nullable=False),
        sa.Column('event_name', sa.String(length=255), nullable=False),
        sa.Column('workspace_id', sa.Integer(), nullable=True),
        sa.Column('user_id', sa.Integer(), nullable=True),
        sa.Column('properties', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('session_id', sa.String(length=255), nullable=True),
        sa.Column('ip_address', sa.String(length=45), nullable=True),
        sa.Column('user_agent', sa.Text(), nullable=True),
        sa.Column('referrer', sa.Text(), nullable=True),
        sa.Column('path', sa.String(length=500), nullable=True),
        sa.Column('query_params', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('duration_ms', sa.Integer(), nullable=True),
        sa.Column('status_code', sa.Integer(), nullable=True),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['workspace_id'], ['workspaces.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_analytics_events_workspace', 'analytics_events', ['workspace_id'])
    op.create_index('idx_analytics_events_user', 'analytics_events', ['user_id'])
    op.create_index('idx_analytics_events_type', 'analytics_events', ['event_type'])
    op.create_index('idx_analytics_events_created', 'analytics_events', ['created_at'])
    op.create_index('idx_analytics_events_session', 'analytics_events', ['session_id'])

    # Create reports table
    op.create_table(
        'reports',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('workspace_id', sa.Integer(), nullable=False),
        sa.Column('creator_id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('report_type', postgresql.ENUM(name='reporttype', create_type=False), nullable=False),
        sa.Column('status', postgresql.ENUM(name='reportstatus', create_type=False), nullable=False, server_default='pending'),
        sa.Column('format', postgresql.ENUM(name='reportformat', create_type=False), nullable=False),
        sa.Column('parameters', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('result_data', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('file_url', sa.String(length=500), nullable=True),
        sa.Column('scheduled_for', sa.DateTime(), nullable=True),
        sa.Column('generated_at', sa.DateTime(), nullable=True),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('now()'), onupdate=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['creator_id'], ['users.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['workspace_id'], ['workspaces.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_reports_workspace', 'reports', ['workspace_id'])
    op.create_index('idx_reports_creator', 'reports', ['creator_id'])
    op.create_index('idx_reports_status', 'reports', ['status'])
    op.create_index('idx_reports_type', 'reports', ['report_type'])

    # Create export_jobs table
    op.create_table(
        'export_jobs',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('workspace_id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('export_type', sa.String(length=100), nullable=False),
        sa.Column('status', postgresql.ENUM(name='exportstatus', create_type=False), nullable=False, server_default='pending'),
        sa.Column('format', postgresql.ENUM(name='reportformat', create_type=False), nullable=False),
        sa.Column('filters', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('file_url', sa.String(length=500), nullable=True),
        sa.Column('file_size', sa.BigInteger(), nullable=True),
        sa.Column('record_count', sa.Integer(), nullable=True),
        sa.Column('expires_at', sa.DateTime(), nullable=True),
        sa.Column('started_at', sa.DateTime(), nullable=True),
        sa.Column('completed_at', sa.DateTime(), nullable=True),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('now()'), onupdate=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['workspace_id'], ['workspaces.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_export_jobs_workspace', 'export_jobs', ['workspace_id'])
    op.create_index('idx_export_jobs_user', 'export_jobs', ['user_id'])
    op.create_index('idx_export_jobs_status', 'export_jobs', ['status'])

    # Create workspace_metrics table
    op.create_table(
        'workspace_metrics',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('workspace_id', sa.Integer(), nullable=False),
        sa.Column('date', sa.Date(), nullable=False),
        sa.Column('active_users', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('total_projects', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('active_projects', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('total_tasks', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('completed_tasks', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('total_messages', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('total_documents', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('storage_used_bytes', sa.BigInteger(), nullable=False, server_default='0'),
        sa.Column('total_meetings', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('meeting_duration_minutes', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('total_time_entries', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('tracked_hours', sa.Float(), nullable=False, server_default='0'),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('now()'), onupdate=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['workspace_id'], ['workspaces.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('workspace_id', 'date', name='uq_workspace_metrics_workspace_date')
    )
    op.create_index('idx_workspace_metrics_workspace', 'workspace_metrics', ['workspace_id'])
    op.create_index('idx_workspace_metrics_date', 'workspace_metrics', ['date'])


def downgrade() -> None:
    # Drop tables
    op.drop_table('workspace_metrics')
    op.drop_table('export_jobs')
    op.drop_table('reports')
    op.drop_table('analytics_events')

    # Drop enums
    op.execute('DROP TYPE IF EXISTS exportstatus')
    op.execute('DROP TYPE IF EXISTS reportformat')
    op.execute('DROP TYPE IF EXISTS reportstatus')
    op.execute('DROP TYPE IF EXISTS reporttype')
    op.execute('DROP TYPE IF EXISTS analyticseventtype')

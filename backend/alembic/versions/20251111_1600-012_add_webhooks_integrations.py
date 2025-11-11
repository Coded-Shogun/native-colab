"""add webhooks and integrations

Revision ID: 012_add_webhooks_integrations
Revises: 011_add_search_system
Create Date: 2025-11-11 16:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '012_add_webhooks_integrations'
down_revision = '011_add_search_system'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create webhook event type enum
    op.execute("""
        CREATE TYPE webhookeventtype AS ENUM (
            'user.created', 'user.updated', 'user.deleted',
            'workspace.created', 'workspace.updated', 'workspace.member_added', 'workspace.member_removed',
            'project.created', 'project.updated', 'project.deleted', 'project.completed',
            'task.created', 'task.updated', 'task.deleted', 'task.assigned', 'task.completed', 'task.comment_added',
            'document.created', 'document.updated', 'document.deleted', 'document.shared', 'document.comment_added',
            'message.created', 'message.updated', 'message.deleted', 'direct_message.created',
            'event.created', 'event.updated', 'event.deleted', 'event.rsvp_updated',
            'meeting.created', 'meeting.started', 'meeting.ended', 'meeting.recording_available',
            'whiteboard.created', 'whiteboard.updated', 'whiteboard.shared',
            'signature_request.created', 'signature_request.completed', 'signature.added',
            'time_entry.created', 'time_entry.updated'
        );
    """)

    # Create webhook status enum
    op.execute("""
        CREATE TYPE webhookstatus AS ENUM ('active', 'inactive', 'failed', 'disabled');
    """)

    # Create delivery status enum
    op.execute("""
        CREATE TYPE deliverystatus AS ENUM ('pending', 'success', 'failed', 'retrying');
    """)

    # Create integration type enum
    op.execute("""
        CREATE TYPE integrationtype AS ENUM (
            'slack', 'github', 'google_calendar', 'microsoft_teams',
            'jira', 'trello', 'zapier', 'custom'
        );
    """)

    # Create integration status enum
    op.execute("""
        CREATE TYPE integrationstatus AS ENUM ('connected', 'disconnected', 'error', 'expired');
    """)

    # Create webhooks table
    op.create_table(
        'webhooks',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('workspace_id', sa.Integer(), nullable=False),
        sa.Column('created_by', sa.Integer(), nullable=False),

        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('url', sa.Text(), nullable=False),

        sa.Column('secret', sa.String(length=255), nullable=True),
        sa.Column('headers', postgresql.JSON(astext_type=sa.Text()), nullable=True),

        sa.Column('events', postgresql.JSON(astext_type=sa.Text()), nullable=False),
        sa.Column('filters', postgresql.JSON(astext_type=sa.Text()), nullable=True),

        sa.Column('status', sa.Enum('active', 'inactive', 'failed', 'disabled', name='webhookstatus'), nullable=False, server_default='active'),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),

        sa.Column('max_retries', sa.Integer(), nullable=False, server_default='3'),
        sa.Column('retry_delay', sa.Integer(), nullable=False, server_default='60'),

        sa.Column('total_deliveries', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('successful_deliveries', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('failed_deliveries', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('last_delivery_at', sa.DateTime(), nullable=True),
        sa.Column('last_success_at', sa.DateTime(), nullable=True),
        sa.Column('last_failure_at', sa.DateTime(), nullable=True),

        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),

        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['workspace_id'], ['workspaces.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['created_by'], ['users.id'], ondelete='CASCADE'),
    )

    op.create_index('ix_webhooks_id', 'webhooks', ['id'])
    op.create_index('ix_webhooks_workspace_id', 'webhooks', ['workspace_id'])
    op.create_index('ix_webhooks_created_by', 'webhooks', ['created_by'])
    op.create_index('ix_webhooks_status', 'webhooks', ['status'])
    op.create_index('ix_webhooks_workspace_status', 'webhooks', ['workspace_id', 'status'])

    # Create webhook_deliveries table
    op.create_table(
        'webhook_deliveries',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('webhook_id', sa.Integer(), nullable=False),

        sa.Column('event_type', sa.Enum(
            'user.created', 'user.updated', 'user.deleted',
            'workspace.created', 'workspace.updated', 'workspace.member_added', 'workspace.member_removed',
            'project.created', 'project.updated', 'project.deleted', 'project.completed',
            'task.created', 'task.updated', 'task.deleted', 'task.assigned', 'task.completed', 'task.comment_added',
            'document.created', 'document.updated', 'document.deleted', 'document.shared', 'document.comment_added',
            'message.created', 'message.updated', 'message.deleted', 'direct_message.created',
            'event.created', 'event.updated', 'event.deleted', 'event.rsvp_updated',
            'meeting.created', 'meeting.started', 'meeting.ended', 'meeting.recording_available',
            'whiteboard.created', 'whiteboard.updated', 'whiteboard.shared',
            'signature_request.created', 'signature_request.completed', 'signature.added',
            'time_entry.created', 'time_entry.updated',
            name='webhookeventtype'
        ), nullable=False),
        sa.Column('event_id', sa.String(length=255), nullable=False),

        sa.Column('payload', postgresql.JSON(astext_type=sa.Text()), nullable=False),

        sa.Column('request_url', sa.Text(), nullable=False),
        sa.Column('request_method', sa.String(length=10), nullable=False, server_default='POST'),
        sa.Column('request_headers', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('request_signature', sa.String(length=255), nullable=True),

        sa.Column('response_status_code', sa.Integer(), nullable=True),
        sa.Column('response_headers', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('response_body', sa.Text(), nullable=True),
        sa.Column('response_time_ms', sa.Integer(), nullable=True),

        sa.Column('status', sa.Enum('pending', 'success', 'failed', 'retrying', name='deliverystatus'), nullable=False, server_default='pending'),
        sa.Column('attempts', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('max_attempts', sa.Integer(), nullable=False, server_default='3'),

        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('error_trace', sa.Text(), nullable=True),

        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('next_retry_at', sa.DateTime(), nullable=True),
        sa.Column('delivered_at', sa.DateTime(), nullable=True),

        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['webhook_id'], ['webhooks.id'], ondelete='CASCADE'),
    )

    op.create_index('ix_webhook_deliveries_id', 'webhook_deliveries', ['id'])
    op.create_index('ix_webhook_deliveries_webhook_id', 'webhook_deliveries', ['webhook_id'])
    op.create_index('ix_webhook_deliveries_event_type', 'webhook_deliveries', ['event_type'])
    op.create_index('ix_webhook_deliveries_status', 'webhook_deliveries', ['status'])
    op.create_index('ix_webhook_deliveries_created_at', 'webhook_deliveries', ['created_at'])
    op.create_index('ix_webhook_deliveries_next_retry_at', 'webhook_deliveries', ['next_retry_at'])
    op.create_index('ix_webhook_deliveries_webhook_status', 'webhook_deliveries', ['webhook_id', 'status'])
    op.create_index('ix_webhook_deliveries_event', 'webhook_deliveries', ['event_type', 'event_id'])

    # Create integrations table
    op.create_table(
        'integrations',
        sa.Column('id', sa.Integer(), nullable=False),

        sa.Column('type', sa.Enum(
            'slack', 'github', 'google_calendar', 'microsoft_teams',
            'jira', 'trello', 'zapier', 'custom',
            name='integrationtype'
        ), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('icon_url', sa.Text(), nullable=True),

        sa.Column('client_id', sa.String(length=255), nullable=True),
        sa.Column('client_secret', sa.String(length=255), nullable=True),
        sa.Column('authorization_url', sa.Text(), nullable=True),
        sa.Column('token_url', sa.Text(), nullable=True),
        sa.Column('scopes', postgresql.JSON(astext_type=sa.Text()), nullable=True),

        sa.Column('api_base_url', sa.Text(), nullable=True),
        sa.Column('api_version', sa.String(length=50), nullable=True),

        sa.Column('settings', postgresql.JSON(astext_type=sa.Text()), nullable=True),

        sa.Column('is_enabled', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('is_oauth', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('is_system', sa.Boolean(), nullable=False, server_default='false'),

        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),

        sa.PrimaryKeyConstraint('id'),
    )

    op.create_index('ix_integrations_id', 'integrations', ['id'])
    op.create_index('ix_integrations_type', 'integrations', ['type'])

    # Create integration_connections table
    op.create_table(
        'integration_connections',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('integration_id', sa.Integer(), nullable=False),
        sa.Column('workspace_id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),

        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),

        sa.Column('access_token', sa.Text(), nullable=True),
        sa.Column('refresh_token', sa.Text(), nullable=True),
        sa.Column('token_expires_at', sa.DateTime(), nullable=True),

        sa.Column('credentials', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('settings', postgresql.JSON(astext_type=sa.Text()), nullable=True),

        sa.Column('external_id', sa.String(length=255), nullable=True),
        sa.Column('external_data', postgresql.JSON(astext_type=sa.Text()), nullable=True),

        sa.Column('status', sa.Enum('connected', 'disconnected', 'error', 'expired', name='integrationstatus'), nullable=False, server_default='connected'),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),

        sa.Column('last_used_at', sa.DateTime(), nullable=True),
        sa.Column('last_sync_at', sa.DateTime(), nullable=True),
        sa.Column('total_syncs', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('failed_syncs', sa.Integer(), nullable=False, server_default='0'),

        sa.Column('last_error', sa.Text(), nullable=True),
        sa.Column('last_error_at', sa.DateTime(), nullable=True),

        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),

        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['integration_id'], ['integrations.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['workspace_id'], ['workspaces.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
    )

    op.create_index('ix_integration_connections_id', 'integration_connections', ['id'])
    op.create_index('ix_integration_connections_integration_id', 'integration_connections', ['integration_id'])
    op.create_index('ix_integration_connections_workspace_id', 'integration_connections', ['workspace_id'])
    op.create_index('ix_integration_connections_user_id', 'integration_connections', ['user_id'])
    op.create_index('ix_integration_connections_status', 'integration_connections', ['status'])
    op.create_index('ix_integration_connections_workspace_integration', 'integration_connections', ['workspace_id', 'integration_id'])
    op.create_index('ix_integration_connections_user_integration', 'integration_connections', ['user_id', 'integration_id'])


def downgrade() -> None:
    # Drop integration_connections table
    op.drop_index('ix_integration_connections_user_integration', table_name='integration_connections')
    op.drop_index('ix_integration_connections_workspace_integration', table_name='integration_connections')
    op.drop_index('ix_integration_connections_status', table_name='integration_connections')
    op.drop_index('ix_integration_connections_user_id', table_name='integration_connections')
    op.drop_index('ix_integration_connections_workspace_id', table_name='integration_connections')
    op.drop_index('ix_integration_connections_integration_id', table_name='integration_connections')
    op.drop_index('ix_integration_connections_id', table_name='integration_connections')
    op.drop_table('integration_connections')

    # Drop integrations table
    op.drop_index('ix_integrations_type', table_name='integrations')
    op.drop_index('ix_integrations_id', table_name='integrations')
    op.drop_table('integrations')

    # Drop webhook_deliveries table
    op.drop_index('ix_webhook_deliveries_event', table_name='webhook_deliveries')
    op.drop_index('ix_webhook_deliveries_webhook_status', table_name='webhook_deliveries')
    op.drop_index('ix_webhook_deliveries_next_retry_at', table_name='webhook_deliveries')
    op.drop_index('ix_webhook_deliveries_created_at', table_name='webhook_deliveries')
    op.drop_index('ix_webhook_deliveries_status', table_name='webhook_deliveries')
    op.drop_index('ix_webhook_deliveries_event_type', table_name='webhook_deliveries')
    op.drop_index('ix_webhook_deliveries_webhook_id', table_name='webhook_deliveries')
    op.drop_index('ix_webhook_deliveries_id', table_name='webhook_deliveries')
    op.drop_table('webhook_deliveries')

    # Drop webhooks table
    op.drop_index('ix_webhooks_workspace_status', table_name='webhooks')
    op.drop_index('ix_webhooks_status', table_name='webhooks')
    op.drop_index('ix_webhooks_created_by', table_name='webhooks')
    op.drop_index('ix_webhooks_workspace_id', table_name='webhooks')
    op.drop_index('ix_webhooks_id', table_name='webhooks')
    op.drop_table('webhooks')

    # Drop enum types
    op.execute('DROP TYPE integrationstatus')
    op.execute('DROP TYPE integrationtype')
    op.execute('DROP TYPE deliverystatus')
    op.execute('DROP TYPE webhookstatus')
    op.execute('DROP TYPE webhookeventtype')

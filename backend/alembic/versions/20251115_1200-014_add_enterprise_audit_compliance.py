"""add enterprise audit and compliance tables

Revision ID: 014_enterprise_audit
Revises: 013_analytics_reporting
Create Date: 2025-01-15 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '014_enterprise_audit'
down_revision = '013_analytics_reporting'
branch_labels = None
depends_on = None


def upgrade():
    # Create audit_logs table
    op.create_table(
        'audit_logs',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('workspace_id', sa.Integer(), nullable=True),
        sa.Column('user_id', sa.Integer(), nullable=True),
        sa.Column('action', sa.String(length=100), nullable=False),
        sa.Column('resource_type', sa.String(length=100), nullable=False),
        sa.Column('resource_id', sa.String(length=255), nullable=True),
        sa.Column('ip_address', sa.String(length=45), nullable=True),
        sa.Column('user_agent', sa.Text(), nullable=True),
        sa.Column('request_method', sa.String(length=10), nullable=True),
        sa.Column('request_path', sa.String(length=500), nullable=True),
        sa.Column('request_id', sa.String(length=100), nullable=True),
        sa.Column('old_values', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('new_values', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('success', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('failure_reason', sa.Text(), nullable=True),
        sa.Column('risk_level', sa.String(length=20), nullable=False, server_default='low'),
        sa.Column('duration_ms', sa.Integer(), nullable=True),
        sa.Column('metadata', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.ForeignKeyConstraint(['workspace_id'], ['workspaces.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_audit_logs_workspace_id'), 'audit_logs', ['workspace_id'], unique=False)
    op.create_index(op.f('ix_audit_logs_user_id'), 'audit_logs', ['user_id'], unique=False)
    op.create_index(op.f('ix_audit_logs_action'), 'audit_logs', ['action'], unique=False)
    op.create_index(op.f('ix_audit_logs_resource_type'), 'audit_logs', ['resource_type'], unique=False)
    op.create_index(op.f('ix_audit_logs_resource_id'), 'audit_logs', ['resource_id'], unique=False)
    op.create_index(op.f('ix_audit_logs_created_at'), 'audit_logs', ['created_at'], unique=False)
    op.create_index(op.f('ix_audit_logs_request_id'), 'audit_logs', ['request_id'], unique=True)
    op.create_index('ix_audit_logs_workspace_date', 'audit_logs', ['workspace_id', 'created_at'], unique=False)
    op.create_index('ix_audit_logs_user_date', 'audit_logs', ['user_id', 'created_at'], unique=False)

    # Create security_events table
    op.create_table(
        'security_events',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('event_type', sa.String(length=100), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=True),
        sa.Column('workspace_id', sa.Integer(), nullable=True),
        sa.Column('severity', sa.String(length=20), nullable=False),
        sa.Column('description', sa.Text(), nullable=False),
        sa.Column('ip_address', sa.String(length=45), nullable=True),
        sa.Column('user_agent', sa.Text(), nullable=True),
        sa.Column('action_taken', sa.String(length=100), nullable=True),
        sa.Column('resolved', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('resolved_at', sa.DateTime(), nullable=True),
        sa.Column('resolved_by', sa.Integer(), nullable=True),
        sa.Column('metadata', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.ForeignKeyConstraint(['resolved_by'], ['users.id'], ),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.ForeignKeyConstraint(['workspace_id'], ['workspaces.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_security_events_event_type'), 'security_events', ['event_type'], unique=False)
    op.create_index(op.f('ix_security_events_user_id'), 'security_events', ['user_id'], unique=False)
    op.create_index(op.f('ix_security_events_workspace_id'), 'security_events', ['workspace_id'], unique=False)
    op.create_index(op.f('ix_security_events_severity'), 'security_events', ['severity'], unique=False)
    op.create_index(op.f('ix_security_events_ip_address'), 'security_events', ['ip_address'], unique=False)
    op.create_index(op.f('ix_security_events_created_at'), 'security_events', ['created_at'], unique=False)

    # Create data_access_logs table
    op.create_table(
        'data_access_logs',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('workspace_id', sa.Integer(), nullable=True),
        sa.Column('resource_type', sa.String(length=100), nullable=False),
        sa.Column('resource_id', sa.String(length=255), nullable=False),
        sa.Column('action', sa.String(length=50), nullable=False),
        sa.Column('data_classification', sa.String(length=50), nullable=True),
        sa.Column('ip_address', sa.String(length=45), nullable=True),
        sa.Column('justification', sa.Text(), nullable=True),
        sa.Column('granted_by_policy', sa.String(length=100), nullable=True),
        sa.Column('metadata', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.ForeignKeyConstraint(['workspace_id'], ['workspaces.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_data_access_logs_user_id'), 'data_access_logs', ['user_id'], unique=False)
    op.create_index(op.f('ix_data_access_logs_workspace_id'), 'data_access_logs', ['workspace_id'], unique=False)
    op.create_index(op.f('ix_data_access_logs_resource_type'), 'data_access_logs', ['resource_type'], unique=False)
    op.create_index(op.f('ix_data_access_logs_resource_id'), 'data_access_logs', ['resource_id'], unique=False)
    op.create_index(op.f('ix_data_access_logs_action'), 'data_access_logs', ['action'], unique=False)
    op.create_index(op.f('ix_data_access_logs_created_at'), 'data_access_logs', ['created_at'], unique=False)

    # Create compliance_logs table
    op.create_table(
        'compliance_logs',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('compliance_type', sa.String(length=50), nullable=False),
        sa.Column('action_type', sa.String(length=100), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=True),
        sa.Column('workspace_id', sa.Integer(), nullable=True),
        sa.Column('description', sa.Text(), nullable=False),
        sa.Column('legal_basis', sa.String(length=100), nullable=True),
        sa.Column('data_subject_id', sa.String(length=255), nullable=True),
        sa.Column('processing_purpose', sa.Text(), nullable=True),
        sa.Column('data_categories', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('retention_period', sa.Integer(), nullable=True),
        sa.Column('expiry_date', sa.DateTime(), nullable=True),
        sa.Column('metadata', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.ForeignKeyConstraint(['workspace_id'], ['workspaces.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_compliance_logs_compliance_type'), 'compliance_logs', ['compliance_type'], unique=False)
    op.create_index(op.f('ix_compliance_logs_action_type'), 'compliance_logs', ['action_type'], unique=False)
    op.create_index(op.f('ix_compliance_logs_user_id'), 'compliance_logs', ['user_id'], unique=False)
    op.create_index(op.f('ix_compliance_logs_workspace_id'), 'compliance_logs', ['workspace_id'], unique=False)
    op.create_index(op.f('ix_compliance_logs_data_subject_id'), 'compliance_logs', ['data_subject_id'], unique=False)
    op.create_index(op.f('ix_compliance_logs_created_at'), 'compliance_logs', ['created_at'], unique=False)

    # Add GDPR-related columns to users table
    op.add_column('users', sa.Column('consent_marketing', sa.Boolean(), nullable=True, server_default='false'))
    op.add_column('users', sa.Column('consent_analytics', sa.Boolean(), nullable=True, server_default='false'))
    op.add_column('users', sa.Column('consent_third_party', sa.Boolean(), nullable=True, server_default='false'))
    op.add_column('users', sa.Column('consent_profiling', sa.Boolean(), nullable=True, server_default='false'))
    op.add_column('users', sa.Column('consent_updated_at', sa.DateTime(), nullable=True))
    op.add_column('users', sa.Column('deletion_requested_at', sa.DateTime(), nullable=True))
    op.add_column('users', sa.Column('deletion_scheduled_for', sa.DateTime(), nullable=True))
    op.add_column('users', sa.Column('is_anonymized', sa.Boolean(), nullable=True, server_default='false'))
    op.add_column('users', sa.Column('anonymized_at', sa.DateTime(), nullable=True))


def downgrade():
    # Remove columns from users table
    op.drop_column('users', 'anonymized_at')
    op.drop_column('users', 'is_anonymized')
    op.drop_column('users', 'deletion_scheduled_for')
    op.drop_column('users', 'deletion_requested_at')
    op.drop_column('users', 'consent_updated_at')
    op.drop_column('users', 'consent_profiling')
    op.drop_column('users', 'consent_third_party')
    op.drop_column('users', 'consent_analytics')
    op.drop_column('users', 'consent_marketing')

    # Drop compliance_logs table
    op.drop_index(op.f('ix_compliance_logs_created_at'), table_name='compliance_logs')
    op.drop_index(op.f('ix_compliance_logs_data_subject_id'), table_name='compliance_logs')
    op.drop_index(op.f('ix_compliance_logs_workspace_id'), table_name='compliance_logs')
    op.drop_index(op.f('ix_compliance_logs_user_id'), table_name='compliance_logs')
    op.drop_index(op.f('ix_compliance_logs_action_type'), table_name='compliance_logs')
    op.drop_index(op.f('ix_compliance_logs_compliance_type'), table_name='compliance_logs')
    op.drop_table('compliance_logs')

    # Drop data_access_logs table
    op.drop_index(op.f('ix_data_access_logs_created_at'), table_name='data_access_logs')
    op.drop_index(op.f('ix_data_access_logs_action'), table_name='data_access_logs')
    op.drop_index(op.f('ix_data_access_logs_resource_id'), table_name='data_access_logs')
    op.drop_index(op.f('ix_data_access_logs_resource_type'), table_name='data_access_logs')
    op.drop_index(op.f('ix_data_access_logs_workspace_id'), table_name='data_access_logs')
    op.drop_index(op.f('ix_data_access_logs_user_id'), table_name='data_access_logs')
    op.drop_table('data_access_logs')

    # Drop security_events table
    op.drop_index(op.f('ix_security_events_created_at'), table_name='security_events')
    op.drop_index(op.f('ix_security_events_ip_address'), table_name='security_events')
    op.drop_index(op.f('ix_security_events_severity'), table_name='security_events')
    op.drop_index(op.f('ix_security_events_workspace_id'), table_name='security_events')
    op.drop_index(op.f('ix_security_events_user_id'), table_name='security_events')
    op.drop_index(op.f('ix_security_events_event_type'), table_name='security_events')
    op.drop_table('security_events')

    # Drop audit_logs table
    op.drop_index('ix_audit_logs_user_date', table_name='audit_logs')
    op.drop_index('ix_audit_logs_workspace_date', table_name='audit_logs')
    op.drop_index(op.f('ix_audit_logs_request_id'), table_name='audit_logs')
    op.drop_index(op.f('ix_audit_logs_created_at'), table_name='audit_logs')
    op.drop_index(op.f('ix_audit_logs_resource_id'), table_name='audit_logs')
    op.drop_index(op.f('ix_audit_logs_resource_type'), table_name='audit_logs')
    op.drop_index(op.f('ix_audit_logs_action'), table_name='audit_logs')
    op.drop_index(op.f('ix_audit_logs_user_id'), table_name='audit_logs')
    op.drop_index(op.f('ix_audit_logs_workspace_id'), table_name='audit_logs')
    op.drop_table('audit_logs')

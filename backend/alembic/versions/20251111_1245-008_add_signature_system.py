"""Add digital signature system tables

Revision ID: 008
Revises: 007
Create Date: 2025-11-11 12:45:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '008'
down_revision: Union[str, None] = '007'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create digital signature system tables"""

    # Create signature_requests table
    op.create_table(
        'signature_requests',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('workspace_id', sa.Integer(), nullable=False),
        sa.Column('document_id', sa.Integer(), nullable=False),
        sa.Column('created_by_id', sa.Integer(), nullable=False),
        sa.Column('title', sa.String(length=255), nullable=False),
        sa.Column('message', sa.Text(), nullable=True),
        sa.Column('status', sa.String(length=50), nullable=False, server_default='draft'),
        sa.Column('signing_order', sa.String(length=50), nullable=False, server_default='parallel'),
        sa.Column('signed_document_id', sa.Integer(), nullable=True),
        sa.Column('expires_at', sa.DateTime(), nullable=True),
        sa.Column('completed_at', sa.DateTime(), nullable=True),
        sa.Column('require_all_signers', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('allow_decline', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('send_reminders', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('metadata', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.ForeignKeyConstraint(['workspace_id'], ['workspaces.id'], ),
        sa.ForeignKeyConstraint(['document_id'], ['documents.id'], ),
        sa.ForeignKeyConstraint(['created_by_id'], ['users.id'], ),
        sa.ForeignKeyConstraint(['signed_document_id'], ['documents.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_signature_requests_id'), 'signature_requests', ['id'], unique=False)
    op.create_index(op.f('ix_signature_requests_workspace_id'), 'signature_requests', ['workspace_id'], unique=False)
    op.create_index(op.f('ix_signature_requests_status'), 'signature_requests', ['status'], unique=False)

    # Create signers table
    op.create_table(
        'signers',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('signature_request_id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=True),
        sa.Column('email', sa.String(length=255), nullable=False),
        sa.Column('full_name', sa.String(length=255), nullable=False),
        sa.Column('role', sa.String(length=100), nullable=True),
        sa.Column('signing_order', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('status', sa.String(length=50), nullable=False, server_default='pending'),
        sa.Column('access_token', sa.String(length=255), nullable=True),
        sa.Column('access_expires_at', sa.DateTime(), nullable=True),
        sa.Column('notified_at', sa.DateTime(), nullable=True),
        sa.Column('viewed_at', sa.DateTime(), nullable=True),
        sa.Column('signed_at', sa.DateTime(), nullable=True),
        sa.Column('declined_at', sa.DateTime(), nullable=True),
        sa.Column('decline_reason', sa.Text(), nullable=True),
        sa.Column('ip_address', sa.String(length=45), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.ForeignKeyConstraint(['signature_request_id'], ['signature_requests.id'], ),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_signers_id'), 'signers', ['id'], unique=False)
    op.create_index(op.f('ix_signers_signature_request_id'), 'signers', ['signature_request_id'], unique=False)
    op.create_index(op.f('ix_signers_email'), 'signers', ['email'], unique=False)
    op.create_index(op.f('ix_signers_access_token'), 'signers', ['access_token'], unique=True)
    op.create_index(op.f('ix_signers_status'), 'signers', ['status'], unique=False)

    # Create signature_fields table
    op.create_table(
        'signature_fields',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('signature_request_id', sa.Integer(), nullable=False),
        sa.Column('signer_id', sa.Integer(), nullable=False),
        sa.Column('field_type', sa.String(length=50), nullable=False, server_default='signature'),
        sa.Column('label', sa.String(length=255), nullable=True),
        sa.Column('is_required', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('page_number', sa.Integer(), nullable=False),
        sa.Column('x_position', sa.Float(), nullable=False),
        sa.Column('y_position', sa.Float(), nullable=False),
        sa.Column('width', sa.Float(), nullable=False),
        sa.Column('height', sa.Float(), nullable=False),
        sa.Column('placeholder', sa.String(length=255), nullable=True),
        sa.Column('default_value', sa.String(length=500), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.ForeignKeyConstraint(['signature_request_id'], ['signature_requests.id'], ),
        sa.ForeignKeyConstraint(['signer_id'], ['signers.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_signature_fields_id'), 'signature_fields', ['id'], unique=False)
    op.create_index(op.f('ix_signature_fields_signature_request_id'), 'signature_fields', ['signature_request_id'], unique=False)
    op.create_index(op.f('ix_signature_fields_signer_id'), 'signature_fields', ['signer_id'], unique=False)

    # Create signatures table
    op.create_table(
        'signatures',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('signer_id', sa.Integer(), nullable=False),
        sa.Column('field_id', sa.Integer(), nullable=False),
        sa.Column('signature_type', sa.String(length=50), nullable=False),
        sa.Column('signature_data', sa.Text(), nullable=True),
        sa.Column('storage_path', sa.String(length=500), nullable=True),
        sa.Column('typed_text', sa.String(length=255), nullable=True),
        sa.Column('font_family', sa.String(length=100), nullable=True),
        sa.Column('ip_address', sa.String(length=45), nullable=True),
        sa.Column('user_agent', sa.String(length=500), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.ForeignKeyConstraint(['signer_id'], ['signers.id'], ),
        sa.ForeignKeyConstraint(['field_id'], ['signature_fields.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_signatures_id'), 'signatures', ['id'], unique=False)
    op.create_index(op.f('ix_signatures_signer_id'), 'signatures', ['signer_id'], unique=False)
    op.create_index(op.f('ix_signatures_field_id'), 'signatures', ['field_id'], unique=False)

    # Create signature_audit_logs table
    op.create_table(
        'signature_audit_logs',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('signature_request_id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=True),
        sa.Column('signer_id', sa.Integer(), nullable=True),
        sa.Column('action', sa.String(length=100), nullable=False),
        sa.Column('description', sa.Text(), nullable=False),
        sa.Column('ip_address', sa.String(length=45), nullable=True),
        sa.Column('user_agent', sa.String(length=500), nullable=True),
        sa.Column('metadata', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.ForeignKeyConstraint(['signature_request_id'], ['signature_requests.id'], ),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.ForeignKeyConstraint(['signer_id'], ['signers.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_signature_audit_logs_id'), 'signature_audit_logs', ['id'], unique=False)
    op.create_index(op.f('ix_signature_audit_logs_signature_request_id'), 'signature_audit_logs', ['signature_request_id'], unique=False)
    op.create_index(op.f('ix_signature_audit_logs_action'), 'signature_audit_logs', ['action'], unique=False)


def downgrade() -> None:
    """Drop digital signature system tables"""

    # Drop signature_audit_logs table
    op.drop_index(op.f('ix_signature_audit_logs_action'), table_name='signature_audit_logs')
    op.drop_index(op.f('ix_signature_audit_logs_signature_request_id'), table_name='signature_audit_logs')
    op.drop_index(op.f('ix_signature_audit_logs_id'), table_name='signature_audit_logs')
    op.drop_table('signature_audit_logs')

    # Drop signatures table
    op.drop_index(op.f('ix_signatures_field_id'), table_name='signatures')
    op.drop_index(op.f('ix_signatures_signer_id'), table_name='signatures')
    op.drop_index(op.f('ix_signatures_id'), table_name='signatures')
    op.drop_table('signatures')

    # Drop signature_fields table
    op.drop_index(op.f('ix_signature_fields_signer_id'), table_name='signature_fields')
    op.drop_index(op.f('ix_signature_fields_signature_request_id'), table_name='signature_fields')
    op.drop_index(op.f('ix_signature_fields_id'), table_name='signature_fields')
    op.drop_table('signature_fields')

    # Drop signers table
    op.drop_index(op.f('ix_signers_status'), table_name='signers')
    op.drop_index(op.f('ix_signers_access_token'), table_name='signers')
    op.drop_index(op.f('ix_signers_email'), table_name='signers')
    op.drop_index(op.f('ix_signers_signature_request_id'), table_name='signers')
    op.drop_index(op.f('ix_signers_id'), table_name='signers')
    op.drop_table('signers')

    # Drop signature_requests table
    op.drop_index(op.f('ix_signature_requests_status'), table_name='signature_requests')
    op.drop_index(op.f('ix_signature_requests_workspace_id'), table_name='signature_requests')
    op.drop_index(op.f('ix_signature_requests_id'), table_name='signature_requests')
    op.drop_table('signature_requests')

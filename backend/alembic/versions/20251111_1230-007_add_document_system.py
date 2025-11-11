"""Add document collaboration system tables

Revision ID: 007
Revises: 006
Create Date: 2025-11-11 12:30:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '007'
down_revision: Union[str, None] = '006'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create document collaboration tables"""

    # Create folders table
    op.create_table(
        'folders',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('workspace_id', sa.Integer(), nullable=False),
        sa.Column('parent_folder_id', sa.Integer(), nullable=True),
        sa.Column('created_by_id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('color', sa.String(length=7), nullable=True),
        sa.Column('is_deleted', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('deleted_at', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.ForeignKeyConstraint(['workspace_id'], ['workspaces.id'], ),
        sa.ForeignKeyConstraint(['parent_folder_id'], ['folders.id'], ),
        sa.ForeignKeyConstraint(['created_by_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_folders_id'), 'folders', ['id'], unique=False)
    op.create_index(op.f('ix_folders_workspace_id'), 'folders', ['workspace_id'], unique=False)
    op.create_index(op.f('ix_folders_is_deleted'), 'folders', ['is_deleted'], unique=False)

    # Create documents table
    op.create_table(
        'documents',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('workspace_id', sa.Integer(), nullable=False),
        sa.Column('folder_id', sa.Integer(), nullable=True),
        sa.Column('created_by_id', sa.Integer(), nullable=False),
        sa.Column('project_id', sa.Integer(), nullable=True),
        sa.Column('task_id', sa.Integer(), nullable=True),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('file_type', sa.String(length=50), nullable=False),
        sa.Column('mime_type', sa.String(length=100), nullable=False),
        sa.Column('file_size', sa.BigInteger(), nullable=False),
        sa.Column('current_version', sa.Integer(), nullable=False, server_default='1'),
        sa.Column('storage_path', sa.String(length=500), nullable=False),
        sa.Column('tags', sa.Text(), nullable=True),
        sa.Column('is_starred', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('is_deleted', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('deleted_at', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.ForeignKeyConstraint(['workspace_id'], ['workspaces.id'], ),
        sa.ForeignKeyConstraint(['folder_id'], ['folders.id'], ),
        sa.ForeignKeyConstraint(['created_by_id'], ['users.id'], ),
        sa.ForeignKeyConstraint(['project_id'], ['projects.id'], ),
        sa.ForeignKeyConstraint(['task_id'], ['tasks.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_documents_id'), 'documents', ['id'], unique=False)
    op.create_index(op.f('ix_documents_workspace_id'), 'documents', ['workspace_id'], unique=False)
    op.create_index(op.f('ix_documents_folder_id'), 'documents', ['folder_id'], unique=False)
    op.create_index(op.f('ix_documents_is_deleted'), 'documents', ['is_deleted'], unique=False)
    op.create_index(op.f('ix_documents_file_type'), 'documents', ['file_type'], unique=False)

    # Create document_versions table
    op.create_table(
        'document_versions',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('document_id', sa.Integer(), nullable=False),
        sa.Column('created_by_id', sa.Integer(), nullable=False),
        sa.Column('version_number', sa.Integer(), nullable=False),
        sa.Column('storage_path', sa.String(length=500), nullable=False),
        sa.Column('file_size', sa.BigInteger(), nullable=False),
        sa.Column('mime_type', sa.String(length=100), nullable=False),
        sa.Column('change_description', sa.Text(), nullable=True),
        sa.Column('is_current', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.ForeignKeyConstraint(['document_id'], ['documents.id'], ),
        sa.ForeignKeyConstraint(['created_by_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_document_versions_id'), 'document_versions', ['id'], unique=False)
    op.create_index(op.f('ix_document_versions_document_id'), 'document_versions', ['document_id'], unique=False)
    op.create_index(op.f('ix_document_versions_is_current'), 'document_versions', ['is_current'], unique=False)

    # Create document_shares table
    op.create_table(
        'document_shares',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('document_id', sa.Integer(), nullable=False),
        sa.Column('shared_by_id', sa.Integer(), nullable=False),
        sa.Column('shared_with_user_id', sa.Integer(), nullable=True),
        sa.Column('shared_with_team_id', sa.Integer(), nullable=True),
        sa.Column('permission', sa.String(length=50), nullable=False, server_default='view'),
        sa.Column('message', sa.Text(), nullable=True),
        sa.Column('expires_at', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.ForeignKeyConstraint(['document_id'], ['documents.id'], ),
        sa.ForeignKeyConstraint(['shared_by_id'], ['users.id'], ),
        sa.ForeignKeyConstraint(['shared_with_user_id'], ['users.id'], ),
        sa.ForeignKeyConstraint(['shared_with_team_id'], ['teams.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_document_shares_id'), 'document_shares', ['id'], unique=False)
    op.create_index(op.f('ix_document_shares_document_id'), 'document_shares', ['document_id'], unique=False)
    op.create_index(op.f('ix_document_shares_shared_with_user_id'), 'document_shares', ['shared_with_user_id'], unique=False)
    op.create_index(op.f('ix_document_shares_shared_with_team_id'), 'document_shares', ['shared_with_team_id'], unique=False)

    # Create document_comments table
    op.create_table(
        'document_comments',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('document_id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('parent_comment_id', sa.Integer(), nullable=True),
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('is_resolved', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('resolved_by_id', sa.Integer(), nullable=True),
        sa.Column('resolved_at', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.ForeignKeyConstraint(['document_id'], ['documents.id'], ),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.ForeignKeyConstraint(['parent_comment_id'], ['document_comments.id'], ),
        sa.ForeignKeyConstraint(['resolved_by_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_document_comments_id'), 'document_comments', ['id'], unique=False)
    op.create_index(op.f('ix_document_comments_document_id'), 'document_comments', ['document_id'], unique=False)
    op.create_index(op.f('ix_document_comments_is_resolved'), 'document_comments', ['is_resolved'], unique=False)


def downgrade() -> None:
    """Drop document collaboration tables"""

    # Drop document_comments table
    op.drop_index(op.f('ix_document_comments_is_resolved'), table_name='document_comments')
    op.drop_index(op.f('ix_document_comments_document_id'), table_name='document_comments')
    op.drop_index(op.f('ix_document_comments_id'), table_name='document_comments')
    op.drop_table('document_comments')

    # Drop document_shares table
    op.drop_index(op.f('ix_document_shares_shared_with_team_id'), table_name='document_shares')
    op.drop_index(op.f('ix_document_shares_shared_with_user_id'), table_name='document_shares')
    op.drop_index(op.f('ix_document_shares_document_id'), table_name='document_shares')
    op.drop_index(op.f('ix_document_shares_id'), table_name='document_shares')
    op.drop_table('document_shares')

    # Drop document_versions table
    op.drop_index(op.f('ix_document_versions_is_current'), table_name='document_versions')
    op.drop_index(op.f('ix_document_versions_document_id'), table_name='document_versions')
    op.drop_index(op.f('ix_document_versions_id'), table_name='document_versions')
    op.drop_table('document_versions')

    # Drop documents table
    op.drop_index(op.f('ix_documents_file_type'), table_name='documents')
    op.drop_index(op.f('ix_documents_is_deleted'), table_name='documents')
    op.drop_index(op.f('ix_documents_folder_id'), table_name='documents')
    op.drop_index(op.f('ix_documents_workspace_id'), table_name='documents')
    op.drop_index(op.f('ix_documents_id'), table_name='documents')
    op.drop_table('documents')

    # Drop folders table
    op.drop_index(op.f('ix_folders_is_deleted'), table_name='folders')
    op.drop_index(op.f('ix_folders_workspace_id'), table_name='folders')
    op.drop_index(op.f('ix_folders_id'), table_name='folders')
    op.drop_table('folders')

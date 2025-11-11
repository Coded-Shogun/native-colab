"""Add notification system tables

Revision ID: 006
Revises: 005
Create Date: 2025-11-11 12:15:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '006'
down_revision: Union[str, None] = '005'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create notification system tables"""

    # Create notifications table
    op.create_table(
        'notifications',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('notification_type', sa.String(length=50), nullable=False),
        sa.Column('priority', sa.String(length=50), nullable=False, server_default='normal'),
        sa.Column('title', sa.String(length=200), nullable=False),
        sa.Column('message', sa.Text(), nullable=False),
        sa.Column('action_url', sa.String(length=500), nullable=True),
        sa.Column('event_id', sa.Integer(), nullable=True),
        sa.Column('message_id', sa.Integer(), nullable=True),
        sa.Column('task_id', sa.Integer(), nullable=True),
        sa.Column('project_id', sa.Integer(), nullable=True),
        sa.Column('workspace_id', sa.Integer(), nullable=True),
        sa.Column('metadata', sa.JSON(), nullable=True),
        sa.Column('is_read', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('read_at', sa.DateTime(), nullable=True),
        sa.Column('sent_in_app', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('sent_email', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('sent_push', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.ForeignKeyConstraint(['event_id'], ['events.id'], ),
        sa.ForeignKeyConstraint(['message_id'], ['messages.id'], ),
        sa.ForeignKeyConstraint(['task_id'], ['tasks.id'], ),
        sa.ForeignKeyConstraint(['project_id'], ['projects.id'], ),
        sa.ForeignKeyConstraint(['workspace_id'], ['workspaces.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_notifications_id'), 'notifications', ['id'], unique=False)
    op.create_index(op.f('ix_notifications_user_id'), 'notifications', ['user_id'], unique=False)
    op.create_index(op.f('ix_notifications_is_read'), 'notifications', ['is_read'], unique=False)
    op.create_index(op.f('ix_notifications_created_at'), 'notifications', ['created_at'], unique=False)

    # Create notification_preferences table
    op.create_table(
        'notification_preferences',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('notification_type', sa.String(length=50), nullable=False),
        sa.Column('in_app_enabled', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('email_enabled', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('push_enabled', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('quiet_hours_start', sa.Integer(), nullable=True),
        sa.Column('quiet_hours_end', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_notification_preferences_id'), 'notification_preferences', ['id'], unique=False)
    op.create_index(op.f('ix_notification_preferences_user_id'), 'notification_preferences', ['user_id'], unique=False)
    # Unique constraint: user can only have one preference per notification type
    op.create_index(
        op.f('ix_notification_preferences_user_type'),
        'notification_preferences',
        ['user_id', 'notification_type'],
        unique=True
    )


def downgrade() -> None:
    """Drop notification system tables"""

    # Drop notification_preferences table
    op.drop_index(op.f('ix_notification_preferences_user_type'), table_name='notification_preferences')
    op.drop_index(op.f('ix_notification_preferences_user_id'), table_name='notification_preferences')
    op.drop_index(op.f('ix_notification_preferences_id'), table_name='notification_preferences')
    op.drop_table('notification_preferences')

    # Drop notifications table
    op.drop_index(op.f('ix_notifications_created_at'), table_name='notifications')
    op.drop_index(op.f('ix_notifications_is_read'), table_name='notifications')
    op.drop_index(op.f('ix_notifications_user_id'), table_name='notifications')
    op.drop_index(op.f('ix_notifications_id'), table_name='notifications')
    op.drop_table('notifications')

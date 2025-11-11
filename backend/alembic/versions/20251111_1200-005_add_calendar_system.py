"""Add calendar system tables

Revision ID: 005
Revises: 004
Create Date: 2025-11-11 12:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '005'
down_revision: Union[str, None] = '004'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create calendar system tables"""

    # Create calendars table
    op.create_table(
        'calendars',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('owner_id', sa.Integer(), nullable=True),
        sa.Column('workspace_id', sa.Integer(), nullable=True),
        sa.Column('name', sa.String(length=200), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('color', sa.String(length=7), nullable=False, server_default='#3B82F6'),
        sa.Column('timezone', sa.String(length=50), nullable=False, server_default='UTC'),
        sa.Column('is_default', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('is_public', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.ForeignKeyConstraint(['owner_id'], ['users.id'], ),
        sa.ForeignKeyConstraint(['workspace_id'], ['workspaces.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_calendars_id'), 'calendars', ['id'], unique=False)

    # Create events table
    op.create_table(
        'events',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('calendar_id', sa.Integer(), nullable=False),
        sa.Column('created_by_id', sa.Integer(), nullable=False),
        sa.Column('project_id', sa.Integer(), nullable=True),
        sa.Column('task_id', sa.Integer(), nullable=True),
        sa.Column('title', sa.String(length=500), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('location', sa.String(length=500), nullable=True),
        sa.Column('event_type', sa.String(length=50), nullable=False, server_default='meeting'),
        sa.Column('visibility', sa.String(length=50), nullable=False, server_default='workspace'),
        sa.Column('start_time', sa.DateTime(), nullable=False),
        sa.Column('end_time', sa.DateTime(), nullable=False),
        sa.Column('is_all_day', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('timezone', sa.String(length=50), nullable=False, server_default='UTC'),
        sa.Column('recurrence_rule', sa.Text(), nullable=True),
        sa.Column('color', sa.String(length=7), nullable=True),
        sa.Column('is_cancelled', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.ForeignKeyConstraint(['calendar_id'], ['calendars.id'], ),
        sa.ForeignKeyConstraint(['created_by_id'], ['users.id'], ),
        sa.ForeignKeyConstraint(['project_id'], ['projects.id'], ),
        sa.ForeignKeyConstraint(['task_id'], ['tasks.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_events_id'), 'events', ['id'], unique=False)
    op.create_index(op.f('ix_events_calendar_id'), 'events', ['calendar_id'], unique=False)
    op.create_index(op.f('ix_events_start_time'), 'events', ['start_time'], unique=False)
    op.create_index(op.f('ix_events_end_time'), 'events', ['end_time'], unique=False)

    # Create event_attendees table
    op.create_table(
        'event_attendees',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('event_id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('rsvp_status', sa.String(length=50), nullable=False, server_default='pending'),
        sa.Column('is_organizer', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('is_optional', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('comment', sa.Text(), nullable=True),
        sa.Column('responded_at', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.ForeignKeyConstraint(['event_id'], ['events.id'], ),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_event_attendees_id'), 'event_attendees', ['id'], unique=False)
    op.create_index(op.f('ix_event_attendees_event_id'), 'event_attendees', ['event_id'], unique=False)
    op.create_index(op.f('ix_event_attendees_user_id'), 'event_attendees', ['user_id'], unique=False)

    # Create event_reminders table
    op.create_table(
        'event_reminders',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('event_id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('reminder_type', sa.String(length=50), nullable=False, server_default='email'),
        sa.Column('minutes_before', sa.Integer(), nullable=False),
        sa.Column('is_sent', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('sent_at', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.ForeignKeyConstraint(['event_id'], ['events.id'], ),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_event_reminders_id'), 'event_reminders', ['id'], unique=False)
    op.create_index(op.f('ix_event_reminders_event_id'), 'event_reminders', ['event_id'], unique=False)


def downgrade() -> None:
    """Drop calendar system tables"""

    # Drop event_reminders table
    op.drop_index(op.f('ix_event_reminders_event_id'), table_name='event_reminders')
    op.drop_index(op.f('ix_event_reminders_id'), table_name='event_reminders')
    op.drop_table('event_reminders')

    # Drop event_attendees table
    op.drop_index(op.f('ix_event_attendees_user_id'), table_name='event_attendees')
    op.drop_index(op.f('ix_event_attendees_event_id'), table_name='event_attendees')
    op.drop_index(op.f('ix_event_attendees_id'), table_name='event_attendees')
    op.drop_table('event_attendees')

    # Drop events table
    op.drop_index(op.f('ix_events_end_time'), table_name='events')
    op.drop_index(op.f('ix_events_start_time'), table_name='events')
    op.drop_index(op.f('ix_events_calendar_id'), table_name='events')
    op.drop_index(op.f('ix_events_id'), table_name='events')
    op.drop_table('events')

    # Drop calendars table
    op.drop_index(op.f('ix_calendars_id'), table_name='calendars')
    op.drop_table('calendars')

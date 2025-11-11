"""add meeting system

Revision ID: 010_add_meeting_system
Revises: 009_add_whiteboard_system
Create Date: 2025-11-11 14:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '010_add_meeting_system'
down_revision = '009_add_whiteboard_system'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create enum types
    op.execute("""
        CREATE TYPE meetingtype AS ENUM ('instant', 'scheduled', 'recurring');
        CREATE TYPE meetingstatus AS ENUM ('scheduled', 'waiting', 'in_progress', 'ended', 'cancelled');
        CREATE TYPE participantrole AS ENUM ('host', 'co_host', 'attendee');
        CREATE TYPE participantstatus AS ENUM ('invited', 'waiting', 'joined', 'left', 'removed');
        CREATE TYPE recordingstatus AS ENUM ('recording', 'processing', 'ready', 'failed');
    """)

    # Create meetings table
    op.create_table(
        'meetings',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('workspace_id', sa.Integer(), nullable=False),
        sa.Column('created_by_id', sa.Integer(), nullable=False),
        sa.Column('project_id', sa.Integer(), nullable=True),
        sa.Column('event_id', sa.Integer(), nullable=True),
        sa.Column('whiteboard_id', sa.Integer(), nullable=True),

        # Meeting details
        sa.Column('title', sa.String(length=255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('meeting_type', sa.Enum('instant', 'scheduled', 'recurring', name='meetingtype'), nullable=False),
        sa.Column('status', sa.Enum('scheduled', 'waiting', 'in_progress', 'ended', 'cancelled', name='meetingstatus'), nullable=False),

        # Scheduling
        sa.Column('scheduled_start_time', sa.DateTime(), nullable=True),
        sa.Column('scheduled_end_time', sa.DateTime(), nullable=True),
        sa.Column('actual_start_time', sa.DateTime(), nullable=True),
        sa.Column('actual_end_time', sa.DateTime(), nullable=True),
        sa.Column('duration_minutes', sa.Integer(), nullable=True),

        # Meeting room settings
        sa.Column('meeting_url', sa.String(length=500), nullable=True),
        sa.Column('meeting_passcode', sa.String(length=50), nullable=True),
        sa.Column('waiting_room_enabled', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('mute_on_join', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('video_on_join', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('allow_screen_share', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('allow_chat', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('allow_recording', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('max_participants', sa.Integer(), nullable=False, server_default='100'),

        # Recording settings
        sa.Column('auto_record', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('is_recording', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('record_audio', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('record_video', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('record_screen_share', sa.Boolean(), nullable=False, server_default='true'),

        # Access control
        sa.Column('is_public', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('require_authentication', sa.Boolean(), nullable=False, server_default='true'),

        # Meeting metadata
        sa.Column('total_participants', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('peak_participants', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('total_duration_seconds', sa.Integer(), nullable=False, server_default='0'),

        # Timestamps
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),

        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['workspace_id'], ['workspaces.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['created_by_id'], ['users.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['project_id'], ['projects.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['event_id'], ['events.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['whiteboard_id'], ['whiteboards.id'], ondelete='SET NULL'),
    )
    op.create_index('ix_meetings_id', 'meetings', ['id'])
    op.create_index('ix_meetings_workspace_id', 'meetings', ['workspace_id'])
    op.create_index('ix_meetings_status', 'meetings', ['status'])
    op.create_index('ix_meetings_scheduled_start_time', 'meetings', ['scheduled_start_time'])

    # Create meeting_participants table
    op.create_table(
        'meeting_participants',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('meeting_id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=True),

        # Participant info (for guests)
        sa.Column('guest_name', sa.String(length=255), nullable=True),
        sa.Column('guest_email', sa.String(length=255), nullable=True),

        # Role and status
        sa.Column('role', sa.Enum('host', 'co_host', 'attendee', name='participantrole'), nullable=False),
        sa.Column('status', sa.Enum('invited', 'waiting', 'joined', 'left', 'removed', name='participantstatus'), nullable=False),

        # Media state
        sa.Column('is_audio_enabled', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('is_video_enabled', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('is_screen_sharing', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('is_hand_raised', sa.Boolean(), nullable=False, server_default='false'),

        # Connection info
        sa.Column('connection_id', sa.String(length=100), nullable=True),
        sa.Column('peer_id', sa.String(length=100), nullable=True),
        sa.Column('connection_quality', sa.String(length=20), nullable=True),

        # Permissions
        sa.Column('can_speak', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('can_share_screen', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('can_chat', sa.Boolean(), nullable=False, server_default='true'),

        # Timestamps
        sa.Column('invited_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('joined_at', sa.DateTime(), nullable=True),
        sa.Column('left_at', sa.DateTime(), nullable=True),
        sa.Column('total_duration_seconds', sa.Integer(), nullable=False, server_default='0'),

        # IP and device info
        sa.Column('ip_address', sa.String(length=45), nullable=True),
        sa.Column('user_agent', sa.Text(), nullable=True),
        sa.Column('device_type', sa.String(length=50), nullable=True),

        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['meeting_id'], ['meetings.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='SET NULL'),
    )
    op.create_index('ix_meeting_participants_id', 'meeting_participants', ['id'])
    op.create_index('ix_meeting_participants_meeting_id', 'meeting_participants', ['meeting_id'])
    op.create_index('ix_meeting_participants_user_id', 'meeting_participants', ['user_id'])
    op.create_index('ix_meeting_participants_status', 'meeting_participants', ['status'])

    # Create meeting_recordings table
    op.create_table(
        'meeting_recordings',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('meeting_id', sa.Integer(), nullable=False),
        sa.Column('started_by_id', sa.Integer(), nullable=False),

        # Recording details
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),

        # Recording metadata
        sa.Column('file_size', sa.BigInteger(), nullable=True),
        sa.Column('duration_seconds', sa.Integer(), nullable=True),
        sa.Column('format', sa.String(length=50), nullable=False, server_default='webm'),
        sa.Column('resolution', sa.String(length=20), nullable=True),

        # Storage
        sa.Column('storage_path', sa.String(length=500), nullable=True),
        sa.Column('thumbnail_path', sa.String(length=500), nullable=True),

        # Processing
        sa.Column('status', sa.Enum('recording', 'processing', 'ready', 'failed', name='recordingstatus'), nullable=False),
        sa.Column('processing_error', sa.Text(), nullable=True),

        # Access control
        sa.Column('is_public', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('is_downloadable', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('password_protected', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('access_password', sa.String(length=255), nullable=True),

        # Transcript
        sa.Column('has_transcript', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('transcript_path', sa.String(length=500), nullable=True),

        # Statistics
        sa.Column('view_count', sa.Integer(), nullable=False, server_default='0'),

        # Timestamps
        sa.Column('recording_started_at', sa.DateTime(), nullable=True),
        sa.Column('recording_ended_at', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),

        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['meeting_id'], ['meetings.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['started_by_id'], ['users.id'], ondelete='CASCADE'),
    )
    op.create_index('ix_meeting_recordings_id', 'meeting_recordings', ['id'])
    op.create_index('ix_meeting_recordings_meeting_id', 'meeting_recordings', ['meeting_id'])
    op.create_index('ix_meeting_recordings_status', 'meeting_recordings', ['status'])

    # Create meeting_chat_messages table
    op.create_table(
        'meeting_chat_messages',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('meeting_id', sa.Integer(), nullable=False),
        sa.Column('sender_id', sa.Integer(), nullable=True),

        # Message content
        sa.Column('message', sa.Text(), nullable=False),
        sa.Column('message_type', sa.String(length=50), nullable=False, server_default='text'),

        # Message metadata
        sa.Column('is_private', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('recipient_id', sa.Integer(), nullable=True),

        # Attachments
        sa.Column('attachment_url', sa.String(length=500), nullable=True),
        sa.Column('attachment_name', sa.String(length=255), nullable=True),
        sa.Column('attachment_size', sa.BigInteger(), nullable=True),

        # Timestamps
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('edited_at', sa.DateTime(), nullable=True),
        sa.Column('is_deleted', sa.Boolean(), nullable=False, server_default='false'),

        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['meeting_id'], ['meetings.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['sender_id'], ['users.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['recipient_id'], ['users.id'], ondelete='SET NULL'),
    )
    op.create_index('ix_meeting_chat_messages_id', 'meeting_chat_messages', ['id'])
    op.create_index('ix_meeting_chat_messages_meeting_id', 'meeting_chat_messages', ['meeting_id'])
    op.create_index('ix_meeting_chat_messages_created_at', 'meeting_chat_messages', ['created_at'])


def downgrade() -> None:
    # Drop tables
    op.drop_index('ix_meeting_chat_messages_created_at', table_name='meeting_chat_messages')
    op.drop_index('ix_meeting_chat_messages_meeting_id', table_name='meeting_chat_messages')
    op.drop_index('ix_meeting_chat_messages_id', table_name='meeting_chat_messages')
    op.drop_table('meeting_chat_messages')

    op.drop_index('ix_meeting_recordings_status', table_name='meeting_recordings')
    op.drop_index('ix_meeting_recordings_meeting_id', table_name='meeting_recordings')
    op.drop_index('ix_meeting_recordings_id', table_name='meeting_recordings')
    op.drop_table('meeting_recordings')

    op.drop_index('ix_meeting_participants_status', table_name='meeting_participants')
    op.drop_index('ix_meeting_participants_user_id', table_name='meeting_participants')
    op.drop_index('ix_meeting_participants_meeting_id', table_name='meeting_participants')
    op.drop_index('ix_meeting_participants_id', table_name='meeting_participants')
    op.drop_table('meeting_participants')

    op.drop_index('ix_meetings_scheduled_start_time', table_name='meetings')
    op.drop_index('ix_meetings_status', table_name='meetings')
    op.drop_index('ix_meetings_workspace_id', table_name='meetings')
    op.drop_index('ix_meetings_id', table_name='meetings')
    op.drop_table('meetings')

    # Drop enum types
    op.execute('DROP TYPE recordingstatus')
    op.execute('DROP TYPE participantstatus')
    op.execute('DROP TYPE participantrole')
    op.execute('DROP TYPE meetingstatus')
    op.execute('DROP TYPE meetingtype')

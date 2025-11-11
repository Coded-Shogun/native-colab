"""Add collaborative whiteboard system tables

Revision ID: 009
Revises: 008
Create Date: 2025-11-11 13:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '009'
down_revision: Union[str, None] = '008'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create collaborative whiteboard system tables"""

    # Create whiteboards table
    op.create_table(
        'whiteboards',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('workspace_id', sa.Integer(), nullable=False),
        sa.Column('created_by_id', sa.Integer(), nullable=False),
        sa.Column('project_id', sa.Integer(), nullable=True),
        sa.Column('meeting_id', sa.Integer(), nullable=True),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('canvas_width', sa.Integer(), nullable=False, server_default='3000'),
        sa.Column('canvas_height', sa.Integer(), nullable=False, server_default='2000'),
        sa.Column('background_color', sa.String(length=7), nullable=False, server_default='#FFFFFF'),
        sa.Column('grid_enabled', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('is_public', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('is_locked', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('is_template', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('thumbnail_url', sa.String(length=500), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.Column('last_activity_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.ForeignKeyConstraint(['workspace_id'], ['workspaces.id'], ),
        sa.ForeignKeyConstraint(['created_by_id'], ['users.id'], ),
        sa.ForeignKeyConstraint(['project_id'], ['projects.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_whiteboards_id'), 'whiteboards', ['id'], unique=False)
    op.create_index(op.f('ix_whiteboards_workspace_id'), 'whiteboards', ['workspace_id'], unique=False)
    op.create_index(op.f('ix_whiteboards_last_activity_at'), 'whiteboards', ['last_activity_at'], unique=False)

    # Create whiteboard_elements table
    op.create_table(
        'whiteboard_elements',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('whiteboard_id', sa.Integer(), nullable=False),
        sa.Column('created_by_id', sa.Integer(), nullable=False),
        sa.Column('element_id', sa.String(length=100), nullable=False),
        sa.Column('element_type', sa.String(length=50), nullable=False),
        sa.Column('x_position', sa.Float(), nullable=False),
        sa.Column('y_position', sa.Float(), nullable=False),
        sa.Column('width', sa.Float(), nullable=True),
        sa.Column('height', sa.Float(), nullable=True),
        sa.Column('stroke_color', sa.String(length=7), nullable=False, server_default='#000000'),
        sa.Column('fill_color', sa.String(length=7), nullable=True),
        sa.Column('stroke_width', sa.Float(), nullable=False, server_default='2.0'),
        sa.Column('opacity', sa.Float(), nullable=False, server_default='1.0'),
        sa.Column('element_data', sa.JSON(), nullable=False),
        sa.Column('z_index', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('is_locked', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('is_deleted', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.ForeignKeyConstraint(['whiteboard_id'], ['whiteboards.id'], ),
        sa.ForeignKeyConstraint(['created_by_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_whiteboard_elements_id'), 'whiteboard_elements', ['id'], unique=False)
    op.create_index(op.f('ix_whiteboard_elements_whiteboard_id'), 'whiteboard_elements', ['whiteboard_id'], unique=False)
    op.create_index(op.f('ix_whiteboard_elements_element_id'), 'whiteboard_elements', ['element_id'], unique=False)
    op.create_index(op.f('ix_whiteboard_elements_is_deleted'), 'whiteboard_elements', ['is_deleted'], unique=False)

    # Create whiteboard_participants table
    op.create_table(
        'whiteboard_participants',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('whiteboard_id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('access_level', sa.String(length=50), nullable=False, server_default='edit'),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('last_seen_at', sa.DateTime(), nullable=True),
        sa.Column('cursor_x', sa.Float(), nullable=True),
        sa.Column('cursor_y', sa.Float(), nullable=True),
        sa.Column('selected_element_id', sa.String(length=100), nullable=True),
        sa.Column('joined_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.ForeignKeyConstraint(['whiteboard_id'], ['whiteboards.id'], ),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_whiteboard_participants_id'), 'whiteboard_participants', ['id'], unique=False)
    op.create_index(op.f('ix_whiteboard_participants_whiteboard_id'), 'whiteboard_participants', ['whiteboard_id'], unique=False)
    op.create_index(op.f('ix_whiteboard_participants_user_id'), 'whiteboard_participants', ['user_id'], unique=False)
    op.create_index(op.f('ix_whiteboard_participants_is_active'), 'whiteboard_participants', ['is_active'], unique=False)
    # Unique constraint: user can only participate once per whiteboard
    op.create_index(
        op.f('ix_whiteboard_participants_unique'),
        'whiteboard_participants',
        ['whiteboard_id', 'user_id'],
        unique=True
    )

    # Create whiteboard_snapshots table
    op.create_table(
        'whiteboard_snapshots',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('whiteboard_id', sa.Integer(), nullable=False),
        sa.Column('created_by_id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('elements_data', sa.JSON(), nullable=False),
        sa.Column('canvas_settings', sa.JSON(), nullable=False),
        sa.Column('thumbnail_url', sa.String(length=500), nullable=True),
        sa.Column('is_auto_save', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.ForeignKeyConstraint(['whiteboard_id'], ['whiteboards.id'], ),
        sa.ForeignKeyConstraint(['created_by_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_whiteboard_snapshots_id'), 'whiteboard_snapshots', ['id'], unique=False)
    op.create_index(op.f('ix_whiteboard_snapshots_whiteboard_id'), 'whiteboard_snapshots', ['whiteboard_id'], unique=False)


def downgrade() -> None:
    """Drop collaborative whiteboard system tables"""

    # Drop whiteboard_snapshots table
    op.drop_index(op.f('ix_whiteboard_snapshots_whiteboard_id'), table_name='whiteboard_snapshots')
    op.drop_index(op.f('ix_whiteboard_snapshots_id'), table_name='whiteboard_snapshots')
    op.drop_table('whiteboard_snapshots')

    # Drop whiteboard_participants table
    op.drop_index(op.f('ix_whiteboard_participants_unique'), table_name='whiteboard_participants')
    op.drop_index(op.f('ix_whiteboard_participants_is_active'), table_name='whiteboard_participants')
    op.drop_index(op.f('ix_whiteboard_participants_user_id'), table_name='whiteboard_participants')
    op.drop_index(op.f('ix_whiteboard_participants_whiteboard_id'), table_name='whiteboard_participants')
    op.drop_index(op.f('ix_whiteboard_participants_id'), table_name='whiteboard_participants')
    op.drop_table('whiteboard_participants')

    # Drop whiteboard_elements table
    op.drop_index(op.f('ix_whiteboard_elements_is_deleted'), table_name='whiteboard_elements')
    op.drop_index(op.f('ix_whiteboard_elements_element_id'), table_name='whiteboard_elements')
    op.drop_index(op.f('ix_whiteboard_elements_whiteboard_id'), table_name='whiteboard_elements')
    op.drop_index(op.f('ix_whiteboard_elements_id'), table_name='whiteboard_elements')
    op.drop_table('whiteboard_elements')

    # Drop whiteboards table
    op.drop_index(op.f('ix_whiteboards_last_activity_at'), table_name='whiteboards')
    op.drop_index(op.f('ix_whiteboards_workspace_id'), table_name='whiteboards')
    op.drop_index(op.f('ix_whiteboards_id'), table_name='whiteboards')
    op.drop_table('whiteboards')

"""Add time tracking tables

Revision ID: 003
Revises: 002
Create Date: 2025-11-11 10:45:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '003'
down_revision: Union[str, None] = '002'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create time tracking tables"""

    # Create time_entries table
    op.create_table(
        'time_entries',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('workspace_id', sa.Integer(), nullable=False),
        sa.Column('project_id', sa.Integer(), nullable=True),
        sa.Column('task_id', sa.Integer(), nullable=True),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('start_time', sa.DateTime(), nullable=False),
        sa.Column('end_time', sa.DateTime(), nullable=True),
        sa.Column('duration_minutes', sa.Numeric(precision=10, scale=2), nullable=True),
        sa.Column('is_billable', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('is_manual', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.ForeignKeyConstraint(['workspace_id'], ['workspaces.id'], ),
        sa.ForeignKeyConstraint(['project_id'], ['projects.id'], ),
        sa.ForeignKeyConstraint(['task_id'], ['tasks.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_time_entries_id'), 'time_entries', ['id'], unique=False)
    op.create_index(op.f('ix_time_entries_user_id'), 'time_entries', ['user_id'], unique=False)
    op.create_index(op.f('ix_time_entries_workspace_id'), 'time_entries', ['workspace_id'], unique=False)
    op.create_index(op.f('ix_time_entries_project_id'), 'time_entries', ['project_id'], unique=False)
    op.create_index(op.f('ix_time_entries_task_id'), 'time_entries', ['task_id'], unique=False)
    op.create_index(op.f('ix_time_entries_start_time'), 'time_entries', ['start_time'], unique=False)


def downgrade() -> None:
    """Drop time tracking tables"""

    # Drop time_entries table
    op.drop_index(op.f('ix_time_entries_start_time'), table_name='time_entries')
    op.drop_index(op.f('ix_time_entries_task_id'), table_name='time_entries')
    op.drop_index(op.f('ix_time_entries_project_id'), table_name='time_entries')
    op.drop_index(op.f('ix_time_entries_workspace_id'), table_name='time_entries')
    op.drop_index(op.f('ix_time_entries_user_id'), table_name='time_entries')
    op.drop_index(op.f('ix_time_entries_id'), table_name='time_entries')
    op.drop_table('time_entries')

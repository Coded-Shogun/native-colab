"""add search system

Revision ID: 011_add_search_system
Revises: 010_add_meeting_system
Create Date: 2025-11-11 15:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '011_add_search_system'
down_revision = '010_add_meeting_system'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create content type enum
    op.execute("""
        CREATE TYPE contenttype AS ENUM (
            'message', 'document', 'task', 'event',
            'whiteboard', 'meeting', 'project', 'folder', 'comment'
        );
    """)

    # Create search_indexes table
    op.create_table(
        'search_indexes',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('content_type', sa.Enum(
            'message', 'document', 'task', 'event',
            'whiteboard', 'meeting', 'project', 'folder', 'comment',
            name='contenttype'
        ), nullable=False),
        sa.Column('content_id', sa.Integer(), nullable=False),

        # Context
        sa.Column('workspace_id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=True),
        sa.Column('project_id', sa.Integer(), nullable=True),

        # Searchable content
        sa.Column('title', sa.String(length=500), nullable=False),
        sa.Column('content', sa.Text(), nullable=False),

        # Full-text search vector
        sa.Column('search_vector', postgresql.TSVECTOR(), nullable=True),

        # Metadata
        sa.Column('metadata', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('tags', postgresql.JSON(astext_type=sa.Text()), nullable=True),

        # Access control
        sa.Column('is_public', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('is_deleted', sa.Boolean(), nullable=False, server_default='false'),

        # Timestamps
        sa.Column('content_created_at', sa.DateTime(), nullable=False),
        sa.Column('content_updated_at', sa.DateTime(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),

        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['workspace_id'], ['workspaces.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['project_id'], ['projects.id'], ondelete='CASCADE'),
    )

    # Create indexes
    op.create_index('ix_search_indexes_id', 'search_indexes', ['id'])
    op.create_index('ix_search_indexes_content_type', 'search_indexes', ['content_type'])
    op.create_index('ix_search_indexes_workspace_id', 'search_indexes', ['workspace_id'])
    op.create_index('ix_search_indexes_user_id', 'search_indexes', ['user_id'])
    op.create_index('ix_search_indexes_project_id', 'search_indexes', ['project_id'])
    op.create_index('ix_search_indexes_content_created_at', 'search_indexes', ['content_created_at'])

    # Create composite indexes
    op.create_index(
        'ix_search_indexes_composite',
        'search_indexes',
        ['workspace_id', 'content_type', 'is_deleted']
    )
    op.create_index(
        'ix_search_indexes_project_type',
        'search_indexes',
        ['project_id', 'content_type']
    )
    op.create_index(
        'ix_search_indexes_user_type',
        'search_indexes',
        ['user_id', 'content_type']
    )

    # Create GIN index for full-text search
    op.create_index(
        'ix_search_indexes_search_vector',
        'search_indexes',
        ['search_vector'],
        postgresql_using='gin'
    )

    # Create trigger to automatically update search_vector
    op.execute("""
        CREATE FUNCTION search_indexes_trigger() RETURNS trigger AS $$
        BEGIN
            NEW.search_vector :=
                setweight(to_tsvector('english', coalesce(NEW.title, '')), 'A') ||
                setweight(to_tsvector('english', coalesce(NEW.content, '')), 'B');
            RETURN NEW;
        END
        $$ LANGUAGE plpgsql;

        CREATE TRIGGER tsvector_update BEFORE INSERT OR UPDATE
        ON search_indexes FOR EACH ROW EXECUTE FUNCTION search_indexes_trigger();
    """)

    # Create search_history table
    op.create_table(
        'search_history',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('workspace_id', sa.Integer(), nullable=False),

        # Search query
        sa.Column('query', sa.String(length=500), nullable=False),
        sa.Column('filters', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('content_types', postgresql.JSON(astext_type=sa.Text()), nullable=True),

        # Results
        sa.Column('results_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('clicked_content_type', sa.String(length=50), nullable=True),
        sa.Column('clicked_content_id', sa.Integer(), nullable=True),

        # Performance
        sa.Column('search_duration_ms', sa.Integer(), nullable=True),

        # IP and device
        sa.Column('ip_address', sa.String(length=45), nullable=True),
        sa.Column('user_agent', sa.Text(), nullable=True),

        # Timestamp
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),

        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['workspace_id'], ['workspaces.id'], ondelete='CASCADE'),
    )

    # Create indexes
    op.create_index('ix_search_history_id', 'search_history', ['id'])
    op.create_index('ix_search_history_user_id', 'search_history', ['user_id'])
    op.create_index('ix_search_history_workspace_id', 'search_history', ['workspace_id'])
    op.create_index('ix_search_history_query', 'search_history', ['query'])
    op.create_index('ix_search_history_created_at', 'search_history', ['created_at'])
    op.create_index(
        'ix_search_history_user_workspace',
        'search_history',
        ['user_id', 'workspace_id', 'created_at']
    )

    # Create saved_searches table
    op.create_table(
        'saved_searches',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('workspace_id', sa.Integer(), nullable=False),

        # Search details
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('query', sa.String(length=500), nullable=False),
        sa.Column('filters', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('content_types', postgresql.JSON(astext_type=sa.Text()), nullable=True),

        # Settings
        sa.Column('is_default', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('is_shared', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('notify_on_new_results', sa.Boolean(), nullable=False, server_default='false'),

        # Usage statistics
        sa.Column('use_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('last_used_at', sa.DateTime(), nullable=True),

        # Timestamps
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),

        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['workspace_id'], ['workspaces.id'], ondelete='CASCADE'),
    )

    # Create indexes
    op.create_index('ix_saved_searches_id', 'saved_searches', ['id'])
    op.create_index('ix_saved_searches_user_id', 'saved_searches', ['user_id'])
    op.create_index('ix_saved_searches_workspace_id', 'saved_searches', ['workspace_id'])
    op.create_index(
        'ix_saved_searches_user_workspace',
        'saved_searches',
        ['user_id', 'workspace_id']
    )


def downgrade() -> None:
    # Drop saved_searches table
    op.drop_index('ix_saved_searches_user_workspace', table_name='saved_searches')
    op.drop_index('ix_saved_searches_workspace_id', table_name='saved_searches')
    op.drop_index('ix_saved_searches_user_id', table_name='saved_searches')
    op.drop_index('ix_saved_searches_id', table_name='saved_searches')
    op.drop_table('saved_searches')

    # Drop search_history table
    op.drop_index('ix_search_history_user_workspace', table_name='search_history')
    op.drop_index('ix_search_history_created_at', table_name='search_history')
    op.drop_index('ix_search_history_query', table_name='search_history')
    op.drop_index('ix_search_history_workspace_id', table_name='search_history')
    op.drop_index('ix_search_history_user_id', table_name='search_history')
    op.drop_index('ix_search_history_id', table_name='search_history')
    op.drop_table('search_history')

    # Drop trigger and function
    op.execute("""
        DROP TRIGGER IF EXISTS tsvector_update ON search_indexes;
        DROP FUNCTION IF EXISTS search_indexes_trigger();
    """)

    # Drop search_indexes table
    op.drop_index('ix_search_indexes_search_vector', table_name='search_indexes')
    op.drop_index('ix_search_indexes_user_type', table_name='search_indexes')
    op.drop_index('ix_search_indexes_project_type', table_name='search_indexes')
    op.drop_index('ix_search_indexes_composite', table_name='search_indexes')
    op.drop_index('ix_search_indexes_content_created_at', table_name='search_indexes')
    op.drop_index('ix_search_indexes_project_id', table_name='search_indexes')
    op.drop_index('ix_search_indexes_user_id', table_name='search_indexes')
    op.drop_index('ix_search_indexes_workspace_id', table_name='search_indexes')
    op.drop_index('ix_search_indexes_content_type', table_name='search_indexes')
    op.drop_index('ix_search_indexes_id', table_name='search_indexes')
    op.drop_table('search_indexes')

    # Drop enum type
    op.execute('DROP TYPE contenttype')

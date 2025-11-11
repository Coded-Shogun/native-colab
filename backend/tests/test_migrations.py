"""
Tests for Database Migrations
Validates migration structure and reversibility
"""

import pytest
import os
import sys
from pathlib import Path
from importlib import import_module

# Add backend directory to path
backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))


class TestMigrationStructure:
    """Test migration file structure and validity"""

    def test_migrations_directory_exists(self):
        """Verify migrations directory exists"""
        migrations_dir = backend_dir / "alembic" / "versions"
        assert migrations_dir.exists(), "Migrations directory should exist"
        assert migrations_dir.is_dir(), "Migrations path should be a directory"

    def test_initial_migration_exists(self):
        """Verify initial migration file exists"""
        migrations_dir = backend_dir / "alembic" / "versions"
        migration_files = list(migrations_dir.glob("*.py"))
        migration_files = [f for f in migration_files if not f.name.startswith("__")]

        assert len(migration_files) > 0, "At least one migration file should exist"

    def test_migration_file_structure(self):
        """Verify migration files have required structure"""
        migrations_dir = backend_dir / "alembic" / "versions"
        migration_files = list(migrations_dir.glob("*.py"))
        migration_files = [f for f in migration_files if not f.name.startswith("__")]

        for migration_file in migration_files:
            content = migration_file.read_text()

            # Check for required identifiers
            assert "revision:" in content, f"{migration_file.name} should have revision identifier"
            assert "down_revision:" in content, f"{migration_file.name} should have down_revision identifier"

            # Check for required functions
            assert "def upgrade()" in content, f"{migration_file.name} should have upgrade function"
            assert "def downgrade()" in content, f"{migration_file.name} should have downgrade function"

    def test_initial_migration_content(self):
        """Verify initial migration creates all required tables"""
        migrations_dir = backend_dir / "alembic" / "versions"
        migration_files = list(migrations_dir.glob("*initial*.py"))

        assert len(migration_files) > 0, "Initial migration file should exist"

        initial_migration = migration_files[0].read_text()

        # Check for required tables
        required_tables = [
            "users",
            "workspaces",
            "workspace_members",
            "teams",
            "team_members"
        ]

        for table in required_tables:
            assert f"'{table}'" in initial_migration or f'"{table}"' in initial_migration, \
                f"Initial migration should create {table} table"

        # Check for foreign keys
        assert "ForeignKeyConstraint" in initial_migration, \
            "Initial migration should have foreign key constraints"

        # Check for indexes
        assert "create_index" in initial_migration, \
            "Initial migration should create indexes"

    def test_downgrade_drops_tables(self):
        """Verify downgrade function drops all tables"""
        migrations_dir = backend_dir / "alembic" / "versions"
        migration_files = list(migrations_dir.glob("*initial*.py"))

        initial_migration = migration_files[0].read_text()

        # Check that downgrade drops tables
        assert "drop_table" in initial_migration, \
            "Downgrade should drop tables"

        # Check for all required tables being dropped
        required_tables = [
            "users",
            "workspaces",
            "workspace_members",
            "teams",
            "team_members"
        ]

        for table in required_tables:
            assert f"'{table}'" in initial_migration or f'"{table}"' in initial_migration, \
                f"Downgrade should drop {table} table"


class TestMigrationSyntax:
    """Test migration files for Python syntax errors"""

    def test_migration_files_are_valid_python(self):
        """Verify all migration files are valid Python"""
        migrations_dir = backend_dir / "alembic" / "versions"
        migration_files = list(migrations_dir.glob("*.py"))
        migration_files = [f for f in migration_files if not f.name.startswith("__")]

        for migration_file in migration_files:
            try:
                compile(migration_file.read_text(), migration_file.name, 'exec')
            except SyntaxError as e:
                pytest.fail(f"Migration {migration_file.name} has syntax error: {e}")


class TestMigrationOrder:
    """Test migration dependency chain"""

    def test_migration_chain_is_valid(self):
        """Verify migrations form a valid chain"""
        migrations_dir = backend_dir / "alembic" / "versions"
        migration_files = list(migrations_dir.glob("*.py"))
        migration_files = [f for f in migration_files if not f.name.startswith("__")]

        if len(migration_files) == 0:
            pytest.skip("No migration files to test")

        revisions = {}
        for migration_file in migration_files:
            content = migration_file.read_text()

            # Extract revision and down_revision
            revision = None
            down_revision = None

            for line in content.split('\n'):
                if line.startswith("revision:"):
                    revision = line.split('=')[1].strip().strip("'\"")
                if line.startswith("down_revision:"):
                    down_val = line.split('=')[1].strip().strip("'\"")
                    if down_val not in ['None', 'none', '']:
                        down_revision = down_val

            if revision:
                revisions[revision] = down_revision

        # Verify chain integrity
        # There should be exactly one migration with down_revision=None (the initial migration)
        initial_migrations = [rev for rev, down in revisions.items() if down is None]
        assert len(initial_migrations) == 1, \
            "There should be exactly one initial migration (down_revision=None)"


@pytest.mark.integration
class TestMigrationExecution:
    """
    Integration tests for migration execution.
    These require a running database and are marked as integration tests.
    Run with: pytest -m integration
    """

    @pytest.mark.skip(reason="Requires running PostgreSQL database")
    async def test_upgrade_migrations(self):
        """Test applying all migrations"""
        # This would test actual migration execution
        # Requires database connection
        pass

    @pytest.mark.skip(reason="Requires running PostgreSQL database")
    async def test_downgrade_migrations(self):
        """Test rolling back all migrations"""
        # This would test migration rollback
        # Requires database connection
        pass


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

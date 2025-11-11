# Database Migrations Guide

This guide covers database migrations using Alembic in the Native Colab platform.

## Overview

We use Alembic for database schema migrations with async SQLAlchemy. Migrations are version-controlled and can be applied or rolled back as needed.

## Quick Start

### Apply Migrations (Upgrade)

```bash
# Using the helper script
./scripts/migrate.sh upgrade

# Or directly with alembic
source venv/bin/activate
alembic upgrade head
```

### Rollback Migrations (Downgrade)

```bash
# Rollback one migration
./scripts/migrate.sh downgrade

# Rollback multiple migrations
./scripts/migrate.sh downgrade 3
```

### Check Current Version

```bash
./scripts/migrate.sh current
```

### View Migration History

```bash
./scripts/migrate.sh history
```

## Creating New Migrations

### Auto-generate from Model Changes

When you modify SQLAlchemy models, create a new migration:

```bash
# Using helper script
./scripts/migrate.sh create "add user preferences table"

# Or directly
alembic revision --autogenerate -m "add user preferences table"
```

**Important**: Always review auto-generated migrations before applying them!

### Manual Migration

For complex changes, create an empty migration and edit it:

```bash
alembic revision -m "complex data migration"
```

Then edit the generated file in `alembic/versions/`.

## Migration File Structure

Each migration file contains:

- **revision**: Unique identifier for this migration
- **down_revision**: Previous migration in the chain
- **upgrade()**: Function to apply changes
- **downgrade()**: Function to rollback changes

Example:

```python
def upgrade() -> None:
    op.create_table(
        'users',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('email', sa.String(255), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )

def downgrade() -> None:
    op.drop_table('users')
```

## Current Migrations

### 001 - Initial Migration (2025-11-11)

Creates the foundational database schema:

**Tables Created:**
- `users` - User accounts with authentication
- `workspaces` - Organization/workspace containers
- `workspace_members` - User-workspace relationships with RBAC
- `teams` - Teams within workspaces
- `team_members` - User-team relationships

**Relationships:**
- Users can own multiple workspaces
- Users can be members of multiple workspaces with different roles
- Workspaces contain multiple teams
- Teams contain multiple members

## Best Practices

### 1. Test Migrations Locally First

Always test migrations on your local database before production:

```bash
# Test upgrade
./scripts/migrate.sh upgrade

# Test downgrade
./scripts/migrate.sh downgrade
./scripts/migrate.sh upgrade
```

### 2. Review Auto-Generated Migrations

Auto-generated migrations may not always be perfect. Check for:
- Missing indexes
- Incorrect column types
- Missing constraints
- Data migration needs

### 3. Make Migrations Reversible

Always implement both `upgrade()` and `downgrade()` functions. This allows for easy rollback if issues occur.

### 4. Keep Migrations Small

Create focused migrations that do one thing. This makes debugging easier and rollbacks safer.

### 5. Never Edit Applied Migrations

Once a migration is applied to production, never edit it. Create a new migration instead.

## Environment-Specific Migrations

### Development

Development uses the `.env` file with local PostgreSQL:

```bash
DATABASE_URL=postgresql+asyncpg://nativecolab:nativecolab123@localhost:5432/nativecolab
```

### Testing

Tests use SQLite with `.env.test`:

```bash
DATABASE_URL=sqlite+aiosqlite:///./test.db
```

### Production

Production uses environment variables from Docker or Kubernetes:

```bash
DATABASE_URL=postgresql+asyncpg://${POSTGRES_USER}:${POSTGRES_PASSWORD}@${POSTGRES_HOST}:5432/${POSTGRES_DB}
```

## Docker Migrations

### Running Migrations in Docker

Migrations run automatically when the backend container starts (see `docker-entrypoint.sh`):

```bash
# Manual migration in Docker
docker compose exec backend ./scripts/migrate.sh upgrade
```

### Initial Database Setup

When starting fresh with Docker:

```bash
# Start PostgreSQL
docker compose up -d postgres

# Run migrations
docker compose exec backend ./scripts/migrate.sh upgrade
```

## Troubleshooting

### Migration Conflict

If you have conflicting migrations (multiple heads):

```bash
# Check current state
alembic heads

# Merge branches
alembic merge -m "merge migration branches" <rev1> <rev2>
```

### Database Out of Sync

If your database schema doesn't match migrations:

```bash
# Mark current database version (dangerous!)
alembic stamp head

# Or reset and re-apply
./scripts/migrate.sh reset
```

### Connection Issues

Ensure your database is running and credentials are correct:

```bash
# Test connection
psql -h localhost -U nativecolab -d nativecolab

# Check .env file
cat .env | grep DATABASE_URL
```

## CI/CD Integration

Migrations are automatically tested in CI/CD pipelines:

### GitLab CI

```yaml
test-migrations:
  script:
    - alembic upgrade head
    - alembic downgrade base
```

### GitHub Actions

```yaml
- name: Run migrations
  run: alembic upgrade head
```

## Data Migrations

For complex data transformations, use the `op.execute()` function:

```python
def upgrade() -> None:
    # Schema change
    op.add_column('users', sa.Column('status', sa.String(50)))

    # Data migration
    op.execute("""
        UPDATE users
        SET status = 'active'
        WHERE is_active = true
    """)

def downgrade() -> None:
    op.drop_column('users', 'status')
```

## Additional Resources

- [Alembic Documentation](https://alembic.sqlalchemy.org/)
- [SQLAlchemy Documentation](https://docs.sqlalchemy.org/)
- [Database Design Guide](../docs/database.md)

## Support

For migration issues, check:
1. Application logs: `docker compose logs backend`
2. PostgreSQL logs: `docker compose logs postgres`
3. Migration history: `./scripts/migrate.sh history`

#!/bin/bash
# Database Migration Helper Script
# This script helps manage Alembic database migrations

set -e

# Load environment variables
if [ -f .env ]; then
    export $(cat .env | grep -v '^#' | xargs)
fi

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Functions
print_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Activate virtual environment if it exists
if [ -d "venv" ]; then
    source venv/bin/activate
    print_info "Virtual environment activated"
fi

# Command handling
case "$1" in
    upgrade)
        print_info "Running database migrations (upgrade)..."
        alembic upgrade head
        print_info "Migrations completed successfully!"
        ;;
    downgrade)
        STEPS=${2:-1}
        print_warning "Downgrading database by $STEPS revision(s)..."
        alembic downgrade -$STEPS
        print_info "Downgrade completed!"
        ;;
    current)
        print_info "Current database revision:"
        alembic current
        ;;
    history)
        print_info "Migration history:"
        alembic history --verbose
        ;;
    create)
        if [ -z "$2" ]; then
            print_error "Please provide a migration message"
            echo "Usage: $0 create 'your migration message'"
            exit 1
        fi
        print_info "Creating new migration: $2"
        alembic revision --autogenerate -m "$2"
        print_info "Migration file created!"
        ;;
    reset)
        print_warning "WARNING: This will drop all tables and re-run migrations!"
        read -p "Are you sure? (yes/no): " confirm
        if [ "$confirm" = "yes" ]; then
            print_info "Downgrading to base..."
            alembic downgrade base
            print_info "Upgrading to head..."
            alembic upgrade head
            print_info "Database reset completed!"
        else
            print_info "Reset cancelled"
        fi
        ;;
    *)
        echo "Database Migration Helper"
        echo ""
        echo "Usage: $0 <command> [options]"
        echo ""
        echo "Commands:"
        echo "  upgrade          Apply all pending migrations"
        echo "  downgrade [n]    Rollback n migrations (default: 1)"
        echo "  current          Show current migration revision"
        echo "  history          Show migration history"
        echo "  create <msg>     Create new migration with autogenerate"
        echo "  reset            Drop all tables and re-run migrations"
        echo ""
        echo "Examples:"
        echo "  $0 upgrade"
        echo "  $0 downgrade 2"
        echo "  $0 create 'add user preferences table'"
        exit 1
        ;;
esac

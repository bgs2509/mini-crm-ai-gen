#!/bin/bash
set -e

echo "🔍 Waiting for PostgreSQL to be ready..."

# Wait for PostgreSQL to be ready
until pg_isready -h "${POSTGRES_HOST:-db}" -U "${POSTGRES_USER:-crm_user}" -d "${POSTGRES_DB:-crm_db}" > /dev/null 2>&1; do
  echo "⏳ PostgreSQL is unavailable - sleeping"
  sleep 2
done

echo "✅ PostgreSQL is ready!"

# Apply database migrations
echo "🔄 Checking for pending database migrations..."
if alembic upgrade head; then
  echo "✅ Database migrations applied successfully"
else
  echo "❌ Failed to apply migrations"
  exit 1
fi

echo "🚀 Starting application..."
# Execute the main command (passed as arguments to this script)
exec "$@"

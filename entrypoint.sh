#!/bin/sh

# Exit immediately if a command exits with a non-zero status
set -e

echo "Starting ClothCRM entrypoint script..."

# Run migrations
echo "Running database migrations via Alembic..."
alembic upgrade head

# Start Gunicorn server with Uvicorn workers
echo "Starting Gunicorn server..."
exec gunicorn app.main:app -w 4 -k uvicorn.workers.UvicornWorker -b 0.0.0.0:8000

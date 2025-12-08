#!/bin/sh
set -e

echo ${DATABASE_URL}
echo "Running database migrations..."
dbmate --url "${DATABASE_URL}" --migrations-dir /app/migrations up

echo "Starting application..."
exec "$@"

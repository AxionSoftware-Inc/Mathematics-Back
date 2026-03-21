#!/bin/sh

# Exit immediately if a command exits with a non-zero status.
set -e

# Wait for the database to be reachable if necessary (though docker-compose depends_on healthcheck handles this)
# echo "Waiting for postgres..."
# while ! nc -z $DB_HOST $DB_PORT; do
#   sleep 0.1
# done
# echo "PostgreSQL started"

# Apply database migrations
echo "Applying database migrations..."
python manage.py migrate --noinput

# Collect static files
echo "Collecting static files..."
python manage.py collectstatic --noinput

# Start Gunicorn
echo "Starting gunicorn..."
exec gunicorn project.wsgi:application --bind 0.0.0.0:8000 --access-logfile - "$@"

#!/bin/sh

# Exit immediately if a command exits with a non-zero status.
set -e

# Wait for the database to be reachable if necessary (though docker-compose depends_on healthcheck handles this)
# echo "Waiting for postgres..."
# while ! nc -z $DB_HOST $DB_PORT; do
#   sleep 0.1
# done
# echo "PostgreSQL started"

# Pre-execution checks can go here

# Execute the final command
echo "Executing command: $@"
exec "$@"

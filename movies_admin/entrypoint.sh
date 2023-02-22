#!/bin/bash
set -e

echo "Start project"

while ! nc -z $DB_HOST $DB_PORT; do
      sleep 0.1
done

python manage.py migrate --noinput

gunicorn config.wsgi:application --bind 0.0.0.0:8000
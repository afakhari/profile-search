#!/bin/sh
set -eu
python manage.py migrate --noinput
until python manage.py bootstrap --dataset /data/raw/linkedin_profiles.csv --report /reports/import-report.json; do
  echo "Waiting for dependencies..."
  sleep 4
done
exec gunicorn config.wsgi:application --bind 0.0.0.0:8000 --workers 2 --timeout 60

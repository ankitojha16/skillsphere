#!/bin/bash
set -e

echo "--- Installing Python dependencies ---"
python3 -m pip install -r requirements.txt --break-system-packages

echo "--- Running database migrations ---"
python3 manage.py migrate --noinput || echo "Migration skipped or completed during build"

echo "--- Collecting static assets ---"
python3 manage.py collectstatic --noinput --clear

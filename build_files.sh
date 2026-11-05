#!/bin/bash
set -e

echo "--- Installing Python dependencies ---"
python3 -m pip install -r requirements.txt --break-system-packages

echo "--- Collecting static assets ---"
python3 manage.py collectstatic --noinput --clear

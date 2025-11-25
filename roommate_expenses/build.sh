#!/usr/bin/env bash
# build.sh - Render build script

set -o errexit

pip install -r requirements.txt
python manage.py cleardb || true
python manage.py migrate
python manage.py collectstatic --no-input

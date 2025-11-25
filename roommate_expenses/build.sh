#!/usr/bin/env bash
# build.sh - Render build script

set -o errexit

echo "📦 Installing dependencies..."
pip install -r requirements.txt

echo "🗑️ Clearing old tables..."
python manage.py cleardb || echo "No tables to clear"

echo "🔄 Running migrations..."
python manage.py makemigrations
python manage.py migrate --run-syncdb

echo "📁 Collecting static files..."
python manage.py collectstatic --no-input

echo "✅ Build complete!"

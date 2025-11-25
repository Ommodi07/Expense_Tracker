echo "📦 Installing dependencies..."
pip install -r requirements.txt

echo "🔄 Running migrations..."
python manage.py makemigrations
python manage.py migrate

# Roommate Expenses - Deployment Guide

## Prerequisites
- Python 3.11.9
- PostgreSQL database (NeonDB already configured)
- Email service (Gmail with App Password recommended)

## Local Setup with Email Verification

### 1. Configure Email Settings
Edit `.env` file and update:
```
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=your-app-password
DEFAULT_FROM_EMAIL=your-email@gmail.com
```

**For Gmail:**
1. Enable 2-Factor Authentication on your Google account
2. Generate an App Password: https://myaccount.google.com/apppasswords
3. Use the 16-character app password (not your regular password)

### 2. Install Dependencies
```bash
pip install -r requirements.txt
```

### 3. Run Migrations
```bash
python manage.py makemigrations
python manage.py migrate
```

### 4. Collect Static Files
```bash
python manage.py collectstatic --noinput
```

### 5. Create Superuser (Optional)
```bash
python manage.py createsuperuser
```

### 6. Run Development Server
```bash
python manage.py runserver
```

## Deployment to Heroku

### 1. Install Heroku CLI
Download from: https://devcenter.heroku.com/articles/heroku-cli

### 2. Login to Heroku
```bash
heroku login
```

### 3. Create Heroku App
```bash
heroku create your-app-name
```

### 4. Set Environment Variables
```bash
heroku config:set SECRET_KEY="your-secret-key-here"
heroku config:set DEBUG=False
heroku config:set ALLOWED_HOSTS="your-app-name.herokuapp.com"
heroku config:set DATABASE_URL="your-neondb-url"
heroku config:set EMAIL_HOST_USER="your-email@gmail.com"
heroku config:set EMAIL_HOST_PASSWORD="your-app-password"
heroku config:set DEFAULT_FROM_EMAIL="your-email@gmail.com"
```

### 5. Deploy
```bash
git init
git add .
git commit -m "Initial commit"
heroku git:remote -a your-app-name
git push heroku main
```

### 6. Run Migrations on Heroku
```bash
heroku run python manage.py migrate
```

### 7. Create Superuser on Heroku
```bash
heroku run python manage.py createsuperuser
```

### 8. Open Your App
```bash
heroku open
```

## Deployment to Render

### 1. Create account at render.com

### 2. Create New Web Service
- Connect your GitHub repository
- Or manually deploy using Git

### 3. Configure Build & Start Commands
- **Build Command:** `pip install -r requirements.txt && python manage.py collectstatic --noinput && python manage.py migrate`
- **Start Command:** `gunicorn roommate_expenses.wsgi`

### 4. Add Environment Variables
In Render dashboard, add:
- `SECRET_KEY`: Generate new secret key
- `DEBUG`: False
- `ALLOWED_HOSTS`: your-app.onrender.com
- `DATABASE_URL`: Your NeonDB URL
- `EMAIL_HOST_USER`: your-email@gmail.com
- `EMAIL_HOST_PASSWORD`: your-app-password
- `DEFAULT_FROM_EMAIL`: your-email@gmail.com
- `PYTHON_VERSION`: 3.11.9

### 5. Deploy
Render will automatically deploy when you push to your repository.

## Deployment to Railway

### 1. Create account at railway.app

### 2. Create New Project
- Connect GitHub repository or use CLI

### 3. Add Environment Variables
```
SECRET_KEY=your-secret-key
DEBUG=False
ALLOWED_HOSTS=your-app.railway.app
DATABASE_URL=your-neondb-url
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=your-app-password
DEFAULT_FROM_EMAIL=your-email@gmail.com
```

### 4. Configure Start Command
Railway will automatically detect Django and use gunicorn.

## Generate New Secret Key
```python
python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
```

## Email Verification Flow

1. User registers with email and password
2. System sends verification email with unique link
3. User clicks link in email (valid for 24 hours)
4. Account is activated and user can log in
5. Unverified users cannot access protected pages

## Testing Email Locally

For testing without actual email sending, use console backend:
```python
# In .env
EMAIL_BACKEND=django.core.mail.backends.console.EmailBackend
```

This prints emails to console instead of sending them.

## Troubleshooting

### Email not sending
- Check EMAIL_HOST_USER and EMAIL_HOST_PASSWORD
- For Gmail, ensure you're using App Password, not regular password
- Check "Less secure app access" is not needed with App Passwords
- Verify 2FA is enabled on Gmail account

### Static files not loading
```bash
python manage.py collectstatic --noinput
```

### Database errors
```bash
python manage.py migrate
```

### Check logs (Heroku)
```bash
heroku logs --tail
```

## Security Checklist for Production

- [ ] Set DEBUG=False
- [ ] Use strong SECRET_KEY (different from development)
- [ ] Configure ALLOWED_HOSTS properly
- [ ] Use HTTPS (automatic on Heroku, Render, Railway)
- [ ] Keep .env file secret (never commit to Git)
- [ ] Use environment variables for sensitive data
- [ ] Regular database backups
- [ ] Monitor application logs

## Important Notes

1. **Email Verification is Required**: New users must verify their email before logging in
2. **Token Expiry**: Verification links expire after 24 hours
3. **Resend Option**: Users can request a new verification email if needed
4. **Database**: Already configured with NeonDB PostgreSQL
5. **Static Files**: Handled by WhiteNoise middleware

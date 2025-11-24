# Quick Start Guide

## Email Verification Setup

### Testing Locally

1. **Update .env file** with your email credentials:
   ```
   EMAIL_HOST_USER=your-email@gmail.com
   EMAIL_HOST_PASSWORD=your-gmail-app-password
   DEFAULT_FROM_EMAIL=your-email@gmail.com
   ```

2. **Get Gmail App Password**:
   - Enable 2-Factor Authentication on your Google account
   - Go to: https://myaccount.google.com/apppasswords
   - Generate an app password (16 characters)
   - Use this password in EMAIL_HOST_PASSWORD

3. **Run the server**:
   ```bash
   cd roommate_expenses
   ../env/Scripts/python.exe manage.py runserver
   ```

4. **Test Registration**:
   - Go to http://localhost:8000/register/
   - Register with a valid email address
   - Check your email for verification link
   - Click the link to verify your account
   - Login with your credentials

### For Testing Without Email (Console Backend)

Update `.env`:
```
EMAIL_BACKEND=django.core.mail.backends.console.EmailBackend
```

Verification emails will print to the console instead of being sent.

## How Email Verification Works

1. **User Registers**: User fills out registration form with username, email, and password
2. **Account Created (Inactive)**: Account is created but `is_active=False`
3. **Email Sent**: Verification email with unique token sent to user's email
4. **User Clicks Link**: User clicks verification link (valid for 24 hours)
5. **Account Activated**: `is_active=True` and `email_verified=True`
6. **User Can Login**: Only verified users can log in

## Deployment Checklist

Before deploying to production:

- [ ] Update SECRET_KEY in .env (generate new one)
- [ ] Set DEBUG=False in .env
- [ ] Update ALLOWED_HOSTS with your domain
- [ ] Configure email settings (EMAIL_HOST_USER, EMAIL_HOST_PASSWORD)
- [ ] Set DATABASE_URL (already configured with NeonDB)
- [ ] Run migrations: `python manage.py migrate`
- [ ] Collect static files: `python manage.py collectstatic`
- [ ] Test email sending in production environment

## Deployment Platforms

See `DEPLOYMENT.md` for detailed instructions on deploying to:
- Heroku
- Render
- Railway

## New Features Added

✅ Email verification required for new accounts
✅ Verification emails with 24-hour expiry
✅ Resend verification email option
✅ Production-ready settings (DEBUG, ALLOWED_HOSTS, Security headers)
✅ Static files configuration with WhiteNoise
✅ Database migrations completed
✅ Deployment files created (Procfile, runtime.txt, requirements.txt)

## Files Modified

- `expenses/models.py` - Added email verification fields
- `expenses/views.py` - Added verification views and updated registration
- `expenses/urls.py` - Added verification routes
- `roommate_expenses/settings.py` - Production settings and email config
- `.env` - Email and production settings

## New Files Created

- `expenses/templates/expenses/verification_sent.html`
- `expenses/templates/expenses/resend_verification.html`
- `requirements.txt`
- `Procfile`
- `runtime.txt`
- `.gitignore`
- `DEPLOYMENT.md`

## Important Notes

⚠️ **Before Deploying**: Replace the SECRET_KEY with a new one for production
⚠️ **Email Required**: Users MUST verify email to access the application
⚠️ **Database**: Already configured with NeonDB PostgreSQL
⚠️ **Security**: All production security settings are configured

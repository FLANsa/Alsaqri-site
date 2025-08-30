# Deployment Configuration Guide
# This file shows what changes are needed for online deployment

"""
CHANGES NEEDED FOR DEPLOYMENT:

1. DATABASE CONFIGURATION:
   - Change from SQLite to PostgreSQL (for production)
   - Update database URI in app.py

2. SECRET KEY:
   - Use environment variables for SECRET_KEY
   - Don't hardcode secrets

3. DEBUG MODE:
   - Set debug=False for production
   - Use proper WSGI server (gunicorn)

4. STATIC FILES:
   - Ensure static files are properly served
   - Configure static file serving

5. ENVIRONMENT VARIABLES:
   - Use environment variables for configuration
   - Don't hardcode sensitive data

EXAMPLE CHANGES:

# In app.py, replace:
app.config['SECRET_KEY'] = 'your-secret-key-here'

# With:
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'fallback-key')

# Replace SQLite with PostgreSQL:
# app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///phone_shop.db'
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', 'sqlite:///phone_shop.db')

# For production, change:
# app.run(debug=True, port=args.port)
# To:
# app.run(debug=False, host='0.0.0.0', port=int(os.environ.get('PORT', 5001)))
"""

# Requirements for deployment:
REQUIREMENTS = """
Flask==2.3.3
Flask-SQLAlchemy==3.0.5
Flask-Login==0.6.3
Werkzeug==2.3.7
python-barcode==0.15.1
Pillow==10.0.1
gunicorn==21.2.0
psycopg2-binary==2.9.7  # For PostgreSQL
"""

# Procfile for Heroku/Railway:
PROCFILE = """
web: gunicorn app:app
"""

# Runtime.txt for Python version:
RUNTIME_TXT = """
python-3.12.0
"""



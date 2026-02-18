"""
PythonAnywhere WSGI Configuration Template

INSTRUCTIONS:
1. Copy this content to your PythonAnywhere WSGI configuration file
   (Web -> your_username.pythonanywhere.com -> WSGI configuration file)

2. Update the following values:
   - PROJECT_PATH: Path to your cloned AIP project
   - POSTGRES_USER: Your PostgreSQL superuser name
   - POSTGRES_PASSWORD: Your PostgreSQL password
   - POSTGRES_HOST: Your PostgreSQL host (e.g., sackson-5021.postgres.pythonanywhere-services.com)
   - POSTGRES_PORT: Your PostgreSQL port (e.g., 15021)
   - POSTGRES_DB: Database name (usually 'postgres' for default)

3. Create a virtualenv on PythonAnywhere:
   mkvirtualenv aip-env --python=python3.10
   pip install -r requirements.txt

4. Reload your web app
"""

import sys
import os

# ============== UPDATE THESE VALUES ==============
PROJECT_PATH = '/home/sackson/AIP'
POSTGRES_USER = 'super'
POSTGRES_PASSWORD = 'YOUR_PASSWORD_HERE'  # Replace with actual password
POSTGRES_HOST = 'sackson-5021.postgres.pythonanywhere-services.com'
POSTGRES_PORT = '15021'
POSTGRES_DB = 'postgres'
SECRET_KEY = 'your-secure-secret-key-change-this-in-production'
# ================================================

# Add project to path
if PROJECT_PATH not in sys.path:
    sys.path.insert(0, PROJECT_PATH)

# Set environment variables
DATABASE_URL = f"postgresql+psycopg2://{POSTGRES_USER}:{POSTGRES_PASSWORD}@{POSTGRES_HOST}:{POSTGRES_PORT}/{POSTGRES_DB}"
os.environ['SQLALCHEMY_DATABASE_URL'] = DATABASE_URL
os.environ['SECRET_KEY'] = SECRET_KEY

# Import the FastAPI app
from backend.main import app

# Wrap ASGI app for WSGI compatibility (required for PythonAnywhere)
from a2wsgi import ASGIMiddleware
application = ASGIMiddleware(app)

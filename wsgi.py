"""
WSGI entry point for PythonAnywhere deployment.
PythonAnywhere requires a WSGI application, so we use a2wsgi to wrap FastAPI.

IMPORTANT: On PythonAnywhere, edit the WSGI config file directly
(Web -> WSGI configuration file) and copy content from pythonanywhere_wsgi_template.py
"""
import sys
import os

# Add the project directory to the path
project_home = os.path.dirname(os.path.abspath(__file__))
if project_home not in sys.path:
    sys.path.insert(0, project_home)

# IMPORTANT: Set environment variables BEFORE importing backend
# These will be overridden by PythonAnywhere WSGI config or .env file
# Load .env file first if it exists
try:
    from dotenv import load_dotenv
    env_path = os.path.join(project_home, '.env')
    if os.path.exists(env_path):
        load_dotenv(env_path)
except ImportError:
    pass

# Fallback to SQLite if no DATABASE_URL is set (for local testing)
if 'SQLALCHEMY_DATABASE_URL' not in os.environ:
    db_path = os.path.join(project_home, 'backend', 'aip_platform.db')
    os.environ['SQLALCHEMY_DATABASE_URL'] = f'sqlite:///{db_path}'

# Import the FastAPI app AFTER setting environment variables
from backend.main import app

# For PythonAnywhere WSGI - use a2wsgi to wrap FastAPI ASGI app
from a2wsgi import ASGIMiddleware
application = ASGIMiddleware(app)

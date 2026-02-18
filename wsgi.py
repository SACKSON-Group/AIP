"""
WSGI entry point for PythonAnywhere deployment.
PythonAnywhere requires a WSGI application, so we use a2wsgi to wrap FastAPI.
"""
import sys
import os

# Add the project directory to the path
project_home = os.path.dirname(os.path.abspath(__file__))
if project_home not in sys.path:
    sys.path.insert(0, project_home)

# PythonAnywhere PostgreSQL configuration
# Set DATABASE_URL in the PythonAnywhere WSGI config file or .env file
# Format: postgresql+psycopg2://user:password@host:port/database
# Example: postgresql+psycopg2://super:PASSWORD@sackson-5021.postgres.pythonanywhere-services.com:15021/postgres

# Load .env file if exists
from dotenv import load_dotenv
env_path = os.path.join(project_home, '.env')
if os.path.exists(env_path):
    load_dotenv(env_path)

# Environment variables should be set in PythonAnywhere or .env file:
# - SQLALCHEMY_DATABASE_URL: PostgreSQL connection string
# - SECRET_KEY: JWT secret key for authentication

from backend.main import app

# For PythonAnywhere WSGI - use a2wsgi to wrap FastAPI ASGI app
from a2wsgi import ASGIMiddleware
application = ASGIMiddleware(app)

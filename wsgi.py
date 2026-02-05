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

# Set environment variables
os.environ.setdefault('DATABASE_URL', 'sqlite:///./aip.db')

from backend.main import app

# For PythonAnywhere WSGI
# Option 1: If using a2wsgi (pip install a2wsgi)
try:
    from a2wsgi import ASGIMiddleware
    application = ASGIMiddleware(app)
except ImportError:
    # Option 2: Direct ASGI (if PythonAnywhere supports it)
    application = app

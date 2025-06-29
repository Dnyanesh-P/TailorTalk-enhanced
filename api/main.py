# Vercel requires the FastAPI app to be in an 'api' directory
import sys
import os

# Add the backend directory to the Python path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'backend'))

# Import your main FastAPI application
from main_trial import app

# Vercel will automatically detect this as the ASGI application

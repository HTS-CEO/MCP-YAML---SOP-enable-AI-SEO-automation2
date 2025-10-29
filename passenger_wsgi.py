import sys
import os

# Add current directory to path
sys.path.insert(0, os.path.dirname(__file__))

# Set environment variable for production
os.environ['ENVIRONMENT'] = 'production'

# Import the Flask app
from main import app as application

# Ensure the app is properly initialized
if __name__ != '__main__':
    application = application
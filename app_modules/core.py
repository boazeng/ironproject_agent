"""
Core Flask application configuration and initialization
"""

from flask import Flask
from flask_cors import CORS
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Configuration constants
import os
# Get the project root directory (parent of app_modules)
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUTPUT_DIR = os.path.join(PROJECT_ROOT, 'io', 'fullorder_output')
PDF_DIR = os.path.join(PROJECT_ROOT, 'io', 'fullorder')
INPUT_DIR = os.path.join(PROJECT_ROOT, 'io', 'input')

# Global variable to track analysis status
analysis_status = {
    'running': False,
    'last_run': None,
    'last_result': None,
    'error': None,
    'current_stage': None,
    'progress_messages': []
}

def create_app():
    """Create and configure the Flask application"""
    app = Flask(__name__, template_folder='../templates', static_folder='../static')

    # Enable CORS
    CORS(app)

    # Configuration
    app.config['SECRET_KEY'] = 'ironman-order-analysis-2024'
    app.config['TEMPLATES_AUTO_RELOAD'] = True
    app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 0

    return app
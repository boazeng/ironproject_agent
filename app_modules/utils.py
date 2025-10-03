"""
Utility functions for the application
"""

import os
import json
import glob
from datetime import datetime
from .core import OUTPUT_DIR

def get_latest_analysis_file():
    """Find and return the path to the latest analysis file"""
    try:
        # Look for analysis files in json_output directory
        json_dir = os.path.join(OUTPUT_DIR, 'json_output')
        if not os.path.exists(json_dir):
            return None

        # Find all *_out.json files
        json_files = glob.glob(os.path.join(json_dir, '*_out.json'))

        if not json_files:
            return None

        # Return the most recent file
        return max(json_files, key=os.path.getmtime)

    except Exception:
        return None

def load_analysis_data(filepath=None):
    """Load analysis data from file"""
    try:
        if not filepath:
            filepath = get_latest_analysis_file()

        if not filepath or not os.path.exists(filepath):
            return None

        with open(filepath, 'r', encoding='utf-8') as f:
            return json.load(f)

    except Exception:
        return None

def save_analysis_data(data, filepath):
    """Save analysis data to file"""
    try:
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        return True
    except Exception:
        return False

def get_order_number_from_filename(filename):
    """Extract order number from filename"""
    # Remove extension
    base_name = os.path.splitext(filename)[0]
    # Remove common suffixes
    for suffix in ['_out', '_analysis', '_ironman_analysis']:
        if base_name.endswith(suffix):
            base_name = base_name.replace(suffix, '')
    return base_name

def create_response(success=True, data=None, error=None, message=None):
    """Create a standardized API response"""
    response = {'success': success}

    if data is not None:
        response['data'] = data
    if error is not None:
        response['error'] = error
    if message is not None:
        response['message'] = message

    return response

def ensure_directory_exists(directory_path):
    """Ensure a directory exists, create if not"""
    os.makedirs(directory_path, exist_ok=True)
    return directory_path

def format_file_size(size_bytes):
    """Format file size in human-readable format"""
    for unit in ['B', 'KB', 'MB', 'GB']:
        if size_bytes < 1024.0:
            return f"{size_bytes:.2f} {unit}"
        size_bytes /= 1024.0
    return f"{size_bytes:.2f} TB"

def is_valid_filename(filename):
    """Check if filename is valid and safe"""
    # Check for directory traversal attempts
    if '..' in filename or '/' in filename or '\\' in filename:
        return False
    # Check for valid extensions
    valid_extensions = ['.pdf', '.png', '.jpg', '.jpeg', '.json']
    return any(filename.lower().endswith(ext) for ext in valid_extensions)
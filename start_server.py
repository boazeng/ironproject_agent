#!/usr/bin/env python3
"""
Simple server starter that ensures Flask runs on 0.0.0.0:5002
"""
import os
import sys

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Import the Flask app
from app import app

if __name__ == "__main__":
    print("IRONMAN Web Interface Starting...")
    print("Navigate to: http://localhost:5003")
    print("Press Ctrl+C to stop the server")
    print("[DEBUG] UPDATED CODE LOADED - Server on 0.0.0.0:5003")

    # Force the app to run on 0.0.0.0:5003
    app.run(debug=True, host='0.0.0.0', port=5003, use_reloader=False, threaded=True)
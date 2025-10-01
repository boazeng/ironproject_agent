#!/usr/bin/env python3
"""
Standalone server script - run this directly from Command Prompt
"""
import os
import sys

# Ensure we can import the app
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    from app import app

    print("=" * 50)
    print("IRONMAN Web Interface")
    print("=" * 50)
    print("Server starting on: http://localhost:5002")
    print("Press Ctrl+C to stop")
    print("=" * 50)

    # Run the server
    app.run(
        host='0.0.0.0',
        port=5002,
        debug=False,
        use_reloader=False,
        threaded=True
    )

except Exception as e:
    print(f"Error starting server: {e}")
    input("Press Enter to exit...")
@echo off
echo Starting IRONMAN Web Interface...
echo Navigate to: http://localhost:5005
echo Press Ctrl+C to stop the server
python -c "
from flask import Flask
import sys
import os
sys.path.insert(0, r'C:\Users\User\Aiprojects\Iron-Projects\Agents')
from app import app
app.run(debug=False, host='0.0.0.0', port=5005, use_reloader=False, threaded=True)
"
pause
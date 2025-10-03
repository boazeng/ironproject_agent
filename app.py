"""
Fully Modular Flask Application - IRONMAN System
All routes are organized in separate modules
"""

from app_modules.core import create_app
from app_modules.routes_basic import basic_bp
from app_modules.routes_files import files_bp
from app_modules.routes_header import header_bp
from app_modules.routes_catalog import catalog_bp
from app_modules.routes_shapes import shapes_bp
from app_modules.routes_ribs import ribs_bp
from app_modules.routes_table import table_bp
from app_modules.routes_analysis import analysis_bp

# Create the Flask app
app = create_app()

# Register all blueprints
app.register_blueprint(basic_bp)
app.register_blueprint(files_bp)
app.register_blueprint(header_bp)
app.register_blueprint(catalog_bp)
app.register_blueprint(shapes_bp)
app.register_blueprint(ribs_bp)
app.register_blueprint(table_bp)
app.register_blueprint(analysis_bp)

# Import any remaining routes that haven't been modularized yet
# These can be moved to modules later
from flask import jsonify, request
import os
import json
import glob
from app_modules.core import OUTPUT_DIR, analysis_status

# Analysis routes moved to routes_analysis.py module

@app.route('/api/analysis-history')
def get_analysis_history():
    """Get analysis history"""
    try:
        history = []
        analysis_files = glob.glob(os.path.join(OUTPUT_DIR, 'json_output', '*_out.json'))

        for file_path in analysis_files:
            file_info = {
                'filename': os.path.basename(file_path),
                'timestamp': os.path.getmtime(file_path),
                'size': os.path.getsize(file_path)
            }
            history.append(file_info)

        # Sort by timestamp (newest first)
        history.sort(key=lambda x: x['timestamp'], reverse=True)

        return jsonify({
            'success': True,
            'history': history[:10]  # Return last 10 analyses
        })

    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        })

if __name__ == '__main__':
    print("="*50)
    print("IRONMAN Fully Modular Web Interface")
    print("="*50)
    print("All routes are organized in modules:")
    print("  - Basic routes & static files: routes_basic.py")
    print("  - File management: routes_files.py")
    print("  - Header processing: routes_header.py")
    print("  - Catalog management: routes_catalog.py")
    print("  - Shape detection: routes_shapes.py")
    print("="*50)
    print("Server starting on: http://localhost:5000")
    print("Press Ctrl+C to stop")
    print("="*50)

    app.run(debug=True, host='0.0.0.0', port=5000)
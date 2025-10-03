"""
File management routes
"""

from flask import Blueprint, jsonify, request, send_file, abort
import os
import json
import glob
from datetime import datetime
from .core import INPUT_DIR, OUTPUT_DIR

# Create blueprint
files_bp = Blueprint('files', __name__)

@files_bp.route('/api/files')
def list_files():
    """List available files for analysis"""
    try:
        files = []

        # List PDF files from INPUT_DIR
        pdf_files = glob.glob(os.path.join(INPUT_DIR, '*.pdf'))
        for pdf_file in pdf_files:
            files.append({
                'name': os.path.basename(pdf_file),
                'type': 'pdf',
                'size': os.path.getsize(pdf_file),
                'modified': datetime.fromtimestamp(os.path.getmtime(pdf_file)).isoformat()
            })

        # List image files from INPUT_DIR
        for ext in ['*.png', '*.jpg', '*.jpeg']:
            img_files = glob.glob(os.path.join(INPUT_DIR, ext))
            for img_file in img_files:
                files.append({
                    'name': os.path.basename(img_file),
                    'type': 'image',
                    'size': os.path.getsize(img_file),
                    'modified': datetime.fromtimestamp(os.path.getmtime(img_file)).isoformat()
                })

        # Sort by modification time (newest first)
        files.sort(key=lambda x: x['modified'], reverse=True)

        return jsonify({
            'success': True,
            'files': files,
            'count': len(files)
        })

    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@files_bp.route('/api/select-file', methods=['POST'])
def select_file():
    """Select a file for processing"""
    try:
        data = request.json
        filename = data.get('filename')

        if not filename:
            return jsonify({'success': False, 'error': 'No filename provided'})

        # Check if file exists in input directory
        file_path = os.path.join(INPUT_DIR, filename)
        if not os.path.exists(file_path):
            return jsonify({'success': False, 'error': 'File not found'})

        # Store the selected file globally or in session
        # For now, we'll return success and let the frontend handle it
        return jsonify({
            'success': True,
            'filename': filename,
            'path': file_path,
            'message': f'File {filename} selected successfully'
        })

    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@files_bp.route('/input/<filename>')
def serve_input_file(filename):
    """Serve files from the input directory"""
    try:
        # Security check - prevent directory traversal
        if '..' in filename or '/' in filename or '\\' in filename:
            abort(403)

        file_path = os.path.join(INPUT_DIR, filename)

        if os.path.exists(file_path):
            if filename.lower().endswith('.pdf'):
                return send_file(file_path, mimetype='application/pdf')
            elif filename.lower().endswith(('.png', '.jpg', '.jpeg')):
                return send_file(file_path, mimetype='image/png')
            else:
                return send_file(file_path)
        else:
            return jsonify({'error': 'File not found'}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@files_bp.route('/api/latest-analysis')
def get_latest_analysis():
    """Get the latest analysis result"""
    try:
        # Look for the latest analysis JSON file
        json_dir = os.path.join(OUTPUT_DIR, 'json_output')
        if not os.path.exists(json_dir):
            return jsonify({
                'file': None,
                'analysis': None,
                'pdf_path': None
            })

        # Find the latest *_out.json file
        json_files = glob.glob(os.path.join(json_dir, '*_out.json'))

        if not json_files:
            return jsonify({
                'file': None,
                'analysis': None,
                'pdf_path': None
            })

        # Get the most recent file
        latest_file = max(json_files, key=os.path.getmtime)

        # Load the analysis data
        with open(latest_file, 'r', encoding='utf-8') as f:
            analysis_data = json.load(f)

        # Get the base filename
        base_filename = os.path.basename(latest_file).replace('_out.json', '')

        # Check for corresponding PDF
        pdf_path = None
        pdf_file = os.path.join('io/fullorder', f"{base_filename}.pdf")
        if os.path.exists(pdf_file):
            pdf_path = f"/pdf/{base_filename}.pdf"

        return jsonify({
            'file': base_filename,
            'analysis': analysis_data,
            'pdf_path': pdf_path
        })

    except Exception as e:
        print(f"Error loading latest analysis: {e}")
        return jsonify({
            'error': str(e),
            'file': None,
            'analysis': None
        }), 500
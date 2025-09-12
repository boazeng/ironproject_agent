"""
Flask Web Application for IRONMAN Order Analysis System
"""

from flask import Flask, render_template, jsonify, send_file, request
from flask_cors import CORS
import os
import json
import subprocess
import threading
from datetime import datetime
import glob

app = Flask(__name__)
CORS(app)

# Configuration
app.config['SECRET_KEY'] = 'ironman-order-analysis-2024'
OUTPUT_DIR = 'io/fullorder_output'
PDF_DIR = 'io/fullorder'

# Global variable to track analysis status
analysis_status = {
    'running': False,
    'last_run': None,
    'last_result': None,
    'error': None
}

@app.route('/')
def index():
    """Serve the main page"""
    return render_template('index.html')

@app.route('/api/run-analysis', methods=['POST'])
def run_analysis():
    """Run the main_global.py analysis script"""
    global analysis_status
    
    if analysis_status['running']:
        return jsonify({
            'success': False,
            'error': 'Analysis already running'
        })
    
    def run_script():
        global analysis_status
        try:
            analysis_status['running'] = True
            analysis_status['error'] = None
            
            # Run the main_global.py script
            result = subprocess.run(
                ['python', 'main_global.py'],
                capture_output=True,
                text=True,
                encoding='utf-8'
            )
            
            analysis_status['last_run'] = datetime.now().isoformat()
            
            if result.returncode == 0:
                analysis_status['last_result'] = 'success'
                print("Analysis completed successfully")
            else:
                analysis_status['last_result'] = 'error'
                analysis_status['error'] = result.stderr
                print(f"Analysis failed: {result.stderr}")
                
        except Exception as e:
            analysis_status['last_result'] = 'error'
            analysis_status['error'] = str(e)
            print(f"Error running analysis: {e}")
        finally:
            analysis_status['running'] = False
    
    # Run in background thread
    thread = threading.Thread(target=run_script)
    thread.start()
    
    return jsonify({
        'success': True,
        'message': 'Analysis started'
    })

@app.route('/api/latest-analysis')
def get_latest_analysis():
    """Get the latest analysis results"""
    try:
        # Find the most recent analysis file
        analysis_files = glob.glob(os.path.join(OUTPUT_DIR, '*_ironman_analysis.json'))
        
        if not analysis_files:
            # Try regular analysis files
            analysis_files = glob.glob(os.path.join(OUTPUT_DIR, '*_analysis.json'))
        
        if not analysis_files:
            return jsonify({})
        
        # Get the most recent file
        latest_file = max(analysis_files, key=os.path.getctime)
        
        # Load the analysis data
        with open(latest_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # Add PDF path if available
        if 'file' in data:
            pdf_name = data['file']
            pdf_path = os.path.join(PDF_DIR, pdf_name)
            if os.path.exists(pdf_path):
                # Convert to web-accessible path
                data['pdf_path'] = f'/pdf/{pdf_name}'
        
        return jsonify(data)
        
    except Exception as e:
        print(f"Error loading analysis: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/status')
def get_status():
    """Get current analysis status"""
    return jsonify(analysis_status)

@app.route('/pdf/<filename>')
def serve_pdf(filename):
    """Serve PDF files"""
    try:
        pdf_path = os.path.join(PDF_DIR, filename)
        if os.path.exists(pdf_path):
            return send_file(pdf_path, mimetype='application/pdf')
        else:
            return jsonify({'error': 'PDF not found'}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/table_image/<filename>')
def serve_table_image(filename):
    """Serve table detection images (main table and header images)"""
    try:
        table_dir = os.path.join(OUTPUT_DIR, 'table_detection')
        image_path = os.path.join(table_dir, filename)
        if os.path.exists(image_path):
            return send_file(image_path, mimetype='image/png')
        else:
            return jsonify({'error': 'Table image not found'}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/files')
def list_files():
    """List available files for analysis"""
    try:
        files = []
        
        # List PDF files
        pdf_files = glob.glob(os.path.join(PDF_DIR, '*.pdf'))
        for pdf_file in pdf_files:
            files.append({
                'name': os.path.basename(pdf_file),
                'type': 'pdf',
                'size': os.path.getsize(pdf_file),
                'modified': datetime.fromtimestamp(os.path.getmtime(pdf_file)).isoformat()
            })
        
        # List image files
        for ext in ['*.png', '*.jpg', '*.jpeg']:
            img_files = glob.glob(os.path.join(PDF_DIR, ext))
            for img_file in img_files:
                files.append({
                    'name': os.path.basename(img_file),
                    'type': 'image',
                    'size': os.path.getsize(img_file),
                    'modified': datetime.fromtimestamp(os.path.getmtime(img_file)).isoformat()
                })
        
        return jsonify({
            'files': files,
            'count': len(files)
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/update-header', methods=['POST'])
def update_header():
    """Update header information"""
    try:
        header_data = request.json
        
        # Find the latest analysis file
        analysis_files = glob.glob(os.path.join(OUTPUT_DIR, '*_ironman_analysis.json'))
        
        if not analysis_files:
            return jsonify({'success': False, 'error': 'No analysis file found'})
        
        latest_file = max(analysis_files, key=os.path.getctime)
        
        # Load existing data
        with open(latest_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # Update header information
        if 'analysis' in data and 'sections' in data['analysis'] and 'header' in data['analysis']['sections']:
            header = data['analysis']['sections']['header']
            
            # Update basic fields
            if header_data.get('orderNumber'):
                header['order_number'] = header_data['orderNumber']
            if header_data.get('customer'):
                header['customer'] = header_data['customer']
            
            # Update header table values
            if 'header_table' in header and 'key_values' in header['header_table']:
                key_values = header['header_table']['key_values']
                
                # Update or add key-value pairs
                updated_values = []
                existing_keys = set()
                
                for kv in key_values:
                    for key, value in kv.items():
                        if 'איש' in key and 'קשר' in key and header_data.get('contact'):
                            updated_values.append({key: header_data['contact']})
                        elif 'טלפון' in key and header_data.get('phone'):
                            updated_values.append({key: header_data['phone']})
                        elif 'כתובת' in key and 'אתר' in key and header_data.get('address'):
                            updated_values.append({key: header_data['address']})
                        elif 'משקל' in key and header_data.get('weight'):
                            updated_values.append({key: header_data['weight']})
                        else:
                            updated_values.append({key: value})
                        existing_keys.add(key.lower())
                
                header['header_table']['key_values'] = updated_values
        
        # Also update the top-level sections for consistency
        if 'sections' in data and 'header' in data['sections']:
            top_header = data['sections']['header']
            if header_data.get('orderNumber'):
                top_header['order_number'] = header_data['orderNumber']
            if header_data.get('customer'):
                top_header['customer'] = header_data['customer']
        
        # Save updated data
        with open(latest_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        
        return jsonify({'success': True, 'message': 'Header updated successfully'})
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/analysis-history')
def get_analysis_history():
    """Get history of all analyses"""
    try:
        history = []
        
        # Get all analysis files
        analysis_files = glob.glob(os.path.join(OUTPUT_DIR, '*.json'))
        
        for file_path in analysis_files:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                history.append({
                    'filename': os.path.basename(file_path),
                    'source_file': data.get('file', 'Unknown'),
                    'timestamp': datetime.fromtimestamp(os.path.getmtime(file_path)).isoformat(),
                    'has_header': data.get('analysis', {}).get('sections', {}).get('header', {}).get('found', False),
                    'has_table': data.get('analysis', {}).get('sections', {}).get('main_table', {}).get('found', False),
                    'row_count': data.get('analysis', {}).get('sections', {}).get('main_table', {}).get('row_count', 0)
                })
            except:
                continue
        
        # Sort by timestamp descending
        history.sort(key=lambda x: x['timestamp'], reverse=True)
        
        return jsonify({
            'history': history,
            'count': len(history)
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    # Create necessary directories
    os.makedirs('templates', exist_ok=True)
    os.makedirs('static/css', exist_ok=True)
    os.makedirs('static/js', exist_ok=True)
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    
    print("IRONMAN Web Interface Starting...")
    print("Navigate to: http://localhost:5000")
    print("Press Ctrl+C to stop the server")
    
    # Run the Flask app
    app.run(debug=True, host='0.0.0.0', port=5000)
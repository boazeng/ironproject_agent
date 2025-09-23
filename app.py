"""
Flask Web Application for IRONMAN Order Analysis System
"""

from flask import Flask, render_template, jsonify, send_file, request, abort
from flask_cors import CORS
import os
import json
import subprocess
import threading
from datetime import datetime
import glob
import io
import sys
import fnmatch

# Import the OrderHeader agent
from agents.llm_agents.orderheader_agent import OrderHeaderAgent
# Import the Form1Dat1 agent for database management
from agents.llm_agents.format1_agent.form1dat1 import Form1Dat1Agent

app = Flask(__name__)
CORS(app)

# Disable template caching for development
app.config['TEMPLATES_AUTO_RELOAD'] = True
app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 0

# Configuration
app.config['SECRET_KEY'] = 'ironman-order-analysis-2024'
app.config['TEMPLATES_AUTO_RELOAD'] = True
OUTPUT_DIR = 'io/fullorder_output'
PDF_DIR = 'io/fullorder'
INPUT_DIR = 'io/input'

# Global variable to track analysis status
analysis_status = {
    'running': False,
    'last_run': None,
    'last_result': None,
    'error': None
}

# Initialize Form1Dat1 agent for database management
form1dat1_agent = Form1Dat1Agent()

@app.route('/')
def index():
    """Serve the main page"""
    return render_template('index.html')

@app.route('/test')
def test():
    """Test template route"""
    return render_template('test.html')

@app.route('/api/run-analysis', methods=['POST'])
def run_analysis():
    """Run the main_global.py analysis script"""
    global analysis_status

    print(f"[DEBUG] /api/run-analysis endpoint called")

    if analysis_status['running']:
        print(f"[DEBUG] Analysis already running, returning error")
        return jsonify({
            'success': False,
            'error': 'Analysis already running'
        })

    # Get the selected filename from request
    data = request.get_json() or {}
    selected_file = data.get('filename', '')
    print(f"[DEBUG] Request data: {data}")
    print(f"[DEBUG] Selected file: {selected_file}")
    
    def run_script():
        global analysis_status
        try:
            print(f"[DEBUG] Starting run_script function")
            print(f"[DEBUG] Selected file: {selected_file}")

            analysis_status['running'] = True
            analysis_status['error'] = None

            # Run the main_table_detection.py script (doesn't accept filename arguments)
            cmd = ['python', 'main_table_detection.py', '--skip-clean']

            print(f"[DEBUG] Running command: {' '.join(cmd)}")
            print(f"[DEBUG] Current working directory: {os.getcwd()}")
            print(f"[DEBUG] Python executable: {sys.executable}")

            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                encoding='utf-8',
                cwd=os.getcwd()
            )

            print(f"[DEBUG] Command return code: {result.returncode}")
            print(f"[DEBUG] Command stdout length: {len(result.stdout)}")
            print(f"[DEBUG] Command stderr length: {len(result.stderr)}")

            if result.stdout:
                print(f"[DEBUG] Command stdout: {result.stdout[:500]}...")
            if result.stderr:
                print(f"[DEBUG] Command stderr: {result.stderr[:500]}...")

            analysis_status['last_run'] = datetime.now().isoformat()

            if result.returncode == 0:
                analysis_status['last_result'] = 'success'
                print("[DEBUG] Analysis completed successfully")
            else:
                analysis_status['last_result'] = 'error'
                analysis_status['error'] = result.stderr
                print(f"[DEBUG] Analysis failed: {result.stderr}")

        except Exception as e:
            analysis_status['last_result'] = 'error'
            analysis_status['error'] = str(e)
            print(f"[DEBUG] Error running analysis: {e}")
            import traceback
            print(f"[DEBUG] Traceback: {traceback.format_exc()}")
        finally:
            analysis_status['running'] = False
            print(f"[DEBUG] run_script function completed")
    
    # Run in background thread
    print(f"[DEBUG] Creating background thread")
    thread = threading.Thread(target=run_script)
    print(f"[DEBUG] Starting background thread")
    thread.start()
    print(f"[DEBUG] Background thread started, returning response")

    return jsonify({
        'success': True,
        'message': 'Analysis started'
    })

@app.route('/api/analysis-status')
def get_analysis_status():
    """Get the current analysis status"""
    return jsonify(analysis_status)

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
        
        # Get the most recent file by modification time
        latest_file = max(analysis_files, key=os.path.getmtime)
        
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

@app.route('/shape_image/<filename>')
def serve_shape_image(filename):
    """Serve shape images from the shapes folder"""
    try:
        shapes_dir = os.path.join(OUTPUT_DIR, 'table_detection', 'shapes')
        image_path = os.path.join(shapes_dir, filename)
        if os.path.exists(image_path):
            return send_file(image_path, mimetype='image/png')
        else:
            return jsonify({'error': 'Shape image not found'}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/shape_column_image/<filename>')
def serve_shape_column_image(filename):
    """Serve shape column images from the shape_column folder"""
    try:
        shape_column_dir = os.path.join(OUTPUT_DIR, 'table_detection', 'shape_column')
        image_path = os.path.join(shape_column_dir, filename)
        if os.path.exists(image_path):
            return send_file(image_path, mimetype='image/png')
        else:
            return jsonify({'error': 'Shape column image not found'}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/order_header_image/<filename>')
def serve_order_header_image(filename):
    """Serve order header images from the order_header folder"""
    try:
        header_dir = os.path.join(OUTPUT_DIR, 'table_detection', 'order_header')
        image_path = os.path.join(header_dir, filename)
        if os.path.exists(image_path):
            return send_file(image_path, mimetype='image/png')
        else:
            return jsonify({'error': 'Order header image not found'}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/catalog_image/<catalog_number>')
def serve_catalog_image(catalog_number):
    """Serve catalog images from the io/catalog folder"""
    try:
        catalog_dir = os.path.join('io', 'catalog')
        # Format: shape XXX.png where XXX is the catalog number
        filename = f"shape {catalog_number}.png"
        image_path = os.path.join(catalog_dir, filename)

        if os.path.exists(image_path):
            return send_file(image_path, mimetype='image/png')
        else:
            return jsonify({'error': f'Catalog image not found for {catalog_number}'}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/files')
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
        
        return jsonify({
            'files': files,
            'count': len(files)
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/select-file', methods=['POST'])
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
            'path': file_path
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/input/<filename>')
def serve_input_file(filename):
    """Serve files from the input directory"""
    try:
        file_path = os.path.join(INPUT_DIR, filename)
        if os.path.exists(file_path):
            if filename.lower().endswith('.pdf'):
                return send_file(file_path, mimetype='application/pdf')
            else:
                return send_file(file_path)
        else:
            return jsonify({'error': 'File not found'}), 404
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

@app.route('/api/save-header-selection', methods=['POST'])
def save_header_selection():
    """Save user-selected area as new header image"""
    try:
        import fitz  # PyMuPDF
        from PIL import Image
        
        data = request.json
        filename = data.get('filename')
        selection = data.get('selection')
        
        if not filename or not selection:
            return jsonify({'success': False, 'error': 'Missing filename or selection data'})
        
        # Find the PDF file
        pdf_path = os.path.join(PDF_DIR, filename)
        if not os.path.exists(pdf_path):
            pdf_path = os.path.join(INPUT_DIR, filename)
            if not os.path.exists(pdf_path):
                return jsonify({'success': False, 'error': 'PDF file not found'})
        
        # Open PDF and extract the selected area
        doc = fitz.open(pdf_path)
        page = doc[selection['page'] - 1]  # Convert to 0-based index
        
        # Get page dimensions
        mat = fitz.Matrix(2.0, 2.0)  # 2x zoom for better quality
        pix = page.get_pixmap(matrix=mat)
        
        # Convert selection coordinates (assuming they're in canvas coordinates)
        # Scale coordinates to PDF coordinates
        scale_x = pix.width / (pix.width / 2.0)  # Adjust based on actual canvas size
        scale_y = pix.height / (pix.height / 2.0)
        
        # Create crop rectangle
        x0 = int(selection['x'] * 2)  # Scale for 2x zoom
        y0 = int(selection['y'] * 2)
        x1 = int((selection['x'] + selection['width']) * 2)
        y1 = int((selection['y'] + selection['height']) * 2)
        
        # Crop the image
        crop_rect = fitz.Rect(x0, y0, x1, y1)
        cropped_pix = pix
        
        # Save as PNG
        base_name = os.path.splitext(filename)[0]
        output_filename = f"{base_name}_user_header.png"
        output_path = os.path.join(OUTPUT_DIR, 'table_detection', 'order_header', output_filename)
        
        # Ensure directory exists
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        
        # Convert to PIL Image for cropping
        img_data = pix.tobytes("png")
        with Image.open(io.BytesIO(img_data)) as img:
            cropped_img = img.crop((x0, y0, x1, y1))
            cropped_img.save(output_path, "PNG")
        
        doc.close()
        
        # Update the analysis file to include the new header image
        analysis_files = glob.glob(os.path.join(OUTPUT_DIR, f'{base_name}_ironman_analysis.json'))
        if analysis_files:
            latest_file = max(analysis_files, key=os.path.getctime)
            
            with open(latest_file, 'r', encoding='utf-8') as f:
                analysis_data = json.load(f)
            
            # Update header image path
            analysis_data['order_header_image_path'] = output_path
            
            with open(latest_file, 'w', encoding='utf-8') as f:
                json.dump(analysis_data, f, ensure_ascii=False, indent=2)
        
        return jsonify({'success': True, 'message': 'Header selection saved successfully', 'image_path': output_filename})
        
    except Exception as e:
        import traceback
        print(f"Error saving header selection: {e}")
        print(traceback.format_exc())
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/save-section-selections', methods=['POST'])
def save_section_selections():
    """Save user-defined section selections for PDF analysis"""
    try:
        import fitz  # PyMuPDF
        from PIL import Image
        
        data = request.json
        filename = data.get('filename')
        sections = data.get('sections', {})
        
        if not filename or not sections:
            return jsonify({'success': False, 'error': 'Missing filename or section data'})
        
        # Find the PDF file
        pdf_path = os.path.join(PDF_DIR, filename)
        if not os.path.exists(pdf_path):
            pdf_path = os.path.join(INPUT_DIR, filename)
            if not os.path.exists(pdf_path):
                return jsonify({'success': False, 'error': 'PDF file not found'})
        
        # Open PDF
        doc = fitz.open(pdf_path)
        base_name = os.path.splitext(filename)[0]
        saved_images = {}
        
        # Process each section
        for section_type, selection in sections.items():
            try:
                page = doc[selection['page'] - 1]  # Convert to 0-based index
                
                # Get page with high resolution
                mat = fitz.Matrix(2.0, 2.0)  # 2x zoom for better quality
                pix = page.get_pixmap(matrix=mat)
                
                # Scale coordinates for cropping
                x0 = int(selection['x'] * 2)
                y0 = int(selection['y'] * 2)
                x1 = int((selection['x'] + selection['width']) * 2)
                y1 = int((selection['y'] + selection['height']) * 2)
                
                # Map section types to existing directory names and file patterns
                directory_mapping = {
                    'order_header': 'order_header',
                    'table_header': 'table_header', 
                    'table_area': 'table',
                    'shape_column': 'shape_column'
                }
                
                filename_mapping = {
                    'order_header': f"{base_name}_order_header.png",
                    'table_header': f"{base_name}_table_header.png",
                    'table_area': f"{base_name}_main_table.png", 
                    'shape_column': f"{base_name}_shape_column.png"
                }
                
                # Save cropped image
                output_filename = filename_mapping.get(section_type, f"{base_name}_{section_type}.png")
                target_directory = directory_mapping.get(section_type, section_type)
                output_path = os.path.join(OUTPUT_DIR, 'table_detection', target_directory, output_filename)
                
                # Ensure directory exists
                os.makedirs(os.path.dirname(output_path), exist_ok=True)
                
                # Check if file already exists
                file_exists = os.path.exists(output_path)
                action = "Replaced" if file_exists else "Created"
                
                # Convert to PIL Image for cropping
                img_data = pix.tobytes("png")
                with Image.open(io.BytesIO(img_data)) as img:
                    cropped_img = img.crop((x0, y0, x1, y1))
                    cropped_img.save(output_path, "PNG")
                
                saved_images[section_type] = {
                    'filename': output_filename,
                    'path': output_path,
                    'selection': selection
                }
                
                print(f"{action} {section_type} section: {output_path}")
                
            except Exception as e:
                print(f"Error processing {section_type}: {e}")
                continue
        
        doc.close()
        
        # Update the analysis file with section selections
        analysis_files = glob.glob(os.path.join(OUTPUT_DIR, f'{base_name}_ironman_analysis.json'))
        if analysis_files:
            latest_file = max(analysis_files, key=os.path.getctime)
            
            with open(latest_file, 'r', encoding='utf-8') as f:
                analysis_data = json.load(f)
            
            # Merge new section selections with existing ones
            if 'user_sections' not in analysis_data:
                analysis_data['user_sections'] = {}
            
            # Update only the sections that were just saved, keep others intact
            for section_type, section_data in saved_images.items():
                analysis_data['user_sections'][section_type] = section_data
            
            print(f"Updated user_sections: {list(analysis_data['user_sections'].keys())}")
            
            # Update specific paths if they exist
            if 'order_header' in saved_images:
                analysis_data['order_header_image_path'] = saved_images['order_header']['path']
            
            with open(latest_file, 'w', encoding='utf-8') as f:
                json.dump(analysis_data, f, ensure_ascii=False, indent=2)
        
        return jsonify({
            'success': True, 
            'message': f'Successfully saved {len(saved_images)} section selections',
            'saved_sections': list(saved_images.keys())
        })
        
    except Exception as e:
        import traceback
        print(f"Error saving section selections: {e}")
        print(traceback.format_exc())
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

@app.route('/api/analyze-order-header', methods=['POST'])
def analyze_order_header():
    """Analyze order header using specialized OrderHeader agent"""
    try:
        # Get the current analysis data to find the header image filename
        analysis_file = None
        analysis_files = glob.glob(os.path.join(OUTPUT_DIR, '*_ironman_analysis.json'))
        
        if analysis_files:
            # Try each analysis file to find one with a valid header image
            header_filename = None
            analysis_file = None

            # Sort by most recent first
            analysis_files.sort(key=os.path.getmtime, reverse=True)

            for file_path in analysis_files:
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        current_data = json.load(f)

                    # Check if there's a user-selected header image
                    if current_data.get('user_sections', {}).get('order_header', {}).get('filename'):
                        header_filename = current_data['user_sections']['order_header']['filename']
                        analysis_file = file_path
                        break
                    elif current_data.get('order_header_image_path'):
                        # Extract filename from path
                        header_filename = os.path.basename(current_data['order_header_image_path'])
                        analysis_file = file_path
                        break
                except Exception:
                    continue

            if not header_filename:
                return jsonify({
                    'success': False,
                    'error': 'No header image found in any analysis file'
                })
                
            # Initialize and run the OrderHeader agent with ChatGPT Vision
            orderheader_agent = OrderHeaderAgent(ocr_provider="chatgpt")
            result = orderheader_agent.process_header_analysis(header_filename)
            
            if result.get('success'):
                # Update the analysis file with new header data from ChatGPT
                try:
                    # Merge the extracted fields back into the current analysis
                    extracted_fields = result.get('extracted_fields', [])
                    if extracted_fields:
                        # Convert extracted fields to the analysis format
                        updated_key_values = []
                        
                        # Start with existing key_values to preserve order and other fields
                        existing_key_values = current_data.get('analysis', {}).get('sections', {}).get('header', {}).get('header_table', {}).get('key_values', [])
                        
                        # Create a map of existing fields for easy lookup
                        existing_fields = {}
                        for kv in existing_key_values:
                            for key, value in kv.items():
                                existing_fields[key] = value
                        
                        # Update with ChatGPT extracted fields
                        for field_obj in extracted_fields:
                            for key, value in field_obj.items():
                                if value and value.strip():  # Only update if value is not empty
                                    existing_fields[key] = value.strip()
                        
                        # Convert back to the analysis format
                        for key, value in existing_fields.items():
                            updated_key_values.append({key: value})
                        
                        # Update both sections.header and analysis.sections.header
                        if 'sections' in current_data:
                            if 'header' in current_data['sections']:
                                if 'header_table' not in current_data['sections']['header']:
                                    current_data['sections']['header']['header_table'] = {}
                                current_data['sections']['header']['header_table']['key_values'] = updated_key_values
                        
                        if 'analysis' in current_data:
                            if 'sections' in current_data['analysis']:
                                if 'header' in current_data['analysis']['sections']:
                                    if 'header_table' not in current_data['analysis']['sections']['header']:
                                        current_data['analysis']['sections']['header']['header_table'] = {}
                                    current_data['analysis']['sections']['header']['header_table']['key_values'] = updated_key_values
                        
                        # Write the updated data back to the analysis file
                        with open(analysis_file, 'w', encoding='utf-8') as f:
                            json.dump(current_data, f, indent=2, ensure_ascii=False)
                        
                        print(f"[OrderHeader] Successfully updated analysis file with {len(extracted_fields)} fields")
                        
                except Exception as update_error:
                    print(f"[OrderHeader] Error updating analysis file: {str(update_error)}")
                    # Continue anyway, just log the error
                
                return jsonify({
                    'success': True,
                    'agent_result': result,
                    'message': f'Header analysis completed. Found {result.get("field_count", 0)} fields and updated analysis file.',
                    'fields_updated': len(result.get('extracted_fields', []))
                })
            else:
                return jsonify({
                    'success': False,
                    'error': result.get('error', 'OrderHeader agent analysis failed'),
                    'agent_result': result
                })
                
        else:
            return jsonify({
                'success': False,
                'error': 'No analysis data found. Please run analysis first.'
            })
            
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'OrderHeader analysis failed: {str(e)}'
        })

@app.route('/api/redetect-shapes', methods=['POST'])
def redetect_shapes():
    """Re-detect shapes using Global agent to regenerate shape files from shape column"""
    try:
        # Get column name from request (default to 'צורה')
        data = request.get_json() or {}
        column_name = data.get('column_name', 'צורה')

        # Find analysis files with shape_column data
        analysis_files = glob.glob(os.path.join(OUTPUT_DIR, '*_ironman_analysis.json'))

        if not analysis_files:
            return jsonify({
                'success': False,
                'error': 'No analysis files found'
            })

        # Try each analysis file to find one with shape_column data
        shape_column_filename = None
        analysis_file = None

        # Sort by most recent first
        analysis_files.sort(key=os.path.getmtime, reverse=True)

        for file_path in analysis_files:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    current_data = json.load(f)

                # Check if there's a shape_column image
                if current_data.get('user_sections', {}).get('shape_column', {}).get('filename'):
                    shape_column_filename = current_data['user_sections']['shape_column']['filename']
                    analysis_file = file_path
                    break
            except Exception:
                continue

        if not shape_column_filename:
            return jsonify({
                'success': False,
                'error': 'No shape column image found in any analysis file'
            })

        # Import and run the Global agent to regenerate shapes
        try:
            from agents.llm_agents.global_agent import GlobalAgent

            # Initialize Global agent with API key from environment
            openai_api_key = os.getenv('OPENAI_API_KEY')
            if not openai_api_key:
                return jsonify({
                    'success': False,
                    'error': 'OpenAI API key not found in environment variables'
                })

            global_agent = GlobalAgent(openai_api_key)

            # Call shape regeneration method with column name
            result = global_agent.regenerate_shapes_from_column(shape_column_filename, column_name=column_name)

            if result.get('success'):
                shapes_count = result.get('shapes_generated', 0)

                return jsonify({
                    'success': True,
                    'message': f'Shapes re-detection completed successfully. Generated {shapes_count} new shape files.',
                    'shapes_count': shapes_count,
                    'shape_column_file': shape_column_filename
                })
            else:
                return jsonify({
                    'success': False,
                    'error': result.get('error', 'Shape regeneration failed')
                })

        except ImportError:
            return jsonify({
                'success': False,
                'error': 'GlobalAgent not available. Make sure global_agent.py exists.'
            })

    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'Shape re-detection failed: {str(e)}'
        })

@app.route('/api/run-ocr-analysis', methods=['POST'])
def run_ocr_analysis():
    """Run the form1ocr1 agent to perform OCR on order header"""
    try:
        # Import the OCR agent
        from agents.llm_agents.format1_agent.form1ocr1 import Form1OCR1Agent

        # Create and run the agent
        agent = Form1OCR1Agent()
        result = agent.process()

        if result['success']:
            # Update the analysis file with OCR data
            analysis_files = glob.glob(os.path.join(OUTPUT_DIR, '*_analysis.json'))

            if analysis_files:
                latest_file = max(analysis_files, key=os.path.getmtime)

                # Load existing data
                with open(latest_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)

                # Add OCR data
                data['ocr_data'] = result['agent_result']['extracted_fields']

                # Save updated data
                with open(latest_file, 'w', encoding='utf-8') as f:
                    json.dump(data, f, ensure_ascii=False, indent=2)

            return jsonify({
                'success': True,
                'agent_result': result['agent_result'],
                'message': 'OCR analysis completed successfully'
            })
        else:
            return jsonify({
                'success': False,
                'error': result.get('error', 'OCR analysis failed')
            })

    except Exception as e:
        print(f"[DEBUG] OCR analysis error: {e}")
        return jsonify({
            'success': False,
            'error': f'OCR analysis failed: {str(e)}'
        })

def get_latest_analysis_file():
    """Helper function to get the latest analysis file"""
    try:
        analysis_files = glob.glob(os.path.join(OUTPUT_DIR, '*_analysis.json'))
        if not analysis_files:
            return None
        return max(analysis_files, key=os.path.getmtime)
    except:
        return None

@app.route('/api/update-table-cell', methods=['POST'])
def update_table_cell():
    """Update a single table cell value and save to database"""
    try:
        data = request.json
        order_number = data.get('orderNumber')
        page_number = data.get('pageNumber')
        row_index = data.get('rowIndex')
        field_name = data.get('fieldName')
        new_value = data.get('value')

        try:
            print(f"[DEBUG] Updating table cell: Order {order_number}, Page {page_number}, Row {row_index}, Field {field_name} = {new_value}")
        except UnicodeEncodeError:
            print(f"[DEBUG] Updating table cell: Order {order_number}, Page {page_number}, Row {row_index}, Field [Hebrew], Value [Hebrew]")

        # First update the OCR file (keep original functionality)
        ocr_file_path = os.path.join(
            OUTPUT_DIR,
            'table_detection',
            'Table_ocr',
            f'{order_number}_table_ocr_page{page_number}.json'
        )

        if not os.path.exists(ocr_file_path):
            return jsonify({
                'success': False,
                'error': 'OCR file not found'
            })

        # Load and update OCR data
        with open(ocr_file_path, 'r', encoding='utf-8') as f:
            ocr_data = json.load(f)

        if 'table_data' in ocr_data and 'rows' in ocr_data['table_data']:
            if row_index < len(ocr_data['table_data']['rows']):
                # Map field names to the correct keys in the data
                field_mapping = {
                    'מס': 'מס',
                    'shape': 'shape',
                    'קוטר': 'קוטר',
                    'סהכ יחידות': 'סהכ יחידות',
                    'אורך': 'אורך',
                    'משקל': 'משקל',
                    'הערות': 'הערות'
                }
                mapped_field = field_mapping.get(field_name, field_name)
                ocr_data['table_data']['rows'][row_index][mapped_field] = new_value

                # Save the updated OCR data back to file
                with open(ocr_file_path, 'w', encoding='utf-8') as f:
                    json.dump(ocr_data, f, ensure_ascii=False, indent=2)

                # Now save to database using form1dat1 agent (Section 3 format)
                line_number = row_index + 1  # Lines are 1-indexed
                save_to_database_section3(order_number, page_number, line_number, ocr_data['table_data']['rows'][row_index])

                print(f"[DEBUG] Successfully updated table cell and saved to database")
                return jsonify({
                    'success': True,
                    'message': 'Cell updated and saved to database successfully'
                })
            else:
                return jsonify({
                    'success': False,
                    'error': 'Invalid row index'
                })
        else:
            return jsonify({
                'success': False,
                'error': 'Invalid OCR data structure'
            })
    except Exception as e:
        try:
            print(f"[DEBUG] Error updating table cell: {e}")
        except UnicodeEncodeError:
            print(f"[DEBUG] Error updating table cell: [Unicode encoding error]")
        try:
            error_msg = str(e)
        except UnicodeEncodeError:
            error_msg = "Unicode encoding error in exception message"
        return jsonify({
            'success': False,
            'error': error_msg
        })

@app.route('/api/table-ocr/<string:page_number>')
def get_table_ocr_data(page_number):
    """Get table data for a specific page from the database"""
    try:
        # Get the current order number from the latest analysis
        latest_file = get_latest_analysis_file()
        if not latest_file:
            return jsonify({
                'success': False,
                'error': 'No analysis file found'
            })

        # Extract order number from filename
        order_number = os.path.basename(latest_file).replace('_analysis.json', '')

        print(f"[DEBUG] Getting table data from database for order {order_number}, page {page_number}")

        # Get data from database Section 3
        section3_data = form1dat1_agent.get_section_data(order_number, "section_3_shape_analysis")

        if not section3_data:
            return jsonify({
                'success': False,
                'error': f'No database data found for order {order_number}',
                'page_number': page_number
            })

        # Look for the specific page
        page_key = f"page_{page_number}"
        if page_key not in section3_data:
            return jsonify({
                'success': False,
                'error': f'No data found for page {page_number}',
                'page_number': page_number
            })

        page_data = section3_data[page_key]
        order_lines = page_data.get('order_lines', {})

        # Convert database format to the format expected by the frontend
        rows = []
        for line_key in sorted(order_lines.keys(), key=lambda x: int(x.split('_')[1])):
            line_data = order_lines[line_key]

            # Map database fields to the format expected by frontend
            row = {
                'row_number': line_data.get('line_number', 0),
                'מס': line_data.get('order_line_no', ''),
                'shape': line_data.get('shape_number', ''),
                'קוטר': line_data.get('diameter', ''),
                'סהכ יחידות': str(line_data.get('number_of_units', 0)),
                'אורך': line_data.get('length', ''),  # Length from database
                'משקל': line_data.get('weight', ''),  # Weight from database
                'הערות': line_data.get('notes', ''),  # Notes from database
                'checked': line_data.get('checked', False)  # Checked status from database
            }
            rows.append(row)

        # Create table_data structure compatible with frontend
        table_data = {
            'format': 'format 1',
            'page_number': page_number,
            'total_rows': len(rows),
            'rows': rows
        }

        print(f"[DEBUG] Retrieved {len(rows)} rows from database for page {page_number}")

        return jsonify({
            'success': True,
            'page_number': page_number,
            'order_number': order_number,
            'table_data': table_data,
            'total_rows': len(rows),
            'rows': rows
        })

    except Exception as e:
        print(f"[DEBUG] Table data error for page {page_number}: {e}")
        return jsonify({
            'success': False,
            'error': f'Failed to load table data: {str(e)}',
            'page_number': page_number
        })

def save_to_database_section3(order_number, page_number, line_number, row_data):
    """
    Save row data to Section 3 of the database using form1dat1 agent
    Follows the database structure defined in readme_database_structure.txt
    """
    try:
        # Initialize order if it doesn't exist
        form1dat1_agent.initialize_order(order_number)

        # Get current Section 3 data or create new structure
        current_section3 = form1dat1_agent.get_section_data(order_number, "section_3_shape_analysis") or {}

        # Create page structure if it doesn't exist
        page_key = f"page_{page_number}"
        if page_key not in current_section3:
            current_section3[page_key] = {
                "page_number": int(page_number),
                "number_of_order_lines": 0,
                "order_lines": {}
            }

        # Create line structure and populate data
        line_key = f"line_{line_number}"
        # Get existing line data to preserve checked status
        existing_line = current_section3[page_key]["order_lines"].get(line_key, {})

        current_section3[page_key]["order_lines"][line_key] = {
            "line_number": line_number,
            "order_line_no": row_data.get('מס', ''),
            "shape_number": row_data.get('shape', ''),
            "number_of_ribs": 0,  # Default, can be updated later
            "diameter": row_data.get('קוטר', ''),
            "number_of_units": int(row_data.get('סהכ יחידות', 0)) if row_data.get('סהכ יחידות', '').isdigit() else 0,
            "length": row_data.get('אורך', ''),  # Length field
            "weight": row_data.get('משקל', ''),  # Weight field
            "notes": row_data.get('הערות', ''),  # Notes field
            "checked": existing_line.get('checked', False),  # Preserve existing checked status or default to False
            "ribs": {}  # Will be populated when shape analysis is available
        }

        # Update the number of order lines for this page
        current_section3[page_key]["number_of_order_lines"] = len(current_section3[page_key]["order_lines"])

        # Save to database
        success = form1dat1_agent.update_section(order_number, "section_3_shape_analysis", current_section3, merge=False)

        if success:
            print(f"[OK] Saved to database: Order {order_number}, Page {page_number}, Line {line_number}")
        else:
            print(f"[ERROR] Failed to save to database")

        return success

    except Exception as e:
        try:
            print(f"[ERROR] Error saving to database Section 3: {str(e)}")
        except UnicodeEncodeError:
            print(f"[ERROR] Error saving to database Section 3: [Unicode encoding error]")
        return False

@app.route('/api/update-checked-status', methods=['POST'])
def update_checked_status():
    """Update the checked status for a specific line and save complete line data from screen"""
    try:
        data = request.json
        order_number = data.get('orderNumber')
        page_number = data.get('pageNumber')
        line_number = data.get('lineNumber')
        checked = data.get('checked')
        row_data_from_screen = data.get('rowData', {})

        print(f"[DEBUG] Updating checked status: Order {order_number}, Page {page_number}, Line {line_number}, Checked: {checked}")
        try:
            print(f"[DEBUG] Screen data: {row_data_from_screen}")
        except UnicodeEncodeError:
            print(f"[DEBUG] Screen data: [Hebrew data with {len(row_data_from_screen)} fields]")

        # Save the complete line data from screen to database
        row_data_saved = False
        if row_data_from_screen:
            # Save the complete line data from screen to database
            save_success = save_to_database_section3(order_number, page_number, line_number, row_data_from_screen)

            if save_success:
                print(f"[OK] Saved complete line data from screen for line {line_number} on page {page_number} (checked={checked})")
                row_data_saved = True
            else:
                print(f"[WARNING] Could not save complete line data for line {line_number}")
        else:
            print(f"[WARNING] No row data received from screen for line {line_number}")

        # Update the checked status
        success = form1dat1_agent.update_line_checked_status(order_number, page_number, line_number, checked)

        if success:
            return jsonify({
                'success': True,
                'message': f'Line {line_number} on page {page_number} marked as {"checked" if checked else "unchecked"} and data saved'
            })
        else:
            return jsonify({
                'success': False,
                'error': 'Failed to update checked status'
            })

    except Exception as e:
        try:
            print(f"[DEBUG] Error updating checked status: {e}")
        except UnicodeEncodeError:
            print(f"[DEBUG] Error updating checked status: [Unicode encoding error]")
        try:
            error_msg = str(e)
        except UnicodeEncodeError:
            error_msg = "Unicode encoding error in exception message"
        return jsonify({
            'success': False,
            'error': error_msg
        })

@app.route('/api/shape-images/<string:order_number>/<int:page_number>')
def get_shape_images(order_number, page_number):
    """Get list of shape images for a specific order and page"""
    try:
        # Path to the shapes folder
        shapes_folder = os.path.join('io', 'fullorder_output', 'table_detection', 'shapes')

        if not os.path.exists(shapes_folder):
            return jsonify({
                'success': False,
                'error': 'Shapes folder not found',
                'images': []
            })

        # Find all shape images for this order and page
        pattern = f"{order_number}_drawing_row_*_page{page_number}.png"
        image_files = []

        for filename in os.listdir(shapes_folder):
            if fnmatch.fnmatch(filename, pattern):
                # Extract row number from filename
                try:
                    # Pattern: {order}_drawing_row_{row}_page{page}.png
                    parts = filename.replace('.png', '').split('_')
                    row_index = parts.index('row')
                    row_number = int(parts[row_index + 1])

                    image_files.append({
                        'filename': filename,
                        'row_number': row_number,
                        'url': f'/api/shape-image/{order_number}/{page_number}/{row_number}'
                    })
                except (ValueError, IndexError):
                    # Skip files that don't match expected pattern
                    continue

        # Sort by row number
        image_files.sort(key=lambda x: x['row_number'])

        print(f"[DEBUG] Found {len(image_files)} shape images for order {order_number}, page {page_number}")

        return jsonify({
            'success': True,
            'order_number': order_number,
            'page_number': page_number,
            'images': image_files,
            'total_images': len(image_files)
        })

    except Exception as e:
        print(f"[ERROR] Failed to get shape images: {e}")
        return jsonify({
            'success': False,
            'error': str(e),
            'images': []
        })

@app.route('/api/shape-image/<string:order_number>/<int:page_number>/<int:row_number>')
def serve_shape_image_by_row(order_number, page_number, row_number):
    """Serve a specific shape image file"""
    try:
        # Construct the filename
        filename = f"{order_number}_drawing_row_{row_number}_page{page_number}.png"

        # Path to the shapes folder
        shapes_folder = os.path.join('io', 'fullorder_output', 'table_detection', 'shapes')
        file_path = os.path.join(shapes_folder, filename)

        if not os.path.exists(file_path):
            # Return a 404 error
            abort(404)

        # Serve the image file
        return send_file(file_path, mimetype='image/png')

    except Exception as e:
        print(f"[ERROR] Failed to serve shape image: {e}")
        abort(500)

if __name__ == "__main__":
    # Create necessary directories
    os.makedirs('templates', exist_ok=True)
    os.makedirs('static/css', exist_ok=True)
    os.makedirs('static/js', exist_ok=True)
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    print("IRONMAN Web Interface Starting...")
    print("Navigate to: http://localhost:5000")
    print("Press Ctrl+C to stop the server")
    print("[DEBUG] UPDATED CODE LOADED - Version with debug logging")

    # Run the Flask app with template auto-reload enabled
    app.run(debug=True, host='0.0.0.0', port=5000, use_reloader=True)
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
import io
import sys

# Import the OrderHeader agent
from agents.llm_agents.orderheader_agent import OrderHeaderAgent

app = Flask(__name__)
CORS(app)

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

if __name__ == '__main__':
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
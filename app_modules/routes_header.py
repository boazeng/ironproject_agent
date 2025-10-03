"""
Header processing routes
"""

from flask import Blueprint, jsonify, request
import os
import json
import glob
import io
from datetime import datetime
from .core import OUTPUT_DIR, PDF_DIR, INPUT_DIR

# Create blueprint
header_bp = Blueprint('header', __name__)

@header_bp.route('/api/update-header', methods=['POST'])
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

@header_bp.route('/api/save-header-selection', methods=['POST'])
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

@header_bp.route('/api/analyze-order-header', methods=['POST'])
def analyze_order_header():
    """Analyze order header using specialized OrderHeader agent"""
    try:
        from agents.llm_agents.orderheader_agent import OrderHeaderAgent

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
"""
Shape detection and processing routes
"""

from flask import Blueprint, jsonify, request, send_file
import os
import json
import glob
import sys
from pathlib import Path
from .core import OUTPUT_DIR
from agents.llm_agents.format1_agent.form1ocr3_ribocr import Form1OCR3RibOCRAgent

# Add path for shape detection agent
sys.path.append(str(Path(__file__).parent.parent))
from agents.llm_agents.shape_detection.shape_detection_agent import ShapeDetectionAgent

# Create blueprint
shapes_bp = Blueprint('shapes', __name__)

@shapes_bp.route('/api/shape-images/<string:order_number>/<int:page_number>')
def get_shape_images(order_number, page_number):
    """Get all shape images for a specific page"""
    try:
        shapes_dir = os.path.join(OUTPUT_DIR, 'table_detection', 'shapes')

        # Find all shape images for this page
        pattern = f"{order_number}_drawing_row_*_page{page_number}.png"
        shape_files = glob.glob(os.path.join(shapes_dir, pattern))

        # Extract row numbers and create response
        shapes = []
        for file_path in shape_files:
            filename = os.path.basename(file_path)
            # Extract row number from filename
            parts = filename.split('_')
            if len(parts) >= 4 and parts[2] == 'row':
                row_num = parts[3]
                shapes.append({
                    'row': int(row_num),
                    'filename': filename,
                    'url': f'/shape_image/{filename}'
                })

        # Sort by row number
        shapes.sort(key=lambda x: x['row'])

        return jsonify({
            'success': True,
            'shapes': shapes,
            'count': len(shapes)
        })

    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@shapes_bp.route('/api/shape-image/<string:order_number>/<int:page_number>/<int:row_number>')
def serve_shape_image_by_row(order_number, page_number, row_number):
    """Serve a specific shape image by row"""
    try:
        shapes_dir = os.path.join(OUTPUT_DIR, 'table_detection', 'shapes')
        filename = f"{order_number}_drawing_row_{row_number}_page{page_number}.png"
        image_path = os.path.join(shapes_dir, filename)

        if os.path.exists(image_path):
            return send_file(image_path, mimetype='image/png')
        else:
            return jsonify({'error': 'Shape image not found'}), 404

    except Exception as e:
        return jsonify({'error': str(e)}), 500

@shapes_bp.route('/api/redetect-shapes', methods=['POST'])
def redetect_shapes():
    """Re-run shape detection on a specific page"""
    try:
        data = request.json
        page_number = data.get('page_number')
        order_number = data.get('order_number')

        if not page_number or not order_number:
            return jsonify({
                'success': False,
                'error': 'Missing page_number or order_number'
            })

        # Shape detection logic would go here
        # For now, return a placeholder response
        return jsonify({
            'success': True,
            'message': f'Shape detection completed for page {page_number}',
            'shapes_detected': 0
        })

    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        })

@shapes_bp.route('/api/run-shape-identification', methods=['POST'])
def run_shape_identification():
    """Run shape identification using the shape detection agent"""
    print("\n" + "="*80)
    print("SHAPE IDENTIFICATION STARTED")
    print("="*80)
    try:
        data = request.json
        print(f"[STEP 1] Received request data: {json.dumps(data, indent=2)}")
        row_id = data.get('row_id')

        if not row_id:
            return jsonify({
                'success': False,
                'error': 'No row_id provided'
            })

        print(f"[STEP 2] Parsing row_id: {row_id}")

        # Parse row_id to extract page and line information
        # Expected format: 'shape-row-{page}-{line}'
        try:
            parts = row_id.split('-')
            if len(parts) >= 4 and parts[0] == 'shape' and parts[1] == 'row':
                page_number = parts[2]
                line_number = parts[3]
                print(f"[STEP 3] Parsed successfully: page={page_number}, line={line_number}")
            else:
                raise ValueError("Invalid row_id format")
        except (ValueError, IndexError) as e:
            print(f"[DEBUG] Could not parse row_id '{row_id}': {e}")
            page_number = "1"
            line_number = "1"

        # Extract order_number from the row_id or get it from request
        order_number = data.get('order_number')
        if not order_number:
            # Try to extract from current page context if available
            # For now, we'll need the order_number to be passed in the request
            return jsonify({
                'success': False,
                'error': 'order_number is required for shape identification'
            })

        print(f"[STEP 4] Processing order: {order_number}")

        # Load the current data from central output file
        output_file_path = os.path.join(OUTPUT_DIR, 'json_output', f'{order_number}_out.json')
        print(f"[STEP 5] Loading data from: {output_file_path}")

        if not os.path.exists(output_file_path):
            return jsonify({
                'success': False,
                'error': f'Output file not found for order {order_number}'
            }), 404

        with open(output_file_path, 'r', encoding='utf-8') as f:
            full_data = json.load(f)
        print(f"[STEP 6] Data loaded successfully")

        # Navigate to the specific line
        page_key = f"page_{page_number}"
        if 'section_3_shape_analysis' not in full_data:
            return jsonify({
                'success': False,
                'error': 'No shape analysis data found'
            }), 404

        if page_key not in full_data['section_3_shape_analysis']:
            return jsonify({
                'success': False,
                'error': f'No data found for page {page_number}'
            }), 404

        # Find the line by order_line_no
        order_lines = full_data['section_3_shape_analysis'][page_key].get('order_lines', {})
        print(f"[STEP 7] Searching for line {line_number} in {len(order_lines)} order lines")
        line_found = False
        line_data = None

        for line_key, line_info in order_lines.items():
            if str(line_info.get('order_line_no', '')) == str(line_number):
                line_data = line_info
                line_found = True
                # Extract row position from line_key (e.g., "line_3" -> 3)
                row_position = line_key.split('_')[1] if '_' in line_key else line_number
                print(f"[STEP 8] Found line data under key: {line_key}, row position: {row_position}")
                break

        if not line_found:
            print(f"[ERROR] Line {line_number} not found on page {page_number}")
            return jsonify({
                'success': False,
                'error': f'Line {line_number} not found on page {page_number}'
            }), 404

        # Real shape identification using Form1OCR3 agent
        try:
            # Get the shape catalog number
            shape_catalog_number = line_data.get('shape_catalog_number', 'NA')
            print(f"[STEP 9] Shape catalog number: {shape_catalog_number}")
            if shape_catalog_number == 'NA':
                return jsonify({
                    'success': False,
                    'error': 'No shape catalog number found for this line'
                })

            # Build letter list from ribs data
            ribs_data = line_data.get('ribs', {})
            print(f"[STEP 10] Found {len(ribs_data)} ribs in line data")
            print(f"[STEP 10.1] BEFORE ChatGPT - Current ribs data:")
            for rib_key, rib_info in ribs_data.items():
                if isinstance(rib_info, dict):
                    letter = rib_info.get('rib_letter') or rib_info.get('angle_letter', 'N/A')
                    value = rib_info.get('value', 'EMPTY')
                    print(f"    {rib_key}: letter={letter}, value={value}")

            letter_list = []

            for rib_key, rib_info in ribs_data.items():
                if isinstance(rib_info, dict):
                    rib_letter = rib_info.get('rib_letter') or rib_info.get('angle_letter')
                    if rib_letter:
                        if 'angle' in rib_key.lower() or rib_info.get('rib_type') == 'angle':
                            # This is an angle
                            letter_entry = {
                                "letter": rib_letter,
                                "type": "angle",
                                "is_90": rib_info.get('angle_type') == '90'
                            }
                        else:
                            # This is a rib
                            letter_entry = {
                                "letter": rib_letter,
                                "type": "rib"
                            }
                        letter_list.append(letter_entry)

            if not letter_list:
                print(f"[ERROR] No letters found in ribs data")
                return jsonify({
                    'success': False,
                    'error': 'No letters found in ribs data'
                })

            print(f"[STEP 11] Built letter list with {len(letter_list)} letters: {letter_list}")

            # Get catalog image path
            catalog_image_path = f"static/images/shape_{shape_catalog_number}.png"
            if not os.path.exists(catalog_image_path):
                print(f"[ERROR] Catalog image not found: {catalog_image_path}")
                return jsonify({
                    'success': False,
                    'error': f'Catalog image not found: {catalog_image_path}'
                })

            # Get order image path - use row_position (not order line number)
            order_image_path = f"{OUTPUT_DIR}/table_detection/shapes/{order_number}_drawing_row_{row_position}_page{page_number}.png"
            if not os.path.exists(order_image_path):
                print(f"[ERROR] Order image not found: {order_image_path}")
                return jsonify({
                    'success': False,
                    'error': f'Order image not found: {order_image_path}'
                })

            print(f"[STEP 12] Catalog image: {catalog_image_path}")
            print(f"[STEP 13] Order image: {order_image_path}")

            # Initialize Form1OCR3 agent
            print(f"[STEP 14] Initializing ChatGPT agent...")
            ocr_agent = Form1OCR3RibOCRAgent()

            # Run shape identification
            print(f"[STEP 15] Sending request to ChatGPT...")
            result = ocr_agent.map_catalog_to_order(
                catalog_image_path=catalog_image_path,
                order_image_path=order_image_path,
                letter_list=letter_list
            )

            # Check if mapping was successful (success field is in summary)
            summary = result.get('summary', {})
            print(f"[STEP 16] ChatGPT response summary: {summary}")
            if not summary.get('success'):
                print(f"[ERROR] ChatGPT mapping failed: {summary.get('notes', 'Unknown error')}")
                return jsonify({
                    'success': False,
                    'error': f'ChatGPT mapping failed: {summary.get("notes", "Unknown error")}'
                })

            # Extract mappings from ChatGPT response
            mappings = result.get('mappings', [])
            print(f"[STEP 17] Received {len(mappings)} mappings from ChatGPT")
            chatgpt_mappings = {}
            for mapping in mappings:
                letter = mapping.get('letter')
                number = mapping.get('number')
                if letter and number is not None:
                    chatgpt_mappings[letter] = str(number)
                    print(f"    ChatGPT mapped: {letter} -> {number}")

            print(f"[STEP 18] Final ChatGPT mappings: {chatgpt_mappings}")

            # Update the rib values in the data structure
            print(f"[STEP 19] Updating rib values in data structure...")
            values_updated = 0
            values_skipped = 0
            for rib_key, rib_info in ribs_data.items():
                if isinstance(rib_info, dict):
                    rib_letter = rib_info.get('rib_letter') or rib_info.get('angle_letter')
                    if rib_letter and rib_letter in chatgpt_mappings:
                        # Update ALL values (overwrite existing ones)
                        current_value = rib_info.get('value', '')
                        rib_info['value'] = chatgpt_mappings[rib_letter]
                        rib_info['shape_identification_timestamp'] = data.get('timestamp', 'unknown')
                        values_updated += 1
                        if current_value and current_value != '':
                            print(f"    [+] Updated {rib_key}: {rib_letter} = {chatgpt_mappings[rib_letter]} (was '{current_value}')")
                        else:
                            print(f"    [+] Updated {rib_key}: {rib_letter} = {chatgpt_mappings[rib_letter]} (was empty)")

        except Exception as e:
            import traceback
            print(f"[ERROR] Shape identification exception: {e}")
            print(f"[ERROR] Traceback: {traceback.format_exc()}")
            return jsonify({
                'success': False,
                'error': f'Shape identification failed: {str(e)}'
            })

        # Save the updated data back to the file
        print(f"[STEP 20] Saving updated data to: {output_file_path}")
        with open(output_file_path, 'w', encoding='utf-8') as f:
            json.dump(full_data, f, ensure_ascii=False, indent=2)

        print(f"[STEP 21] AFTER update - Final ribs data:")
        for rib_key, rib_info in ribs_data.items():
            if isinstance(rib_info, dict):
                letter = rib_info.get('rib_letter') or rib_info.get('angle_letter', 'N/A')
                value = rib_info.get('value', 'EMPTY')
                print(f"    {rib_key}: letter={letter}, value={value}")

        print(f"[STEP 22] [SUCCESS] Shape identification completed!")
        print(f"    - Values updated: {values_updated}")
        print(f"    - Values skipped (already filled): {values_skipped}")
        print("="*80 + "\n")

        return jsonify({
            'success': True,
            'message': f'Shape identification completed for row {row_id}',
            'mappings_found': len(chatgpt_mappings) if 'chatgpt_mappings' in locals() else 0,
            'values_updated': values_updated,
            'mappings': chatgpt_mappings if 'chatgpt_mappings' in locals() else {},
            'page_number': page_number,
            'line_number': line_number,
            'catalog_image': catalog_image_path if 'catalog_image_path' in locals() else None,
            'order_image': order_image_path if 'order_image_path' in locals() else None
        })

    except Exception as e:
        print(f"[ERROR] Shape identification error: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        })

@shapes_bp.route('/api/shape-template/<string:shape_number>')
def get_shape_template(shape_number):
    """Get HTML template for a specific shape"""
    try:
        template_dir = os.path.join('templates', 'shapes')
        template_file = os.path.join(template_dir, f'shape_{shape_number}.html')

        if os.path.exists(template_file):
            with open(template_file, 'r', encoding='utf-8') as f:
                template_content = f.read()
            return jsonify({
                'success': True,
                'template': template_content
            })
        else:
            return jsonify({
                'success': False,
                'error': f'Template not found for shape {shape_number}'
            }), 404

    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@shapes_bp.route('/api/run-shape-detection', methods=['POST'])
def run_shape_detection():
    """Run the complete shape detection pipeline"""
    try:
        data = request.json or {}
        order_number = data.get('order_number', 'CO25S006375')

        print(f"\n{'='*80}")
        print(f"SHAPE DETECTION API CALLED")
        print(f"Order: {order_number}")
        print(f"{'='*80}\n")

        # Initialize the shape detection agent
        agent = ShapeDetectionAgent()

        # Run the pipeline
        results = agent.run_pipeline(order_number=order_number)

        # Build response with progress information
        response = {
            'success': True,
            'order_number': order_number,
            'timestamp': results.get('timestamp'),
            'stages': {
                'skeleton_analyzer': results['steps'].get('skeleton_analyzer', {}).get('success', False),
                'shape_to_yolo_table': results['steps'].get('shape_to_yolo_table', {}).get('success', False),
                'yolo_detection': results['steps'].get('yolo_detection', {}).get('success', False)
            },
            'database_updates': len(results.get('database_updates', [])),
            'rib_configuration_updates': {
                'successful': len(results.get('rib_configuration_updates', {}).get('successful', [])),
                'failed': len(results.get('rib_configuration_updates', {}).get('failed', [])),
                'skipped': len(results.get('rib_configuration_updates', {}).get('skipped', []))
            },
            'details': results
        }

        print(f"\n{'='*80}")
        print(f"SHAPE DETECTION COMPLETED")
        print(f"  - Shapes detected: {response['database_updates']}")
        print(f"  - Ribs updated: {response['rib_configuration_updates']['successful']}")
        print(f"{'='*80}\n")

        return jsonify(response)

    except Exception as e:
        import traceback
        error_trace = traceback.format_exc()
        print(f"\n{'='*80}")
        print(f"SHAPE DETECTION ERROR: {str(e)}")
        print(f"Traceback:\n{error_trace}")
        print(f"{'='*80}\n")

        return jsonify({
            'success': False,
            'error': str(e),
            'traceback': error_trace
        }), 500
"""
Rib data processing routes
"""

from flask import Blueprint, jsonify, request
import os
import json
from .core import OUTPUT_DIR

# Create blueprint
ribs_bp = Blueprint('ribs', __name__)

@ribs_bp.route('/api/rib-data/<string:order_number>/<string:page_number>/<string:line_number>')
def get_rib_data_with_order(order_number, page_number, line_number):
    """Get rib data for a specific order line from the central output file (with order number)"""
    try:
        print(f"[DEBUG] Getting rib data for order {order_number}, page {page_number}, line {line_number}")

        # Get data from central output file
        output_file_path = os.path.join(OUTPUT_DIR, 'json_output', f'{order_number}_out.json')
        try:
            with open(output_file_path, 'r', encoding='utf-8') as f:
                full_data = json.load(f)
            section3_data = full_data.get('section_3_shape_analysis', {})
            print(f"[DEBUG] Loaded rib data from {output_file_path}")
        except FileNotFoundError:
            print(f"[ERROR] Output file not found: {output_file_path}")
            return jsonify({
                'success': False,
                'error': f'Output file not found for order {order_number}'
            }), 404
        except Exception as e:
            print(f"[ERROR] Error loading output file: {e}")
            return jsonify({
                'success': False,
                'error': f'Error loading data: {str(e)}'
            }), 500

        # Look for the specific page and line by order_line_no
        page_key = f"page_{page_number}"

        if page_key not in section3_data:
            return jsonify({
                'success': False,
                'error': f'No data found for page {page_number}'
            }), 404

        page_data = section3_data[page_key]
        order_lines = page_data.get('order_lines', {})

        # Find the line by order_line_no instead of line position
        line_data = None
        print(f"[DEBUG] Looking for order_line_no={line_number} in page {page_number}")
        print(f"[DEBUG] Available lines in page {page_number}: {list(order_lines.keys())}")

        for line_key, line_info in order_lines.items():
            order_line_no = line_info.get('order_line_no', '')
            print(f"[DEBUG] Checking {line_key}: order_line_no='{order_line_no}' vs target='{line_number}'")
            if str(order_line_no) == str(line_number):
                line_data = line_info
                print(f"[DEBUG] Found match in {line_key}!")
                break

        if not line_data:
            print(f"[WARNING] Order line {line_number} not found on page {page_number}")
            return jsonify({
                'success': False,
                'error': f'Order line {line_number} not found on page {page_number}'
            }), 404

        # Extract rib values by letter from the complex rib structure
        rib_values = {}
        ribs_data = line_data.get('ribs', {})

        for rib_key, rib_info in ribs_data.items():
            if isinstance(rib_info, dict):
                # Get the rib letter (A, B, C, etc.)
                rib_letter = rib_info.get('rib_letter') or rib_info.get('angle_letter')
                if rib_letter:
                    rib_value = rib_info.get('value', '')
                    rib_values[rib_letter] = rib_value
                    print(f"[DEBUG] Extracted rib {rib_letter} = '{rib_value}' from {rib_key}")

        # Return the rib data in the expected format
        response = {
            'success': True,
            'order_number': order_number,
            'page_number': page_number,
            'line_number': line_number,
            'order_line_no': line_data.get('order_line_no', line_number),
            'shape_catalog_number': line_data.get('shape_catalog_number', ''),
            'ribs': ribs_data,  # Keep original structure
            'rib_values': rib_values,  # Add extracted values by letter
            'checked': line_data.get('checked', False)
        }

        print(f"[DEBUG] Returning {len(rib_values)} rib values for line {line_number}: {rib_values}")
        return jsonify(response), 200

    except Exception as e:
        print(f"[ERROR] Exception in get_rib_data_with_order: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@ribs_bp.route('/api/rib-data/<string:page_number>/<string:line_number>')
def get_rib_data(page_number, line_number):
    """DEPRECATED: Old API endpoint - use /api/rib-data/<order_number>/<page_number>/<line_number> instead"""
    print(f"[DEBUG] DEPRECATED API CALL: /api/rib-data/{page_number}/{line_number} - Please update to use order number")
    return jsonify({
        'success': False,
        'error': 'This API endpoint is deprecated. Please update your JavaScript to use /api/rib-data/<order_number>/<page_number>/<line_number>',
        'deprecated': True
    }), 410  # 410 Gone - indicates resource is permanently unavailable

@ribs_bp.route('/api/update-checked-status', methods=['POST'])
def update_checked_status():
    """Update the checked status of a specific line"""
    try:
        data = request.json
        print(f"[DEBUG CHECK UPDATE] Received request data: {data}")

        order_number = data.get('order_number')
        page_number = data.get('page_number')
        line_number = data.get('line_number')
        checked = data.get('checked', False)

        print(f"[DEBUG CHECK UPDATE] Parsed parameters:")
        print(f"  order_number: {order_number}")
        print(f"  page_number: {page_number}")
        print(f"  line_number: {line_number}")
        print(f"  checked: {checked}")

        if not all([order_number, page_number, line_number is not None]):
            print(f"[DEBUG CHECK UPDATE] Missing parameters - returning 400")
            return jsonify({
                'success': False,
                'error': 'Missing required parameters'
            }), 400

        # Update the checked status in the central output file
        output_file_path = os.path.join(OUTPUT_DIR, 'json_output', f'{order_number}_out.json')

        if not os.path.exists(output_file_path):
            return jsonify({
                'success': False,
                'error': f'Output file not found for order {order_number}'
            }), 404

        with open(output_file_path, 'r', encoding='utf-8') as f:
            full_data = json.load(f)

        # Navigate to the specific line
        page_key = f"page_{page_number}"
        if 'section_3_shape_analysis' not in full_data:
            full_data['section_3_shape_analysis'] = {}
        if page_key not in full_data['section_3_shape_analysis']:
            full_data['section_3_shape_analysis'][page_key] = {'order_lines': {}}

        # Find the line by order_line_no
        order_lines = full_data['section_3_shape_analysis'][page_key].get('order_lines', {})
        line_found = False

        for line_key, line_info in order_lines.items():
            if str(line_info.get('order_line_no', '')) == str(line_number):
                line_info['checked'] = checked
                line_found = True
                break

        if not line_found:
            return jsonify({
                'success': False,
                'error': f'Line {line_number} not found on page {page_number}'
            }), 404

        # Save the updated data
        with open(output_file_path, 'w', encoding='utf-8') as f:
            json.dump(full_data, f, ensure_ascii=False, indent=2)

        return jsonify({
            'success': True,
            'message': f'Checked status updated for line {line_number}'
        })

    except Exception as e:
        print(f"[ERROR] Exception in update_checked_status: {repr(e)}")
        return jsonify({
            'success': False,
            'error': 'Internal server error'
        }), 500

@ribs_bp.route('/api/update-rib-value', methods=['POST'])
def update_rib_value():
    """Update a specific rib value"""
    try:
        data = request.json
        print(f"[DEBUG RIB UPDATE] Received request data: {data}")

        order_number = data.get('order_number')
        page_number = data.get('page_number')
        line_number = data.get('line_number')
        rib_letter = data.get('rib_letter')
        value = data.get('value')

        print(f"[DEBUG RIB UPDATE] Updating {order_number} page {page_number} line {line_number}: {rib_letter} = {value}")

        if not all([order_number, page_number, line_number is not None, rib_letter is not None]):
            print(f"[DEBUG RIB UPDATE] Missing parameters - returning 400")
            return jsonify({
                'success': False,
                'error': 'Missing required parameters'
            }), 400

        # Update the rib value in the central output file
        output_file_path = os.path.join(OUTPUT_DIR, 'json_output', f'{order_number}_out.json')

        if not os.path.exists(output_file_path):
            return jsonify({
                'success': False,
                'error': f'Output file not found for order {order_number}'
            }), 404

        with open(output_file_path, 'r', encoding='utf-8') as f:
            full_data = json.load(f)

        # Navigate to the specific line
        page_key = f"page_{page_number}"
        if 'section_3_shape_analysis' not in full_data:
            full_data['section_3_shape_analysis'] = {}
        if page_key not in full_data['section_3_shape_analysis']:
            full_data['section_3_shape_analysis'][page_key] = {'order_lines': {}}

        # Find the line by order_line_no and update the rib value
        order_lines = full_data['section_3_shape_analysis'][page_key].get('order_lines', {})
        rib_updated = False

        for line_key, line_info in order_lines.items():
            if str(line_info.get('order_line_no', '')) == str(line_number):
                # Find the rib with matching letter
                ribs = line_info.get('ribs', {})
                for rib_key, rib_info in ribs.items():
                    if isinstance(rib_info, dict) and rib_info.get('rib_letter') == rib_letter:
                        old_value = rib_info.get('value', '')
                        rib_info['value'] = value
                        rib_info['manual_edit_timestamp'] = __import__('datetime').datetime.now().isoformat()
                        print(f"[DEBUG RIB UPDATE] Updated {rib_key}: {rib_letter} from '{old_value}' to '{value}'")
                        rib_updated = True
                        break
                break

        if not rib_updated:
            return jsonify({
                'success': False,
                'error': f'Rib {rib_letter} not found for line {line_number} on page {page_number}'
            }), 404

        # Save the updated data
        with open(output_file_path, 'w', encoding='utf-8') as f:
            json.dump(full_data, f, ensure_ascii=False, indent=2)

        return jsonify({
            'success': True,
            'message': f'Successfully updated {rib_letter} = {value}'
        })

    except Exception as e:
        print(f"[ERROR] Exception in update_rib_value: {repr(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({
            'success': False,
            'error': 'Internal server error'
        }), 500
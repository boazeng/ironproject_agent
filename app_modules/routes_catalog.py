"""
Catalog management routes
"""

from flask import Blueprint, jsonify, request, send_file
import os
import json
import glob
from .core import OUTPUT_DIR

# Import the Form1Dat2Agent for catalog updates
import sys
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'agents', 'llm_agents', 'format1_agent'))
from form1dat2 import Form1Dat2Agent

# Create blueprint
catalog_bp = Blueprint('catalog', __name__)

@catalog_bp.route('/catalog_image/<catalog_number>')
def serve_catalog_image(catalog_number):
    """Serve catalog images from the io/catalog folder"""
    try:
        # Get the project root directory (parent of app_modules)
        project_root = os.path.dirname(os.path.dirname(__file__))
        catalog_dir = os.path.join(project_root, 'io', 'catalog')
        # Format: shape XXX.png where XXX is the catalog number
        filename = f"shape {catalog_number}.png"
        image_path = os.path.join(catalog_dir, filename)

        if os.path.exists(image_path):
            return send_file(image_path, mimetype='image/png')
        else:
            return jsonify({'error': f'Catalog image not found for {catalog_number}'}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@catalog_bp.route('/api/catalog-data')
def get_catalog_data():
    """Get catalog data for shape matching"""
    try:
        # Get the project root directory (parent of app_modules)
        project_root = os.path.dirname(os.path.dirname(__file__))
        catalog_file = os.path.join(project_root, 'io', 'catalog', 'catalog_format.json')

        if not os.path.exists(catalog_file):
            return jsonify({'error': 'Catalog data not found'}), 404

        with open(catalog_file, 'r', encoding='utf-8') as f:
            catalog_data = json.load(f)

        return jsonify(catalog_data)

    except Exception as e:
        return jsonify({'error': str(e)}), 500

@catalog_bp.route('/api/catalog-ribs/<string:catalog_number>')
def get_catalog_ribs(catalog_number):
    """Get rib configuration for a specific catalog shape"""
    try:
        # Get the project root directory (parent of app_modules)
        project_root = os.path.dirname(os.path.dirname(__file__))
        catalog_file = os.path.join(project_root, 'io', 'catalog', 'catalog_format.json')

        if not os.path.exists(catalog_file):
            return jsonify({'error': 'Catalog data not found'}), 404

        with open(catalog_file, 'r', encoding='utf-8') as f:
            catalog_data = json.load(f)

        # Find the shape in catalog
        for shape_id, shape_info in catalog_data.items():
            if shape_info.get('catalog_number') == catalog_number:
                return jsonify({
                    'success': True,
                    'catalog_number': catalog_number,
                    'shape_id': shape_id,
                    'ribs': shape_info.get('ribs', []),
                    'rib_count': len(shape_info.get('ribs', []))
                })

        return jsonify({'error': f'Shape {catalog_number} not found in catalog'}), 404

    except Exception as e:
        return jsonify({'error': str(e)}), 500

@catalog_bp.route('/api/update-catalog-number', methods=['POST'])
def update_catalog_number():
    """Update catalog number for a shape in the analysis"""
    try:
        data = request.json
        page_number = data.get('page')
        line_number = data.get('line')
        catalog_number = data.get('catalog_number')

        if not all([page_number, line_number, catalog_number]):
            return jsonify({'success': False, 'error': 'Missing required parameters'})

        # Find the order number from the latest analysis file
        final_json_files = glob.glob(os.path.join(OUTPUT_DIR, 'json_output', '*_out.json'))

        if not final_json_files:
            return jsonify({'success': False, 'error': 'No analysis files found'})

        # Extract order number from filename (e.g., CO25S006375_out.json -> CO25S006375)
        latest_file = final_json_files[0]  # Take the first one for now
        order_number = os.path.basename(latest_file).replace('_out.json', '')

        # Initialize the Form1Dat2Agent
        agent = Form1Dat2Agent()

        # Update the catalog number in the central output file
        result = agent.update_shape_in_order(
            order_number=order_number,
            page_number=int(page_number),
            line_number=int(line_number),
            new_shape_number=catalog_number
        )

        if result['status'] == 'success':
            return jsonify({
                'success': True,
                'message': f'Successfully updated catalog number to {catalog_number} for page {page_number}, line {line_number}',
                'details': result
            })
        else:
            return jsonify({
                'success': False,
                'error': result.get('error', 'Unknown error'),
                'details': result
            })

    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@catalog_bp.route('/api/update-table-cell', methods=['POST'])
def update_table_cell():
    """Update table cell data - compatibility endpoint"""
    try:
        data = request.json
        page_number = data.get('page')
        row_index = data.get('row_index')
        field_name = data.get('field_name')
        new_value = data.get('new_value')

        # Debug logging
        print(f"[DEBUG CATALOG UPDATE] Received request:")
        print(f"  page_number: {page_number}")
        print(f"  row_index: {row_index}")
        print(f"  field_name: {repr(field_name)}")  # Use repr() to safely print Hebrew
        print(f"  new_value: {new_value}")

        if not all([page_number, row_index is not None, field_name, new_value is not None]):
            print(f"[DEBUG CATALOG UPDATE] Missing parameters - returning error")
            return jsonify({'success': False, 'error': 'Missing required parameters'})

        # For catalog field updates, use the same logic as update-catalog-number
        if field_name in ['קטלוג', 'catalog']:  # Hebrew or English for "catalog"
            # Find the order number from the latest analysis file
            final_json_files = glob.glob(os.path.join(OUTPUT_DIR, 'json_output', '*_out.json'))

            if not final_json_files:
                return jsonify({'success': False, 'error': 'No analysis files found'})

            # Extract order number from filename
            latest_file = final_json_files[0]
            order_number = os.path.basename(latest_file).replace('_out.json', '')

            # Initialize the Form1Dat2Agent
            agent = Form1Dat2Agent()

            # Convert row_index (0-based) to line_number (1-based)
            line_number = int(row_index) + 1

            # Update the catalog number in the central output file
            print(f"[DEBUG CATALOG UPDATE] Calling Form1Dat2Agent with:")
            print(f"  order_number: {order_number}")
            print(f"  page_number: {int(page_number)}")
            print(f"  line_number: {line_number}")
            print(f"  new_shape_number: {str(new_value)}")

            result = agent.update_shape_in_order(
                order_number=order_number,
                page_number=int(page_number),
                line_number=line_number,
                new_shape_number=str(new_value)
            )

            print(f"[DEBUG CATALOG UPDATE] Form1Dat2Agent result: {result}")

            if result['status'] == 'success':
                print(f"[DEBUG CATALOG UPDATE] Success - returning success response")
                return jsonify({
                    'success': True,
                    'message': f'Successfully updated catalog to {new_value} for page {page_number}, line {line_number}',
                    'details': result
                })
            else:
                print(f"[DEBUG CATALOG UPDATE] Failed - returning error response")
                return jsonify({
                    'success': False,
                    'error': result.get('error', 'Unknown error'),
                    'details': result
                })
        else:
            # For non-catalog fields, just return success (placeholder)
            return jsonify({
                'success': True,
                'message': f'Updated field to {new_value} for page {page_number}, row {row_index}'
            })

    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})
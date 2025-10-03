"""
Table OCR and data processing routes
"""

from flask import Blueprint, jsonify
import os
import json
import glob
from .core import OUTPUT_DIR

# Create blueprint
table_bp = Blueprint('table', __name__)

@table_bp.route('/api/table-ocr/<string:page_number>')
def get_table_ocr_data(page_number):
    """Get processed table data for a specific page with correct shape catalog numbers"""
    try:
        # First, try to get processed data from the final analysis JSON
        final_json_files = glob.glob(os.path.join(OUTPUT_DIR, 'json_output', '*_out.json'))

        if final_json_files:
            # Load the final analysis data
            with open(final_json_files[0], 'r', encoding='utf-8') as f:
                final_data = json.load(f)

            # Extract data for the requested page
            page_key = f'page_{page_number}'
            page_data = final_data.get('section_3_shape_analysis', {}).get(page_key, {})

            if page_data and 'order_lines' in page_data:
                # Convert to table format with processed shape catalog numbers
                processed_rows = []
                for line_key, line_data in page_data['order_lines'].items():
                    # Get shape catalog number (processed) instead of raw OCR shape description
                    shape_catalog_number = line_data.get('shape_catalog_number', 'NA')
                    if shape_catalog_number == 'NA':
                        shape_catalog_number = ''

                    row = {
                        'row_number': line_data.get('line_number', 0),
                        'מס': line_data.get('order_line_no', ''),
                        'shape': shape_catalog_number,  # Use processed catalog number instead of raw OCR
                        'קוטר': line_data.get('diameter', ''),
                        'סהכ יחידות': line_data.get('number_of_units', ''),
                        'אורך': line_data.get('length', ''),
                        'משקל': line_data.get('weight', ''),
                        'הערות': line_data.get('notes', ''),
                        'קטלוג': shape_catalog_number  # Also set catalog field
                    }
                    processed_rows.append(row)

                response = {
                    'success': True,
                    'rows': processed_rows
                }
                return jsonify(response)

        # Fallback to original OCR data if final analysis not available
        ocr_dir = os.path.join(OUTPUT_DIR, 'table_detection', 'table_ocr')
        ocr_files = glob.glob(os.path.join(ocr_dir, f'*_table_ocr_page{page_number}.json'))

        if not ocr_files:
            return jsonify({'success': False, 'error': f'No data found for page {page_number}'}), 404

        # Load the OCR file as fallback
        with open(ocr_files[0], 'r', encoding='utf-8') as f:
            ocr_data = json.load(f)

        response = {
            'success': True,
            'rows': ocr_data.get('table_data', {}).get('rows', [])
        }
        return jsonify(response)

    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500
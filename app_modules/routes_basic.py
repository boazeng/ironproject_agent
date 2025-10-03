"""
Basic routes and static file serving
"""

from flask import Blueprint, render_template, jsonify, send_file
import os
from .core import OUTPUT_DIR, PDF_DIR

# Create blueprint
basic_bp = Blueprint('basic', __name__)

@basic_bp.route('/')
def index():
    """Serve the main page"""
    return render_template('index.html')

@basic_bp.route('/test')
def test():
    """Test template route"""
    return "Test route is working!"

@basic_bp.route('/status')
def status():
    """Simple status route"""
    return {"status": "ok", "message": "Server is running"}

@basic_bp.route('/api/status')
def get_status():
    """API status endpoint"""
    return jsonify({'status': 'ok', 'message': 'Server is running'})

# PDF serving route
@basic_bp.route('/pdf/<filename>')
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

# Image serving routes
@basic_bp.route('/table_image/<filename>')
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

@basic_bp.route('/shape_image/<filename>')
def serve_shape_image(filename):
    """Serve shape images from the shapes folder"""
    try:
        # Try templates/shapes/shape_images first
        project_root = os.path.dirname(os.path.dirname(__file__))
        template_images_dir = os.path.join(project_root, 'templates', 'shapes', 'shape_images')
        template_image_path = os.path.join(template_images_dir, filename)

        if os.path.exists(template_image_path):
            return send_file(template_image_path, mimetype='image/png')

        # Fallback to original shapes directory
        shapes_dir = os.path.join(OUTPUT_DIR, 'table_detection', 'shapes')
        image_path = os.path.join(shapes_dir, filename)
        if os.path.exists(image_path):
            return send_file(image_path, mimetype='image/png')
        else:
            return jsonify({'error': 'Shape image not found'}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@basic_bp.route('/templates/shapes/shape_images/<filename>')
def serve_template_shape_image(filename):
    """Serve shape images from the templates/shapes/shape_images folder"""
    try:
        # Get absolute path to templates folder
        project_root = os.path.dirname(os.path.dirname(__file__))
        template_images_dir = os.path.join(project_root, 'templates', 'shapes', 'shape_images')
        image_path = os.path.join(template_images_dir, filename)
        if os.path.exists(image_path):
            return send_file(image_path, mimetype='image/png')
        else:
            return jsonify({'error': 'Template shape image not found'}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@basic_bp.route('/shape_template/shape_images/<filename>')
def serve_shape_template_image(filename):
    """Serve shape images for template relative paths"""
    try:
        # Get absolute path to templates folder
        project_root = os.path.dirname(os.path.dirname(__file__))
        template_images_dir = os.path.join(project_root, 'templates', 'shapes', 'shape_images')
        image_path = os.path.join(template_images_dir, filename)
        if os.path.exists(image_path):
            return send_file(image_path, mimetype='image/png')
        else:
            return jsonify({'error': 'Shape template image not found'}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@basic_bp.route('/shape_column_image/<filename>')
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

@basic_bp.route('/order_header_image/<filename>')
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

@basic_bp.route('/shape_template/<shape_number>')
def serve_shape_template(shape_number):
    """Serve shape template HTML files from templates/shapes folder"""
    try:
        template_dir = os.path.join('templates', 'shapes')
        # Format: shape_XXX.html where XXX is the shape number
        filename = f"shape_{shape_number}.html"
        template_path = os.path.join(template_dir, filename)

        if os.path.exists(template_path):
            with open(template_path, 'r', encoding='utf-8') as f:
                template_content = f.read()
            return template_content, 200, {'Content-Type': 'text/html; charset=utf-8'}
        else:
            return f'<div class="template-placeholder"><span>תבנית לא נמצאה עבור צורה {shape_number}</span></div>', 404
    except Exception as e:
        return f'<div class="template-placeholder"><span>שגיאה בטעינת התבנית: {str(e)}</span></div>', 500

@basic_bp.route('/test_template.html')
def serve_test_template():
    """Serve test template page"""
    try:
        import os
        # Get absolute path to test file
        project_root = os.path.dirname(os.path.dirname(__file__))
        test_file = os.path.join(project_root, 'test_template.html')
        return send_file(test_file)
    except Exception as e:
        return f"Error serving test template: {str(e)}", 500

@basic_bp.route('/simple_test.html')
def serve_simple_test():
    """Serve simple test page"""
    try:
        import os
        # Get absolute path to test file
        project_root = os.path.dirname(os.path.dirname(__file__))
        test_file = os.path.join(project_root, 'simple_test.html')
        return send_file(test_file)
    except Exception as e:
        return f"Error serving simple test: {str(e)}", 500

@basic_bp.route('/debug_table.html')
def serve_debug_table():
    """Serve debug table page"""
    try:
        import os
        # Get absolute path to debug file
        project_root = os.path.dirname(os.path.dirname(__file__))
        debug_file = os.path.join(project_root, 'debug_table.html')
        return send_file(debug_file)
    except Exception as e:
        return f"Error serving debug table: {str(e)}", 500
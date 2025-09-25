"""
Shape Template Generator
Converts JSON positioning data from shape_positioning_tool to HTML templates
"""
import json
import os
import base64
from datetime import datetime
from PIL import Image
import io


class ShapeTemplateGenerator:
    def __init__(self):
        self.templates_dir = os.path.join("templates", "shapes")
        self.ensure_templates_dir()

    def ensure_templates_dir(self):
        """Ensure templates/shapes directory exists"""
        if not os.path.exists(self.templates_dir):
            os.makedirs(self.templates_dir, exist_ok=True)

    def image_to_base64(self, image_path):
        """Convert image file to base64 data URI"""
        try:
            if not os.path.exists(image_path):
                return None

            # Open and optimize image
            with Image.open(image_path) as img:
                # Convert to RGB if necessary
                if img.mode in ('RGBA', 'LA', 'P'):
                    img = img.convert('RGB')

                # Resize if too large (max 600x400 for templates)
                max_size = (600, 400)
                img.thumbnail(max_size, Image.Resampling.LANCZOS)

                # Save to bytes
                buffer = io.BytesIO()
                img.save(buffer, format='PNG', optimize=True)
                img_bytes = buffer.getvalue()

                # Convert to base64
                img_base64 = base64.b64encode(img_bytes).decode('utf-8')
                return f"data:image/png;base64,{img_base64}"

        except Exception as e:
            print(f"Error converting image to base64: {str(e)}")
            return None

    def json_to_html(self, json_file_path, shape_number):
        """Convert JSON positioning file to HTML template"""
        try:
            with open(json_file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)

            # Extract shape data
            canvas_width = data.get('canvas_width', 350)
            canvas_height = data.get('canvas_height', 250)
            elements = data.get('elements', [])
            shape_name = data.get('shape_name', f'Shape {shape_number}')
            absolute_positioning = data.get('absolute_positioning', {'enabled': False})

            # Generate HTML content
            html_content = self.generate_html_template(
                shape_number, shape_name, elements, canvas_width, canvas_height, absolute_positioning
            )

            # Save HTML file
            html_file_path = os.path.join(self.templates_dir, f"shape_{shape_number}.html")
            with open(html_file_path, 'w', encoding='utf-8') as f:
                f.write(html_content)

            return html_file_path

        except Exception as e:
            raise Exception(f"Error converting JSON to HTML: {str(e)}")

    def generate_html_template(self, shape_number, shape_name, elements, canvas_width, canvas_height, absolute_positioning=None):
        """Generate HTML template from positioning data"""

        # Start HTML template with absolute positioning info
        html = f"""<!-- Shape {shape_number} Content -->\n"""
        if absolute_positioning and absolute_positioning.get('enabled'):
            ref_point = absolute_positioning.get('reference_point', {})
            html += f"""<!-- Generated with absolute positioning: reference point ({ref_point.get('x', 0)}, {ref_point.get('y', 0)}) -->\n"""
        html += f"""<div id="shape-{shape_number}" class="shape-content">\n"""
        html += f"""    <div class="shape-diagram-with-input" style="position: relative; text-align: center; padding: 60px 20px; min-height: 350px;">\n\n"""

        # Generate input fields from elements
        input_fields = []
        svg_elements = []

        for element in elements:
            element_type = element.get('type', '')

            if element_type == 'text' and element.get('text', '').strip():
                # Check if this is an "Input Field" placeholder (should be standalone) or actual label
                text_content = element.get('text', '').strip()

                if text_content == 'Input Field':
                    # This is a standalone input field, treat as input type
                    element_type = 'input'
                    field_id = f'field_{len(input_fields) + 1}'
                    x = element.get('x', 0)
                    y = element.get('y', 0)
                    width = element.get('width', 100)
                    height = element.get('height', 32)
                    placeholder = element.get('placeholder', '0')

                    # Use absolute positioning if available, otherwise use canvas coordinates
                    if absolute_positioning and absolute_positioning.get('enabled') and 'absolute_positioning' in element:
                        # Use precise positioning from the absolute reference system
                        rel_x = element['absolute_positioning']['relative_x']
                        rel_y = element['absolute_positioning']['relative_y']

                        # Convert relative coordinates to CSS positioning
                        # The reference point is the origin, so add offset for container positioning
                        css_left = rel_x + 175  # Center in 350px container
                        css_top = rel_y + 175   # Center in 350px container

                        # Add comment with absolute positioning info
                        abs_comment = f" <!-- Absolute: rel({rel_x:+.0f},{rel_y:+.0f}) dist={element['absolute_positioning']['distance_from_ref']:.1f} -->"
                    else:
                        # Fallback to canvas coordinates
                        css_left = x - (width // 2)  # Center the input field on the coordinates
                        css_top = y - (height // 2)   # Center the input field on the coordinates
                        abs_comment = f" <!-- Canvas: ({x},{y}) -->"

                    input_html = f"""        <!-- Standalone input field{abs_comment} -->\n"""
                    input_html += f"""        <div style="position: absolute; top: {css_top}px; left: {css_left}px;">\n"""
                    input_html += f"""            <input type="text"\n"""
                    input_html += f"""                   id="length-{field_id}-{shape_number}"\n"""
                    input_html += f"""                   class="inline-shape-input shape-{shape_number}-input"\n"""
                    input_html += f"""                   maxlength="8"\n"""
                    input_html += f"""                   placeholder="{placeholder}"\n"""
                    input_html += f"""                   style="width: {width}px; height: {height}px; font-size: 20px; border: 2px solid #4a90e2; border-radius: 4px; background: #e6f2ff;">\n"""
                    input_html += f"""        </div>\n\n"""
                    input_fields.append(input_html)
                    continue

                # This is a real label - create labeled input field
                label = text_content
                x = element.get('x', 0)
                y = element.get('y', 0)
                font_size = element.get('font_size', 24)

                # Use absolute positioning if available, otherwise use canvas coordinates
                if absolute_positioning and absolute_positioning.get('enabled') and 'absolute_positioning' in element:
                    # Use precise positioning from the absolute reference system
                    rel_x = element['absolute_positioning']['relative_x']
                    rel_y = element['absolute_positioning']['relative_y']

                    # Convert relative coordinates to CSS positioning
                    # The reference point is the origin, so add offset for container positioning
                    css_left = rel_x + 175  # Center in 350px container
                    css_top = rel_y + 175   # Center in 350px container

                    # Add comment with absolute positioning info
                    abs_comment = f" <!-- Absolute: rel({rel_x:+.0f},{rel_y:+.0f}) dist={element['absolute_positioning']['distance_from_ref']:.1f} -->"
                else:
                    # Fallback to canvas coordinates
                    css_left = x - 50  # Adjust for input field width
                    css_top = y - 16   # Adjust for input field height
                    abs_comment = f" <!-- Canvas: ({x},{y}) -->"

                input_html = f"""        <!-- {label} field with label{abs_comment} -->\n"""
                input_html += f"""        <div style="position: absolute; top: {css_top}px; left: {css_left}px; display: flex; align-items: center;">\n"""
                input_html += f"""            <span style="font-size: {font_size}px; font-weight: bold; color: red; margin-right: 8px;">{label}</span>\n"""
                input_html += f"""            <input type="text"\n"""
                input_html += f"""                   id="length-{label}-{shape_number}"\n"""
                input_html += f"""                   class="inline-shape-input shape-{shape_number}-input"\n"""
                input_html += f"""                   maxlength="8"\n"""
                input_html += f"""                   placeholder="0"\n"""
                input_html += f"""                   style="width: 100px; height: 32px; font-size: 20px; border: 2px solid #4a90e2; border-radius: 4px; background: #e6f2ff;">\n"""
                input_html += f"""        </div>\n\n"""
                input_fields.append(input_html)

            elif element_type == 'input':
                # Direct input field without label
                field_id = element.get('field_id', element.get('text', f'field_{len(input_fields)}'))
                x = element.get('x', 0)
                y = element.get('y', 0)
                width = element.get('width', 100)
                height = element.get('height', 32)
                placeholder = element.get('placeholder', '0')

                # Use absolute positioning if available, otherwise use canvas coordinates
                if absolute_positioning and absolute_positioning.get('enabled') and 'absolute_positioning' in element:
                    # Use precise positioning from the absolute reference system
                    rel_x = element['absolute_positioning']['relative_x']
                    rel_y = element['absolute_positioning']['relative_y']

                    # Convert relative coordinates to CSS positioning
                    # The reference point is the origin, so add offset for container positioning
                    css_left = rel_x + 175  # Center in 350px container
                    css_top = rel_y + 175   # Center in 350px container

                    # Add comment with absolute positioning info
                    abs_comment = f" <!-- Absolute: rel({rel_x:+.0f},{rel_y:+.0f}) dist={element['absolute_positioning']['distance_from_ref']:.1f} -->"
                else:
                    # Fallback to canvas coordinates
                    css_left = x - (width // 2)  # Center the input field on the coordinates
                    css_top = y - (height // 2)   # Center the input field on the coordinates
                    abs_comment = f" <!-- Canvas: ({x},{y}) -->"

                input_html = f"""        <!-- Direct input field{abs_comment} -->\n"""
                input_html += f"""        <div style="position: absolute; top: {css_top}px; left: {css_left}px;">\n"""
                input_html += f"""            <input type="text"\n"""
                input_html += f"""                   id="length-{field_id}-{shape_number}"\n"""
                input_html += f"""                   class="inline-shape-input shape-{shape_number}-input"\n"""
                input_html += f"""                   maxlength="8"\n"""
                input_html += f"""                   placeholder="{placeholder}"\n"""
                input_html += f"""                   style="width: {width}px; height: {height}px; font-size: 20px; border: 2px solid #4a90e2; border-radius: 4px; background: #e6f2ff;">\n"""
                input_html += f"""        </div>\n\n"""
                input_fields.append(input_html)

            elif element_type == 'line':
                # Convert line to SVG
                x1 = element.get('start_x', 0)
                y1 = element.get('start_y', 0)
                x2 = element.get('end_x', 0)
                y2 = element.get('end_y', 0)
                color = element.get('color', 'black')
                width = element.get('width', 2)

                svg_line = f"""            <line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" stroke="{color}" stroke-width="{width}"/>\n"""
                svg_elements.append(svg_line)

            elif element_type == 'rectangle':
                # Convert rectangle to SVG
                x = element.get('x', 0)
                y = element.get('y', 0)
                width = element.get('width', 50)
                height = element.get('height', 50)
                color = element.get('color', 'black')
                line_width = element.get('line_width', 2)

                svg_rect = f"""            <rect x="{x}" y="{y}" width="{width}" height="{height}" stroke="{color}" stroke-width="{line_width}" fill="none"/>\n"""
                svg_elements.append(svg_rect)

        # Add input fields to HTML
        for field in input_fields:
            html += field

        # Add SVG section if there are drawing elements
        if svg_elements:
            html += f"""        <!-- Shape drawing -->\n"""
            html += f"""        <svg width="{canvas_width}" height="{canvas_height}" viewBox="0 0 {canvas_width} {canvas_height}" style="margin: 0 auto; display: block;">\n"""
            for svg_element in svg_elements:
                html += svg_element
            html += f"""        </svg>\n\n"""

        # Add user's saved image if available - embed as base64
        image_path = data.get('image_path')
        if image_path and os.path.exists(image_path):
            # Convert image to base64 data URI
            base64_image = self.image_to_base64(image_path)
            if base64_image:
                html += f"""        <!-- User's saved image from positioning tool (embedded) -->\n"""
                html += f"""        <div style="text-align: center; margin-top: 20px;">\n"""
                html += f"""            <img src="{base64_image}"\n"""
                html += f"""                 alt="Shape {shape_number}"\n"""
                html += f"""                 style="max-width: 300px; height: auto; border: 2px solid #ddd; border-radius: 8px; padding: 20px; background-color: white;">\n"""
                html += f"""        </div>\n\n"""
            else:
                # Fallback to external reference if base64 conversion fails
                fallback_path = f'/static/images/shape_{shape_number}.png?v=2024092403'
                html += f"""        <!-- User's saved image from positioning tool (fallback) -->\n"""
                html += f"""        <div style="text-align: center; margin-top: 20px;">\n"""
                html += f"""            <img src="{fallback_path}"\n"""
                html += f"""                 alt="Shape {shape_number}"\n"""
                html += f"""                 style="max-width: 300px; height: auto; border: 2px solid #ddd; border-radius: 8px; padding: 20px; background-color: white;">\n"""
                html += f"""        </div>\n\n"""
        else:
            # Fallback to external reference if no image path in data
            fallback_path = f'/static/images/shape_{shape_number}.png?v=2024092403'
            html += f"""        <!-- Default catalog image (fallback) -->\n"""
            html += f"""        <div style="text-align: center; margin-top: 20px;">\n"""
            html += f"""            <img src="{fallback_path}"\n"""
            html += f"""                 alt="Shape {shape_number}"\n"""
            html += f"""                 style="max-width: 300px; height: auto; border: 2px solid #ddd; border-radius: 8px; padding: 20px; background-color: white;">\n"""
            html += f"""        </div>\n\n"""

        # Add shape name
        html += f"""        <!-- Shape name/description -->\n"""
        html += f"""        <div style="position: absolute; top: 10px; left: 50%; transform: translateX(-50%);\n"""
        html += f"""                    font-size: 18px; font-weight: bold; color: #333;">\n"""
        html += f"""            {shape_name}\n"""
        html += f"""        </div>\n"""

        # Add save button
        html += f"""    </div>\n\n"""
        html += f"""    <div class="modal-buttons" style="margin-top: 30px; text-align: center;">\n"""
        html += f"""        <button id="save-shape-{shape_number}" class="btn btn-success" onclick="saveShape('{shape_number}')"\n"""
        html += f"""                style="padding: 10px 30px; font-size: 18px; background: #28a745; color: white;\n"""
        html += f"""                       border: none; border-radius: 5px; cursor: pointer;">\n"""
        html += f"""            שמור\n"""
        html += f"""        </button>\n"""
        html += f"""    </div>\n"""
        html += f"""</div>\n"""

        return html

    def auto_convert_from_positioning_tool(self, json_file_path):
        """Automatically detect shape number and convert positioning tool JSON to HTML"""
        try:
            # Extract shape number from filename or JSON content
            filename = os.path.basename(json_file_path)
            shape_number = None

            # Try to extract from filename
            if 'shape' in filename.lower():
                parts = filename.lower().replace('.json', '').split('_')
                for part in parts:
                    if part.isdigit():
                        shape_number = part
                        break

            # If not found in filename, try JSON content
            if not shape_number:
                with open(json_file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                shape_number = data.get('shape_number', '999')

            if not shape_number:
                shape_number = '999'  # Default fallback

            # Convert to HTML
            html_file_path = self.json_to_html(json_file_path, shape_number)
            return html_file_path, shape_number

        except Exception as e:
            raise Exception(f"Error in auto-conversion: {str(e)}")


def convert_positioning_json_to_html(json_file_path, shape_number=None):
    """Utility function to convert positioning tool JSON to HTML template"""
    generator = ShapeTemplateGenerator()

    if shape_number:
        return generator.json_to_html(json_file_path, shape_number)
    else:
        return generator.auto_convert_from_positioning_tool(json_file_path)


if __name__ == "__main__":
    # Test the generator
    generator = ShapeTemplateGenerator()
    print("Shape Template Generator ready")
    print(f"Templates will be saved to: {generator.templates_dir}")
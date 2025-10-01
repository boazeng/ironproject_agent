"""Test script to generate shape 218 template with unique positions for each field"""

import json

# Shape 218 has 3 fields: E, C, A
# Based on the eraser coordinates from the tool output, we can estimate field positions:
# Erased area: (128,53) to (164,91) - likely field E position
# Erased area: (244,128) to (265,172) - likely field C position
# Erased area: (130,211) to (177,249) - likely field A position

# Let's create a template with these distinct positions
shape_num = 218
image_width = 300  # max width in web display
image_height = 300  # estimated

# Calculate positions based on erased areas (using center points)
field_positions = {
    'E': {
        'canvas_x': (128 + 164) / 2,  # 146
        'canvas_y': (53 + 91) / 2,     # 72
    },
    'C': {
        'canvas_x': (244 + 265) / 2,  # 254.5
        'canvas_y': (128 + 172) / 2,  # 150
    },
    'A': {
        'canvas_x': (130 + 177) / 2,  # 153.5
        'canvas_y': (211 + 249) / 2,  # 230
    }
}

# Convert canvas positions to web display positions
# The canvas image appears to be around 300x300 pixels
canvas_width = 300
canvas_height = 300

template_parts = []
template_parts.append(f"")
template_parts.append(f"        <div id=\"shape-{shape_num}\" class=\"shape-content\">")
template_parts.append(f"            <div class=\"shape-diagram-with-input\" style=\"position: relative; text-align: center; padding: 40px 0;\">")

for field_letter, pos in field_positions.items():
    # Calculate relative position (0-1 range)
    relative_x = pos['canvas_x'] / canvas_width
    relative_y = pos['canvas_y'] / canvas_height

    # Convert to web display coordinates
    web_pos_x = relative_x * image_width
    web_pos_y = relative_y * image_height

    # Container offsets
    container_padding_top = 40
    image_margin_top = 20

    # Calculate absolute position
    web_top_px = container_padding_top + image_margin_top + web_pos_y

    # For horizontal: offset from center
    center_offset_x = web_pos_x - (image_width / 2)
    web_left_px = center_offset_x

    print(f"Field {field_letter}: canvas({pos['canvas_x']:.1f}, {pos['canvas_y']:.1f}) -> web(top:{web_top_px:.0f}px, left:calc(50% + {web_left_px:.0f}px))")

    # Generate HTML for this field
    template_parts.append(f"                <!-- {field_letter} field - positioned at its original location -->")
    template_parts.append(f"                <div style=\"position: absolute; top: {web_top_px:.0f}px; left: calc(50% + {web_left_px:.0f}px); transform: translate(-50%, -50%); display: flex; align-items: center;\">")
    template_parts.append(f"                    <span style=\"font-size: 20px; font-weight: bold; color: red; margin-right: 8px;\">{field_letter}</span>")
    template_parts.append(f"                    <input type=\"text\"")
    template_parts.append(f"                           id=\"length-{field_letter}-{shape_num}\"")
    template_parts.append(f"                           class=\"inline-shape-input shape-{shape_num}-input\"")
    template_parts.append(f"                           maxlength=\"8\"")
    template_parts.append(f"                           placeholder=\"0\"")
    template_parts.append(f"                           style=\"width: 80px; height: 28px; font-size: 18px; border: 2px solid #4a90e2; border-radius: 4px; background: #e6f2ff;\">")
    template_parts.append(f"                </div>")

# Add the image
template_parts.append(f"")
template_parts.append(f"                <!-- Original catalog shape {shape_num} image -->")
template_parts.append(f"                <div style=\"text-align: center; margin-top: 20px;\">")
template_parts.append(f"                    <img src=\"/static/images/shape_{shape_num}.png?v=2024092403\"")
template_parts.append(f"                         alt=\"Shape {shape_num}\"")
template_parts.append(f"                         style=\"max-width: 300px; height: auto; border: 2px solid #ddd; border-radius: 8px; padding: 20px; background-color: white;\">")
template_parts.append(f"                </div>")

# Close containers
template_parts.append(f"            </div>")
template_parts.append(f"            <div class=\"modal-buttons\" style=\"margin-top: 30px;\">")
template_parts.append(f"                <button id=\"save-shape-{shape_num}\" class=\"btn btn-success\" onclick=\"saveShape('{shape_num}')\">שמור</button>")
template_parts.append(f"            </div>")
template_parts.append(f"        </div>")
template_parts.append(f"    ")

# Save the template
template_content = '\n'.join(template_parts)
output_file = f"C:\\Users\\User\\Aiprojects\\Iron-Projects\\Agents\\templates\\shapes\\shape_{shape_num}.html"

with open(output_file, 'w', encoding='utf-8') as f:
    f.write(template_content)

print(f"\nTemplate saved to: {output_file}")
print("\nGenerated template with unique positions for each field!")
"""Verify template coordinates match JSON coordinates"""

import json

# Current template coordinates
template_coords = {
    "field_1": {"top": 149, "left_offset": 72},
    "field_2": {"top": 149, "left_offset": -3},
    "field_3": {"top": 207, "left_offset": 58}
}

# Load current JSON coordinates
with open('test_shape_location.json', 'r') as f:
    json_data = json.load(f)

json_coords = {
    "Input Field_1": {"x": 146.0, "y": 61.0},
    "Input Field_2": {"x": 143.0, "y": 196.0},
    "Input Field_3": {"x": 239.0, "y": 127.0}
}

# Image and display parameters
original_width = 306
original_height = 280
web_max_width = 300
scale_factor = web_max_width / original_width
web_width = web_max_width
web_height = original_height * scale_factor

# CSS styling
image_padding = 20
effective_image_width = web_width - (2 * image_padding)
effective_image_height = web_height - (2 * image_padding)

# Content scaling
content_scale_x = effective_image_width / original_width
content_scale_y = effective_image_height / original_height

# Container structure
container_padding_top = 40
image_margin_top = 20

print("Template vs JSON Coordinate Verification")
print("=" * 50)
print(f"Scaling factors: x={content_scale_x:.3f}, y={content_scale_y:.3f}")
print()

field_mapping = [
    ("field_1", "Input Field_1"),
    ("field_2", "Input Field_2"),
    ("field_3", "Input Field_3")
]

for template_key, json_key in field_mapping:
    template = template_coords[template_key]
    json_coord = json_coords[json_key]

    print(f"{template_key} / {json_key}:")
    print(f"  Template: top={template['top']}px, left=calc(50% + {template['left_offset']}px)")
    print(f"  JSON: x={json_coord['x']}, y={json_coord['y']}")

    # Calculate what template should be based on JSON
    orig_x = json_coord['x']
    orig_y = json_coord['y']

    # Scale to content area
    scaled_x = orig_x * content_scale_x
    scaled_y = orig_y * content_scale_y

    # Convert to HTML coordinates
    y_from_top_in_content = effective_image_height - scaled_y
    expected_top = container_padding_top + image_margin_top + image_padding + y_from_top_in_content

    x_in_full_image = image_padding + scaled_x
    expected_left_offset = x_in_full_image - (web_width / 2)

    print(f"  Expected from JSON: top={expected_top:.0f}px, left=calc(50% + {expected_left_offset:.0f}px)")

    # Check differences
    top_diff = abs(template['top'] - expected_top)
    left_diff = abs(template['left_offset'] - expected_left_offset)

    print(f"  Difference: top={top_diff:.1f}px, left={left_diff:.1f}px", end="")

    if top_diff <= 2 and left_diff <= 2:
        print(" ✓ MATCH")
    else:
        print(" ✗ MISMATCH")

    print()

print("=" * 50)
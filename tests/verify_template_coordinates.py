"""Verify web template coordinates against JSON using direct image coordinates"""

import json

# Read JSON data
with open('test_shape_location.json', 'r') as f:
    json_data = json.load(f)

json_coords = json_data['shapes']['shape_218']['fields']
img_dims = json_data['shapes']['shape_218']['image_dimensions']

# Template coordinates from HTML
template_coords = {
    "field_1": {"bottom": 133, "left_offset": 14},
    "field_2": {"bottom": 268, "left_offset": 16},
    "field_3": {"bottom": 203, "left_offset": 113}
}

print("TEMPLATE COORDINATE VERIFICATION")
print("=" * 50)
print(f"Image dimensions: {img_dims['width']} x {img_dims['height']}")
print()

# Web display scaling parameters
original_width = img_dims['width']
original_height = img_dims['height']
web_max_width = 300
scale_factor = web_max_width / original_width
web_height = original_height * scale_factor
image_padding = 20
effective_image_width = web_max_width - (2 * image_padding)
effective_image_height = web_height - (2 * image_padding)
content_scale_x = effective_image_width / original_width
content_scale_y = effective_image_height / original_height
container_padding_bottom = 30
image_margin_bottom = 20

print(f"Web scaling: {scale_factor:.3f}")
print(f"Content scaling: x={content_scale_x:.3f}, y={content_scale_y:.3f}")
print()

field_mapping = [
    ("field_1", "Input Field_1"),
    ("field_2", "Input Field_2"),
    ("field_3", "Input Field_3")
]

print("COORDINATE VERIFICATION:")
print("-" * 50)

for template_key, json_key in field_mapping:
    template = template_coords[template_key]
    json_coord = json_coords[json_key]

    print(f"\n{json_key}:")
    print(f"  JSON: x={json_coord['x']:.1f}, y={json_coord['y']:.1f}")

    # Calculate what template should be based on direct JSON coordinates
    orig_x = json_coord['x']
    orig_y = json_coord['y']

    # Scale to web display
    scaled_x = orig_x * content_scale_x
    scaled_y = orig_y * content_scale_y

    # Calculate web positioning
    expected_bottom = container_padding_bottom + image_margin_bottom + image_padding + scaled_y
    x_in_full_image = image_padding + scaled_x
    expected_left_offset = x_in_full_image - (web_max_width / 2)

    print(f"  Expected: bottom={expected_bottom:.0f}px, left=calc(50% + {expected_left_offset:.0f}px)")
    print(f"  Template: bottom={template['bottom']}px, left=calc(50% + {template['left_offset']}px)")

    # Check differences
    bottom_diff = abs(template['bottom'] - expected_bottom)
    left_diff = abs(template['left_offset'] - expected_left_offset)

    print(f"  Difference: bottom={bottom_diff:.1f}px, left={left_diff:.1f}px")

    if bottom_diff <= 2 and left_diff <= 2:
        print(f"  Status: MATCH ✓")
    else:
        print(f"  Status: MISMATCH ✗")

print("\n" + "=" * 50)
print("This verification shows if the template coordinates correctly")
print("represent the JSON image coordinates in the web display.")
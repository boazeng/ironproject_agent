"""Debug coordinate differences between JSON and template"""

import json

# Read current JSON data
with open('test_shape_location.json', 'r') as f:
    json_data = json.load(f)

json_coords = json_data['shapes']['shape_218']['fields']
image_dims = json_data['shapes']['shape_218']['image_dimensions']

# Current template coordinates from HTML
template_coords = {
    "field_1": {"bottom": 133, "left_offset": 14},
    "field_2": {"bottom": 268, "left_offset": 16},
    "field_3": {"bottom": 203, "left_offset": 113}
}

print("COORDINATE MISMATCH ANALYSIS")
print("=" * 60)
print(f"Image dimensions: {image_dims['width']} x {image_dims['height']}")
print()

# Scaling parameters used in template generation
original_width = image_dims['width']  # 306
original_height = image_dims['height']  # 280
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

print("SCALING FACTORS:")
print(f"  Scale factor: {scale_factor:.3f}")
print(f"  Content scale X: {content_scale_x:.3f}")
print(f"  Content scale Y: {content_scale_y:.3f}")
print(f"  Web dimensions: {web_max_width} x {web_height:.1f}")
print(f"  Effective area: {effective_image_width:.1f} x {effective_image_height:.1f}")
print()

print("DETAILED COORDINATE ANALYSIS:")
print("-" * 60)

field_mapping = [
    ("field_1", "Input Field_1"),
    ("field_2", "Input Field_2"),
    ("field_3", "Input Field_3")
]

for template_key, json_key in field_mapping:
    template = template_coords[template_key]
    json_coord = json_coords[json_key]

    print(f"\n{json_key}:")
    print(f"  JSON coordinates: x={json_coord['x']:.1f}, y={json_coord['y']:.1f}")

    # Calculate what the template SHOULD be based on JSON
    orig_x = json_coord['x']
    orig_y = json_coord['y']

    # Scale to content area (this is what the tool should be doing)
    scaled_x = orig_x * content_scale_x
    scaled_y = orig_y * content_scale_y

    # Calculate web positioning
    expected_bottom = container_padding_bottom + image_margin_bottom + image_padding + scaled_y
    x_in_full_image = image_padding + scaled_x
    expected_left_offset = x_in_full_image - (web_max_width / 2)

    print(f"  Expected template: bottom={expected_bottom:.0f}px, left=calc(50% + {expected_left_offset:.0f}px)")
    print(f"  Actual template:   bottom={template['bottom']}px, left=calc(50% + {template['left_offset']}px)")

    # Calculate differences
    bottom_diff = abs(template['bottom'] - expected_bottom)
    left_diff = abs(template['left_offset'] - expected_left_offset)

    print(f"  DIFFERENCE: bottom={bottom_diff:.1f}px, left={left_diff:.1f}px")

    if bottom_diff > 5 or left_diff > 5:
        print(f"  >> LARGE DIFFERENCE DETECTED!")

        # Let's see what the template coordinate translates back to in JSON
        # Reverse calculation
        actual_scaled_y = template['bottom'] - container_padding_bottom - image_margin_bottom - image_padding
        actual_scaled_x = (template['left_offset'] + (web_max_width / 2)) - image_padding

        reverse_y = actual_scaled_y / content_scale_y
        reverse_x = actual_scaled_x / content_scale_x

        print(f"  Template reverse-calculated JSON: x={reverse_x:.1f}, y={reverse_y:.1f}")
        print(f"  Difference from actual JSON: x={abs(reverse_x - orig_x):.1f}, y={abs(reverse_y - orig_y):.1f}")

print("\n" + "=" * 60)
print("CONCLUSION:")
print("If large differences exist, the coordinate conversion in the")
print("positioning tool is not working correctly.")
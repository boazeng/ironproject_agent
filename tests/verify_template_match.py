"""Verify that the HTML template positions match the JSON coordinates"""

import json

# Load JSON data
with open('test_shape_location.json', 'r') as f:
    data = json.load(f)

shape_218 = data['shapes']['shape_218']
image_height = shape_218['image_dimensions']['height']  # 280
image_width = shape_218['image_dimensions']['width']    # 306

# HTML template positions from the file (current template)
html_positions = {
    "field_1": {"top": 279, "left_offset": -7},
    "field_2": {"top": 143, "left_offset": -8},
    "field_3": {"top": 209, "left_offset": 70}
}

# JSON positions (current values)
json_positions = {
    "Input Field_1": {"x": 152.0, "y": 60.0},
    "Input Field_2": {"x": 232.0, "y": 131.0},
    "Input Field_3": {"x": 152.0, "y": 197.0}
}

# HTML template structure
container_padding_top = 40
image_margin_top = 20

print("Verification: Template vs JSON coordinates")
print("=" * 60)
print(f"Image dimensions: {image_width}x{image_height}")
print(f"Container structure: padding-top={container_padding_top}px, image margin-top={image_margin_top}px")
print()

field_pairs = [
    ("field_1", "Input Field_1"),
    ("field_2", "Input Field_2"),
    ("field_3", "Input Field_3")
]

for html_key, json_key in field_pairs:
    html_pos = html_positions[html_key]
    json_pos = json_positions[json_key]

    print(f"{html_key} / {json_key}:")
    print(f"  HTML: top={html_pos['top']}px, left=calc(50% + {html_pos['left_offset']}px)")
    print(f"  JSON: x={json_pos['x']}, y={json_pos['y']} (from lower-left)")

    # Convert HTML to lower-left coordinates
    html_top = html_pos['top']
    html_left_offset = html_pos['left_offset']

    # Calculate y from bottom
    # HTML top includes container padding + image margin
    image_y_from_top = html_top - container_padding_top - image_margin_top
    y_from_bottom = image_height - image_y_from_top

    # Calculate x from left
    # HTML left is offset from center (50%)
    x_from_left = (image_width / 2) + html_left_offset

    print(f"  HTML converted to lower-left: x={x_from_left:.1f}, y={y_from_bottom:.1f}")

    # Check if they match (within 1-2 pixels)
    x_diff = abs(x_from_left - json_pos['x'])
    y_diff = abs(y_from_bottom - json_pos['y'])

    print(f"  Difference: x={x_diff:.1f}px, y={y_diff:.1f}px", end="")

    if x_diff <= 2 and y_diff <= 2:
        print(" ✓ MATCH")
    else:
        print(" ✗ MISMATCH")

    print()

print("=" * 60)

# Check if all positions are reasonable
all_match = True
for html_key, json_key in field_pairs:
    html_pos = html_positions[html_key]
    json_pos = json_positions[json_key]

    # Convert HTML to lower-left
    html_top = html_pos['top']
    html_left_offset = html_pos['left_offset']
    image_y_from_top = html_top - container_padding_top - image_margin_top
    y_from_bottom = image_height - image_y_from_top
    x_from_left = (image_width / 2) + html_left_offset

    x_diff = abs(x_from_left - json_pos['x'])
    y_diff = abs(y_from_bottom - json_pos['y'])

    if x_diff > 2 or y_diff > 2:
        all_match = False

if all_match:
    print("✓ RESULT: Template coordinates match JSON coordinates!")
    print("  The positioning tool is now working correctly.")
else:
    print("✗ RESULT: Template coordinates do NOT match JSON coordinates.")
    print("  There may still be an issue with the coordinate conversion.")
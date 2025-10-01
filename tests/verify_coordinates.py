"""Verify and correct coordinate calculations from JSON to HTML template"""

import json

# Load the JSON file
with open('test_shape_location.json', 'r') as f:
    data = json.load(f)

shape_218 = data['shapes']['shape_218']
image_height = shape_218['image_dimensions']['height']
image_width = shape_218['image_dimensions']['width']

print(f"Image dimensions: {image_width}x{image_height}")
print(f"Reference point (lower-left): (0, {image_height})")
print("\n" + "="*50)

# Container structure in HTML template
container_padding_top = 40  # padding: 40px 0
image_margin_top = 20       # margin-top: 20px

print("\nHTML Template Structure:")
print(f"- Container padding-top: {container_padding_top}px")
print(f"- Image margin-top: {image_margin_top}px")
print(f"- Image starts at: {container_padding_top + image_margin_top}px from container top")
print("\n" + "="*50)

fields = shape_218['fields']
for field_name, field_data in fields.items():
    print(f"\n{field_name}:")
    x = field_data['x']
    y = field_data['y']

    print(f"  JSON stored values: x={x}, y={y}")

    # The issue: y is negative because we're subtracting from image_height incorrectly
    # The canvas coordinates have (0,0) at top-left
    # We need to convert properly

    # If x and y are canvas coordinates (top-left origin):
    # Then distance from bottom = image_height - y
    # But the stored values show negative, which means they're already past the image bounds

    # Let's recalculate what the positions should be:
    # For web display with lower-left reference:
    # - x stays the same (distance from left)
    # - y from bottom = image_height - canvas_y

    # But wait, the x values (470-550) are way larger than image width (306)!
    # This suggests these are not image coordinates but canvas coordinates

    print(f"  Issue: x={x} is larger than image width {image_width}")
    print(f"  Issue: y={y} is negative (below bottom)")

print("\n" + "="*50)
print("\nThe problem: The tool is saving canvas widget coordinates, not image coordinates!")
print("We need to convert canvas coordinates to image-relative coordinates.")

# From the HTML template, let's reverse-engineer the correct positions:
html_positions = {
    "field_1": {"top": 275, "left_offset": -4},
    "field_2": {"top": 141, "left_offset": -6},
    "field_3": {"top": 206, "left_offset": 71}
}

print("\n" + "="*50)
print("\nCorrect positions from HTML template:")
for field, pos in html_positions.items():
    top_px = pos['top']
    left_offset = pos['left_offset']

    # Convert HTML top to y-from-bottom
    # top_px includes container_padding_top + image_margin_top
    image_top_offset = top_px - container_padding_top - image_margin_top
    y_from_bottom = image_height - image_top_offset

    # Convert left offset to x from left
    # left offset is from center, so x = (image_width/2) + offset
    x_from_left = (image_width / 2) + left_offset

    print(f"\n{field}:")
    print(f"  HTML: top={top_px}px, left=calc(50% + {left_offset}px)")
    print(f"  Converted to lower-left reference:")
    print(f"    x (from left): {x_from_left:.1f}px")
    print(f"    y (from bottom): {y_from_bottom:.1f}px")
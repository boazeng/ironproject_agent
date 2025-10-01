"""Manual coordinate calculation from JSON to HTML template"""

# JSON coordinates (lower-left reference)
json_coords = {
    "Input Field_1": {"x": 238.0, "y": 198.0},
    "Input Field_2": {"x": 149.0, "y": 198.0},
    "Input Field_3": {"x": 221.0, "y": 128.0}
}

# Image dimensions
image_width = 306
image_height = 280

# HTML template structure
container_padding_top = 40
image_margin_top = 20

print("Converting JSON coordinates to HTML template coordinates:")
print("=" * 60)

for field_name, coords in json_coords.items():
    x_from_left = coords['x']
    y_from_bottom = coords['y']

    print(f"\n{field_name}:")
    print(f"  JSON: x={x_from_left}, y={y_from_bottom} (from lower-left)")

    # Convert y from bottom to top positioning
    y_from_top = image_height - y_from_bottom
    web_top_px = container_padding_top + image_margin_top + y_from_top

    # Convert x to offset from center
    center_offset_x = x_from_left - (image_width / 2)
    web_left_px = center_offset_x

    print(f"  HTML: top={web_top_px:.0f}px, left=calc(50% + {web_left_px:.0f}px)")
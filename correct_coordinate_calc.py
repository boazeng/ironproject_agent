"""Correct coordinate calculation accounting for web scaling and CSS"""

# JSON coordinates (lower-left reference)
json_coords = {
    "Input Field_1": {"x": 238.0, "y": 198.0},
    "Input Field_2": {"x": 149.0, "y": 198.0},
    "Input Field_3": {"x": 221.0, "y": 128.0}
}

# Original image dimensions
original_width = 306
original_height = 280

# Web display scaling
web_max_width = 300
scale_factor = web_max_width / original_width  # 0.980
web_width = web_max_width  # 300
web_height = original_height * scale_factor  # 275

print(f"Web scaling: {scale_factor:.3f}")
print(f"Web image size: {web_width}x{web_height:.0f}")

# CSS styling affects effective image size
css_padding = 20  # padding: 20px
effective_image_width = web_width
effective_image_height = web_height

# HTML template structure
container_padding_top = 40
image_margin_top = 20

print("\nCorrected coordinate calculation:")
print("=" * 60)

for field_name, coords in json_coords.items():
    # Original coordinates
    orig_x = coords['x']
    orig_y = coords['y']

    # Scale coordinates to web display size
    scaled_x = orig_x * scale_factor
    scaled_y = orig_y * scale_factor

    print(f"\n{field_name}:")
    print(f"  Original: x={orig_x}, y={orig_y}")
    print(f"  Scaled: x={scaled_x:.1f}, y={scaled_y:.1f}")

    # Convert y from bottom to top positioning (within scaled image)
    y_from_top_in_image = web_height - scaled_y
    web_top_px = container_padding_top + image_margin_top + y_from_top_in_image

    # Convert x to offset from center (within scaled image)
    center_offset_x = scaled_x - (web_width / 2)
    web_left_px = center_offset_x

    print(f"  HTML: top={web_top_px:.0f}px, left=calc(50% + {web_left_px:.0f}px)")
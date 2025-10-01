"""Final coordinate calculation accounting for image padding"""

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

# CSS styling: padding: 20px on the image
image_padding = 20
effective_image_width = web_width - (2 * image_padding)  # 300 - 40 = 260
effective_image_height = web_height - (2 * image_padding)  # 275 - 40 = 235

print(f"Web image total size: {web_width}x{web_height:.0f}")
print(f"Image padding: {image_padding}px")
print(f"Effective image content: {effective_image_width}x{effective_image_height:.0f}")

# Additional scaling needed for effective content area
content_scale_x = effective_image_width / original_width
content_scale_y = effective_image_height / original_height

print(f"Content scaling: x={content_scale_x:.3f}, y={content_scale_y:.3f}")

# HTML template structure
container_padding_top = 40
image_margin_top = 20

print("\nFinal coordinate calculation with padding:")
print("=" * 60)

for field_name, coords in json_coords.items():
    # Original coordinates
    orig_x = coords['x']
    orig_y = coords['y']

    # Scale coordinates to effective content area
    scaled_x = orig_x * content_scale_x
    scaled_y = orig_y * content_scale_y

    print(f"\n{field_name}:")
    print(f"  Original: x={orig_x}, y={orig_y}")
    print(f"  Scaled to content area: x={scaled_x:.1f}, y={scaled_y:.1f}")

    # Convert y from bottom to top positioning (within content area)
    y_from_top_in_content = effective_image_height - scaled_y
    # Add padding offset and container structure
    web_top_px = container_padding_top + image_margin_top + image_padding + y_from_top_in_content

    # Convert x to offset from center (within content area)
    # Add padding offset to account for left padding
    x_in_full_image = image_padding + scaled_x
    center_offset_x = x_in_full_image - (web_width / 2)
    web_left_px = center_offset_x

    print(f"  HTML: top={web_top_px:.0f}px, left=calc(50% + {web_left_px:.0f}px)")
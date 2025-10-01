"""Calculate correct template coordinates from new JSON values"""

# New JSON coordinates
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

print("Correct template coordinates from JSON:")
print("=" * 50)

for field_name, coords in json_coords.items():
    orig_x = coords['x']
    orig_y = coords['y']

    # Scale to content area
    scaled_x = orig_x * content_scale_x
    scaled_y = orig_y * content_scale_y

    # Convert to HTML coordinates
    y_from_top_in_content = effective_image_height - scaled_y
    web_top_px = container_padding_top + image_margin_top + image_padding + y_from_top_in_content

    x_in_full_image = image_padding + scaled_x
    web_left_px = x_in_full_image - (web_width / 2)

    print(f"\n{field_name}:")
    print(f"  JSON: x={orig_x}, y={orig_y}")
    print(f"  Template: top={web_top_px:.0f}px, left=calc(50% + {web_left_px:.0f}px)")
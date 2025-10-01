"""Analyze what reference point the web display is actually using"""

# JSON coordinates (lower-left reference system)
json_coords = {
    "Input Field_1": {"x": 150.0, "y": 61.0},
    "Input Field_2": {"x": 208.0, "y": 128.0},
    "Input Field_3": {"x": 136.0, "y": 201.0}
}

# Template coordinates (top-left reference system with container offset)
template_coords = {
    "field_1": {"top": 263, "left_offset": -3},
    "field_2": {"top": 207, "left_offset": 47},
    "field_3": {"top": 146, "left_offset": -14}
}

# Web display structure
container_padding_top = 40  # From "padding: 40px 0"
image_margin_top = 20       # From "margin-top: 20px"
image_padding = 20          # From "padding: 20px" on image
border_width = 2           # From "border: 2px solid"

# Image dimensions
original_width = 306
original_height = 280
web_max_width = 300
scale_factor = web_max_width / original_width
web_height = original_height * scale_factor

print("WEB REFERENCE POINT ANALYSIS")
print("=" * 50)
print(f"Container structure:")
print(f"  - Container padding top: {container_padding_top}px")
print(f"  - Image margin top: {image_margin_top}px")
print(f"  - Image border: {border_width}px")
print(f"  - Image padding: {image_padding}px")
print(f"  - Total offset to image content: {container_padding_top + image_margin_top + border_width + image_padding}px")
print()

# The web template uses:
# - position: absolute with top values (from container top-left)
# - left: calc(50% + offset) (from container center horizontally)

web_reference_offset = container_padding_top + image_margin_top + border_width + image_padding

print("COORDINATE SYSTEM ANALYSIS:")
print("-" * 50)

for i, (field_name, json_coord) in enumerate(json_coords.items(), 1):
    template_key = f"field_{i}"
    template = template_coords[template_key]

    print(f"\n{field_name}:")
    print(f"  JSON (lower-left ref): x={json_coord['x']}, y={json_coord['y']}")
    print(f"  Template: top={template['top']}px, left=calc(50% + {template['left_offset']}px)")

    # Calculate where this should be if web uses different reference

    # If web reference is top-left of image content area:
    image_top_in_content = web_reference_offset
    y_from_image_top = template['top'] - image_top_in_content

    # If web reference is top-left of container:
    y_from_container_top = template['top']

    print(f"  Distance from container top: {y_from_container_top}px")
    print(f"  Distance from image content top: {y_from_image_top}px")

    # Convert JSON lower-left to upper-left for comparison
    y_from_image_bottom = json_coord['y']
    y_from_image_top_calculated = original_height - y_from_image_bottom

    print(f"  JSON converted to top-ref: y={y_from_image_top_calculated}px from image top")

    # Check if template uses container top-left as reference
    expected_top_from_container = web_reference_offset + y_from_image_top_calculated
    diff_container_ref = abs(template['top'] - expected_top_from_container)

    print(f"  Expected top (container ref): {expected_top_from_container}px")
    print(f"  Difference: {diff_container_ref}px")

    if diff_container_ref <= 5:
        print("  → WEB USES CONTAINER TOP-LEFT AS REFERENCE ✓")
    else:
        print("  → Different reference point ✗")

print("\n" + "=" * 50)
print("CONCLUSION:")
print("The web display uses CONTAINER TOP-LEFT as reference point,")
print("NOT the image lower-left corner as stored in JSON.")
print("The coordinates need to account for the full container structure.")
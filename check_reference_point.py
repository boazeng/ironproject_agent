"""Check what the actual reference point should be in the web display"""

# Current JSON coordinates (lower-left reference system)
json_coords = {
    "Input Field_1": {"x": 150.0, "y": 61.0},
    "Input Field_2": {"x": 208.0, "y": 128.0},
    "Input Field_3": {"x": 136.0, "y": 201.0}
}

# Current template coordinates
template_coords = {
    "field_1": {"top": 263, "left_offset": -3},
    "field_2": {"top": 207, "left_offset": 47},
    "field_3": {"top": 146, "left_offset": -14}
}

# Image dimensions
image_width = 306
image_height = 280

# Container structure in web display
container_padding_top = 40
image_margin_top = 20
total_offset = container_padding_top + image_margin_top  # 60px

print("Reference Point Analysis")
print("=" * 40)
print(f"Image dimensions: {image_width}x{image_height}")
print(f"JSON reference point: lower-left corner (0, {image_height})")
print(f"Container offset: {total_offset}px from top")
print()

print("Current Coordinates Analysis:")
print("-" * 40)

# Let's reverse-engineer what the web display coordinates mean
for i, (field_name, json_coord) in enumerate(json_coords.items(), 1):
    template_key = f"field_{i}"
    template = template_coords[template_key]

    print(f"\n{field_name}:")
    print(f"  JSON (from lower-left): x={json_coord['x']}, y={json_coord['y']}")
    print(f"  Template: top={template['top']}px, left=calc(50% + {template['left_offset']}px)")

    # Calculate what the web coordinates mean in terms of image position
    # Template top includes container offset, so actual image position is:
    image_top_pos = template['top'] - total_offset

    # Template left offset from center, so actual image position is:
    image_left_pos = (image_width / 2) + template['left_offset']

    print(f"  Web position on image: x={image_left_pos:.1f}, y={image_top_pos:.1f} (from top-left)")

    # Convert to lower-left coordinates
    y_from_bottom = image_height - image_top_pos

    print(f"  Converted to lower-left: x={image_left_pos:.1f}, y={y_from_bottom:.1f}")

    # Check if this matches JSON
    x_diff = abs(image_left_pos - json_coord['x'])
    y_diff = abs(y_from_bottom - json_coord['y'])

    print(f"  Difference from JSON: x={x_diff:.1f}, y={y_diff:.1f}")

    if x_diff > 5 or y_diff > 5:
        print("  ⚠️  LARGE DISCREPANCY - Reference point may be wrong")

print("\n" + "=" * 40)
print("Analysis Summary:")
print("If differences are large, the issue might be:")
print("1. Web scaling not accounted for properly")
print("2. CSS padding/border affecting position")
print("3. Reference point calculation error")
print("4. Container positioning offset error")
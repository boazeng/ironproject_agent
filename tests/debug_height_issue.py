"""Debug why fields are positioned too high"""

import json

# Read current data
with open('test_shape_location.json', 'r') as f:
    json_data = json.load(f)

json_coords = json_data['shapes']['shape_218']['fields']
img_dims = json_data['shapes']['shape_218']['image_dimensions']

print("HEIGHT POSITIONING DEBUG")
print("=" * 50)
print(f"Image dimensions: {img_dims['width']} x {img_dims['height']}")
print()

print("CURRENT LOGIC:")
print("1. JSON: Field is 61px from image BOTTOM")
print("2. Template: bottom: 112px (61px + 51px container offset)")
print("3. Result: Field appears too HIGH")
print()

print("PROBLEM ANALYSIS:")
print("The CSS 'bottom: 112px' means 112px FROM THE CONTAINER BOTTOM")
print("If this makes the field appear too HIGH, then either:")
print("a) The container offset is wrong")
print("b) We need to position relative to TOP instead of bottom")
print("c) The coordinate conversion is inverted")
print()

print("TESTING DIFFERENT APPROACHES:")
print()

# Current template shows bottom: 112px for field with JSON y=61
# If this is too high, maybe we need to use top positioning instead

original_height = img_dims['height']  # 280px
print(f"Image height: {original_height}px")
print()

for field_name, coord in json_coords.items():
    json_y = coord['y']  # Distance from image bottom

    print(f"{field_name}:")
    print(f"  JSON: {json_y}px from image bottom")

    # Convert to distance from image TOP
    y_from_top = original_height - json_y
    print(f"  Equivalent: {y_from_top}px from image top")

    # Maybe we should use TOP positioning instead?
    # Container padding-top(40) + image margin-top(20) + border(2) + padding(20) = 82px
    container_to_image_top = 40 + 20 + 2 + 20  # 82px
    top_position = container_to_image_top + (y_from_top * 0.838)  # Apply scaling

    print(f"  Alternative TOP positioning: {top_position:.0f}px from container top")
    print()

print("RECOMMENDATION:")
print("Try using TOP positioning instead of BOTTOM positioning")
print("This might fix the 'too high' issue by positioning from the correct reference.")
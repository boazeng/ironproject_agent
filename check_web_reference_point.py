"""Check what the actual web display reference point should be"""

import json

# Read JSON data
with open('test_shape_location.json', 'r') as f:
    json_data = json.load(f)

json_coords = json_data['shapes']['shape_218']['fields']
img_dims = json_data['shapes']['shape_218']['image_dimensions']

print("WEB DISPLAY REFERENCE POINT ANALYSIS")
print("=" * 50)
print(f"Image dimensions: {img_dims['width']} x {img_dims['height']}")
print(f"JSON reference point: Lower-left corner (0, {img_dims['height']})")
print()

print("CURRENT WEB TEMPLATE STRUCTURE:")
print("- Container: padding: 40px 0")
print("- Image: margin-top: 20px")
print("- Image: padding: 20px")
print("- Image: border: 2px solid")
print()

print("ISSUE ANALYSIS:")
print("The web template uses CSS 'bottom' positioning, but the reference point")
print("for 'bottom' in CSS is the BOTTOM EDGE of the CONTAINER, not the image.")
print()

print("CURRENT TEMPLATE POSITIONING:")
print("position: absolute; bottom: Xpx; left: calc(50% + Ypx)")
print("This means:")
print("- bottom: Xpx = X pixels from CONTAINER bottom")
print("- left: calc(50% + Ypx) = Y pixels from CONTAINER center")
print()

print("CORRECT REFERENCE SHOULD BE:")
print("The bottom edge of the IMAGE CONTENT AREA, not the container bottom.")
print()

print("SOLUTION:")
print("We need to adjust the 'bottom' values to account for:")
print("1. Container structure (padding, margins)")
print("2. Image positioning within container")
print("3. Make the reference point the bottom of the IMAGE, not container")
print()

# Current JSON coordinates should represent distance from image bottom-left
print("JSON COORDINATES (distance from image bottom-left):")
for field_name, coord in json_coords.items():
    print(f"  {field_name}: x={coord['x']:.1f}, y={coord['y']:.1f}")
print()

print("RECOMMENDATION:")
print("Modify the template generation to use the IMAGE bottom as reference,")
print("not the container bottom. This means adjusting the 'bottom' calculation")
print("to position fields relative to where the image actually starts.")
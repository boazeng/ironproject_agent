"""Debug vertical positioning issues"""

import json

# Read current data
with open('test_shape_location.json', 'r') as f:
    json_data = json.load(f)

json_coords = json_data['shapes']['shape_218']['fields']
img_dims = json_data['shapes']['shape_218']['image_dimensions']

print("VERTICAL POSITIONING DEBUG")
print("=" * 50)
print(f"Image dimensions: {img_dims['width']} x {img_dims['height']}")
print()

print("HTML STRUCTURE ANALYSIS:")
print("1. Container: <div style='padding: 40px 0;'>")
print("2. Input fields: position: absolute; bottom: Xpx")
print("3. Image: margin-top: 20px; border: 2px; padding: 20px")
print()

print("CURRENT DISTANCE CALCULATION:")
print("buttons(30px) + image_margin(20px) + border(2px) + padding(20px) = 72px")
print()

print("ACTUAL WEB STRUCTURE ANALYSIS:")
print("Let's check what the actual distances should be...")
print()

# The issue might be that we're not accounting for the correct container structure
print("POSSIBLE ISSUES:")
print("1. Container padding-top (40px) creates space at TOP, not bottom")
print("2. Image margin-top (20px) is from container top, not bottom")
print("3. Bottom reference should be from container bottom edge")
print()

print("CORRECT CALCULATION SHOULD BE:")
print("Container bottom to image bottom:")
print("- Buttons section: 30px (below image)")
print("- Image margin-bottom: might not be 20px")
print("- Image border-bottom: 2px")
print("- Image padding-bottom: 20px")
print("Total: 30 + 0 + 2 + 20 = 52px")
print()

print("OR the image might be positioned differently...")
print("Let's check if the image is actually at the bottom of its container.")
print()

print("RECOMMENDATION:")
print("Check the actual CSS layout to see where the image bottom is")
print("relative to the container bottom. The current 72px offset")
print("might be incorrect.")
print()

print("JSON COORDINATES (from image bottom):")
for field_name, coord in json_coords.items():
    print(f"  {field_name}: y={coord['y']:.1f}px from image bottom")
print()

print("If Field_1 y=65px should be 65px from image bottom,")
print("and template shows bottom=126px, then:")
print("126px - 65px = 61px offset (not 72px)")
print("This suggests the container-to-image offset is 61px, not 72px")
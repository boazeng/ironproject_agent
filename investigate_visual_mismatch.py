"""Investigate why coordinates appear correct but visually don't match"""

import json

# Read current JSON data
with open('test_shape_location.json', 'r') as f:
    json_data = json.load(f)

json_coords = json_data['shapes']['shape_218']['fields']

print("VISUAL MISMATCH INVESTIGATION")
print("=" * 50)
print("Even though coordinates mathematically match, there could be issues with:")
print()

print("1. COORDINATE SYSTEM MISMATCH:")
print("   - JSON saves coordinates from positioning tool canvas")
print("   - Template uses coordinates for web display")
print("   - These might use different coordinate systems")
print()

print("2. CURRENT JSON COORDINATES:")
for field_name, coord in json_coords.items():
    print(f"   {field_name}: x={coord['x']:.1f}, y={coord['y']:.1f}")
print()

print("3. POSSIBLE ISSUES:")
print("   a) Canvas coordinates vs Image coordinates")
print("      - Tool might be saving canvas widget coordinates")
print("      - Instead of actual image pixel coordinates")
print()
print("   b) Different image scaling in tool vs web")
print("      - Tool displays image at one size")
print("      - Web displays at different size")
print()
print("   c) Container positioning differences")
print("      - Tool container structure")
print("      - Web container structure")
print()

print("4. DEBUGGING STEPS NEEDED:")
print("   - Check what coordinates the positioning tool actually saves")
print("   - Verify these match the actual image positions")
print("   - Test if tool and web show fields in same relative positions")
print()

print("5. COORDINATE VALIDATION:")
print("   The JSON coordinates should represent:")
print("   - Distance from lower-left corner of the ACTUAL IMAGE")
print("   - NOT distance from canvas widget corner")
print("   - NOT distance from container corner")
print()

print("RECOMMENDATION:")
print("Check if the positioning tool is saving the correct image coordinates")
print("by comparing where you click vs what gets saved in JSON.")
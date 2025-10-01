"""Debug image scaling between positioning tool and web display"""

from PIL import Image
import os

# Load the actual shape image
image_path = "io/catalog/shape_218.png"
if os.path.exists(image_path):
    img = Image.open(image_path)
    actual_width, actual_height = img.size
    print(f"Actual image file: {actual_width}x{actual_height}")
else:
    print("Shape 218 image not found")

# Check static images folder
static_image_path = "static/images/shape_218.png"
if os.path.exists(static_image_path):
    img = Image.open(static_image_path)
    static_width, static_height = img.size
    print(f"Static image file: {static_width}x{static_height}")
else:
    print("Static shape 218 image not found")

# JSON coordinates (what positioning tool recorded)
json_dims = {"width": 306, "height": 280}
print(f"JSON recorded dimensions: {json_dims['width']}x{json_dims['height']}")

# Web display scaling
web_display_max_width = 300
if json_dims["width"] > web_display_max_width:
    scale_factor = web_display_max_width / json_dims["width"]
    web_width = web_display_max_width
    web_height = json_dims["height"] * scale_factor
    print(f"Web display scaling: {scale_factor:.3f}")
    print(f"Web display size: {web_width:.0f}x{web_height:.0f}")
else:
    print(f"Web display size: {json_dims['width']}x{json_dims['height']} (no scaling)")

# This could be the issue - if the actual image dimensions differ from what's recorded in JSON
print("\nPossible issues:")
print("1. Image file dimensions don't match JSON recorded dimensions")
print("2. Web display scaling is different from positioning tool")
print("3. CSS styling (padding/border) affects effective image size")
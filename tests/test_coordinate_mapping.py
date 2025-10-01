"""Test and verify coordinate mapping from positioning tool to web display"""

# Based on the erased areas from shape 218:
# Erased area: (128,53) to (164,91) - field E
# Erased area: (244,128) to (265,172) - field C
# Erased area: (130,211) to (177,249) - field A

# These represent where fields were placed on the canvas
# We need to ensure these exact positions translate to the web display

def calculate_web_position(canvas_x, canvas_y, canvas_width=300, canvas_height=300):
    """Calculate web display position from canvas coordinates"""

    # Web display parameters
    web_display_width = 300  # max-width: 300px in template
    container_padding_top = 40  # padding: 40px 0
    image_margin_top = 20  # margin-top: 20px

    # Calculate relative position (0-1 range)
    relative_x = canvas_x / canvas_width
    relative_y = canvas_y / canvas_height

    # Convert to web display coordinates
    web_pos_x = relative_x * web_display_width
    web_pos_y = relative_y * web_display_width  # Use width for both to maintain aspect ratio

    # Calculate absolute position from container top
    web_top_px = container_padding_top + image_margin_top + web_pos_y

    # For horizontal: offset from center
    center_offset_x = web_pos_x - (web_display_width / 2)
    web_left_px = center_offset_x

    return web_top_px, web_left_px

# Test with actual field positions (using center of erased areas)
fields = {
    'E': {'canvas_x': (128 + 164) / 2, 'canvas_y': (53 + 91) / 2},     # 146, 72
    'C': {'canvas_x': (244 + 265) / 2, 'canvas_y': (128 + 172) / 2},   # 254.5, 150
    'A': {'canvas_x': (130 + 177) / 2, 'canvas_y': (211 + 249) / 2},   # 153.5, 230
}

print("Coordinate mapping for shape 218 fields:")
print("=" * 50)

for field_name, pos in fields.items():
    canvas_x = pos['canvas_x']
    canvas_y = pos['canvas_y']
    web_top, web_left = calculate_web_position(canvas_x, canvas_y)

    print(f"\nField {field_name}:")
    print(f"  Canvas position: ({canvas_x:.1f}, {canvas_y:.1f})")
    print(f"  Web position: top={web_top:.0f}px, left=calc(50% + {web_left:.0f}px)")

print("\n" + "=" * 50)
print("\nTo ensure correct display:")
print("1. Fields should appear at their exact canvas positions")
print("2. The image is centered with max-width: 300px")
print("3. Each field maintains its unique x,y coordinate")
print("\nGenerated template positions:")

# Generate the corrected template
template_lines = []
for field_name, pos in fields.items():
    canvas_x = pos['canvas_x']
    canvas_y = pos['canvas_y']
    web_top, web_left = calculate_web_position(canvas_x, canvas_y)

    template_lines.append(f"""                <!-- {field_name} field - positioned at its original location -->
                <div style="position: absolute; top: {web_top:.0f}px; left: calc(50% + {web_left:.0f}px); transform: translate(-50%, -50%); display: flex; align-items: center;">
                    <span style="font-size: 20px; font-weight: bold; color: red; margin-right: 8px;">{field_name}</span>
                    <input type="text"
                           id="length-{field_name}-218"
                           class="inline-shape-input shape-218-input"
                           maxlength="8"
                           placeholder="0"
                           style="width: 80px; height: 28px; font-size: 18px; border: 2px solid #4a90e2; border-radius: 4px; background: #e6f2ff;">
                </div>""")

print("\n".join(template_lines))
#!/usr/bin/env python3
"""
Test script for absolute positioning functionality
Demonstrates the complete workflow from positioning tool to template generation
"""

import json
import os
from shape_template_generator import ShapeTemplateGenerator

def create_test_absolute_positioning_data():
    """Create test data with absolute positioning information"""

    # Simulate data from positioning tool with absolute reference point
    test_data = {
        "shape_number": "107",
        "shape_name": "צורת U",
        "image_path": "test_shape.png",
        "canvas_width": 350,
        "canvas_height": 250,
        "absolute_positioning": {
            "reference_point": {"x": 175, "y": 125},  # Center of canvas as reference
            "enabled": True
        },
        "elements": [
            {
                "type": "text",
                "text": "A",
                "x": 300,
                "y": 100,
                "font_size": 24,
                "color": "red",
                "absolute_positioning": {
                    "relative_x": 125,   # 300 - 175 = 125px right of reference
                    "relative_y": -25,   # 100 - 125 = -25px above reference
                    "distance_from_ref": 127.5
                }
            },
            {
                "type": "text",
                "text": "E",
                "x": 50,
                "y": 100,
                "font_size": 24,
                "color": "red",
                "absolute_positioning": {
                    "relative_x": -125,  # 50 - 175 = -125px left of reference
                    "relative_y": -25,   # 100 - 125 = -25px above reference
                    "distance_from_ref": 127.5
                }
            },
            {
                "type": "text",
                "text": "C",
                "x": 175,
                "y": 200,
                "font_size": 24,
                "color": "red",
                "absolute_positioning": {
                    "relative_x": 0,     # 175 - 175 = 0px from reference
                    "relative_y": 75,    # 200 - 125 = 75px below reference
                    "distance_from_ref": 75.0
                }
            }
        ]
    }

    return test_data

def test_absolute_positioning_generation():
    """Test the complete absolute positioning workflow"""
    print("Testing Absolute Positioning System")
    print("=" * 50)

    try:
        # Create test data
        print("1. Creating test data with absolute positioning...")
        test_data = create_test_absolute_positioning_data()

        # Save test JSON file
        test_file = "test_absolute_positioning_107.json"
        with open(test_file, 'w', encoding='utf-8') as f:
            json.dump(test_data, f, indent=2, ensure_ascii=False)
        print(f"   ✓ Saved test data to {test_file}")

        # Initialize template generator
        print("2. Initializing template generator...")
        generator = ShapeTemplateGenerator()
        print("   ✓ Template generator initialized")

        # Generate HTML template with absolute positioning
        print("3. Generating HTML template with absolute positioning...")
        html_file = generator.json_to_html(test_file, "107")
        print(f"   ✓ Generated template: {html_file}")

        # Verify the template contains absolute positioning information
        print("4. Verifying template contains absolute positioning data...")
        with open(html_file, 'r', encoding='utf-8') as f:
            template_content = f.read()

        checks = [
            ("Reference point comment", "Generated with absolute positioning" in template_content),
            ("Element A with absolute data", "Absolute: rel(+125,-25)" in template_content),
            ("Element E with absolute data", "Absolute: rel(-125,-25)" in template_content),
            ("Element C with absolute data", "Absolute: rel(+0,+75)" in template_content),
            ("Distance information", "dist=" in template_content)
        ]

        all_passed = True
        for check_name, result in checks:
            status = "✓ PASS" if result else "✗ FAIL"
            print(f"   {status}: {check_name}")
            if not result:
                all_passed = False

        # Print positioning summary
        print("\n5. Absolute positioning summary:")
        abs_pos = test_data['absolute_positioning']
        ref_point = abs_pos['reference_point']
        print(f"   Reference point: ({ref_point['x']}, {ref_point['y']})")

        for element in test_data['elements']:
            if 'absolute_positioning' in element:
                abs_data = element['absolute_positioning']
                print(f"   Element {element['text']}: rel({abs_data['relative_x']:+}, {abs_data['relative_y']:+}) distance={abs_data['distance_from_ref']:.1f}")

        # Cleanup
        if os.path.exists(test_file):
            os.remove(test_file)
            print(f"   ✓ Cleaned up {test_file}")

        if all_passed:
            print(f"\n🎉 SUCCESS: Absolute positioning system is working correctly!")
            print(f"   Template generated with precise positioning from reference point")
            print(f"   All elements positioned with exact distance measurements")
        else:
            print(f"\n❌ FAILED: Some absolute positioning features are not working")

        return all_passed

    except Exception as e:
        print(f"❌ TEST FAILED: {str(e)}")
        return False

def demonstrate_workflow():
    """Demonstrate the complete absolute positioning workflow"""
    print("\nAbsolute Positioning Workflow:")
    print("-" * 40)
    print("1. User sets reference point in positioning tool")
    print("2. User positions elements (labels, drawings)")
    print("3. Tool calculates distances from reference point")
    print("4. Export includes absolute positioning data")
    print("5. Template generator uses precise coordinates")
    print("6. Generated template has exact positioning")
    print("\nBenefits:")
    print("• Precise positioning with distance measurements")
    print("• Consistent layout regardless of canvas size")
    print("• Easy to reproduce exact designs")
    print("• Mathematical precision for all elements")

if __name__ == "__main__":
    # Run the test
    success = test_absolute_positioning_generation()

    # Show workflow explanation
    demonstrate_workflow()

    if success:
        print(f"\n✅ The absolute positioning system is ready for use!")
    else:
        print(f"\n❌ Fix the issues above before using the system")
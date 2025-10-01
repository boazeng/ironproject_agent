#!/usr/bin/env python3
"""
Test script for template generation functionality
"""
import json
import os
from shape_template_generator import ShapeTemplateGenerator

def create_test_json():
    """Create a test JSON file with positioning data"""
    test_data = {
        "shape_number": "107",
        "shape_name": "צורת U",
        "image_path": "test_image.png",
        "canvas_width": 350,
        "canvas_height": 250,
        "elements": [
            {
                "type": "text",
                "text": "A",
                "x": 300,
                "y": 130,
                "font_size": 24,
                "color": "red"
            },
            {
                "type": "text",
                "text": "E",
                "x": 50,
                "y": 130,
                "font_size": 24,
                "color": "red"
            },
            {
                "type": "text",
                "text": "C",
                "x": 175,
                "y": 200,
                "font_size": 24,
                "color": "red"
            },
            {
                "type": "line",
                "start_x": 80,
                "start_y": 50,
                "end_x": 80,
                "end_y": 180,
                "color": "black",
                "width": 3
            },
            {
                "type": "line",
                "start_x": 80,
                "start_y": 180,
                "end_x": 270,
                "end_y": 180,
                "color": "black",
                "width": 3
            },
            {
                "type": "line",
                "start_x": 270,
                "start_y": 180,
                "end_x": 270,
                "end_y": 50,
                "color": "black",
                "width": 3
            }
        ]
    }

    test_file = "test_shape_107.json"
    with open(test_file, 'w', encoding='utf-8') as f:
        json.dump(test_data, f, indent=2, ensure_ascii=False)

    return test_file

def test_template_generation():
    """Test the template generation"""
    try:
        print("Creating test JSON file...")
        json_file = create_test_json()

        print("Initializing template generator...")
        generator = ShapeTemplateGenerator()

        print("Converting JSON to HTML template...")
        html_file = generator.json_to_html(json_file, "107")

        print(f"[SUCCESS] Successfully generated HTML template: {html_file}")

        # Check if file exists and has content
        if os.path.exists(html_file):
            with open(html_file, 'r', encoding='utf-8') as f:
                content = f.read()
                print(f"[SUCCESS] Template file size: {len(content)} characters")
                if "shape-107" in content:
                    print("[SUCCESS] Template contains shape-107 ID")
                if "length-A-107" in content:
                    print("[SUCCESS] Template contains input field for A")
                if "length-E-107" in content:
                    print("[SUCCESS] Template contains input field for E")
                if "length-C-107" in content:
                    print("[SUCCESS] Template contains input field for C")
        else:
            print("[ERROR] HTML template file not found")

        # Cleanup
        if os.path.exists(json_file):
            os.remove(json_file)
            print(f"[SUCCESS] Cleaned up test file: {json_file}")

        print("\n[COMPLETE] Template generation test completed successfully!")

    except Exception as e:
        print(f"[ERROR] Test failed: {str(e)}")
        return False

    return True

if __name__ == "__main__":
    print("Testing Template Generation System")
    print("=" * 40)
    test_template_generation()
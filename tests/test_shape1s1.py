#!/usr/bin/env python3
"""
Test script for Shape1S1 Agent
"""

import os
import sys
from agents.shape_detection.shape1s1 import Shape1S1Agent

def main():
    """Test the Shape1S1 agent"""
    print("=== Testing Shape1S1 Agent ===")

    # Initialize agent
    agent = Shape1S1Agent()

    # Process shape files
    print("\n1. Processing all shape files...")
    results = agent.process_shape_files()

    print(f"\nResults:")
    print(f"Status: {results['status']}")
    print(f"Total shapes processed: {results['total_shapes']}")
    print(f"Errors: {len(results.get('errors', []))}")

    # Show details for first few shapes
    processed_shapes = results.get('processed_shapes', [])
    if processed_shapes:
        print(f"\n2. Sample shape analysis results:")
        for i, shape in enumerate(processed_shapes[:3]):  # Show first 3
            print(f"\nShape {i+1}: {shape['filename']}")

            # Geometry info
            geometry = shape.get('detected_geometry', {})
            print(f"  - Lines detected: {geometry.get('lines_detected', 0)}")
            print(f"  - Horizontal lines: {geometry.get('horizontal_lines', 0)}")
            print(f"  - Vertical lines: {geometry.get('vertical_lines', 0)}")
            print(f"  - Estimated shape: {geometry.get('estimated_shape', 'unknown')}")

            # Catalog match
            catalog_match = shape.get('catalog_match', {})
            best_match = catalog_match.get('best_match')
            if best_match:
                print(f"  - Catalog match: {best_match['shape_id']} ({best_match['confidence']:.1%} confidence)")
            else:
                print(f"  - Catalog match: No match found")

    # Test specific shape
    print(f"\n3. Testing specific shape analysis...")
    shapes_dir = "io/fullorder_output/table_detection/shapes"
    if os.path.exists(shapes_dir):
        shape_files = [f for f in os.listdir(shapes_dir) if f.endswith('.png')]
        if shape_files:
            test_file = os.path.join(shapes_dir, shape_files[0])
            print(f"Analyzing: {shape_files[0]}")

            shape_result = agent.analyze_shape(test_file)
            print(f"Analysis completed for: {shape_result.get('filename', 'unknown')}")

            # Show user message
            print("\n=== USER MESSAGE ===")
            agent.send_user_message(shape_result)
            print("===================")

    print(f"\n=== Shape1S1 Agent Test Complete ===")

if __name__ == "__main__":
    main()
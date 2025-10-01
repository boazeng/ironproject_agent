#!/usr/bin/env python3
"""
Test script for Shape1S1 Agent - Single Shape Processing
"""

import os
from agents.shape_detection.shape1s1 import Shape1S1Agent

def main():
    """Test single shape processing"""
    print("=== Shape1S1 Agent - Single Shape Processing ===")

    # Initialize agent
    agent = Shape1S1Agent()

    print("\n1. Getting next shape file from folder...")
    next_shape = agent.get_next_shape_file()

    if next_shape:
        print(f"Found shape file: {os.path.basename(next_shape)}")

        print(f"\n2. Processing single shape...")
        result = agent.process_single_shape(next_shape)

        print(f"Status: {result.get('status')}")

        if result.get('status') == 'completed':
            shape_analysis = result.get('shape_analysis', {})
            print(f"\n3. Shape Analysis Results:")
            print(f"   File: {shape_analysis.get('filename', 'unknown')}")

            # Geometry
            geometry = shape_analysis.get('detected_geometry', {})
            print(f"   Lines detected: {geometry.get('lines_detected', 0)}")
            print(f"   Estimated shape: {geometry.get('estimated_shape', 'unknown')}")

            # Catalog match
            catalog_match = shape_analysis.get('catalog_match', {})
            best_match = catalog_match.get('best_match')
            if best_match:
                print(f"   Catalog match: {best_match['shape_id']} ({best_match['confidence']:.1%} confidence)")
            else:
                print(f"   Catalog match: No match found")

            print(f"\n4. User Message:")
            agent.send_user_message(shape_analysis)

        else:
            print(f"Error: {result.get('message', 'Unknown error')}")

    else:
        print("No shape files found in the shapes directory.")
        print("Make sure there are PNG files in: io/fullorder_output/table_detection/shapes/")

    print(f"\n=== Single Shape Processing Complete ===")

if __name__ == "__main__":
    main()
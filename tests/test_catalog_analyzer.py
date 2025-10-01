#!/usr/bin/env python3
"""
Test script for Catalog Analyzer Agent (catdet)
"""

import os
from catalog_analyzer import CatalogAnalyzerAgent

def demo_catalog_analyzer():
    """Demonstrate the catalog analyzer functionality"""

    print("="*70)
    print("CATALOG ANALYZER AGENT (CATDET) - DEMO")
    print("="*70)

    # Initialize agent
    print("\n1. Initializing Catalog Analyzer Agent...")
    agent = CatalogAnalyzerAgent()
    print("   ✓ Agent initialized successfully")
    print(f"   - Output directory: {agent.output_dir}")
    print(f"   - Catalog file: {agent.catalog_output_file}")

    # Show existing catalog
    print("\n2. Current catalog status:")
    agent.list_catalog_shapes()

    # Show sample workflow
    print("\n3. Sample workflow for analyzing a catalog shape:")
    print("-" * 50)

    print("\n   Step 1: Load catalog shape image")
    print("   agent.process_catalog_image('path/to/catalog/shape.png')")

    print("\n   Step 2: Agent will display the image")
    print("   - Shows shape image in popup window (if matplotlib available)")
    print("   - Or provides path for manual viewing")

    print("\n   Step 3: Agent collects user input:")
    print("   - Shape name: e.g., 'L_BRACKET_90'")
    print("   - Number of ribs: e.g., '2'")
    print("   - Clock direction: e.g., 'clockwise'")
    print("   - For each rib:")
    print("     * Rib letter: e.g., 'A', 'B'")
    print("     * Angle to next: e.g., '90' (degrees)")

    print("\n   Step 4: Agent saves to catalog_format.json")

    # Show catalog format example
    print("\n4. Example catalog_format.json structure:")
    print("-" * 50)

    example_catalog = {
        "catalog_info": {
            "created_by": "catalog_analyzer_agent",
            "version": "1.0",
            "created_date": "2025-09-24T00:00:00",
            "description": "Bent iron shape catalog database"
        },
        "shapes": {
            "L_BRACKET_90": {
                "shape_name": "L_BRACKET_90",
                "image_file": "l_bracket.png",
                "number_of_ribs": 2,
                "clock_direction": "clockwise",
                "ribs": [
                    {
                        "rib_letter": "A",
                        "rib_number": 1,
                        "angle_to_next": 90
                    },
                    {
                        "rib_letter": "B",
                        "rib_number": 2,
                        "angle_to_next": None
                    }
                ],
                "status": "analyzed"
            }
        }
    }

    import json
    print(json.dumps(example_catalog, indent=2))

    # Show usage instructions
    print("\n5. How to use the agent:")
    print("-" * 50)
    print("\n   Interactive mode:")
    print("   python catalog_analyzer.py")

    print("\n   Programmatic usage:")
    print("   from catalog_analyzer import CatalogAnalyzerAgent")
    print("   agent = CatalogAnalyzerAgent()")
    print("   result = agent.process_catalog_image('shape.png')")

    # Check for sample images
    print("\n6. Looking for sample images to analyze...")
    shapes_dir = "io/fullorder_output/table_detection/shapes"
    if os.path.exists(shapes_dir):
        shape_files = [f for f in os.listdir(shapes_dir) if f.endswith('.png')]
        if shape_files:
            sample_file = os.path.join(shapes_dir, shape_files[0])
            print(f"   Found sample image: {shape_files[0]}")
            print(f"   To analyze this shape, run:")
            print(f"   agent.process_catalog_image('{sample_file}')")
        else:
            print("   No PNG files found in shapes directory")
    else:
        print("   Shapes directory not found")

    print("\n" + "="*70)
    print("CATALOG ANALYZER AGENT READY FOR USE!")
    print("="*70)

def test_with_simulated_input():
    """Test with simulated user input (non-interactive demo)"""
    print("\n" + "="*50)
    print("SIMULATED CATALOG ENTRY DEMO")
    print("="*50)

    agent = CatalogAnalyzerAgent()

    # Create a simulated shape entry
    sample_shape_data = {
        "shape_name": "L_BRACKET_90_DEMO",
        "image_file": "demo_shape.png",
        "image_path": "/path/to/demo_shape.png",
        "number_of_ribs": 2,
        "clock_direction": "clockwise",
        "ribs": [
            {
                "rib_letter": "A",
                "rib_number": 1,
                "angle_to_next": 90.0
            },
            {
                "rib_letter": "B",
                "rib_number": 2,
                "angle_to_next": None
            }
        ],
        "created_date": "2025-09-24T00:00:00",
        "status": "analyzed"
    }

    # Add to catalog
    shape_id = "L_BRACKET_90_DEMO"
    agent.catalog_data['shapes'][shape_id] = sample_shape_data

    # Show summary
    agent.show_data_summary(sample_shape_data)

    # Save catalog
    agent.save_catalog()

    print(f"\n✓ Demo shape '{sample_shape_data['shape_name']}' added to catalog")
    print(f"✓ Catalog saved to: {os.path.join(agent.output_dir, agent.catalog_output_file)}")

if __name__ == "__main__":
    demo_catalog_analyzer()
    test_with_simulated_input()
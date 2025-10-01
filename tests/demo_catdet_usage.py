#!/usr/bin/env python3
"""
CATALOG ANALYZER AGENT (CATDET) - Usage Demo

This script demonstrates how to use the catalog_analyzer agent
to build a catalog database of bent iron shapes.
"""

import os
from catalog_analyzer import CatalogAnalyzerAgent

def show_usage_example():
    """Show how to use the catalog analyzer agent"""

    print("="*70)
    print("CATALOG ANALYZER AGENT (CATDET) - USAGE GUIDE")
    print("="*70)

    print("\n[STEP 1] Initialize the agent")
    print("from catalog_analyzer import CatalogAnalyzerAgent")
    print("agent = CatalogAnalyzerAgent()")

    print("\n[STEP 2] Process a catalog shape image")
    print("result = agent.process_catalog_image('path/to/shape.png')")

    print("\n[STEP 3] Agent will ask for:")
    print("1. Shape name (e.g., 'L_BRACKET_90')")
    print("2. Number of ribs (e.g., '2')")
    print("3. Clock direction ('clockwise' or 'counterclockwise')")
    print("4. For each rib:")
    print("   - Rib letter (e.g., 'A', 'B')")
    print("   - Angle to next rib (e.g., '90' degrees)")

    print("\n[STEP 4] Agent saves to catalog_format.json")

    # Initialize agent for demo
    print("\n" + "="*70)
    print("DEMO INITIALIZATION")
    print("="*70)

    agent = CatalogAnalyzerAgent()
    print("Agent initialized successfully!")
    print(f"Output directory: {agent.output_dir}")
    print(f"Catalog file: {agent.catalog_output_file}")

    # Show catalog status
    print("\nCurrent catalog status:")
    agent.list_catalog_shapes()

    # Show expected file format
    print("\nExpected catalog_format.json structure:")
    print("=" * 50)

    example = '''
{
  "catalog_info": {
    "created_by": "catalog_analyzer_agent",
    "version": "1.0",
    "created_date": "2025-09-24T01:00:00",
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
          "angle_to_next": null
        }
      ],
      "status": "analyzed"
    }
  }
}'''
    print(example)

    # Look for available shape images
    print("\n" + "="*70)
    print("AVAILABLE SHAPE IMAGES FOR ANALYSIS")
    print("="*70)

    shapes_dir = "io/fullorder_output/table_detection/shapes"
    if os.path.exists(shapes_dir):
        shape_files = [f for f in os.listdir(shapes_dir) if f.endswith('.png')]
        if shape_files:
            print(f"Found {len(shape_files)} shape images:")
            for i, filename in enumerate(shape_files[:5], 1):  # Show first 5
                full_path = os.path.join(shapes_dir, filename)
                print(f"{i}. {filename}")
                print(f"   Path: {full_path}")

            if len(shape_files) > 5:
                print(f"   ... and {len(shape_files) - 5} more files")

            print(f"\nTo analyze the first shape:")
            print(f"agent.process_catalog_image('{os.path.join(shapes_dir, shape_files[0])}')")
        else:
            print("No PNG files found in shapes directory")
    else:
        print("Shapes directory not found")
        print("Run the shape detection pipeline first to generate shape images")

    print("\n" + "="*70)
    print("READY TO ANALYZE CATALOG SHAPES!")
    print("="*70)
    print("\nTo start interactive mode:")
    print("python catalog_analyzer.py")
    print("\nTo use programmatically:")
    print("from catalog_analyzer import CatalogAnalyzerAgent")
    print("agent = CatalogAnalyzerAgent()")
    print("result = agent.process_catalog_image('your_shape_image.png')")

def test_interactive_simulation():
    """Simulate the interactive workflow (for testing)"""
    print("\n" + "="*50)
    print("INTERACTIVE WORKFLOW SIMULATION")
    print("="*50)

    print("\n[Simulated] User selects shape image: 'L_bracket_sample.png'")
    print("[Agent] Displaying image...")
    print("[Agent] Collecting user input...")

    print("\n[Agent] 1. Enter shape name: L_BRACKET_90")
    print("[Agent] 2. Enter number of ribs: 2")
    print("[Agent] 3. Enter clock direction: clockwise")
    print("[Agent] 4. Enter data for each rib:")
    print("[Agent]    Rib 1: Letter = A, Angle to next = 90")
    print("[Agent]    Rib 2: Letter = B, (last rib)")
    print("[Agent] Data summary displayed...")
    print("[Agent] User confirms: y")
    print("[Agent] Shape 'L_BRACKET_90' added to catalog")
    print("[Agent] Catalog saved to catalog_format.json")

    print("\nSimulation complete!")

if __name__ == "__main__":
    show_usage_example()
    test_interactive_simulation()
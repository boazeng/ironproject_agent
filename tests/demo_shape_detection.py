#!/usr/bin/env python3
"""
Demo: Shape1S1 Agent - Simplified Single Shape Processing

This script demonstrates how the Shape1S1 agent now works with individual
shape images one at a time, without needing table detection.
"""

import os
from agents.shape_detection.shape1s1 import Shape1S1Agent

def demo_shape_detection():
    """Demonstrate simplified shape detection workflow"""

    print("="*60)
    print("🔧 SHAPE1S1 AGENT - SIMPLIFIED WORKFLOW DEMO")
    print("="*60)

    # Initialize the agent
    print("\n📋 Step 1: Initialize Shape1S1 Agent")
    agent = Shape1S1Agent()
    print("   ✅ Agent initialized successfully")

    # Get next shape file from folder
    print("\n📁 Step 2: Get next shape from folder")
    shape_file = agent.get_next_shape_file()

    if not shape_file:
        print("   ❌ No shape files found!")
        print("   💡 Make sure there are PNG files in: io/fullorder_output/table_detection/shapes/")
        return

    filename = os.path.basename(shape_file)
    print(f"   📄 Found shape file: {filename}")

    # Process single shape
    print(f"\n🔍 Step 3: Analyze single shape")
    print(f"   Processing: {filename}")

    result = agent.process_single_shape(shape_file)

    if result.get('status') != 'completed':
        print(f"   ❌ Analysis failed: {result.get('message', 'Unknown error')}")
        return

    # Show results
    shape_analysis = result.get('shape_analysis', {})
    print(f"   ✅ Analysis completed successfully!")

    print(f"\n📊 Step 4: Analysis Results")
    print(f"   📸 Image size: {shape_analysis.get('image_size', {})}")

    # Geometry detection
    geometry = shape_analysis.get('detected_geometry', {})
    print(f"   📐 Geometry:")
    print(f"      • Lines detected: {geometry.get('lines_detected', 0)}")
    print(f"      • Horizontal lines: {geometry.get('horizontal_lines', 0)}")
    print(f"      • Vertical lines: {geometry.get('vertical_lines', 0)}")
    print(f"      • Estimated shape: {geometry.get('estimated_shape', 'unknown')}")

    # Catalog matching
    catalog_match = shape_analysis.get('catalog_match', {})
    best_match = catalog_match.get('best_match')
    print(f"   📋 Catalog matching:")
    if best_match:
        print(f"      • Shape ID: {best_match['shape_id']}")
        print(f"      • Type: {best_match['shape_info']['description']}")
        print(f"      • Confidence: {best_match['confidence']:.1%}")
        print(f"      • Ribs: {best_match['shape_info']['ribs']}")
        print(f"      • Angles: {best_match['shape_info']['angles']}")
    else:
        print(f"      • No catalog match found")

    # Dimensions
    dimensions = shape_analysis.get('extracted_dimensions', {})
    print(f"   📏 Dimensions:")
    print(f"      • Red markings detected: {dimensions.get('has_red_markings', False)}")
    if dimensions.get('red_regions_count'):
        print(f"      • Red regions: {dimensions['red_regions_count']}")

    # User message
    print(f"\n💬 Step 5: User notification")
    agent.send_user_message(shape_analysis)

    # Output files
    output_dir = agent.output_dir
    print(f"\n💾 Step 6: Output files")
    print(f"   📁 Results saved to: {output_dir}")

    # List recent output files
    if os.path.exists(output_dir):
        files = [f for f in os.listdir(output_dir) if f.startswith('shape_analysis_')]
        if files:
            latest_file = sorted(files)[-1]
            print(f"   📄 Latest analysis: {latest_file}")

    print(f"\n✨ DEMO COMPLETE - Shape processing simplified!")
    print(f"   The agent now processes one shape at a time from the shapes folder")
    print(f"   No table detection needed - just individual shape analysis")

    print("="*60)

def show_usage():
    """Show how to use the agent"""
    print("\n🚀 USAGE EXAMPLES:")
    print("="*40)

    print("\n1️⃣ Get next shape file:")
    print("   from agents.shape_detection.shape1s1 import Shape1S1Agent")
    print("   agent = Shape1S1Agent()")
    print("   shape_file = agent.get_next_shape_file()")

    print("\n2️⃣ Process single shape:")
    print("   result = agent.process_single_shape(shape_file)")

    print("\n3️⃣ One-liner processing:")
    print("   agent = Shape1S1Agent()")
    print("   shape = agent.get_next_shape_file()")
    print("   result = agent.process_single_shape(shape) if shape else None")

    print("\n💡 The agent automatically:")
    print("   • Detects geometric features (lines, angles)")
    print("   • Matches against catalog shapes")
    print("   • Extracts dimensions from markings")
    print("   • Sends user notification")
    print("   • Saves analysis results to JSON")

if __name__ == "__main__":
    demo_shape_detection()
    show_usage()
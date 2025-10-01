#!/usr/bin/env python3
"""
Test script to integrate table OCR files into the database
This should be run after form1ocr1 creates all the OCR files
"""

import sys
import os

# Add the current directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from agents.llm_agents.format1_agent.form1dat1 import Form1Dat1Agent

def main():
    """Run the table OCR integration"""

    print("=== Table OCR Integration Test ===")

    # Initialize the form1dat1 agent
    form1dat1 = Form1Dat1Agent()

    # Order to process
    order_number = "CO25S006375"

    print(f"Processing order: {order_number}")

    # Run the integration
    success = form1dat1.integrate_table_ocr_files(order_number)

    if success:
        print("\n✅ Integration completed successfully!")

        # Display the results
        section3_data = form1dat1.get_section_data(order_number, "section_3_shape_analysis")
        if section3_data:
            print(f"\n📊 Integration Summary:")
            total_lines = 0
            for page_key, page_data in section3_data.items():
                page_num = page_data.get('page_number', '?')
                line_count = page_data.get('number_of_order_lines', 0)
                total_lines += line_count
                print(f"  📄 Page {page_num}: {line_count} order lines")
            print(f"  📈 Total order lines: {total_lines}")

    else:
        print("\n❌ Integration failed!")
        return False

    return True

if __name__ == "__main__":
    main()
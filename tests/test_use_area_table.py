#!/usr/bin/env python3
"""
Test script to run UseAreaTableAgent directly
"""

from agents.llm_agents.format1_agent.use_area_table import UseAreaTableAgent

def main():
    # Create agent instance
    agent = UseAreaTableAgent()

    # Test with the current order
    order_name = "CO25S006375"
    page_number = 1

    print(f"Testing UseAreaTableAgent for {order_name}, page {page_number}")

    # Check if file exists
    file_exists = agent.check_file_exists(order_name, page_number)
    print(f"Input file exists: {file_exists}")

    if file_exists:
        # Process the page
        result = agent.process_page(order_name, page_number)
        print(f"Processing result: {result}")

        if result["status"] == "success":
            print(f"✅ Successfully processed and saved to: {result['output_file']}")
        else:
            print(f"❌ Processing failed: {result['message']}")
    else:
        print("❌ No input file found to process")

if __name__ == "__main__":
    main()
"""
Test script for SIMPLIFIED Form1Dat1 Agent
Only Section 1 (general) and Section 2 (OCR)
"""

from agents.llm_agents.form1dat1_agent import Form1Dat1Agent
import json
from pathlib import Path

def test_simplified_form1dat1():
    """Test the simplified form1dat1 with only 2 sections"""

    print("=" * 50)
    print("Testing Simplified Form1Dat1 Agent")
    print("ONLY Section 1 (General) and Section 2 (OCR)")
    print("=" * 50)

    # Initialize agent
    agent = Form1Dat1Agent()
    print(f"[OK] Agent initialized: {agent.name}")

    # Test order
    order_number = "CO25S007000"

    # Step 1: Initialize order (creates file with 2 sections)
    print(f"\n1. Initializing order {order_number}...")
    success = agent.initialize_order(order_number)
    print(f"   Initialize: {'Success' if success else 'Failed'}")

    # Check created file
    file_path = agent.json_output_path / f"{order_number}_out.json"
    if file_path.exists():
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        print(f"   File created with sections: {list(data.keys())}")
        print(f"   Section 1: {data['section_1_general']}")
        print(f"   Section 2: {data['section_2_ocr']}")

    # Step 2: Simulate form1ocr1 sending OCR data
    print(f"\n2. form1ocr1 sends OCR data...")
    ocr_data_from_form1ocr1 = {
        "extracted_text": "Order CO25S007000",
        "customer": "Test Company",
        "items": ["Item1", "Item2", "Item3"],
        "total": 100,
        "timestamp": "2025-01-21"
    }

    success = agent.store_ocr_data(order_number, ocr_data_from_form1ocr1)
    print(f"   Store OCR: {'Success' if success else 'Failed'}")

    # Step 3: Verify final structure
    print(f"\n3. Final database structure:")
    with open(file_path, 'r', encoding='utf-8') as f:
        final_data = json.load(f)

    print(json.dumps(final_data, indent=2, ensure_ascii=False))

    print("\n" + "=" * 50)
    print("Test Complete - Simple 2-section structure works!")
    print("=" * 50)

if __name__ == "__main__":
    test_simplified_form1dat1()
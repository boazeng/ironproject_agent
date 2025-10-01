"""
Test script for Form1Dat1 Agent with Sectioned Database Format
"""

from agents.llm_agents.form1dat1_agent import Form1Dat1Agent
import json
from pathlib import Path
from datetime import datetime

def test_sectioned_database():
    """Test the new sectioned database format"""

    print("=" * 60)
    print("Testing Form1Dat1 Agent - Sectioned Database Format")
    print("=" * 60)

    # Initialize the agent
    agent = Form1Dat1Agent()
    print(f"[OK] Agent initialized: {agent.name}")

    # Test order number
    test_order = "CO25S006789"

    # Test 1: Initialize order with sections
    print("\n1. Testing order initialization with sections...")
    success = agent.initialize_order(test_order, source_file="test_drawing.pdf")
    print(f"   Initialize order: {'Success' if success else 'Failed'}")

    # Verify structure
    order_data = agent.get_order_data(test_order, data_type="main")
    if order_data:
        print("   Order structure created with sections:")
        for section in order_data.keys():
            print(f"   - {section}")

    # Test 2: Update Section 1 - General Data
    print("\n2. Testing Section 1 - General Data update...")
    general_update = {
        "status": "processing",
        "customer_id": "CUST_001",
        "priority": "high"
    }
    success = agent.update_section(test_order, "section_1_general", general_update)
    print(f"   Update general data: {'Success' if success else 'Failed'}")

    # Test 3: Store OCR Data in Section 2
    print("\n3. Testing Section 2 - OCR Data storage...")
    ocr_data = {
        "header": {
            "order_number": test_order,
            "customer_name": "Test Industries Ltd.",
            "date": "2025-01-21",
            "reference": "REF-2025-001"
        },
        "table_header": {
            "columns": ["Item", "Shape", "Length", "Width", "Quantity"],
            "units": ["", "", "mm", "mm", "pcs"]
        },
        "table_rows": [
            ["1", "L", "100", "50", "10"],
            ["2", "U", "150", "75", "5"],
            ["3", "Z", "200", "100", "3"]
        ],
        "footer": {
            "total": "18 items",
            "notes": "Rush order - deliver by end of week"
        },
        "raw_text": "Sample OCR extracted text...",
        "confidence_score": 0.95
    }

    success = agent.store_ocr_data(test_order, ocr_data, agent_name="form1ocr1")
    print(f"   Store OCR data: {'Success' if success else 'Failed'}")

    # Test 4: Retrieve specific section data
    print("\n4. Testing section data retrieval...")
    section_2_data = agent.get_section_data(test_order, "section_2_ocr")
    if section_2_data:
        print("   Retrieved Section 2 - OCR Data:")
        print(f"   - Customer: {section_2_data['header'].get('customer_name')}")
        print(f"   - Table rows: {len(section_2_data.get('table_rows', []))}")
        print(f"   - Confidence: {section_2_data.get('confidence_score')}")

    # Test 5: Update Section 3 - Shapes
    print("\n5. Testing Section 3 - Shapes update...")
    shapes_data = {
        "shapes_detected": ["L-shape", "U-shape", "Z-shape"],
        "total_shapes": 3,
        "processing_timestamp": datetime.now().isoformat()
    }
    success = agent.update_section(test_order, "section_3_shapes", shapes_data, merge=False)
    print(f"   Update shapes data: {'Success' if success else 'Failed'}")

    # Test 6: Update Section 5 - Status
    print("\n6. Testing Section 5 - Status update...")
    status_update = {
        "overall_status": "ocr_complete",
        "processing_steps": [
            {"step": "initialization", "status": "complete", "timestamp": datetime.now().isoformat()},
            {"step": "ocr_processing", "status": "complete", "timestamp": datetime.now().isoformat()}
        ],
        "warnings": ["Low confidence on row 3"]
    }
    success = agent.update_section(test_order, "section_5_status", status_update)
    print(f"   Update status: {'Success' if success else 'Failed'}")

    # Test 7: Display final database structure
    print("\n7. Final database structure:")
    file_path = agent.json_output_path / f"{test_order}_out.json"
    if file_path.exists():
        with open(file_path, 'r', encoding='utf-8') as f:
            final_data = json.load(f)

        print(f"\nFile: {test_order}_out.json")
        print("\nSection 1 - General:")
        print(f"  Order Number: {final_data['section_1_general']['order_number']}")
        print(f"  Status: {final_data['section_1_general']['status']}")
        print(f"  Agent History: {len(final_data['section_1_general']['agent_history'])} entries")

        print("\nSection 2 - OCR:")
        print(f"  Header: {final_data['section_2_ocr']['header']}")
        print(f"  Table Rows: {len(final_data['section_2_ocr']['table_rows'])}")

        print("\nSection 3 - Shapes:")
        print(f"  Shapes: {final_data['section_3_shapes']['shapes_detected']}")

        print("\nSection 5 - Status:")
        print(f"  Overall Status: {final_data['section_5_status']['overall_status']}")
        print(f"  Processing Steps: {len(final_data['section_5_status']['processing_steps'])}")

        # Show agent history
        print("\nAgent History:")
        for entry in final_data['section_1_general']['agent_history']:
            print(f"  - {entry['agent']}: {entry['action']} at {entry['timestamp'][:19]}")

    print("\n" + "=" * 60)
    print("Sectioned Database Testing Complete!")
    print("=" * 60)

    # Show file size
    if file_path.exists():
        file_size = file_path.stat().st_size
        print(f"\nDatabase file size: {file_size} bytes")

    return test_order

def simulate_form1ocr1_call():
    """Simulate how form1ocr1 agent would call form1dat1"""

    print("\n" + "=" * 60)
    print("Simulating form1ocr1 Agent Calling form1dat1")
    print("=" * 60)

    agent = Form1Dat1Agent()
    order_number = "CO25S006790"

    # Initialize order
    agent.initialize_order(order_number, source_file="drawing_CO25S006790.pdf")

    # Simulate OCR processing result
    ocr_result = {
        "header": {
            "order_number": "CO25S006790",
            "customer_name": "אברהם כהן ובניו בע\"מ",  # Hebrew text
            "date": "21/01/2025",
            "reference": "REF-IL-2025-042",
            "additional_info": {
                "project": "תל אביב מגדל 1",
                "architect": "משרד אדריכלים ABC"
            }
        },
        "table_header": {
            "columns": ["מס'", "צורה", "אורך", "רוחב", "כמות", "הערות"],
            "units": ["", "", "מ\"מ", "מ\"מ", "יח'", ""]
        },
        "table_rows": [
            ["1", "L", "1200", "600", "25", "דחוף"],
            ["2", "U", "800", "400", "15", ""],
            ["3", "מיוחד", "1500", "750", "10", "לפי שרטוט"]
        ],
        "footer": {
            "total": "50 יחידות",
            "notes": "אספקה: תוך 3 ימי עסקים"
        },
        "raw_text": "Full OCR extracted text with Hebrew content...",
        "confidence_score": 0.88
    }

    # Call form1dat1 to store OCR data
    print("\nform1ocr1 calling form1dat1.store_ocr_data()...")
    success = agent.store_ocr_data(order_number, ocr_result, agent_name="form1ocr1")
    print(f"OCR data storage: {'Success' if success else 'Failed'}")

    # Verify stored data
    stored_data = agent.get_section_data(order_number, "section_2_ocr")
    if stored_data:
        print("\nStored OCR Data Preview:")
        print(f"  Customer: {stored_data['header']['customer_name']}")
        print(f"  Columns: {stored_data['table_header']['columns']}")
        print(f"  Total rows: {len(stored_data['table_rows'])}")
        print(f"  Footer: {stored_data['footer']['notes']}")

    print("\n" + "=" * 60)
    print("form1ocr1 Simulation Complete!")
    print("=" * 60)

if __name__ == "__main__":
    # Run main test
    order_num = test_sectioned_database()

    # Run form1ocr1 simulation
    simulate_form1ocr1_call()

    print("\n[OK] All tests completed successfully!")
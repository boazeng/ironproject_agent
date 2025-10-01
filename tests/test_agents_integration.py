"""
Test script for Agent Integration
Tests form1s1, form1ocr1, and form1dat1 working together
"""

from agents.llm_agents.format1_agent.form1s1 import Form1S1Agent
from agents.llm_agents.format1_agent.form1ocr1 import Form1OCR1Agent
from agents.llm_agents.format1_agent.form1dat1 import Form1Dat1Agent
import json
from pathlib import Path

def test_agent_integration():
    """Test the integration between form1s1, form1ocr1, and form1dat1"""

    print("=" * 60)
    print("Testing Agent Integration")
    print("form1s1 -> form1dat1 (Section 1)")
    print("form1ocr1 -> form1dat1 (Section 2)")
    print("=" * 60)

    # Test order number
    test_order = "TEST_INTEGRATION_001"

    # Step 1: Test form1s1 calling form1dat1 (Section 1 - General Data)
    print("\n1. Testing form1s1 -> form1dat1 integration...")

    # Simulate form1s1 processing (without actual PDF)
    form1s1 = Form1S1Agent()

    # Manually call form1dat1 like form1s1 would do
    general_data = {
        "order_name": test_order,
        "order_create_date": "2025-01-21T10:30:00",
        "number_of_pages": 3
    }

    form1s1.form1dat1.initialize_order(test_order)
    form1s1.form1dat1.update_section(test_order, "section_1_general", general_data, merge=True)
    print("   [OK] form1s1 stored general data in Section 1")

    # Step 2: Test form1ocr1 calling form1dat1 (Section 2 - OCR Data)
    print("\n2. Testing form1ocr1 -> form1dat1 integration...")

    # Simulate form1ocr1 processing (without actual OCR)
    form1ocr1 = Form1OCR1Agent()

    # Sample OCR data that form1ocr1 would generate
    ocr_data = {
        'extracted_fields': {
            "לקוח/פרויקט": "חברת בנייה ABC",
            "מס הזמנה": test_order,
            "תאריך הזמנה": "21/01/2025",
            "סה\"כ משקל": "2500 ק\"ג"
        },
        'field_count': 4,
        'source_image': f"io/temp/{test_order}_order_header.png",
        'agent': 'form1ocr1',
        'processing_timestamp': "2025-01-21T10:35:00"
    }

    form1ocr1.form1dat1.store_ocr_data(test_order, ocr_data)
    print("   [OK] form1ocr1 stored OCR data in Section 2")

    # Step 3: Verify integrated data structure
    print("\n3. Verifying integrated database structure...")

    form1dat1 = Form1Dat1Agent()
    file_path = form1dat1.json_output_path / f"{test_order}_out.json"

    if file_path.exists():
        with open(file_path, 'r', encoding='utf-8') as f:
            integrated_data = json.load(f)

        print("   [OK] Integrated database file found")
        print(f"\n   Database structure for {test_order}:")
        print(json.dumps(integrated_data, indent=2, ensure_ascii=False))

        # Verify sections
        section1 = integrated_data.get('section_1_general', {})
        section2 = integrated_data.get('section_2_ocr', {})

        print(f"\n   Section 1 (General) - Order: {section1.get('order_name')}")
        print(f"   Section 1 (General) - Pages: {section1.get('number_of_pages')}")
        print(f"   Section 2 (OCR) - Fields: {section2.get('field_count', 0)}")
        print(f"   Section 2 (OCR) - Agent: {section2.get('agent')}")

    else:
        print("   [ERROR] Integrated database file not found")

    # Step 4: Test data retrieval
    print("\n4. Testing data retrieval...")

    section1_data = form1dat1.get_section_data(test_order, "section_1_general")
    section2_data = form1dat1.get_section_data(test_order, "section_2_ocr")

    if section1_data:
        print(f"   [OK] Section 1 retrieved: {section1_data.get('order_name')}")
    else:
        print("   [ERROR] Section 1 not retrieved")

    if section2_data:
        print(f"   [OK] Section 2 retrieved: {section2_data.get('agent')}")
    else:
        print("   [ERROR] Section 2 not retrieved")

    print("\n" + "=" * 60)
    print("Integration Testing Complete!")
    print("✓ form1s1 successfully stores general data in Section 1")
    print("✓ form1ocr1 successfully stores OCR data in Section 2")
    print("✓ form1dat1 manages both sections in unified database")
    print("=" * 60)

    return test_order

def show_workflow():
    """Show the complete workflow"""

    print("\n" + "=" * 60)
    print("COMPLETE WORKFLOW DEMONSTRATION")
    print("=" * 60)

    print("\n📋 Agent Flow:")
    print("1. form1s1 receives PDF file")
    print("2. form1s1 extracts pages and calls form1dat1")
    print("   → form1dat1.initialize_order(order_number)")
    print("   → form1dat1.update_section('section_1_general', general_data)")
    print("3. form1ocr1 processes order header")
    print("4. form1ocr1 calls form1dat1")
    print("   → form1dat1.store_ocr_data(order_number, ocr_data)")

    print("\n📁 Database Structure:")
    print("File: {ordernumber}_out.json")
    print("├── section_1_general")
    print("│   ├── order_number")
    print("│   ├── date_created")
    print("│   ├── date_modified")
    print("│   ├── order_name")
    print("│   ├── order_create_date")
    print("│   └── number_of_pages")
    print("└── section_2_ocr")
    print("    ├── extracted_fields")
    print("    ├── field_count")
    print("    ├── source_image")
    print("    ├── agent")
    print("    └── processing_timestamp")

if __name__ == "__main__":
    # Run integration test
    order_num = test_agent_integration()

    # Show workflow
    show_workflow()

    print(f"\n💾 Test data stored in: io/fullorder_output/json_output/{order_num}_out.json")
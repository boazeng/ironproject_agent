"""
Test script for Form1Dat1 Agent
"""

from agents.llm_agents.form1dat1_agent import Form1Dat1Agent
import json
from pathlib import Path

def test_form1dat1_agent():
    """Test the Form1Dat1 agent functionality"""

    print("=" * 50)
    print("Testing Form1Dat1 Agent")
    print("=" * 50)

    # Initialize the agent
    agent = Form1Dat1Agent()
    print(f"[OK] Agent initialized: {agent.name}")
    print(f"[OK] JSON output path: {agent.json_output_path}")

    # Test order number
    test_order = "TEST_ORDER_001"

    # Test 1: Store main order data
    print("\n1. Testing main order data storage...")
    main_data = {
        "customer": "Test Customer",
        "date": "2025-01-21",
        "total_items": 5,
        "status": "pending",
        "shapes": ["L-shape", "U-shape"],
        "dimensions": {
            "width": 100,
            "height": 200
        }
    }

    success = agent.store_order_data(test_order, main_data, data_type="main")
    print(f"   Store main data: {'Success' if success else 'Failed'}")

    # Test 2: Append data to existing order
    print("\n2. Testing data append...")
    success = agent.append_data(test_order, "notes", "First note", data_type="main")
    print(f"   Append first note: {'Success' if success else 'Failed'}")

    success = agent.append_data(test_order, "notes", "Second note", data_type="main")
    print(f"   Append second note: {'Success' if success else 'Failed'}")

    # Test 3: Store shape-specific data
    print("\n3. Testing shape data storage...")
    shape_data = {
        "shape_type": "L-shape",
        "angle": 90,
        "material": "Steel",
        "thickness": 5
    }

    success = agent.store_order_data(test_order, shape_data, data_type="shapes")
    print(f"   Store shape data: {'Success' if success else 'Failed'}")

    # Test 4: Process agent request
    print("\n4. Testing agent request processing...")
    request_data = {
        "measurement": 150,
        "unit": "mm",
        "verified": True
    }

    response = agent.process_agent_request(
        sender_agent="measurement_agent",
        order_number=test_order,
        data=request_data,
        action="store"
    )
    print(f"   Process request: {response['status']} - {response['message']}")

    # Test 5: Retrieve order data
    print("\n5. Testing data retrieval...")
    retrieved_data = agent.get_order_data(test_order, data_type="main")
    if retrieved_data:
        print(f"   Retrieved main data: Success")
        print(f"   - Order number: {retrieved_data.get('order_number')}")
        print(f"   - Customer: {retrieved_data.get('customer')}")
        print(f"   - Notes: {retrieved_data.get('notes', [])}")
    else:
        print(f"   Retrieved data: Failed")

    # Test 6: Bulk store
    print("\n6. Testing bulk store...")
    bulk_items = [
        {
            "data_type": "dimensions",
            "data": {
                "length": 300,
                "width": 200,
                "height": 100
            }
        },
        {
            "data_type": "materials",
            "data": {
                "type": "iron",
                "grade": "A36",
                "coating": "galvanized"
            }
        }
    ]

    success = agent.bulk_store(test_order, bulk_items)
    print(f"   Bulk store: {'Success' if success else 'Failed'}")

    # Test 7: List stored orders
    print("\n7. Testing list stored orders...")
    orders = agent.list_stored_orders()
    print(f"   Found {len(orders)} order(s): {orders}")

    # Test 8: Verify file structure
    print("\n8. Verifying file structure...")
    json_path = agent.json_output_path
    files = list(json_path.glob(f"{test_order}*.json"))
    print(f"   Found {len(files)} file(s) for test order:")
    for file in files:
        print(f"   - {file.name}")
        # Display file content
        with open(file, 'r') as f:
            content = json.load(f)
            print(f"     Keys: {list(content.keys())}")

    print("\n" + "=" * 50)
    print("Form1Dat1 Agent Testing Complete!")
    print("=" * 50)

    # Cleanup test files (optional)
    cleanup = input("\nClean up test files? (y/n): ")
    if cleanup.lower() == 'y':
        for file in files:
            file.unlink()
        print("[OK] Test files cleaned up")

if __name__ == "__main__":
    test_form1dat1_agent()
import json
import os
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, Optional

class Form1Dat1Agent:
    """
    Form1Dat1 Agent - Centralized data storage agent
    Collects data from different agents and stores it in JSON format
    """

    def __init__(self):
        self.name = "form1dat1_agent"
        self.system_message = """You are Form1Dat1, the centralized data storage agent.
        Your role is to:
        1. Collect data from various agents
        2. Store data in organized JSON format with defined sections
        3. Manage data files in the json_output folder
        4. Ensure data integrity and proper formatting
        5. Handle data updates and modifications

        Default storage location: io/fullorder_output/json_output/
        Main order file naming: {ordernumber}_out.json

        Database Structure:
        - Section 1: General Data (order number, date, etc.)
        - Section 2: OCR Data (from form1ocr1 agent)
        """

        # Set up storage paths
        self.base_output_path = Path("io/fullorder_output")
        self.json_output_path = self.base_output_path / "json_output"

        # Create json_output directory if it doesn't exist
        self.json_output_path.mkdir(parents=True, exist_ok=True)

        # In-memory data cache
        self.data_cache = {}

        # Define simplified database structure template - ONLY 2 SECTIONS
        self.database_template = {
            "section_1_general": {
                "order_number": "",
                "date_created": "",
                "date_modified": ""
            },
            "section_2_ocr": {}
        }

    def store_order_data(self, order_number: str, data: Dict[str, Any], data_type: str = "main") -> bool:
        """
        Store order data to JSON file

        Args:
            order_number: The order number identifier
            data: The data to store
            data_type: Type of data (main, shapes, dimensions, etc.)

        Returns:
            bool: Success status
        """
        try:
            # Determine file path based on data type
            if data_type == "main":
                file_name = f"{order_number}_out.json"
            else:
                file_name = f"{order_number}_{data_type}.json"

            file_path = self.json_output_path / file_name

            # Load existing data if file exists
            existing_data = {}
            if file_path.exists():
                with open(file_path, 'r', encoding='utf-8') as f:
                    existing_data = json.load(f)

            # Update with new data
            if data_type == "main":
                # For main data, merge at top level
                existing_data.update(data)
            else:
                # For specific data types, store under that key
                if data_type not in existing_data:
                    existing_data[data_type] = {}
                existing_data[data_type].update(data)

            # Add metadata
            existing_data['last_updated'] = datetime.now().isoformat()
            existing_data['order_number'] = order_number

            # Save to file
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(existing_data, f, indent=2, ensure_ascii=False)

            # Update cache
            cache_key = f"{order_number}_{data_type}"
            self.data_cache[cache_key] = existing_data

            print(f"[OK] Data saved to {file_path}")
            return True

        except Exception as e:
            print(f"[ERROR] Error storing data: {str(e)}")
            return False

    def append_data(self, order_number: str, key: str, value: Any, data_type: str = "main") -> bool:
        """
        Append data to a specific key in the order file

        Args:
            order_number: The order number identifier
            key: The key to append data to
            value: The value to append
            data_type: Type of data file

        Returns:
            bool: Success status
        """
        try:
            # Determine file path
            if data_type == "main":
                file_name = f"{order_number}_out.json"
            else:
                file_name = f"{order_number}_{data_type}.json"

            file_path = self.json_output_path / file_name

            # Load existing data
            existing_data = {}
            if file_path.exists():
                with open(file_path, 'r', encoding='utf-8') as f:
                    existing_data = json.load(f)

            # Navigate to the correct location and append
            if data_type != "main" and data_type not in existing_data:
                existing_data[data_type] = {}

            target = existing_data if data_type == "main" else existing_data[data_type]

            if key not in target:
                target[key] = []
            elif not isinstance(target[key], list):
                target[key] = [target[key]]

            target[key].append(value)

            # Update metadata
            existing_data['last_updated'] = datetime.now().isoformat()
            existing_data['order_number'] = order_number

            # Save to file
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(existing_data, f, indent=2, ensure_ascii=False)

            return True

        except Exception as e:
            print(f"[ERROR] Error appending data: {str(e)}")
            return False

    def get_order_data(self, order_number: str, data_type: str = "main") -> Optional[Dict[str, Any]]:
        """
        Retrieve order data from JSON file

        Args:
            order_number: The order number identifier
            data_type: Type of data to retrieve

        Returns:
            Dict or None: The stored data if found
        """
        try:
            # Check cache first
            cache_key = f"{order_number}_{data_type}"
            if cache_key in self.data_cache:
                return self.data_cache[cache_key]

            # Load from file
            if data_type == "main":
                file_name = f"{order_number}_out.json"
            else:
                file_name = f"{order_number}_{data_type}.json"

            file_path = self.json_output_path / file_name

            if file_path.exists():
                with open(file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)

                # Update cache
                self.data_cache[cache_key] = data
                return data

            return None

        except Exception as e:
            print(f"[ERROR] Error retrieving data: {str(e)}")
            return None

    def process_agent_request(self, sender_agent: str, order_number: str, data: Dict[str, Any], action: str = "store") -> Dict[str, Any]:
        """
        Process data storage request from another agent

        Args:
            sender_agent: Name of the agent sending the data
            order_number: The order number
            data: The data to process
            action: The action to perform (store, append, retrieve)

        Returns:
            Dict: Response with status and any retrieved data
        """
        response = {
            'status': 'success',
            'message': '',
            'data': None
        }

        try:
            # Add sender information to data
            data['source_agent'] = sender_agent
            data['timestamp'] = datetime.now().isoformat()

            if action == "store":
                success = self.store_order_data(order_number, data, data_type="main")
                response['status'] = 'success' if success else 'failed'
                response['message'] = f"Data from {sender_agent} stored for order {order_number}"

            elif action == "append":
                # Extract key and value from data
                if 'key' in data and 'value' in data:
                    success = self.append_data(order_number, data['key'], data['value'])
                    response['status'] = 'success' if success else 'failed'
                    response['message'] = f"Data appended to order {order_number}"
                else:
                    response['status'] = 'failed'
                    response['message'] = "Missing 'key' or 'value' in append request"

            elif action == "retrieve":
                retrieved_data = self.get_order_data(order_number)
                response['data'] = retrieved_data
                response['status'] = 'success' if retrieved_data else 'not_found'
                response['message'] = f"Data retrieved for order {order_number}"

            else:
                response['status'] = 'failed'
                response['message'] = f"Unknown action: {action}"

        except Exception as e:
            response['status'] = 'failed'
            response['message'] = f"Error processing request: {str(e)}"

        return response

    def bulk_store(self, order_number: str, data_items: list) -> bool:
        """
        Store multiple data items at once

        Args:
            order_number: The order number
            data_items: List of dictionaries containing data_type and data

        Returns:
            bool: Success status
        """
        try:
            for item in data_items:
                if 'data_type' in item and 'data' in item:
                    self.store_order_data(
                        order_number,
                        item['data'],
                        data_type=item.get('data_type', 'main')
                    )
            return True

        except Exception as e:
            print(f"[ERROR] Error in bulk store: {str(e)}")
            return False

    def list_stored_orders(self) -> list:
        """
        List all stored order numbers

        Returns:
            list: List of order numbers
        """
        try:
            orders = set()
            for file in self.json_output_path.glob("*_out.json"):
                order_number = file.stem.replace("_out", "")
                orders.add(order_number)

            return sorted(list(orders))

        except Exception as e:
            print(f"[ERROR] Error listing orders: {str(e)}")
            return []

    def initialize_order(self, order_number: str) -> bool:
        """
        Initialize a new order with the database template structure
        Creates the main {ordernumber}_out.json file with ONLY 2 sections

        Args:
            order_number: The order number identifier

        Returns:
            bool: Success status
        """
        try:
            file_path = self.json_output_path / f"{order_number}_out.json"

            # Check if file already exists
            if file_path.exists():
                print(f"[INFO] Order {order_number} already exists.")
                return True

            # Create new order from template
            import copy
            new_order = copy.deepcopy(self.database_template)

            # Fill in Section 1 - General Data (minimal)
            new_order["section_1_general"]["order_number"] = order_number
            new_order["section_1_general"]["date_created"] = datetime.now().isoformat()
            new_order["section_1_general"]["date_modified"] = datetime.now().isoformat()

            # Section 2 starts empty - will be filled by form1ocr1
            new_order["section_2_ocr"] = {}

            # Save to file
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(new_order, f, indent=2, ensure_ascii=False)

            # Update cache
            self.data_cache[f"{order_number}_main"] = new_order

            print(f"[OK] Order {order_number} initialized at {file_path}")
            return True

        except Exception as e:
            print(f"[ERROR] Error initializing order: {str(e)}")
            return False

    def update_section(self, order_number: str, section: str, data: Dict[str, Any], merge: bool = True) -> bool:
        """
        Update a specific section of the order database

        Args:
            order_number: The order number identifier
            section: Section name (e.g., 'section_1_general', 'section_2_ocr')
            data: Data to update in the section
            merge: If True, merge with existing data; if False, replace entirely

        Returns:
            bool: Success status
        """
        try:
            file_path = self.json_output_path / f"{order_number}_out.json"

            # Load existing order or initialize new one
            if not file_path.exists():
                self.initialize_order(order_number)

            # Load current data
            with open(file_path, 'r', encoding='utf-8') as f:
                order_data = json.load(f)

            # Update the specified section
            if section not in order_data:
                order_data[section] = {}

            if merge:
                # Merge data into existing section
                self._deep_merge(order_data[section], data)
            else:
                # Replace section entirely
                order_data[section] = data

            # Update metadata
            order_data["section_1_general"]["date_modified"] = datetime.now().isoformat()

            # Save updated data
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(order_data, f, indent=2, ensure_ascii=False)

            # Update cache
            self.data_cache[f"{order_number}_main"] = order_data

            print(f"[OK] Section '{section}' updated for order {order_number}")
            return True

        except Exception as e:
            print(f"[ERROR] Error updating section: {str(e)}")
            return False

    def _deep_merge(self, target: dict, source: dict) -> None:
        """
        Deep merge source dictionary into target dictionary

        Args:
            target: Target dictionary to merge into
            source: Source dictionary to merge from
        """
        for key, value in source.items():
            if key in target:
                if isinstance(target[key], dict) and isinstance(value, dict):
                    self._deep_merge(target[key], value)
                elif isinstance(target[key], list) and isinstance(value, list):
                    target[key].extend(value)
                else:
                    target[key] = value
            else:
                target[key] = value

    def store_ocr_data(self, order_number: str, ocr_data: Dict[str, Any]) -> bool:
        """
        Store OCR data in Section 2 of the order database
        Called by form1ocr1 agent

        Args:
            order_number: The order number identifier
            ocr_data: OCR data from form1ocr1 agent (stores whatever is provided)

        Returns:
            bool: Success status
        """
        try:
            # Initialize order if needed
            file_path = self.json_output_path / f"{order_number}_out.json"
            if not file_path.exists():
                self.initialize_order(order_number)

            # Store OCR data exactly as provided by form1ocr1
            success = self.update_section(order_number, "section_2_ocr", ocr_data, merge=False)

            if success:
                print(f"[OK] OCR data stored for order {order_number}")

            return success

        except Exception as e:
            print(f"[ERROR] Error storing OCR data: {str(e)}")
            return False

    def get_section_data(self, order_number: str, section: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve data from a specific section

        Args:
            order_number: The order number identifier
            section: Section name to retrieve

        Returns:
            Dict or None: The section data if found
        """
        try:
            file_path = self.json_output_path / f"{order_number}_out.json"

            if not file_path.exists():
                print(f"[WARNING] Order {order_number} not found")
                return None

            with open(file_path, 'r', encoding='utf-8') as f:
                order_data = json.load(f)

            return order_data.get(section, None)

        except Exception as e:
            print(f"[ERROR] Error retrieving section data: {str(e)}")
            return None

    def integrate_table_ocr_files(self, order_number: str) -> bool:
        """
        Integrate all table_ocr files for an order into Section 3 of the database
        This should be called after form1ocr1 creates all the OCR files

        Args:
            order_number: The order number identifier

        Returns:
            bool: Success status
        """
        try:
            print(f"[INFO] Starting table OCR integration for order {order_number}")

            # Initialize order if it doesn't exist
            self.initialize_order(order_number)

            # Path to table_ocr files
            table_ocr_path = self.base_output_path / "table_detection" / "Table_ocr"

            # Find all table_ocr files for this order
            import glob
            pattern = str(table_ocr_path / f"{order_number}_table_ocr_page*.json")
            ocr_files = glob.glob(pattern)

            if not ocr_files:
                print(f"[WARNING] No table OCR files found for order {order_number}")
                return False

            print(f"[INFO] Found {len(ocr_files)} table OCR files")

            # Initialize Section 3 structure
            section3_data = {}

            # Process each OCR file
            for ocr_file in sorted(ocr_files):
                try:
                    # Extract page number from filename
                    filename = os.path.basename(ocr_file)
                    page_num = filename.split('_page')[1].split('.json')[0]

                    print(f"[INFO] Processing page {page_num}")

                    # Load OCR data
                    with open(ocr_file, 'r', encoding='utf-8') as f:
                        ocr_data = json.load(f)

                    # Check if this file has table data
                    if 'table_data' not in ocr_data or 'rows' not in ocr_data['table_data']:
                        print(f"[WARNING] No table data found in {filename}")
                        continue

                    rows = ocr_data['table_data']['rows']
                    if not rows:
                        print(f"[WARNING] No rows found in {filename}")
                        continue

                    # Create page structure
                    page_key = f"page_{page_num}"
                    section3_data[page_key] = {
                        "page_number": int(page_num),
                        "number_of_order_lines": len(rows),
                        "order_lines": {}
                    }

                    # Process each row
                    for row_index, row_data in enumerate(rows):
                        line_number = row_index + 1
                        line_key = f"line_{line_number}"

                        # Extract data according to database structure
                        section3_data[page_key]["order_lines"][line_key] = {
                            "line_number": line_number,
                            "order_line_no": row_data.get('מס', ''),
                            "shape_number": row_data.get('shape', ''),
                            "number_of_ribs": 0,  # Default, will be updated when shape analysis is available
                            "diameter": row_data.get('קוטר', ''),
                            "number_of_units": self._safe_int_convert(row_data.get('סהכ יחידות', '')),
                            "length": row_data.get('אורך', ''),  # Length field from table_ocr
                            "weight": row_data.get('משקל', ''),  # Weight field from table_ocr
                            "notes": row_data.get('הערות', ''),  # Notes field from table_ocr
                            "checked": False,  # User verification status - default false
                            "ribs": {}  # Will be populated when shape analysis is available
                        }

                        try:
                            # Use safe printing to avoid encoding issues
                            order_no = row_data.get('מס', '')
                            shape = row_data.get('shape', '')
                            print(f"[INFO] Integrated line {line_number}: Order {order_no}")
                        except UnicodeEncodeError:
                            print(f"[INFO] Integrated line {line_number}")

                except Exception as e:
                    print(f"[ERROR] Error processing {ocr_file}: {str(e)}")
                    continue

            # Save the integrated data to Section 3
            if section3_data:
                success = self.update_section(order_number, "section_3_shape_analysis", section3_data, merge=False)

                if success:
                    print(f"[OK] Successfully integrated {len(section3_data)} pages into database")
                    print(f"[OK] Total order lines integrated: {sum(page['number_of_order_lines'] for page in section3_data.values())}")
                    return True
                else:
                    print(f"[ERROR] Failed to save integrated data to database")
                    return False
            else:
                print(f"[WARNING] No data to integrate")
                return False

        except Exception as e:
            print(f"[ERROR] Error in table OCR integration: {str(e)}")
            return False

    def _safe_int_convert(self, value: str) -> int:
        """
        Safely convert string to integer

        Args:
            value: String value to convert

        Returns:
            int: Converted value or 0 if conversion fails
        """
        try:
            if isinstance(value, str) and value.isdigit():
                return int(value)
            elif isinstance(value, int):
                return value
            else:
                return 0
        except:
            return 0

    def update_line_checked_status(self, order_number: str, page_number: int, line_number: int, checked: bool) -> bool:
        """
        Update the checked status for a specific line

        Args:
            order_number: The order number identifier
            page_number: Page number (1-based)
            line_number: Line number within the page (1-based)
            checked: True if checked, False if unchecked

        Returns:
            bool: Success status
        """
        try:
            file_path = self.json_output_path / f"{order_number}_out.json"

            if not file_path.exists():
                print(f"[ERROR] Order {order_number} not found")
                return False

            # Load current data
            with open(file_path, 'r', encoding='utf-8') as f:
                order_data = json.load(f)

            # Navigate to the specific line
            page_key = f"page_{page_number}"
            line_key = f"line_{line_number}"

            if "section_3_shape_analysis" not in order_data:
                print(f"[ERROR] Section 3 not found in order {order_number}")
                return False

            if page_key not in order_data["section_3_shape_analysis"]:
                print(f"[ERROR] Page {page_number} not found in order {order_number}")
                return False

            if line_key not in order_data["section_3_shape_analysis"][page_key]["order_lines"]:
                print(f"[ERROR] Line {line_number} not found in page {page_number} of order {order_number}")
                return False

            # Update the checked status
            order_data["section_3_shape_analysis"][page_key]["order_lines"][line_key]["checked"] = checked

            # Update metadata
            order_data["section_1_general"]["date_modified"] = datetime.now().isoformat()

            # Save updated data
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(order_data, f, indent=2, ensure_ascii=False)

            # Update cache
            self.data_cache[f"{order_number}_main"] = order_data

            status_text = "checked" if checked else "unchecked"
            print(f"[OK] Line {line_number} on page {page_number} marked as {status_text}")
            return True

        except Exception as e:
            print(f"[ERROR] Error updating checked status: {str(e)}")
            return False
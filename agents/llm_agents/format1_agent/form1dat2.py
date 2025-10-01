"""
Form1Dat2 Agent - Shape Catalog Integration Agent

This agent is responsible for updating order line data when shape_catalog_number changes.
It fetches shape data from the catalog and embeds it into the central output file.
"""

import json
import os
from pathlib import Path
from typing import Dict, Any, Optional, List
from datetime import datetime


class Form1Dat2Agent:
    """
    Agent responsible for integrating shape catalog data into order lines
    when shape_catalog_number is changed or updated.
    """

    def __init__(self):
        """Initialize the Form1Dat2 agent with necessary paths and data."""
        # Base paths
        self.base_dir = Path(os.getcwd())
        self.catalog_path = self.base_dir / "io" / "catalog" / "catalog_format.json"
        self.json_output_path = self.base_dir / "io" / "fullorder_output" / "json_output"

        # Load catalog data on initialization
        self.catalog_data = self._load_catalog_data()

        print("[FORM1DAT2] Agent initialized successfully")

    def _load_catalog_data(self) -> Dict[str, Any]:
        """
        Load the catalog format data from file.

        Returns:
            Dict containing the catalog shape data
        """
        try:
            if not self.catalog_path.exists():
                print(f"[WARNING] Catalog file not found at {self.catalog_path}")
                return {}

            with open(self.catalog_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                print(f"[INFO] Loaded catalog with {len(data.get('shapes', {}))} shapes")
                return data
        except Exception as e:
            print(f"[ERROR] Failed to load catalog data: {str(e)}")
            return {}

    def update_shape_in_order(self, order_number: str, page_number: int, line_number: int,
                              new_shape_number: str) -> Dict[str, Any]:
        """
        Update a specific order line with new shape catalog data.

        Args:
            order_number: The order identifier
            page_number: The page number (1-based)
            line_number: The line number within the page (1-based)
            new_shape_number: The new shape catalog number to apply

        Returns:
            Dict with status and details of the update
        """
        try:
            # Construct file path
            output_file = self.json_output_path / f"{order_number}_out.json"

            if not output_file.exists():
                return {
                    "status": "error",
                    "error": f"Order file not found: {output_file}"
                }

            # Load order data
            with open(output_file, 'r', encoding='utf-8') as f:
                order_data = json.load(f)

            # Get shape data from catalog
            shape_data = self._get_shape_from_catalog(new_shape_number)
            if not shape_data:
                return {
                    "status": "error",
                    "error": f"Shape {new_shape_number} not found in catalog"
                }

            # Update the specific order line
            page_key = f"page_{page_number}"
            line_key = f"line_{line_number}"

            if 'section_3_shape_analysis' not in order_data:
                return {
                    "status": "error",
                    "error": "No shape analysis section found in order"
                }

            if page_key not in order_data['section_3_shape_analysis']:
                return {
                    "status": "error",
                    "error": f"Page {page_number} not found in order"
                }

            page_data = order_data['section_3_shape_analysis'][page_key]

            if 'order_lines' not in page_data or line_key not in page_data['order_lines']:
                return {
                    "status": "error",
                    "error": f"Line {line_number} not found on page {page_number}"
                }

            # Update the order line with catalog data
            line_data = page_data['order_lines'][line_key]
            updated_fields = self._embed_catalog_data(line_data, shape_data, new_shape_number)

            # Update metadata
            order_data['section_1_general']['date_modified'] = datetime.now().isoformat()

            # Save updated data
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(order_data, f, indent=2, ensure_ascii=False)

            print(f"[OK] Updated order {order_number}, page {page_number}, line {line_number} with shape {new_shape_number}")

            return {
                "status": "success",
                "message": f"Successfully updated with shape {new_shape_number}",
                "updated_fields": updated_fields,
                "page": page_number,
                "line": line_number
            }

        except Exception as e:
            error_msg = f"Failed to update shape: {str(e)}"
            print(f"[ERROR] {error_msg}")
            return {
                "status": "error",
                "error": error_msg
            }

    def _get_shape_from_catalog(self, shape_number: str) -> Optional[Dict[str, Any]]:
        """
        Get shape data from the catalog.

        Args:
            shape_number: The shape catalog number

        Returns:
            Shape data dictionary or None if not found
        """
        if not self.catalog_data or 'shapes' not in self.catalog_data:
            return None

        return self.catalog_data['shapes'].get(shape_number)

    def _embed_catalog_data(self, line_data: Dict[str, Any], shape_data: Dict[str, Any],
                            shape_number: str) -> List[str]:
        """
        Embed catalog data into the order line.

        Args:
            line_data: The current order line data
            shape_data: The shape data from catalog
            shape_number: The shape catalog number

        Returns:
            List of field names that were updated
        """
        updated_fields = []

        # Create a new ordered dictionary with existing fields in the correct order
        ordered_data = {}

        # Preserve initial fields in order
        if 'line_number' in line_data:
            ordered_data['line_number'] = line_data['line_number']
        if 'order_line_no' in line_data:
            ordered_data['order_line_no'] = line_data['order_line_no']

        # 1. Update shape_catalog_number
        ordered_data['shape_catalog_number'] = shape_number
        updated_fields.append('shape_catalog_number')

        # 2. Add shape_label right after shape_catalog_number
        if 'shape_label' in shape_data:
            ordered_data['shape_label'] = shape_data['shape_label']
            updated_fields.append('shape_label')

        # 3. Update shape_description from catalog
        if 'shape_description' in shape_data:
            ordered_data['shape_description'] = shape_data['shape_description']
            updated_fields.append('shape_description')

        # 4. Update number_of_ribs
        if 'number_of_ribs' in shape_data:
            ordered_data['number_of_ribs'] = shape_data['number_of_ribs']
            updated_fields.append('number_of_ribs')

        # Preserve existing fields (diameter, units, length, weight, notes)
        for field in ['diameter', 'number_of_units', 'length', 'weight', 'notes']:
            if field in line_data:
                ordered_data[field] = line_data[field]

        # 5. Preserve checked field
        if 'checked' in line_data:
            ordered_data['checked'] = line_data['checked']

        # 6. Add clock_direction right after checked
        if 'clock_direction' in shape_data:
            ordered_data['clock_direction'] = shape_data['clock_direction']
            updated_fields.append('clock_direction')

        # 7. Update ribs data
        if 'ribs' in shape_data:
            # Clear existing ribs and add catalog ribs
            ordered_data['ribs'] = {}

            for i, rib in enumerate(shape_data['ribs'], 1):
                rib_key = f"rib_{i}"

                # Create rib entry with all available data
                rib_entry = {}

                # Copy all rib attributes
                for key, value in rib.items():
                    rib_entry[key] = value

                # Add a default value field for user input
                if 'rib_number' in rib:
                    # Regular ribs start empty - user will fill later
                    rib_entry['value'] = ""
                elif 'angle_letter' in rib:
                    # Angles get default values based on type
                    angle_type = rib.get('angle_type', '') or rib.get('angle type', '')
                    if angle_type == "90":
                        rib_entry['value'] = "90"  # 90-degree angles get value 90
                    else:
                        rib_entry['value'] = ""    # Other angles start empty

                ordered_data['ribs'][rib_key] = rib_entry

            updated_fields.append('ribs')
        elif 'ribs' in line_data:
            # Preserve existing ribs if no new ribs data
            ordered_data['ribs'] = line_data['ribs']

        # Clear the original line_data and update with ordered data
        line_data.clear()
        line_data.update(ordered_data)

        return updated_fields

    def batch_update_shapes(self, order_number: str, updates: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Batch update multiple shapes in an order.

        Args:
            order_number: The order identifier
            updates: List of update dictionaries containing:
                     - page_number: int
                     - line_number: int
                     - shape_catalog_number: str

        Returns:
            Dict with overall status and individual results
        """
        results = {
            "status": "success",
            "total_updates": len(updates),
            "successful": 0,
            "failed": 0,
            "details": []
        }

        for update in updates:
            result = self.update_shape_in_order(
                order_number=order_number,
                page_number=update.get('page_number'),
                line_number=update.get('line_number'),
                new_shape_number=update.get('shape_catalog_number')
            )

            if result['status'] == 'success':
                results['successful'] += 1
            else:
                results['failed'] += 1
                results['status'] = 'partial' if results['successful'] > 0 else 'error'

            results['details'].append({
                "page": update.get('page_number'),
                "line": update.get('line_number'),
                "shape": update.get('shape_catalog_number'),
                "result": result
            })

        print(f"[FORM1DAT2] Batch update completed: {results['successful']} successful, {results['failed']} failed")

        return results

    def get_available_shapes(self) -> List[str]:
        """
        Get list of available shape numbers from the catalog.

        Returns:
            List of shape catalog numbers
        """
        if self.catalog_data and 'shapes' in self.catalog_data:
            return list(self.catalog_data['shapes'].keys())
        return []

    def get_shape_info(self, shape_number: str) -> Optional[Dict[str, Any]]:
        """
        Get detailed information about a specific shape.

        Args:
            shape_number: The shape catalog number

        Returns:
            Shape information or None if not found
        """
        shape_data = self._get_shape_from_catalog(shape_number)
        if shape_data:
            # Create a summary of the shape
            return {
                "shape_number": shape_number,
                "shape_label": shape_data.get('shape_label', 'NA'),
                "shape_description": shape_data.get('shape_description', 'NA'),
                "number_of_ribs": shape_data.get('number_of_ribs', 0),
                "clock_direction": shape_data.get('clock_direction', 'NA'),
                "rib_count": len(shape_data.get('ribs', []))
            }
        return None


# Example usage
if __name__ == "__main__":
    # Initialize agent
    agent = Form1Dat2Agent()

    # Example: Update a single shape
    result = agent.update_shape_in_order(
        order_number="CO25S006375",
        page_number=1,
        line_number=1,
        new_shape_number="107"
    )

    print(f"\nUpdate result: {result}")

    # Example: Get available shapes
    shapes = agent.get_available_shapes()
    print(f"\nAvailable shapes: {shapes}")

    # Example: Get shape info
    info = agent.get_shape_info("107")
    if info:
        print(f"\nShape 107 info:")
        for key, value in info.items():
            print(f"  {key}: {value}")
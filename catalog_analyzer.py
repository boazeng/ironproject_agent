#!/usr/bin/env python3
"""
Catalog Analyzer Agent (catdet)

This agent analyzes catalog shape images and collects user input to build
a comprehensive catalog database for bent iron shapes.
"""

import os
import json
import logging
from datetime import datetime
from pathlib import Path
import cv2
import numpy as np
from PIL import Image
import matplotlib.pyplot as plt

logger = logging.getLogger(__name__)

class CatalogAnalyzerAgent:
    """
    Catalog Analyzer Agent (catdet) - Catalog Shape Database Builder

    Responsibilities:
    1. Read catalog shape image files
    2. Ask user for shape data:
       - Shape name
       - Number of ribs
       - Clock direction (clockwise/counterclockwise)
       - For each rib: letter and angle to next rib
    3. Output all data to catalog_format JSON file
    """

    def __init__(self):
        self.name = "catalog_analyzer"
        self.short_name = "CATDET"
        self.output_dir = "io/catalog"
        self.catalog_output_file = "catalog_format.json"

        # Create output directory
        os.makedirs(self.output_dir, exist_ok=True)

        logger.info(f"[{self.short_name}] Agent initialized - Catalog Shape Database Builder")

        # Initialize catalog data structure
        self.catalog_data = {
            "catalog_info": {
                "created_by": "catalog_analyzer_agent",
                "version": "1.0",
                "created_date": datetime.now().isoformat(),
                "last_updated": datetime.now().isoformat(),
                "description": "Bent iron shape catalog database"
            },
            "shapes": {}
        }

        # Load existing catalog if it exists
        self.load_existing_catalog()

    def load_existing_catalog(self):
        """Load existing catalog data if available"""
        try:
            catalog_path = os.path.join(self.output_dir, self.catalog_output_file)
            if os.path.exists(catalog_path):
                with open(catalog_path, 'r', encoding='utf-8') as f:
                    existing_data = json.load(f)

                # Update with existing shapes
                if 'shapes' in existing_data:
                    self.catalog_data['shapes'].update(existing_data['shapes'])

                logger.info(f"[{self.short_name}] Loaded existing catalog with {len(self.catalog_data['shapes'])} shapes")
            else:
                logger.info(f"[{self.short_name}] No existing catalog found, starting fresh")

        except Exception as e:
            logger.warning(f"[{self.short_name}] Could not load existing catalog: {str(e)}")

    def display_shape_image(self, image_path):
        """
        Display the shape image for user analysis

        Args:
            image_path (str): Path to the shape image file
        """
        try:
            print(f"\n{'='*60}")
            print(f"ANALYZING SHAPE IMAGE: {os.path.basename(image_path)}")
            print(f"{'='*60}")

            # Load and display image info
            image = cv2.imread(image_path)
            if image is None:
                print(f"ERROR: Could not load image: {image_path}")
                return False

            height, width = image.shape[:2]
            print(f"Image dimensions: {width} x {height} pixels")
            print(f"Image path: {image_path}")

            # Try to display using matplotlib if available
            try:
                # Convert BGR to RGB for matplotlib
                image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)

                plt.figure(figsize=(10, 6))
                plt.imshow(image_rgb)
                plt.title(f"Catalog Shape: {os.path.basename(image_path)}")
                plt.axis('off')
                plt.show(block=False)
                plt.pause(0.1)

                print("Shape image displayed in popup window.")

            except Exception as e:
                print(f"Could not display image graphically: {str(e)}")
                print("Please view the image manually at the path shown above.")

            return True

        except Exception as e:
            logger.error(f"[{self.short_name}] Error displaying image: {str(e)}")
            return False

    def collect_user_input(self, image_path):
        """
        Collect shape data from user input

        Args:
            image_path (str): Path to the shape image

        Returns:
            dict: Collected shape data or None if cancelled
        """
        try:
            filename = os.path.basename(image_path)
            print(f"\nCollecting data for shape: {filename}")
            print("-" * 50)

            # 1. Shape name (shape number)
            shape_name = input("1. Enter shape number: ").strip()
            if not shape_name:
                print("Shape number is required. Cancelling...")
                return None

            # 2. Shape label
            shape_label = input("2. Enter shape label: ").strip()
            if not shape_label:
                print("Shape label is required. Cancelling...")
                return None

            # 3. Shape description
            shape_description = input("3. Enter shape description: ").strip()
            if not shape_description:
                print("Shape description is required. Cancelling...")
                return None

            # 4. Number of ribs
            while True:
                try:
                    num_ribs = int(input("4. Enter number of ribs: ").strip())
                    if num_ribs <= 0:
                        print("Number of ribs must be positive. Please try again.")
                        continue
                    break
                except ValueError:
                    print("Please enter a valid number. Try again.")

            # 5. Clock direction
            while True:
                direction = input("5. Enter clock direction (clockwise/counterclockwise): ").strip().lower()
                if direction in ['clockwise', 'counterclockwise', 'cw', 'ccw']:
                    # Normalize the input
                    if direction in ['clockwise', 'cw']:
                        direction = 'clockwise'
                    else:
                        direction = 'counterclockwise'
                    break
                else:
                    print("Please enter 'clockwise' or 'counterclockwise' (or 'cw'/'ccw')")

            # 6. For each rib: number, type, letter, and angle to next rib
            ribs_data = []
            print(f"\n6. Enter data for each of the {num_ribs} ribs:")

            for i in range(num_ribs):
                print(f"\n   Rib {i+1} of {num_ribs}:")

                # Rib number (auto-assigned)
                rib_number = i + 1

                # Rib type
                while True:
                    rib_type = input(f"      Enter rib type: ").strip()
                    if rib_type:
                        break
                    else:
                        print("      Please enter a rib type")

                # Rib letter
                while True:
                    rib_letter = input(f"      Enter rib letter: ").strip().upper()
                    if rib_letter and len(rib_letter) <= 3:  # Allow short identifiers
                        break
                    else:
                        print("      Please enter a valid rib letter/identifier")

                # Angle to next rib (skip for last rib)
                angle_to_next = None
                if i < num_ribs - 1:  # Not the last rib
                    while True:
                        try:
                            angle_input = input(f"      Enter angle to next rib (degrees): ").strip()
                            if angle_input:
                                angle_to_next = float(angle_input)
                                break
                            else:
                                print("      Please enter an angle value")
                        except ValueError:
                            print("      Please enter a valid number for the angle")
                else:
                    print("      (Last rib - no angle to next rib)")

                rib_data = {
                    "rib_number": rib_number,
                    "rib_type": rib_type,
                    "rib_letter": rib_letter,
                    "angle_to_next": angle_to_next
                }
                ribs_data.append(rib_data)

            # Compile shape data
            shape_data = {
                "shape_name": shape_name,
                "shape_label": shape_label,
                "shape_description": shape_description,
                "number_of_ribs": num_ribs,
                "clock_direction": direction,
                "ribs": ribs_data,
                "created_date": datetime.now().isoformat(),
                "status": "analyzed"
            }

            # Show summary for confirmation
            self.show_data_summary(shape_data)

            # Confirm with user
            while True:
                confirm = input("\nIs this data correct? (y/n): ").strip().lower()
                if confirm in ['y', 'yes']:
                    return shape_data
                elif confirm in ['n', 'no']:
                    print("Data entry cancelled.")
                    return None
                else:
                    print("Please enter 'y' or 'n'")

        except KeyboardInterrupt:
            print("\n\nData entry cancelled by user.")
            return None
        except Exception as e:
            logger.error(f"[{self.short_name}] Error collecting user input: {str(e)}")
            return None

    def show_data_summary(self, shape_data):
        """
        Display a summary of the collected shape data

        Args:
            shape_data (dict): The collected shape data
        """
        print(f"\n{'='*50}")
        print(f"SHAPE DATA SUMMARY")
        print(f"{'='*50}")
        print(f"Shape Number: {shape_data['shape_name']}")
        print(f"Shape Label: {shape_data['shape_label']}")
        print(f"Shape Description: {shape_data['shape_description']}")
        print(f"Number of Ribs: {shape_data['number_of_ribs']}")
        print(f"Clock Direction: {shape_data['clock_direction']}")
        print(f"\nRibs Details:")

        for rib in shape_data['ribs']:
            if rib['angle_to_next'] is not None:
                print(f"  Rib {rib['rib_number']}: Type={rib['rib_type']}, Letter={rib['rib_letter']}, Angle={rib['angle_to_next']}°")
            else:
                print(f"  Rib {rib['rib_number']}: Type={rib['rib_type']}, Letter={rib['rib_letter']} (last rib)")

    def analyze_catalog_shape(self, image_path):
        """
        Analyze a catalog shape image with user input

        Args:
            image_path (str): Path to the catalog shape image

        Returns:
            dict: Analysis results
        """
        try:
            filename = os.path.basename(image_path)
            logger.info(f"[{self.short_name}] Starting catalog analysis for: {filename}")

            # Check if file exists
            if not os.path.exists(image_path):
                error_msg = f"Image file not found: {image_path}"
                logger.error(f"[{self.short_name}] {error_msg}")
                return {"status": "error", "message": error_msg}

            # Display shape image
            if not self.display_shape_image(image_path):
                return {"status": "error", "message": "Could not display image"}

            # Collect user input
            shape_data = self.collect_user_input(image_path)

            if not shape_data:
                return {"status": "cancelled", "message": "User cancelled data entry"}

            # Add to catalog
            shape_id = shape_data['shape_name'].upper().replace(' ', '_')
            self.catalog_data['shapes'][shape_id] = shape_data
            self.catalog_data['catalog_info']['last_updated'] = datetime.now().isoformat()

            # Save catalog
            self.save_catalog()

            # Return success
            result = {
                "status": "completed",
                "shape_id": shape_id,
                "shape_data": shape_data,
                "message": f"Shape '{shape_data['shape_name']}' added to catalog"
            }

            logger.info(f"[{self.short_name}] Catalog analysis completed for: {filename}")
            return result

        except Exception as e:
            error_msg = f"Error analyzing catalog shape {image_path}: {str(e)}"
            logger.error(f"[{self.short_name}] {error_msg}")
            return {"status": "error", "message": error_msg}

    def save_catalog(self):
        """Save the catalog data to JSON file"""
        try:
            catalog_path = os.path.join(self.output_dir, self.catalog_output_file)

            with open(catalog_path, 'w', encoding='utf-8') as f:
                json.dump(self.catalog_data, f, indent=2, ensure_ascii=False)

            logger.info(f"[{self.short_name}] Catalog saved to: {catalog_path}")
            print(f"\nCatalog saved to: {catalog_path}")
            print(f"Total shapes in catalog: {len(self.catalog_data['shapes'])}")

        except Exception as e:
            logger.error(f"[{self.short_name}] Error saving catalog: {str(e)}")

    def list_catalog_shapes(self):
        """List all shapes currently in the catalog"""
        if not self.catalog_data['shapes']:
            print("No shapes in catalog yet.")
            return

        print(f"\nCATALOG SHAPES ({len(self.catalog_data['shapes'])} total):")
        print("-" * 60)

        for shape_id, shape_data in self.catalog_data['shapes'].items():
            print(f"ID: {shape_id}")
            print(f"  Name: {shape_data['shape_name']}")
            print(f"  Ribs: {shape_data['number_of_ribs']}")
            print(f"  Direction: {shape_data['clock_direction']}")
            print(f"  Created: {shape_data.get('created_date', 'unknown')}")
            print()

    def process_catalog_image(self, image_path):
        """
        Main method to process a catalog image

        Args:
            image_path (str): Path to the catalog image

        Returns:
            dict: Processing results
        """
        print(f"\n[{self.short_name}] Processing catalog image: {os.path.basename(image_path)}")

        result = self.analyze_catalog_shape(image_path)

        if result['status'] == 'completed':
            print(f"\n✓ SUCCESS: {result['message']}")
        elif result['status'] == 'cancelled':
            print(f"\n- CANCELLED: {result['message']}")
        else:
            print(f"\n✗ ERROR: {result['message']}")

        return result


def main():
    """Test the catalog analyzer agent"""
    print("CATALOG ANALYZER AGENT (CATDET) - Interactive Mode")
    print("="*60)

    agent = CatalogAnalyzerAgent()

    # Show existing catalog
    agent.list_catalog_shapes()

    # Example usage
    print("\nTo analyze a catalog shape image:")
    print("agent.process_catalog_image('path/to/catalog/shape.png')")
    print("\nEntering interactive mode...")

    while True:
        try:
            image_path = input("\nEnter path to catalog image (or 'quit' to exit): ").strip()

            if image_path.lower() in ['quit', 'exit', 'q']:
                break

            if image_path and os.path.exists(image_path):
                agent.process_catalog_image(image_path)
            elif image_path:
                print(f"File not found: {image_path}")

        except KeyboardInterrupt:
            print("\n\nExiting...")
            break

    print("Catalog Analyzer session ended.")


if __name__ == "__main__":
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(message)s'
    )

    main()
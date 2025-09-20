#!/usr/bin/env python3
"""
Form1S5 Agent - Order Title Detection
Extracts the order title/header area above the table from ordertable_gridlines.png

Input: ordertable_gridlines.png (output from Form1S3)
Output: Order title image saved to order_header folder
"""

import os
import cv2
import numpy as np
import logging
from datetime import datetime
from pathlib import Path
import json

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class Form1S5Agent:
    """Agent for extracting order title/header from table images"""

    def __init__(self):
        self.name = "form1s5"
        self.short_name = "Form1S5 Order Title Detector"
        self.margin = 3  # Small margin to avoid cutting off text

    def detect_red_bounding_box(self, image):
        """
        Detect the red bounding box in the image to locate table boundaries.

        Args:
            image: Input image (BGR format)

        Returns:
            dict: Bounding box coordinates or None if not found
        """
        try:
            # Convert to HSV for better color detection
            hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)

            # Define range for red color
            lower_red1 = np.array([0, 50, 50])
            upper_red1 = np.array([10, 255, 255])
            lower_red2 = np.array([170, 50, 50])
            upper_red2 = np.array([180, 255, 255])

            # Create masks for red color
            mask1 = cv2.inRange(hsv, lower_red1, upper_red1)
            mask2 = cv2.inRange(hsv, lower_red2, upper_red2)
            mask = mask1 + mask2

            # Find contours
            contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

            if not contours:
                logger.warning(f"[{self.name.upper()}] No red bounding box found")
                return None

            # Find the largest rectangular contour
            largest_contour = max(contours, key=cv2.contourArea)
            x, y, w, h = cv2.boundingRect(largest_contour)

            logger.info(f"[{self.name.upper()}] Detected red bounding box: x={x}, y={y}, w={w}, h={h}")

            return {
                "x": x,
                "y": y,
                "width": w,
                "height": h
            }

        except Exception as e:
            logger.error(f"[{self.name.upper()}] Error detecting red bounding box: {str(e)}")
            return None

    def extract_order_title(self, image, red_box):
        """
        Extract the order title area above the red bounding box.

        Args:
            image: Input image (BGR format)
            red_box: Red bounding box coordinates dict

        Returns:
            numpy.ndarray: Extracted title image
        """
        try:
            # Extract area above the table (from top of image to top of red box)
            title_left = max(0, red_box["x"] - self.margin)
            title_right = min(image.shape[1], red_box["x"] + red_box["width"] + self.margin)
            title_top = 0  # Start from top of image
            title_bottom = max(0, red_box["y"] - self.margin)  # Stop at table top

            # Ensure we have valid dimensions
            if title_bottom <= title_top or title_right <= title_left:
                logger.warning(f"[{self.name.upper()}] Invalid title area dimensions")
                return None

            # Extract the title area
            title_image = image[title_top:title_bottom, title_left:title_right]

            title_height = title_bottom - title_top
            title_width = title_right - title_left

            logger.info(f"[{self.name.upper()}] Extracted title area: {title_width}x{title_height} px")
            logger.info(f"[{self.name.upper()}] Title coordinates: left={title_left}, right={title_right}, top={title_top}, bottom={title_bottom}")

            return title_image

        except Exception as e:
            logger.error(f"[{self.name.upper()}] Error extracting order title: {str(e)}")
            return None

    def save_title_image(self, title_image, order_name, output_dir):
        """
        Save the extracted title image to the order_header folder.

        Args:
            title_image: Extracted title image
            order_name: Name of the order (for filename)
            output_dir: Base output directory

        Returns:
            str: Path to saved file or None if failed
        """
        try:
            # Create order_header directory under table_detection
            header_dir = os.path.join(output_dir, "table_detection", "order_header")
            os.makedirs(header_dir, exist_ok=True)

            # Generate filename
            filename = f"{order_name}_order_header.png"
            filepath = os.path.join(header_dir, filename)

            # Save the image
            success = cv2.imwrite(filepath, title_image)

            if success:
                logger.info(f"[{self.name.upper()}] Saved order title: {filepath}")
                return filepath
            else:
                logger.error(f"[{self.name.upper()}] Failed to save title image to {filepath}")
                return None

        except Exception as e:
            logger.error(f"[{self.name.upper()}] Error saving title image: {str(e)}")
            return None

    def process_image(self, input_path, output_dir=None):
        """
        Main processing method to extract order title from ordertable_gridlines.png

        Args:
            input_path: Path to ordertable_gridlines.png
            output_dir: Output directory (defaults to io/fullorder_output)

        Returns:
            dict: Processing results
        """
        try:
            logger.info(f"[{self.name.upper()}] Starting order title extraction process")
            logger.info(f"[{self.name.upper()}] Input file: {input_path}")

            # Set default output directory
            if output_dir is None:
                output_dir = "io/fullorder_output"

            # Check if input file exists
            if not os.path.exists(input_path):
                error_msg = f"Input file not found: {input_path}"
                logger.error(f"[{self.name.upper()}] {error_msg}")
                return {
                    "status": "error",
                    "error": error_msg
                }

            # Load the image
            print(f"[DEBUG] Loading image: {input_path}")
            image = cv2.imread(input_path)

            if image is None:
                error_msg = f"Failed to load image: {input_path}"
                logger.error(f"[{self.name.upper()}] {error_msg}")
                return {
                    "status": "error",
                    "error": error_msg
                }

            print(f"[DEBUG] Image loaded successfully: {image.shape}")
            logger.info(f"[{self.name.upper()}] Loaded image: {image.shape}")

            # Detect red bounding box to locate table
            red_box = self.detect_red_bounding_box(image)

            if red_box is None:
                error_msg = "Could not detect red bounding box in image"
                logger.error(f"[{self.name.upper()}] {error_msg}")
                return {
                    "status": "error",
                    "error": error_msg
                }

            # Extract order title area above the table
            title_image = self.extract_order_title(image, red_box)

            if title_image is None:
                error_msg = "Failed to extract order title area"
                logger.error(f"[{self.name.upper()}] {error_msg}")
                return {
                    "status": "error",
                    "error": error_msg
                }

            # Determine order name from input filename with page number
            input_filename = os.path.basename(input_path)
            if "_page1_gridlines.png" in input_filename:
                # Extract order name from gridlines filename (e.g., CO25S006375_ordertable_page1_gridlines.png -> CO25S006375_order_title_page1)
                base_name = input_filename.replace("_ordertable_page1_gridlines.png", "")
                order_name = f"{base_name}_order_title_page1"
            elif "ordertable_gridlines" in input_filename:
                # Fallback for old naming convention
                order_name = "order_title_order_header"
            else:
                # Extract from filename
                order_name = os.path.splitext(input_filename)[0]

            # Save the title image
            saved_path = self.save_title_image(title_image, order_name, output_dir)

            if saved_path is None:
                error_msg = "Failed to save order title image"
                logger.error(f"[{self.name.upper()}] {error_msg}")
                return {
                    "status": "error",
                    "error": error_msg
                }

            # Prepare result
            result = {
                "status": "success",
                "input_file": input_path,
                "red_bounding_box": red_box,
                "title_extraction": {
                    "title_dimensions": {
                        "width": title_image.shape[1],
                        "height": title_image.shape[0]
                    },
                    "saved_file": saved_path,
                    "output_directory": os.path.dirname(saved_path)
                },
                "method": "opencv_red_box_title_extraction"
            }

            logger.info(f"[{self.name.upper()}] Order title extraction completed successfully")
            return result

        except Exception as e:
            error_msg = f"Unexpected error during title extraction: {str(e)}"
            logger.error(f"[{self.name.upper()}] {error_msg}")
            return {
                "status": "error",
                "error": error_msg
            }

def main():
    """Test the Form1S5 agent"""
    agent = Form1S5Agent()

    # Test with the expected input file
    input_file = "io/fullorder_output/table_detection/grid/CO25S006375_ordertable_page1_gridlines.png"

    if os.path.exists(input_file):
        print(f"Testing {agent.short_name} with: {input_file}")
        result = agent.process_image(input_file)

        print(f"\n=== {agent.name.upper()} RESULTS ===")
        print(json.dumps(result, indent=2))

        if result["status"] == "success":
            title_info = result["title_extraction"]
            print(f"\nOrder title extraction successful!")
            print(f"Title dimensions: {title_info['title_dimensions']['width']}x{title_info['title_dimensions']['height']} px")
            print(f"Saved to: {title_info['saved_file']}")
        else:
            print(f"\nError: {result.get('error', 'Unknown error')}")
    else:
        print(f"Input file not found: {input_file}")
        print("Please run the main table detection pipeline first to generate the input file.")

if __name__ == "__main__":
    main()
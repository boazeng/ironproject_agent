import os
import logging
import cv2
import numpy as np
from PIL import Image
import json
from pathlib import Path

logger = logging.getLogger(__name__)

class Form1S4_1Agent:
    """
    Form1S4_1 Agent - Full Drawing Column Extraction
    Extracts the complete drawing column (6th column between 6th and 7th vertical lines)
    Input: Output from form1s3 agent (green grid lines image)
    Output: Full drawing column image saved to shape_column folder
    """

    def __init__(self):
        self.name = "form1s4_1"
        self.short_name = "form1s4_1"
        self.output_dir = "io/fullorder_output"
        self.shape_column_dir = "io/fullorder_output/table_detection/shape_column"
        logger.info(f"[{self.short_name.upper()}] Agent initialized - Full Drawing Column Extractor")

        # Create output directories if they don't exist
        os.makedirs(self.output_dir, exist_ok=True)
        os.makedirs(self.shape_column_dir, exist_ok=True)

    def process_order(self, file_path=None, order_name=None):
        """
        Process an order to extract full drawing column

        Args:
            file_path (str): Path to the input file (form1s3 output) or None to auto-detect
            order_name (str): Name of the order or None to extract from file_path

        Returns:
            dict: Processing results including output file path
        """
        try:
            # If no file path provided, try to find the most recent form1s3 output
            if file_path is None:
                logger.info(f"[{self.short_name.upper()}] Auto-detecting form1s3 output files...")

                # Look for files matching pattern *_gridlines.png in the grid directory
                pattern = os.path.join(self.output_dir, "table_detection", "grid", "*_gridlines.png")
                import glob
                files = glob.glob(pattern)

                if not files:
                    logger.error(f"[{self.short_name.upper()}] No form1s3 output files found")
                    return {
                        "status": "error",
                        "error": "No form1s3 output files found",
                        "agent": self.name
                    }

                # Use the most recent file
                file_path = max(files, key=os.path.getctime)
                logger.info(f"[{self.short_name.upper()}] Using file: {file_path}")

            # Extract order name from file path if not provided
            if order_name is None:
                base_name = os.path.basename(file_path)
                # Extract order name from patterns like CO25S006375_ordertable_page1_gridlines.png
                if "_ordertable_" in base_name:
                    order_name = base_name.split("_ordertable_")[0]
                elif "_gridlines" in base_name:
                    order_name = base_name.split("_")[0]
                elif "_page" in base_name:
                    order_name = base_name.split("_page")[0]
                else:
                    order_name = os.path.splitext(base_name)[0]

            logger.info(f"[{self.short_name.upper()}] Processing order: {order_name}")

            result = {
                "status": "processing",
                "input_file": file_path,
                "order_name": order_name,
                "agent": self.name,
                "short_name": self.short_name
            }

            # Check if input file exists
            if not os.path.exists(file_path):
                logger.error(f"[{self.short_name.upper()}] File not found: {file_path}")
                result["status"] = "error"
                result["error"] = f"File not found: {file_path}"
                return result

            # Load the image
            img = cv2.imread(file_path)
            if img is None:
                logger.error(f"[{self.short_name.upper()}] Failed to load image: {file_path}")
                result["status"] = "error"
                result["error"] = f"Failed to load image: {file_path}"
                return result

            height, width = img.shape[:2]
            logger.info(f"[{self.short_name.upper()}] Image dimensions: {width}x{height}")

            # Extract the full drawing column
            column_img = self.extract_drawing_column(img, order_name)

            if column_img is not None:
                # Determine page number from filename
                page_num = "1"
                if "_page" in os.path.basename(file_path):
                    try:
                        page_part = os.path.basename(file_path).split("_page")[1]
                        page_num = page_part.split(".")[0].split("_")[0]
                    except:
                        page_num = "1"

                # Save the column image
                output_filename = f"{order_name}_shape_column_page{page_num}.png"
                output_path = os.path.join(self.shape_column_dir, output_filename)

                cv2.imwrite(output_path, column_img)
                logger.info(f"[{self.short_name.upper()}] Shape column saved to: {output_path}")

                column_height, column_width = column_img.shape[:2]

                result["status"] = "success"
                result["output_file"] = output_path
                result["output_filename"] = output_filename
                result["column_width"] = column_width
                result["column_height"] = column_height
                result["page_number"] = page_num
                result["message"] = f"Successfully extracted full drawing column for page {page_num}"
            else:
                result["status"] = "error"
                result["error"] = "Failed to extract drawing column"

        except Exception as e:
            logger.error(f"[{self.short_name.upper()}] Unexpected error: {str(e)}")
            result = {
                "status": "error",
                "error": f"Unexpected error: {str(e)}",
                "agent": self.name
            }

        return result

    def extract_drawing_column(self, img, order_name):
        """
        Extract the full drawing column (6th column between 6th and 7th vertical lines)

        Args:
            img: Input image with green grid lines
            order_name: Name of the order for logging

        Returns:
            numpy array: Cropped column image or None if extraction failed
        """
        try:
            # Convert to HSV for better green detection
            hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)

            # Define range for green color (more specific for bright green)
            lower_green = np.array([35, 50, 50])
            upper_green = np.array([85, 255, 255])

            # Create mask for green pixels
            green_mask = cv2.inRange(hsv, lower_green, upper_green)

            # Find all vertical green lines
            vertical_lines = []

            # Scan each column to find green vertical lines
            for x in range(img.shape[1]):
                green_pixel_count = np.sum(green_mask[:, x] > 0)
                # If more than 40% of the column is green, it's likely a vertical line
                if green_pixel_count > img.shape[0] * 0.4:
                    vertical_lines.append(x)

            logger.info(f"[{self.short_name.upper()}] Found {len(vertical_lines)} potential vertical lines")

            # Find all horizontal green lines to determine table boundaries
            horizontal_lines = []

            # Scan each row to find green horizontal lines
            for y in range(img.shape[0]):
                green_pixel_count = np.sum(green_mask[y, :] > 0)
                # If more than 40% of the row is green, it's likely a horizontal line
                if green_pixel_count > img.shape[1] * 0.4:
                    horizontal_lines.append(y)

            logger.info(f"[{self.short_name.upper()}] Found {len(horizontal_lines)} potential horizontal lines")

            if len(vertical_lines) >= 7 and len(horizontal_lines) >= 2:
                # Group consecutive vertical lines (lines within 10 pixels of each other)
                vertical_line_groups = []
                current_group = [vertical_lines[0]]

                for i in range(1, len(vertical_lines)):
                    if vertical_lines[i] - vertical_lines[i-1] <= 10:
                        current_group.append(vertical_lines[i])
                    else:
                        if len(current_group) > 0:
                            vertical_line_groups.append(current_group)
                        current_group = [vertical_lines[i]]

                # Add the last group
                if len(current_group) > 0:
                    vertical_line_groups.append(current_group)

                logger.info(f"[{self.short_name.upper()}] Identified {len(vertical_line_groups)} distinct vertical line groups")

                # Group consecutive horizontal lines (lines within 10 pixels of each other)
                horizontal_line_groups = []
                if horizontal_lines:
                    current_group = [horizontal_lines[0]]

                    for i in range(1, len(horizontal_lines)):
                        if horizontal_lines[i] - horizontal_lines[i-1] <= 10:
                            current_group.append(horizontal_lines[i])
                        else:
                            if len(current_group) > 0:
                                horizontal_line_groups.append(current_group)
                            current_group = [horizontal_lines[i]]

                    # Add the last group
                    if len(current_group) > 0:
                        horizontal_line_groups.append(current_group)

                logger.info(f"[{self.short_name.upper()}] Identified {len(horizontal_line_groups)} distinct horizontal line groups")

                # We need at least 7 vertical line groups and at least 2 horizontal line groups
                if len(vertical_line_groups) >= 7 and len(horizontal_line_groups) >= 2:
                    # Get the average X position for the 6th and 7th vertical line groups
                    sixth_line_x = int(np.mean(vertical_line_groups[5]))  # 6th line (0-indexed)
                    seventh_line_x = int(np.mean(vertical_line_groups[6]))  # 7th line (0-indexed)

                    # Get the first and last horizontal line groups for table boundaries
                    first_horizontal_y = int(np.mean(horizontal_line_groups[0]))  # Top boundary
                    last_horizontal_y = int(np.mean(horizontal_line_groups[-1]))  # Bottom boundary

                    logger.info(f"[{self.short_name.upper()}] 6th vertical line at X={sixth_line_x}, 7th at X={seventh_line_x}")
                    logger.info(f"[{self.short_name.upper()}] Top horizontal line at Y={first_horizontal_y}, Bottom at Y={last_horizontal_y}")

                    # The drawing column is between these boundaries
                    left_x = sixth_line_x + len(vertical_line_groups[5])  # Start after the 6th green line
                    right_x = seventh_line_x  # End at the 7th green line
                    top_y = first_horizontal_y + len(horizontal_line_groups[0])  # Start after the top green line
                    bottom_y = last_horizontal_y  # End at the bottom green line

                    # Ensure valid boundaries
                    left_x = max(0, left_x)
                    right_x = min(img.shape[1], right_x)
                    top_y = max(0, top_y)
                    bottom_y = min(img.shape[0], bottom_y)

                    # Extract the column within table boundaries
                    column_img = img[top_y:bottom_y, left_x:right_x]

                    logger.info(f"[{self.short_name.upper()}] Extracted column: {column_img.shape[1]}x{column_img.shape[0]} pixels")
                    logger.info(f"[{self.short_name.upper()}] Column extracted from X={left_x} to X={right_x}, Y={top_y} to Y={bottom_y}")

                    return column_img
                else:
                    logger.warning(f"[{self.short_name.upper()}] Not enough line groups found (need >=7 vertical, >=2 horizontal, found {len(vertical_line_groups)} vertical, {len(horizontal_line_groups)} horizontal)")
            else:
                logger.warning(f"[{self.short_name.upper()}] Not enough lines detected (need >=7 vertical, >=2 horizontal, found {len(vertical_lines)} vertical, {len(horizontal_lines)} horizontal)")

            # If we couldn't detect lines properly, return None
            logger.error(f"[{self.short_name.upper()}] Failed to detect drawing column properly")
            return None

        except Exception as e:
            logger.error(f"[{self.short_name.upper()}] Error extracting column: {str(e)}")
            return None

    def process_batch(self, input_dir=None):
        """
        Process all form1s3 output files

        Args:
            input_dir (str): Directory containing input files (defaults to output_dir/table_detection/grid)

        Returns:
            list: Results for all processed files
        """
        if input_dir is None:
            input_dir = os.path.join(self.output_dir, "table_detection", "grid")

        logger.info(f"[{self.short_name.upper()}] Starting batch processing from: {input_dir}")

        results = []

        # Find all form1s3 output files
        import glob
        pattern = os.path.join(input_dir, "*_gridlines.png")
        files = glob.glob(pattern)

        if not files:
            logger.warning(f"[{self.short_name.upper()}] No form1s3 output files found in {input_dir}")
            return results

        logger.info(f"[{self.short_name.upper()}] Found {len(files)} file(s) to process")

        for file_path in files:
            logger.info(f"[{self.short_name.upper()}] Processing: {file_path}")
            result = self.process_order(file_path)
            results.append(result)

            if result["status"] == "success":
                logger.info(f"[{self.short_name.upper()}] Successfully processed: {os.path.basename(file_path)}")
            else:
                logger.error(f"[{self.short_name.upper()}] Failed to process: {os.path.basename(file_path)}")

        logger.info(f"[{self.short_name.upper()}] Batch processing complete. Processed {len(results)} file(s)")
        return results
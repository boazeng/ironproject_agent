import os
import logging
import cv2
import numpy as np
from PIL import Image
import json
from pathlib import Path

logger = logging.getLogger(__name__)

class Form1S3_3Agent:
    """
    Form1S3_3 Agent - Table Header Extraction
    Extracts the header row of the table (upper row of green grid lines)
    Input: Output from form1s3 agent (green grid lines image)
    Output: Table header image saved to table_header folder
    """

    def __init__(self):
        self.name = "form1s3_3"
        self.short_name = "form1s3_3"
        self.output_dir = "io/fullorder_output"
        self.table_header_dir = "io/fullorder_output/table_detection/table_header"
        logger.info(f"[{self.short_name.upper()}] Agent initialized - Table Header Extractor")

        # Create output directories if they don't exist
        os.makedirs(self.output_dir, exist_ok=True)
        os.makedirs(self.table_header_dir, exist_ok=True)

    def process_order(self, file_path=None, order_name=None):
        """
        Process an order to extract table header

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

            # Extract header based on green grid lines
            header_img = self.extract_header_from_grid(img, order_name)

            if header_img is not None:
                # Determine page number from filename
                page_num = "1"
                if "_page" in os.path.basename(file_path):
                    try:
                        page_part = os.path.basename(file_path).split("_page")[1]
                        page_num = page_part.split(".")[0].split("_")[0]
                    except:
                        page_num = "1"

                # Save the header image
                output_filename = f"{order_name}_table_header_page{page_num}.png"
                output_path = os.path.join(self.table_header_dir, output_filename)

                cv2.imwrite(output_path, header_img)
                logger.info(f"[{self.short_name.upper()}] Table header saved to: {output_path}")

                header_height, header_width = header_img.shape[:2]

                result["status"] = "success"
                result["output_file"] = output_path
                result["output_filename"] = output_filename
                result["header_width"] = header_width
                result["header_height"] = header_height
                result["page_number"] = page_num
                result["message"] = f"Successfully extracted table header for page {page_num}"
            else:
                result["status"] = "error"
                result["error"] = "Failed to extract table header"

        except Exception as e:
            logger.error(f"[{self.short_name.upper()}] Unexpected error: {str(e)}")
            result = {
                "status": "error",
                "error": f"Unexpected error: {str(e)}",
                "agent": self.name
            }

        return result

    def extract_header_from_grid(self, img, order_name):
        """
        Extract the header row from the image based on green grid lines

        Args:
            img: Input image with green grid lines
            order_name: Name of the order for logging

        Returns:
            numpy array: Cropped header image or None if extraction failed
        """
        try:
            # Convert to HSV for better green detection
            hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)

            # Define range for green color (more specific for bright green)
            lower_green = np.array([35, 50, 50])
            upper_green = np.array([85, 255, 255])

            # Create mask for green pixels
            green_mask = cv2.inRange(hsv, lower_green, upper_green)

            # Find all horizontal green lines
            horizontal_lines = []

            # Scan each row to find green horizontal lines
            for y in range(img.shape[0]):
                green_pixel_count = np.sum(green_mask[y, :] > 0)
                # If more than 40% of the row is green, it's likely a horizontal line
                if green_pixel_count > img.shape[1] * 0.4:
                    horizontal_lines.append(y)

            logger.info(f"[{self.short_name.upper()}] Found {len(horizontal_lines)} potential horizontal lines")

            if len(horizontal_lines) >= 2:
                # Group consecutive lines (lines within 10 pixels of each other)
                line_groups = []
                current_group = [horizontal_lines[0]]

                for i in range(1, len(horizontal_lines)):
                    if horizontal_lines[i] - horizontal_lines[i-1] <= 10:
                        current_group.append(horizontal_lines[i])
                    else:
                        if len(current_group) > 0:
                            line_groups.append(current_group)
                        current_group = [horizontal_lines[i]]

                # Add the last group
                if len(current_group) > 0:
                    line_groups.append(current_group)

                logger.info(f"[{self.short_name.upper()}] Identified {len(line_groups)} distinct line groups")

                # We need at least 2 line groups for header extraction
                if len(line_groups) >= 2:
                    # Get the average Y position for each line group
                    first_line_y = int(np.mean(line_groups[0]))
                    second_line_y = int(np.mean(line_groups[1]))

                    logger.info(f"[{self.short_name.upper()}] First green line at Y={first_line_y}, Second at Y={second_line_y}")

                    # The header is between these two lines
                    # Add the line thickness to properly include content
                    top_y = first_line_y + len(line_groups[0])  # Start after the first green line
                    bottom_y = second_line_y  # End at the second green line

                    # Ensure valid boundaries
                    top_y = max(0, top_y)
                    bottom_y = min(img.shape[0], bottom_y)

                    # Extract the header region
                    header_img = img[top_y:bottom_y, :]

                    logger.info(f"[{self.short_name.upper()}] Extracted header: {header_img.shape[1]}x{header_img.shape[0]} pixels")
                    logger.info(f"[{self.short_name.upper()}] Header extracted from Y={top_y} to Y={bottom_y}")

                    return header_img
                else:
                    logger.warning(f"[{self.short_name.upper()}] Not enough distinct line groups found")
            else:
                logger.warning(f"[{self.short_name.upper()}] Not enough horizontal lines detected")

            # If we couldn't detect lines properly, return None instead of a fallback
            logger.error(f"[{self.short_name.upper()}] Failed to detect table header properly")
            return None

        except Exception as e:
            logger.error(f"[{self.short_name.upper()}] Error extracting header: {str(e)}")
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
"""
Form1S3.1 Agent - Table Body Extraction
Extracts the table body content inside the green grid lines from form1s3 output.
Creates two files:
1. {order}_table_body_page{num}.png - Full table body including header
2. {order}_table_bodyonly_page{num}.png - Table body without header (excludes top 15%)
"""

import cv2
import numpy as np
import os
import logging
from typing import Optional, Tuple, Dict, Any

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class Form1S31Agent:
    """Agent for extracting table body content inside green grid lines."""

    def __init__(self, name: str = "form1s3_1"):
        """
        Initialize the Form1S3.1 agent.

        Args:
            name: Agent name for logging
        """
        self.name = name
        self.margin = 3  # Margin to avoid grid lines

    def extract_table_body(self, input_file: str, output_dir: str) -> Dict[str, Any]:
        """
        Extract table body content inside the outermost green grid lines.

        Args:
            input_file: Path to form1s3 output file (ordertable_gridlines.png)
            output_dir: Directory to save the extracted table body

        Returns:
            Dictionary with extraction results
        """
        try:
            logger.info(f"[{self.name.upper()}] Starting table body extraction process")
            logger.info(f"[{self.name.upper()}] Input file: {input_file}")

            # Load the image
            if not os.path.exists(input_file):
                raise FileNotFoundError(f"Input file not found: {input_file}")

            image = cv2.imread(input_file)
            if image is None:
                raise ValueError(f"Could not load image: {input_file}")

            height, width = image.shape[:2]
            logger.info(f"[{self.name.upper()}] Loaded image: ({height}, {width}, {image.shape[2]})")
            print(f"[DEBUG] Loading image: {input_file}")
            print(f"[DEBUG] Image loaded successfully: {image.shape}")

            # Detect green grid lines to find table boundaries
            green_boundaries = self.detect_table_boundaries(image)
            if not green_boundaries:
                raise ValueError("Could not detect green grid boundaries")

            # Extract table body content
            table_body = self.extract_table_content(image, green_boundaries)

            # Extract table body content without header
            table_body_only = self.extract_table_content_without_header(image, green_boundaries)

            # Save the extracted files
            os.makedirs(output_dir, exist_ok=True)

            # Extract page number from input filename (e.g., CO25S006375_ordertable_page2_gridlines.png -> CO25S006375_table_body_page2.png)
            input_filename = os.path.basename(input_file)
            import re
            page_match = re.search(r'_page(\d+)_gridlines\.png$', input_filename)
            if page_match:
                page_num = page_match.group(1)
                base_name = input_filename.replace(f"_ordertable_page{page_num}_gridlines.png", "")
                output_filename = f"{base_name}_table_body_page{page_num}.png"
                output_filename_bodyonly = f"{base_name}_table_bodyonly_page{page_num}.png"
            else:
                output_filename = "table_body.png"
                output_filename_bodyonly = "table_bodyonly.png"

            # Save both files
            output_file = os.path.join(output_dir, output_filename)
            output_file_bodyonly = os.path.join(output_dir, output_filename_bodyonly)
            cv2.imwrite(output_file, table_body)
            cv2.imwrite(output_file_bodyonly, table_body_only)

            result = {
                "status": "success",
                "input_file": input_file,
                "output_file": output_file,
                "output_file_bodyonly": output_file_bodyonly,
                "table_dimensions": {
                    "width": table_body.shape[1],
                    "height": table_body.shape[0]
                },
                "table_bodyonly_dimensions": {
                    "width": table_body_only.shape[1],
                    "height": table_body_only.shape[0]
                },
                "boundaries": green_boundaries
            }

            logger.info(f"[{self.name.upper()}] Table body extraction completed")
            logger.info(f"[{self.name.upper()}] Table dimensions: {table_body.shape[1]}x{table_body.shape[0]} px")
            logger.info(f"[{self.name.upper()}] Table body-only dimensions: {table_body_only.shape[1]}x{table_body_only.shape[0]} px")
            logger.info(f"[{self.name.upper()}] Saved table_body to: {output_file}")
            logger.info(f"[{self.name.upper()}] Saved table_bodyonly to: {output_file_bodyonly}")

            return result

        except Exception as e:
            logger.error(f"[{self.name.upper()}] Error extracting table body: {str(e)}")
            return {
                "status": "error",
                "error": str(e),
                "input_file": input_file
            }

    def detect_table_boundaries(self, image: np.ndarray) -> Optional[Dict[str, int]]:
        """
        Detect the outermost green grid lines to determine table boundaries.

        Args:
            image: Input image with green grid lines

        Returns:
            Dictionary with boundary coordinates or None if not found
        """
        try:
            print(f"[DEBUG] Detecting green grid lines for table boundaries...")

            # Convert to HSV for better green detection
            hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)

            # Define green color range (more inclusive range)
            lower_green = np.array([35, 40, 40])
            upper_green = np.array([85, 255, 255])

            # Create mask for green colors
            green_mask = cv2.inRange(hsv, lower_green, upper_green)

            # Apply morphological operations to clean up the mask
            kernel = np.ones((3, 3), np.uint8)
            green_mask = cv2.morphologyEx(green_mask, cv2.MORPH_CLOSE, kernel)
            green_mask = cv2.morphologyEx(green_mask, cv2.MORPH_OPEN, kernel)

            # Find contours to detect green line regions
            contours, _ = cv2.findContours(green_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

            if not contours:
                logger.warning(f"[{self.name.upper()}] No green contours found")
                return None

            # Find the bounding box that encompasses all green lines
            all_points = []
            for contour in contours:
                for point in contour:
                    all_points.append(point[0])

            if not all_points:
                return None

            all_points = np.array(all_points)

            # Get the extreme coordinates
            left = int(np.min(all_points[:, 0]))
            right = int(np.max(all_points[:, 0]))
            top = int(np.min(all_points[:, 1]))
            bottom = int(np.max(all_points[:, 1]))

            boundaries = {
                "left": left,
                "right": right,
                "top": top,
                "bottom": bottom,
                "width": right - left,
                "height": bottom - top
            }

            print(f"[DEBUG] Table boundaries detected: left={left}, right={right}, top={top}, bottom={bottom}")
            print(f"[DEBUG] Table size: {boundaries['width']}x{boundaries['height']} px")

            logger.info(f"[{self.name.upper()}] Detected table boundaries: {boundaries['width']}x{boundaries['height']} px")

            return boundaries

        except Exception as e:
            logger.error(f"[{self.name.upper()}] Error detecting table boundaries: {str(e)}")
            return None

    def extract_table_content(self, image: np.ndarray, boundaries: Dict[str, int]) -> np.ndarray:
        """
        Extract the table content inside the green grid boundaries.

        Args:
            image: Input image
            boundaries: Dictionary with boundary coordinates

        Returns:
            Extracted table body image
        """
        try:
            # Add margin to include content inside grid lines but exclude the lines themselves
            content_left = boundaries["left"] + self.margin
            content_right = boundaries["right"] - self.margin
            content_top = boundaries["top"] + self.margin
            content_bottom = boundaries["bottom"] - self.margin

            # Ensure we don't go out of bounds
            content_left = max(0, content_left)
            content_right = min(image.shape[1], content_right)
            content_top = max(0, content_top)
            content_bottom = min(image.shape[0], content_bottom)

            # Extract the table content
            table_body = image[content_top:content_bottom, content_left:content_right]

            print(f"[DEBUG] Extracted table content: left={content_left}, right={content_right}, top={content_top}, bottom={content_bottom}")
            print(f"[DEBUG] Table body size: {table_body.shape[1]}x{table_body.shape[0]} px")

            logger.info(f"[{self.name.upper()}] Extracted table content: {table_body.shape[1]}x{table_body.shape[0]} px")
            logger.info(f"[{self.name.upper()}] Content coordinates: left={content_left}, right={content_right}, top={content_top}, bottom={content_bottom}")

            return table_body

        except Exception as e:
            logger.error(f"[{self.name.upper()}] Error extracting table content: {str(e)}")
            raise

    def extract_table_content_without_header(self, image: np.ndarray, boundaries: Dict[str, int]) -> np.ndarray:
        """
        Extract the table content inside the green grid boundaries, excluding the table header.
        Detects the exact green horizontal line that separates header from data rows.

        Args:
            image: Input image
            boundaries: Dictionary with boundary coordinates

        Returns:
            Extracted table body image without header
        """
        try:
            # Add margin to include content inside grid lines but exclude the lines themselves
            content_left = boundaries["left"] + self.margin
            content_right = boundaries["right"] - self.margin
            content_top = boundaries["top"] + self.margin
            content_bottom = boundaries["bottom"] - self.margin

            # Ensure we don't go out of bounds
            content_left = max(0, content_left)
            content_right = min(image.shape[1], content_right)
            content_top = max(0, content_top)
            content_bottom = min(image.shape[0], content_bottom)

            # Find the first horizontal green line after the header
            header_separator_y = self.find_header_separator_line(image, content_left, content_right, content_top, content_bottom)

            if header_separator_y is None:
                # Fallback to percentage method if line detection fails
                table_height = content_bottom - content_top
                header_height = int(table_height * 0.08)
                content_top_no_header = content_top + header_height
                print(f"[DEBUG] Fallback to percentage method, header height: {header_height} px")
            else:
                # Use the detected separator line position plus small margin
                content_top_no_header = header_separator_y + 3
                print(f"[DEBUG] Found header separator line at y={header_separator_y}")

            # Extract the table content without header
            table_body_only = image[content_top_no_header:content_bottom, content_left:content_right]

            print(f"[DEBUG] Extracted table content without header: left={content_left}, right={content_right}, top={content_top_no_header}, bottom={content_bottom}")
            print(f"[DEBUG] Table body-only size: {table_body_only.shape[1]}x{table_body_only.shape[0]} px")

            logger.info(f"[{self.name.upper()}] Extracted table content without header: {table_body_only.shape[1]}x{table_body_only.shape[0]} px")
            logger.info(f"[{self.name.upper()}] Header separator at y={header_separator_y if header_separator_y else 'not found'}")

            return table_body_only

        except Exception as e:
            logger.error(f"[{self.name.upper()}] Error extracting table content without header: {str(e)}")
            raise

    def find_header_separator_line(self, image: np.ndarray, left: int, right: int, top: int, bottom: int) -> Optional[int]:
        """
        Find the horizontal green line that separates the header from the first data row.

        Args:
            image: Input image
            left, right, top, bottom: Search boundaries

        Returns:
            Y-coordinate of the header separator line, or None if not found
        """
        try:
            print(f"[DEBUG] Searching for header separator line in region: left={left}, right={right}, top={top}, bottom={bottom}")

            # Convert to HSV for better green detection
            hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)

            # Define green color range
            lower_green = np.array([35, 40, 40])
            upper_green = np.array([85, 255, 255])

            # Create mask for green colors
            green_mask = cv2.inRange(hsv, lower_green, upper_green)

            # Search for horizontal lines in the top portion of the table (first 30%)
            search_height = int((bottom - top) * 0.30)
            search_bottom = min(top + search_height, bottom)

            # Look for horizontal green lines by scanning row by row
            min_line_length = int((right - left) * 0.7)  # Line should span at least 70% of table width

            # Skip the first few lines to avoid the top border, look for the SECOND horizontal line
            found_lines = []
            for y in range(top + 50, search_bottom):  # Start further down to skip top border and first line
                # Count green pixels in this horizontal line
                green_pixels_in_row = np.sum(green_mask[y, left:right])

                if green_pixels_in_row > min_line_length:
                    # Check if this is a continuous horizontal line
                    line_segments = []
                    current_segment_start = None

                    for x in range(left, right):
                        if green_mask[y, x] > 0:  # Green pixel found
                            if current_segment_start is None:
                                current_segment_start = x
                        else:  # Non-green pixel
                            if current_segment_start is not None:
                                line_segments.append(x - current_segment_start)
                                current_segment_start = None

                    # Close the last segment if it ends at the right edge
                    if current_segment_start is not None:
                        line_segments.append(right - current_segment_start)

                    # Check if we have a long enough continuous segment
                    if line_segments and max(line_segments) > min_line_length:
                        found_lines.append(y)
                        print(f"[DEBUG] Found horizontal line #{len(found_lines)} at y={y}, green pixels={green_pixels_in_row}, longest segment={max(line_segments)}")

                        # Return the second horizontal line found (first is top border, second should be header separator)
                        if len(found_lines) >= 2:
                            header_separator_y = found_lines[1]
                            print(f"[DEBUG] Using second horizontal line as header separator at y={header_separator_y}")
                            return header_separator_y

            # If we only found one line, it might be the header separator
            if len(found_lines) == 1:
                print(f"[DEBUG] Only found one line, using it as header separator at y={found_lines[0]}")
                return found_lines[0]

            print(f"[DEBUG] No header separator line found in search region")
            return None

        except Exception as e:
            logger.error(f"[{self.name.upper()}] Error finding header separator line: {str(e)}")
            return None

    def process_file(self, input_file: str, output_dir: str) -> Dict[str, Any]:
        """
        Process a single file for table body extraction.

        Args:
            input_file: Path to input image file
            output_dir: Directory to save extracted table body

        Returns:
            Processing result dictionary
        """
        return self.extract_table_body(input_file, output_dir)

    def process_all_pages(self, input_dir: str, output_dir: str, order_number: str = "CO25S006375") -> Dict[str, Any]:
        """
        Process all pages for table body extraction.

        Args:
            input_dir: Directory containing input gridlines files
            output_dir: Directory to save extracted table bodies
            order_number: Order number to process (default: CO25S006375)

        Returns:
            Dictionary with processing results for all pages
        """
        import glob
        import os

        try:
            logger.info(f"[{self.name.upper()}] Starting multi-page table body extraction for order {order_number}")

            # Find all gridlines files for this order
            pattern = os.path.join(input_dir, f"{order_number}_ordertable_page*_gridlines.png")
            input_files = glob.glob(pattern)
            input_files.sort()  # Ensure proper page order

            if not input_files:
                return {
                    "status": "error",
                    "error": f"No gridlines files found for order {order_number} in {input_dir}",
                    "pattern": pattern
                }

            results = {
                "status": "success",
                "order_number": order_number,
                "total_pages": len(input_files),
                "processed_pages": 0,
                "pages": {},
                "summary": []
            }

            # Process each page
            for input_file in input_files:
                try:
                    # Extract page number from filename
                    import re
                    page_match = re.search(r'_page(\d+)_gridlines\.png$', input_file)
                    if not page_match:
                        continue

                    page_num = page_match.group(1)
                    logger.info(f"[{self.name.upper()}] Processing page {page_num}...")

                    # Process the page
                    result = self.process_file(input_file, output_dir)

                    if result["status"] == "success":
                        results["pages"][f"page_{page_num}"] = {
                            "status": "success",
                            "input_file": input_file,
                            "output_file": result["output_file"],
                            "output_file_bodyonly": result["output_file_bodyonly"],
                            "table_dimensions": result["table_dimensions"],
                            "table_bodyonly_dimensions": result["table_bodyonly_dimensions"]
                        }
                        results["processed_pages"] += 1
                        results["summary"].append(f"✅ Page {page_num}: {result['table_bodyonly_dimensions']['width']}x{result['table_bodyonly_dimensions']['height']} px")
                        logger.info(f"[{self.name.upper()}] Page {page_num} completed successfully")
                    else:
                        results["pages"][f"page_{page_num}"] = {
                            "status": "error",
                            "error": result["error"],
                            "input_file": input_file
                        }
                        results["summary"].append(f"❌ Page {page_num}: {result['error']}")
                        logger.error(f"[{self.name.upper()}] Page {page_num} failed: {result['error']}")

                except Exception as e:
                    logger.error(f"[{self.name.upper()}] Error processing page {page_num}: {str(e)}")
                    results["summary"].append(f"❌ Page {page_num}: {str(e)}")

            # Final status
            if results["processed_pages"] == results["total_pages"]:
                logger.info(f"[{self.name.upper()}] All {results['total_pages']} pages processed successfully")
            else:
                results["status"] = "partial_success"
                logger.warning(f"[{self.name.upper()}] Only {results['processed_pages']}/{results['total_pages']} pages processed successfully")

            return results

        except Exception as e:
            logger.error(f"[{self.name.upper()}] Error in multi-page processing: {str(e)}")
            return {
                "status": "error",
                "error": str(e),
                "order_number": order_number
            }


def main():
    """Main function for testing the Form1S3.1 agent."""
    # Initialize agent
    agent = Form1S31Agent()

    # Process all pages
    input_dir = "io/fullorder_output/table_detection/grid"
    output_dir = "io/fullorder_output/table_detection/table"
    order_number = "CO25S006375"

    # Process all pages for the order
    results = agent.process_all_pages(input_dir, output_dir, order_number)

    # Print results
    if results["status"] == "success":
        print(f"✅ All pages processed successfully!")
        print(f"📊 Order: {results['order_number']}")
        print(f"📄 Total pages: {results['total_pages']}")
        print(f"📁 Output directory: {output_dir}")
        print("\n📋 Summary:")
        for summary in results["summary"]:
            print(f"   {summary}")
    elif results["status"] == "partial_success":
        print(f"⚠️ Partial success: {results['processed_pages']}/{results['total_pages']} pages processed")
        print(f"📊 Order: {results['order_number']}")
        print("\n📋 Summary:")
        for summary in results["summary"]:
            print(f"   {summary}")
    else:
        print(f"❌ Processing failed: {results['error']}")


if __name__ == "__main__":
    main()
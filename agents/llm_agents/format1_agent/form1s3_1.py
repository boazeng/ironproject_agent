"""
Form1S3.1 Agent - Table Body Extraction
Extracts the table body content inside the green grid lines from form1s3 output.
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

            # Save the extracted table body
            os.makedirs(output_dir, exist_ok=True)

            # Extract page number from input filename (e.g., CO25S006375_ordertable_page1_gridlines.png -> CO25S006375_table_body_page1.png)
            input_filename = os.path.basename(input_file)
            if "_page1_gridlines.png" in input_filename:
                base_name = input_filename.replace("_ordertable_page1_gridlines.png", "")
                output_filename = f"{base_name}_table_body_page1.png"
            else:
                output_filename = "table_body.png"

            output_file = os.path.join(output_dir, output_filename)
            cv2.imwrite(output_file, table_body)

            result = {
                "status": "success",
                "input_file": input_file,
                "output_file": output_file,
                "table_dimensions": {
                    "width": table_body.shape[1],
                    "height": table_body.shape[0]
                },
                "boundaries": green_boundaries
            }

            logger.info(f"[{self.name.upper()}] Table body extraction completed")
            logger.info(f"[{self.name.upper()}] Table dimensions: {table_body.shape[1]}x{table_body.shape[0]} px")
            logger.info(f"[{self.name.upper()}] Saved to: {output_file}")

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


def main():
    """Main function for testing the Form1S3.1 agent."""
    # Initialize agent
    agent = Form1S31Agent()

    # Test file paths
    input_file = "io/fullorder_output/table_detection/grid/CO25S006375_ordertable_page1_gridlines.png"
    output_dir = "io/fullorder_output/table_detection/table"

    # Process the file
    result = agent.process_file(input_file, output_dir)

    # Print results
    if result["status"] == "success":
        print(f"✅ Table body extraction successful!")
        print(f"📁 Output: {result['output_file']}")
        print(f"📏 Dimensions: {result['table_dimensions']['width']}x{result['table_dimensions']['height']} px")
    else:
        print(f"❌ Table body extraction failed: {result['error']}")


if __name__ == "__main__":
    main()
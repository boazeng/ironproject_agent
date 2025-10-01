"""
Use Area Table Agent - Processes user-saved table area images and adds green row lines
Author: Claude Code Assistant
Date: 2025-09-23
"""

import os
import cv2
import numpy as np
import logging
from typing import Optional, Tuple, List

class UseAreaTableAgent:
    """
    Agent that processes user-saved table area images from user_saved_area folder
    and creates modified versions with green lines for row detection
    """

    def __init__(self):
        self.name = "use_area_table"
        self.short_name = "areatable"
        self.logger = logging.getLogger(f"agents.llm_agents.format1_agent.{self.name}")
        self.logger.setLevel(logging.INFO)

        # Create handler if not exists
        if not self.logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(f'[{self.short_name.upper()}] %(message)s')
            handler.setFormatter(formatter)
            self.logger.addHandler(handler)

        self.logger.info(f"Agent initialized - {self.name}")

    def process_page(self, order_name: str, page_number: int, base_output_dir: str = "io/fullorder_output") -> dict:
        """
        Process a specific page's table area image if it exists in user_saved_area

        Args:
            order_name: Order name (e.g., "CO25S006375")
            page_number: Page number to process
            base_output_dir: Base output directory path

        Returns:
            dict: Processing result with status and file paths
        """
        try:
            self.logger.info(f"Processing table area for order {order_name}, page {page_number}")

            # Check if user-saved table area file exists
            user_saved_dir = os.path.join(base_output_dir, "user_saved_area")
            table_area_filename = f"{order_name}_table_area_page{page_number}.png"
            table_area_path = os.path.join(user_saved_dir, table_area_filename)

            if not os.path.exists(table_area_path):
                self.logger.info(f"No user-saved table area found for page {page_number}")
                return {
                    "status": "no_file",
                    "message": f"No table area file found for page {page_number}",
                    "input_file": None,
                    "output_file": None
                }

            self.logger.info(f"Found table area file: {table_area_path}")

            # Load the image
            image = cv2.imread(table_area_path)
            if image is None:
                self.logger.error(f"Failed to load image: {table_area_path}")
                return {
                    "status": "error",
                    "message": "Failed to load image file",
                    "input_file": table_area_path,
                    "output_file": None
                }

            # Process image to add green grid lines (rows and columns)
            processed_image = self._add_green_row_lines(image)

            # Create output directory for table detection
            table_detection_dir = os.path.join(base_output_dir, "table_detection", "table")
            os.makedirs(table_detection_dir, exist_ok=True)

            # Create output filename that will replace the original table_bodyonly file
            output_filename = f"{order_name}_table_bodyonly_page{page_number}.png"
            output_path = os.path.join(table_detection_dir, output_filename)

            # Save processed image
            success = cv2.imwrite(output_path, processed_image)
            if not success:
                self.logger.error(f"Failed to save processed image: {output_path}")
                return {
                    "status": "error",
                    "message": "Failed to save processed image",
                    "input_file": table_area_path,
                    "output_file": None
                }

            self.logger.info(f"Successfully created processed image: {output_path}")

            return {
                "status": "success",
                "message": f"Successfully processed table area for page {page_number}",
                "input_file": table_area_path,
                "output_file": output_path,
                "rows_detected": self._count_detected_rows(processed_image)
            }

        except Exception as e:
            self.logger.error(f"Error processing page {page_number}: {e}")
            return {
                "status": "error",
                "message": f"Processing error: {str(e)}",
                "input_file": table_area_path if 'table_area_path' in locals() else None,
                "output_file": None
            }

    def _add_green_row_lines(self, image: np.ndarray) -> np.ndarray:
        """
        Detect precise table grid lines and add green lines at exact positions for both rows and columns

        Args:
            image: Input image array

        Returns:
            np.ndarray: Image with green grid lines added at precise locations
        """
        # Create a copy of the image to modify
        result_image = image.copy()
        height, width = image.shape[:2]

        # Convert to grayscale for line detection
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

        # Use Hough Line Transform for precise line detection
        edges = cv2.Canny(gray, 50, 150, apertureSize=3)
        lines = cv2.HoughLinesP(edges, 1, np.pi/180, threshold=80, minLineLength=min(width*0.4, height*0.4), maxLineGap=10)

        horizontal_y_coords = []
        vertical_x_coords = []

        if lines is not None:
            for line in lines:
                x1, y1, x2, y2 = line[0]

                # Check if line is horizontal (small y difference)
                if abs(y2 - y1) <= 5:
                    line_length = abs(x2 - x1)
                    # Only consider lines that span at least 60% of width
                    if line_length > width * 0.6:
                        y_coord = (y1 + y2) // 2
                        horizontal_y_coords.append(y_coord)

                # Check if line is vertical (small x difference)
                elif abs(x2 - x1) <= 5:
                    line_length = abs(y2 - y1)
                    # Only consider lines that span at least 40% of height
                    if line_length > height * 0.4:
                        x_coord = (x1 + x2) // 2
                        vertical_x_coords.append(x_coord)

        # Fallback: Morphological approach if Hough doesn't find enough lines
        if len(horizontal_y_coords) < 3:
            _, binary = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)

            # Detect horizontal lines
            horizontal_kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (width // 3, 1))
            horizontal_lines = cv2.morphologyEx(binary, cv2.MORPH_OPEN, horizontal_kernel, iterations=1)
            contours, _ = cv2.findContours(horizontal_lines, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

            for contour in contours:
                x, y, w, h = cv2.boundingRect(contour)
                if w > width * 0.7:
                    horizontal_y_coords.append(y + h // 2)

        if len(vertical_x_coords) < 3:
            _, binary = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)

            # Detect vertical lines
            vertical_kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (1, height // 4))
            vertical_lines = cv2.morphologyEx(binary, cv2.MORPH_OPEN, vertical_kernel, iterations=1)
            contours, _ = cv2.findContours(vertical_lines, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

            for contour in contours:
                x, y, w, h = cv2.boundingRect(contour)
                if h > height * 0.5:
                    vertical_x_coords.append(x + w // 2)

        # Process horizontal lines (rows)
        horizontal_y_coords = self._process_line_coordinates(horizontal_y_coords, height, is_horizontal=True)

        # Process vertical lines (columns)
        vertical_x_coords = self._process_line_coordinates(vertical_x_coords, width, is_horizontal=False)

        # Draw green lines at precise detected positions
        green_color = (0, 255, 0)  # BGR format for green
        line_thickness = 2

        # Draw horizontal lines (row separators)
        for y_coord in horizontal_y_coords:
            cv2.line(result_image, (0, y_coord), (width, y_coord), green_color, line_thickness)

        # Draw vertical lines (column separators)
        for x_coord in vertical_x_coords:
            cv2.line(result_image, (x_coord, 0), (x_coord, height), green_color, line_thickness)

        self.logger.info(f"Added {len(horizontal_y_coords)} precise green row separator lines at positions: {horizontal_y_coords}")
        self.logger.info(f"Added {len(vertical_x_coords)} precise green column separator lines at positions: {vertical_x_coords}")

        return result_image

    def _process_line_coordinates(self, coords: List[int], max_dimension: int, is_horizontal: bool) -> List[int]:
        """
        Process and filter line coordinates for precision

        Args:
            coords: List of coordinates (x for vertical lines, y for horizontal lines)
            max_dimension: Maximum dimension (width for vertical, height for horizontal)
            is_horizontal: True for horizontal lines, False for vertical lines

        Returns:
            List[int]: Filtered and precise coordinates
        """
        if not coords:
            return []

        # Remove duplicates and sort
        coords = sorted(list(set(coords)))

        # Precision grouping: Group lines within 3 pixels
        precise_coords = []
        if coords:
            current_group = [coords[0]]

            for i in range(1, len(coords)):
                if coords[i] - coords[i-1] <= 3:
                    current_group.append(coords[i])
                else:
                    # Take median of the group for precision
                    precise_coords.append(int(np.median(current_group)))
                    current_group = [coords[i]]

            # Add the last group
            if current_group:
                precise_coords.append(int(np.median(current_group)))

            coords = precise_coords

        # Filter out lines too close to edges or other lines
        filtered_coords = []
        min_distance = 25 if is_horizontal else 30  # Slightly wider spacing for columns

        for coord in coords:
            # Skip if too close to edges
            if coord < 15 or coord > max_dimension - 15:
                continue

            # Skip if too close to already added lines
            too_close = False
            for existing_coord in filtered_coords:
                if abs(coord - existing_coord) < min_distance:
                    too_close = True
                    break

            if not too_close:
                filtered_coords.append(coord)

        return sorted(filtered_coords)

    def _count_detected_rows(self, image: np.ndarray) -> int:
        """
        Count the number of rows based on green lines in the processed image

        Args:
            image: Processed image with green lines

        Returns:
            int: Number of detected rows
        """
        # Convert to HSV to detect green lines
        hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)

        # Define range for green color
        lower_green = np.array([35, 50, 50])
        upper_green = np.array([85, 255, 255])

        # Create mask for green pixels
        green_mask = cv2.inRange(hsv, lower_green, upper_green)

        # Find horizontal lines in the mask
        height, width = green_mask.shape
        horizontal_lines = []

        for y in range(height):
            row = green_mask[y, :]
            if np.sum(row) > width * 0.5 * 255:  # If more than 50% of row is green
                horizontal_lines.append(y)

        # Group nearby lines together (within 5 pixels)
        if not horizontal_lines:
            return 1  # At least one row assumed

        grouped_lines = []
        current_group = [horizontal_lines[0]]

        for i in range(1, len(horizontal_lines)):
            if horizontal_lines[i] - horizontal_lines[i-1] <= 5:
                current_group.append(horizontal_lines[i])
            else:
                grouped_lines.append(current_group)
                current_group = [horizontal_lines[i]]

        if current_group:
            grouped_lines.append(current_group)

        # Number of rows = number of line groups + 1
        return len(grouped_lines) + 1

    def check_file_exists(self, order_name: str, page_number: int, base_output_dir: str = "io/fullorder_output") -> bool:
        """
        Check if a table area file exists for the given order and page

        Args:
            order_name: Order name (e.g., "CO25S006375")
            page_number: Page number to check
            base_output_dir: Base output directory path

        Returns:
            bool: True if file exists, False otherwise
        """
        user_saved_dir = os.path.join(base_output_dir, "user_saved_area")
        table_area_filename = f"{order_name}_table_area_page{page_number}.png"
        table_area_path = os.path.join(user_saved_dir, table_area_filename)

        return os.path.exists(table_area_path)


# Example usage and testing
if __name__ == "__main__":
    # Set up logging
    logging.basicConfig(level=logging.INFO, format='%(message)s')

    # Create agent instance
    agent = UseAreaTableAgent()

    # Test with example data
    order_name = "CO25S006375"
    page_number = 1

    print(f"Testing {agent.name} agent...")
    print(f"Checking if file exists for {order_name}, page {page_number}...")

    file_exists = agent.check_file_exists(order_name, page_number)
    print(f"File exists: {file_exists}")

    if file_exists:
        print("Processing table area...")
        result = agent.process_page(order_name, page_number)
        print(f"Result: {result}")
    else:
        print("No table area file found to process")
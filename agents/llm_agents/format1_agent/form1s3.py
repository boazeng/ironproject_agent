import cv2
import numpy as np
import os
import logging
import json

logger = logging.getLogger(__name__)

class Form1S3Agent:
    def __init__(self):
        self.name = "form1s3"
        logger.info(f"[{self.name.upper()}] Initialized Form1S3 Agent")

    def detect_red_bounding_box(self, image):
        """
        Detect the red bounding box in the image using HSV color space.
        Returns the bounding box coordinates (x, y, width, height).
        """
        try:
            # Convert BGR to HSV for better red color detection
            hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)

            # Define red color range in HSV
            # Red has two ranges in HSV: 0-10 and 170-180
            lower_red1 = np.array([0, 120, 70])
            upper_red1 = np.array([10, 255, 255])
            lower_red2 = np.array([170, 120, 70])
            upper_red2 = np.array([180, 255, 255])

            # Create masks for both red ranges
            mask1 = cv2.inRange(hsv, lower_red1, upper_red1)
            mask2 = cv2.inRange(hsv, lower_red2, upper_red2)

            # Combine masks
            red_mask = cv2.bitwise_or(mask1, mask2)

            # Apply morphological operations to clean up the mask
            kernel = np.ones((3, 3), np.uint8)
            red_mask = cv2.morphologyEx(red_mask, cv2.MORPH_CLOSE, kernel)
            red_mask = cv2.morphologyEx(red_mask, cv2.MORPH_OPEN, kernel)

            # Find contours
            contours, _ = cv2.findContours(red_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

            if not contours:
                logger.warning(f"[{self.name.upper()}] No red bounding box detected")
                return None

            # Find the largest rectangular contour (should be our red bounding box)
            best_rect = None
            max_area = 0

            for contour in contours:
                # Approximate the contour to a polygon
                epsilon = 0.02 * cv2.arcLength(contour, True)
                approx = cv2.approxPolyDP(contour, epsilon, True)

                # Check if it's roughly rectangular (4 corners)
                if len(approx) >= 4:
                    area = cv2.contourArea(contour)
                    if area > max_area:
                        max_area = area
                        best_rect = cv2.boundingRect(contour)

            if best_rect is None:
                logger.warning(f"[{self.name.upper()}] No rectangular red bounding box found")
                return None

            x, y, w, h = best_rect
            logger.info(f"[{self.name.upper()}] Detected red bounding box: x={x}, y={y}, w={w}, h={h}")
            return (x, y, w, h)

        except Exception as e:
            logger.error(f"[{self.name.upper()}] Error detecting red bounding box: {str(e)}")
            return None

    def detect_grid_lines(self, roi_image):
        """
        Detect horizontal and vertical grid lines in the ROI using Hough Line Transform.
        Returns lists of horizontal and vertical lines that span at least 95% of the table.
        """
        try:
            height, width = roi_image.shape[:2]

            # Convert to grayscale
            gray = cv2.cvtColor(roi_image, cv2.COLOR_BGR2GRAY)

            # Apply edge detection
            edges = cv2.Canny(gray, 50, 150, apertureSize=3)

            # Use Hough Line Transform to detect lines
            lines = cv2.HoughLinesP(
                edges,
                rho=1,
                theta=np.pi/180,
                threshold=50,
                minLineLength=30,
                maxLineGap=10
            )

            if lines is None:
                logger.warning(f"[{self.name.upper()}] No lines detected in ROI")
                return [], []

            horizontal_lines = []
            vertical_lines = []

            # Minimum span requirements (95% of table dimensions)
            min_horizontal_span = 0.95 * width
            min_vertical_span = 0.95 * height

            for line in lines:
                x1, y1, x2, y2 = line[0]

                # Calculate line length and angle
                length = np.sqrt((x2 - x1)**2 + (y2 - y1)**2)
                angle = np.abs(np.arctan2(y2 - y1, x2 - x1) * 180 / np.pi)

                # Check if line is horizontal (angle close to 0 or 180)
                if angle < 10 or angle > 170:
                    if length >= min_horizontal_span:
                        horizontal_lines.append((x1, y1, x2, y2))
                        logger.debug(f"[{self.name.upper()}] Accepted horizontal line: ({x1},{y1}) to ({x2},{y2}), length={length:.1f}")

                # Check if line is vertical (angle close to 90)
                elif 80 < angle < 100:
                    if length >= min_vertical_span:
                        vertical_lines.append((x1, y1, x2, y2))
                        logger.debug(f"[{self.name.upper()}] Accepted vertical line: ({x1},{y1}) to ({x2},{y2}), length={length:.1f}")

            logger.info(f"[{self.name.upper()}] Detected {len(horizontal_lines)} horizontal lines and {len(vertical_lines)} vertical lines")
            return horizontal_lines, vertical_lines

        except Exception as e:
            logger.error(f"[{self.name.upper()}] Error detecting grid lines: {str(e)}")
            return [], []

    def draw_grid_lines(self, image, bbox, horizontal_lines, vertical_lines):
        """
        Draw the detected grid lines in green on the original image.
        Lines are drawn relative to the bounding box position.
        """
        try:
            result_image = image.copy()
            x_offset, y_offset, _, _ = bbox

            # Draw horizontal lines in green
            for x1, y1, x2, y2 in horizontal_lines:
                # Adjust coordinates relative to original image
                start_point = (x1 + x_offset, y1 + y_offset)
                end_point = (x2 + x_offset, y2 + y_offset)
                cv2.line(result_image, start_point, end_point, (0, 255, 0), 2)

            # Draw vertical lines in green
            for x1, y1, x2, y2 in vertical_lines:
                # Adjust coordinates relative to original image
                start_point = (x1 + x_offset, y1 + y_offset)
                end_point = (x2 + x_offset, y2 + y_offset)
                cv2.line(result_image, start_point, end_point, (0, 255, 0), 2)

            logger.info(f"[{self.name.upper()}] Drew {len(horizontal_lines)} horizontal and {len(vertical_lines)} vertical grid lines")
            return result_image

        except Exception as e:
            logger.error(f"[{self.name.upper()}] Error drawing grid lines: {str(e)}")
            return image

    def process_image(self, input_image_path):
        """
        Main processing function that reads the image from form1s2 output,
        detects the red bounding box, finds grid lines, and outputs the result.
        """
        try:
            logger.info(f"[{self.name.upper()}] Starting grid line detection process")

            # Check if input image exists
            if not os.path.exists(input_image_path):
                error_msg = f"Input image not found: {input_image_path}"
                logger.error(f"[{self.name.upper()}] {error_msg}")
                return {"status": "error", "error": error_msg}

            # Load the image
            image = cv2.imread(input_image_path)
            if image is None:
                error_msg = f"Failed to load image: {input_image_path}"
                logger.error(f"[{self.name.upper()}] {error_msg}")
                return {"status": "error", "error": error_msg}

            logger.info(f"[{self.name.upper()}] Loaded image: {input_image_path}")

            # Step 1: Detect the red bounding box
            bbox = self.detect_red_bounding_box(image)
            if bbox is None:
                error_msg = "Failed to detect red bounding box"
                logger.error(f"[{self.name.upper()}] {error_msg}")
                return {"status": "error", "error": error_msg}

            x, y, w, h = bbox

            # Step 2: Extract the ROI (Region of Interest) inside the red box
            roi = image[y:y+h, x:x+w]
            logger.info(f"[{self.name.upper()}] Extracted ROI: {w}x{h} at ({x},{y})")

            # Step 3: Detect grid lines in the ROI
            horizontal_lines, vertical_lines = self.detect_grid_lines(roi)

            if not horizontal_lines and not vertical_lines:
                logger.warning(f"[{self.name.upper()}] No grid lines detected that meet the 95% span criteria")

            # Step 4: Draw the grid lines on the original image
            result_image = self.draw_grid_lines(image, bbox, horizontal_lines, vertical_lines)

            # Step 5: Save the result
            # Use absolute path relative to project root
            project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
            output_dir = os.path.join(project_root, "io", "fullorder_output", "table_detection", "grid")
            os.makedirs(output_dir, exist_ok=True)

            # Generate output filename based on input
            base_name = os.path.splitext(os.path.basename(input_image_path))[0]
            output_filename = f"{base_name}_gridlines.png"
            output_path = os.path.join(output_dir, output_filename)

            cv2.imwrite(output_path, result_image)
            logger.info(f"[{self.name.upper()}] Saved result image: {output_path}")

            # Convert numpy arrays to standard Python lists for JSON serialization
            horizontal_lines_json = [[int(x1), int(y1), int(x2), int(y2)] for x1, y1, x2, y2 in horizontal_lines]
            vertical_lines_json = [[int(x1), int(y1), int(x2), int(y2)] for x1, y1, x2, y2 in vertical_lines]

            # Prepare result
            result = {
                "status": "success",
                "input_file": input_image_path,
                "output_image_path": output_path,
                "red_bounding_box": {
                    "x": int(x),
                    "y": int(y),
                    "width": int(w),
                    "height": int(h)
                },
                "grid_lines": {
                    "horizontal_count": len(horizontal_lines),
                    "vertical_count": len(vertical_lines),
                    "horizontal_lines": horizontal_lines_json,
                    "vertical_lines": vertical_lines_json
                },
                "method": "opencv_hough_transform"
            }

            logger.info(f"[{self.name.upper()}] Grid line detection completed successfully")
            return result

        except Exception as e:
            error_msg = f"Error processing image: {str(e)}"
            logger.error(f"[{self.name.upper()}] {error_msg}")
            return {"status": "error", "error": error_msg}


def main():
    """
    Test function to run the form1s3 agent independently.
    """
    try:
        agent = Form1S3Agent()

        # Look for the output from form1s2 (ordertable.png) in grid folder with page number
        input_path = "../../../io/fullorder_output/table_detection/grid/CO25S006375_ordertable_page1.png"

        if not os.path.exists(input_path):
            print(f"Input file not found: {input_path}")
            print("Please run form1s2 first to generate the table detection image.")
            return

        # Process the image
        result = agent.process_image(input_path)

        print("=== FORM1S3 RESULTS ===")
        print(json.dumps(result, indent=2))

        if result["status"] == "success":
            print(f"Grid lines detected: {result['grid_lines']['horizontal_count']} horizontal, {result['grid_lines']['vertical_count']} vertical")
            print(f"Output image saved: {result['output_image_path']}")
        else:
            print(f"Error: {result.get('error', 'Unknown error')}")

    except Exception as e:
        print(f"Error in main: {e}")


if __name__ == "__main__":
    main()
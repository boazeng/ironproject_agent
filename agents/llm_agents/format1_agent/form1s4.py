import cv2
import numpy as np
import os
import logging
import json

logger = logging.getLogger(__name__)

class Form1S4Agent:
    def __init__(self):
        self.name = "form1s4"
        self.margin = 3  # Margin to avoid grid lines but preserve drawing content
        logger.info(f"[{self.name.upper()}] Initialized Form1S4 Agent")

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

    def detect_green_grid_lines(self, roi_image):
        """
        Detect green grid lines in the ROI using HSV masking and Hough Line Transform.
        Returns lists of horizontal and vertical line positions.
        """
        try:
            # Convert BGR to HSV for better green color detection
            hsv = cv2.cvtColor(roi_image, cv2.COLOR_BGR2HSV)

            # Define green color range in HSV - broader range for better detection
            # Green in HSV: Hue 35-85, Saturation 25+, Value 25+
            lower_green = np.array([35, 25, 25])
            upper_green = np.array([85, 255, 255])

            # Create green mask
            green_mask = cv2.inRange(hsv, lower_green, upper_green)

            # Apply morphological operations to clean up the mask
            kernel = np.ones((3, 3), np.uint8)
            green_mask = cv2.morphologyEx(green_mask, cv2.MORPH_CLOSE, kernel)

            # Debug: Check if we have any green pixels detected
            green_pixel_count = np.sum(green_mask > 0)
            logger.debug(f"[{self.name.upper()}] Green pixels detected: {green_pixel_count}")

            if green_pixel_count == 0:
                logger.warning(f"[{self.name.upper()}] No green pixels found in mask - trying alternative detection")

                # Debug: Save the ROI and HSV mask for inspection
                debug_dir = "../../../io/fullorder_output/table_detection/debug"
                os.makedirs(debug_dir, exist_ok=True)
                cv2.imwrite(os.path.join(debug_dir, "roi_image.png"), roi_image)
                cv2.imwrite(os.path.join(debug_dir, "hsv_green_mask.png"), green_mask)
                hsv_image = cv2.cvtColor(roi_image, cv2.COLOR_BGR2HSV)
                cv2.imwrite(os.path.join(debug_dir, "hsv_image.png"), hsv_image)
                logger.info(f"[{self.name.upper()}] Debug images saved to {debug_dir}")

                # Try direct BGR color detection as fallback
                return self._detect_green_lines_bgr_fallback(roi_image)

            # Apply Canny edge detection on the green mask
            edges = cv2.Canny(green_mask, 50, 150, apertureSize=3)

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
                logger.warning(f"[{self.name.upper()}] No green grid lines detected in ROI")
                return [], []

            horizontal_positions = []
            vertical_positions = []

            height, width = roi_image.shape[:2]

            for line in lines:
                x1, y1, x2, y2 = line[0]

                # Calculate line angle
                angle = np.abs(np.arctan2(y2 - y1, x2 - x1) * 180 / np.pi)

                # Check if line is horizontal (angle close to 0 or 180)
                if angle < 10 or angle > 170:
                    # Use average y position for horizontal lines
                    y_pos = int((y1 + y2) / 2)
                    horizontal_positions.append(y_pos)

                # Check if line is vertical (angle close to 90)
                elif 80 < angle < 100:
                    # Use average x position for vertical lines
                    x_pos = int((x1 + x2) / 2)
                    vertical_positions.append(x_pos)

            logger.info(f"[{self.name.upper()}] Detected {len(horizontal_positions)} horizontal and {len(vertical_positions)} vertical grid line positions")
            return horizontal_positions, vertical_positions

        except Exception as e:
            logger.error(f"[{self.name.upper()}] Error detecting green grid lines: {str(e)}")
            return [], []

    def _detect_green_lines_bgr_fallback(self, roi_image):
        """
        Fallback method to detect green lines using direct BGR color detection.
        """
        try:
            logger.info(f"[{self.name.upper()}] Using BGR fallback for green line detection")

            # Define green color range in BGR - form1s3 uses (0, 255, 0)
            # We need to capture pure green (0, 255, 0) exactly
            lower_green_bgr = np.array([0, 255, 0])  # B, G, R - exact match
            upper_green_bgr = np.array([0, 255, 0])  # B, G, R - exact match

            # Create green mask in BGR
            green_mask = cv2.inRange(roi_image, lower_green_bgr, upper_green_bgr)

            # Apply morphological operations
            kernel = np.ones((3, 3), np.uint8)
            green_mask = cv2.morphologyEx(green_mask, cv2.MORPH_CLOSE, kernel)

            green_pixel_count = np.sum(green_mask > 0)
            logger.debug(f"[{self.name.upper()}] BGR fallback green pixels detected: {green_pixel_count}")

            if green_pixel_count == 0:
                logger.warning(f"[{self.name.upper()}] No green pixels found in BGR fallback either")

                # Debug: Save the BGR mask for inspection
                debug_dir = "../../../io/fullorder_output/table_detection/debug"
                os.makedirs(debug_dir, exist_ok=True)
                cv2.imwrite(os.path.join(debug_dir, "bgr_green_mask.png"), green_mask)
                logger.info(f"[{self.name.upper()}] BGR debug mask saved")

                # Let's also inspect a small sample of pixel values
                logger.info(f"[{self.name.upper()}] Sample pixel values from ROI:")
                h, w = roi_image.shape[:2]
                for i in range(0, min(h, 10), 2):
                    for j in range(0, min(w, 10), 2):
                        pixel_bgr = roi_image[i, j]
                        logger.info(f"  Pixel ({i},{j}): BGR={pixel_bgr}")

                return [], []

            # Apply Canny edge detection
            edges = cv2.Canny(green_mask, 50, 150, apertureSize=3)

            # Use Hough Line Transform
            lines = cv2.HoughLinesP(
                edges,
                rho=1,
                theta=np.pi/180,
                threshold=50,
                minLineLength=30,
                maxLineGap=10
            )

            if lines is None:
                logger.warning(f"[{self.name.upper()}] No lines detected in BGR fallback")
                return [], []

            horizontal_positions = []
            vertical_positions = []

            for line in lines:
                x1, y1, x2, y2 = line[0]
                angle = np.abs(np.arctan2(y2 - y1, x2 - x1) * 180 / np.pi)

                if angle < 10 or angle > 170:
                    y_pos = int((y1 + y2) / 2)
                    horizontal_positions.append(y_pos)
                elif 80 < angle < 100:
                    x_pos = int((x1 + x2) / 2)
                    vertical_positions.append(x_pos)

            logger.info(f"[{self.name.upper()}] BGR fallback detected {len(horizontal_positions)} horizontal and {len(vertical_positions)} vertical positions")
            return horizontal_positions, vertical_positions

        except Exception as e:
            logger.error(f"[{self.name.upper()}] Error in BGR fallback: {str(e)}")
            return [], []

    def deduplicate_and_sort_lines(self, horizontal_positions, vertical_positions, tolerance=5):
        """
        Deduplicate nearby line positions and sort them.

        Args:
            horizontal_positions: List of y coordinates for horizontal lines
            vertical_positions: List of x coordinates for vertical lines
            tolerance: Minimum distance between lines to be considered different

        Returns:
            Tuple of (sorted_horizontal_positions, sorted_vertical_positions)
        """
        def deduplicate_positions(positions, tolerance):
            if not positions:
                return []

            # Sort positions
            sorted_positions = sorted(set(positions))
            deduplicated = [sorted_positions[0]]

            for pos in sorted_positions[1:]:
                # Only add if it's far enough from the last added position
                if pos - deduplicated[-1] > tolerance:
                    deduplicated.append(pos)

            return deduplicated

        horizontal_clean = deduplicate_positions(horizontal_positions, tolerance)
        vertical_clean = deduplicate_positions(vertical_positions, tolerance)

        logger.info(f"[{self.name.upper()}] After deduplication: {len(horizontal_clean)} horizontal, {len(vertical_clean)} vertical lines")
        logger.debug(f"[{self.name.upper()}] Horizontal positions: {horizontal_clean}")
        logger.debug(f"[{self.name.upper()}] Vertical positions: {vertical_clean}")

        return horizontal_clean, vertical_clean

    def extract_drawing_cells(self, roi_image, horizontal_lines, vertical_lines):
        """
        Extract drawing cells from the 6th column (between 6th and 7th vertical lines).

        Args:
            roi_image: The cropped ROI image
            horizontal_lines: Sorted list of horizontal line y-positions
            vertical_lines: Sorted list of vertical line x-positions

        Returns:
            List of dictionaries containing cell info and cropped images
        """
        try:
            extracted_cells = []

            # Check if we have enough vertical lines for the 6th column
            if len(vertical_lines) < 7:
                logger.warning(f"[{self.name.upper()}] Not enough vertical lines detected for 6th column. Found {len(vertical_lines)}, need at least 7")
                return extracted_cells

            # Check if we have enough horizontal lines for rows
            if len(horizontal_lines) < 2:
                logger.warning(f"[{self.name.upper()}] Not enough horizontal lines detected for rows. Found {len(horizontal_lines)}, need at least 2")
                return extracted_cells

            # Get the 6th column boundaries (between 5th and 6th index, 0-based)
            left_x = vertical_lines[5]  # 6th vertical line (0-based index 5)
            right_x = vertical_lines[6]  # 7th vertical line (0-based index 6)

            logger.info(f"[{self.name.upper()}] Drawing column boundaries: x={left_x} to x={right_x} (width={right_x-left_x})")

            # Skip the header row (first row), start from the second row
            for row_idx in range(1, len(horizontal_lines) - 1):
                top_y = horizontal_lines[row_idx]
                bottom_y = horizontal_lines[row_idx + 1]

                # Add margin to avoid grid lines but preserve content
                cell_left = left_x + self.margin
                cell_right = right_x - self.margin
                cell_top = top_y + self.margin
                cell_bottom = bottom_y - self.margin

                # Ensure we don't go out of bounds
                cell_left = max(0, cell_left)
                cell_right = min(roi_image.shape[1], cell_right)
                cell_top = max(0, cell_top)
                cell_bottom = min(roi_image.shape[0], cell_bottom)

                # Check if the cell dimensions are valid
                if cell_right <= cell_left or cell_bottom <= cell_top:
                    logger.warning(f"[{self.name.upper()}] Invalid cell dimensions for row {row_idx}: left={cell_left}, right={cell_right}, top={cell_top}, bottom={cell_bottom}")
                    continue

                # Crop the cell
                cell_image = roi_image[cell_top:cell_bottom, cell_left:cell_right]

                # Check if cell is empty (high mean intensity indicates white/empty cell)
                mean_intensity = np.mean(cv2.cvtColor(cell_image, cv2.COLOR_BGR2GRAY))

                if mean_intensity > 250:
                    logger.debug(f"[{self.name.upper()}] Skipping empty cell in row {row_idx} (mean intensity: {mean_intensity:.1f})")
                    continue

                cell_info = {
                    "row_index": row_idx,  # Data row index (1-based, skipping header)
                    "coordinates": {
                        "left": int(cell_left),
                        "right": int(cell_right),
                        "top": int(cell_top),
                        "bottom": int(cell_bottom)
                    },
                    "dimensions": {
                        "width": int(cell_right - cell_left),
                        "height": int(cell_bottom - cell_top)
                    },
                    "mean_intensity": float(mean_intensity),
                    "cell_image": cell_image
                }

                extracted_cells.append(cell_info)
                logger.info(f"[{self.name.upper()}] Extracted drawing cell from row {row_idx}: {cell_info['dimensions']['width']}x{cell_info['dimensions']['height']} px, intensity: {mean_intensity:.1f}")

            logger.info(f"[{self.name.upper()}] Successfully extracted {len(extracted_cells)} drawing cells")
            return extracted_cells

        except Exception as e:
            logger.error(f"[{self.name.upper()}] Error extracting drawing cells: {str(e)}")
            return []

    def find_drawing_column(self, full_image, horizontal_lines, vertical_lines):
        """
        Analyze all columns to find which one contains drawings by looking for
        columns with complex/non-text content.

        Returns the column index that most likely contains drawings.
        """
        try:
            if len(vertical_lines) < 3 or len(horizontal_lines) < 3:
                logger.warning(f"[{self.name.upper()}] Not enough lines to analyze columns")
                return None

            # Test cells between specific line pairs to find actual drawing content
            # We need to check between lines where actual data rows are
            test_row_pairs = []
            if len(horizontal_lines) >= 4:
                # Check all data row pairs dynamically (start from first data row)
                # Process all available data rows between header and footer
                for i in range(1, len(horizontal_lines) - 1):  # Test all data row pairs dynamically
                    test_row_pairs.append(i)

            if not test_row_pairs:
                test_row_pairs = [1]  # Fallback to first data row pair

            column_scores = {}

            # Analyze each column
            for col_idx in range(len(vertical_lines) - 1):
                left_x = vertical_lines[col_idx] + self.margin
                right_x = vertical_lines[col_idx + 1] - self.margin

                # Skip very narrow columns (likely borders or artifacts)
                # But always analyze Column 2 regardless of width
                column_width = right_x - left_x
                if column_width < 30 and col_idx != 2:  # Always include Column 2
                    continue

                print(f"[DEBUG] Analyzing column {col_idx}: width={column_width} px, x={vertical_lines[col_idx]} to {vertical_lines[col_idx + 1]}")

                column_score = 0
                samples = 0

                # Sample cells from this column in test row pairs
                for row_idx in test_row_pairs:
                    if row_idx >= len(horizontal_lines) - 1:
                        continue

                    top_y = horizontal_lines[row_idx] + self.margin
                    bottom_y = horizontal_lines[row_idx + 1] - self.margin

                    if bottom_y <= top_y or bottom_y - top_y < 20:  # Skip tiny cells
                        continue

                    # Ensure bounds are valid
                    left_x = max(0, left_x)
                    right_x = min(full_image.shape[1], right_x)
                    top_y = max(0, top_y)
                    bottom_y = min(full_image.shape[0], bottom_y)

                    if right_x > left_x and bottom_y > top_y:
                        cell_image = full_image[top_y:bottom_y, left_x:right_x]

                        # Convert to grayscale for analysis
                        gray = cv2.cvtColor(cell_image, cv2.COLOR_BGR2GRAY)

                        # Calculate complexity metrics
                        mean_intensity = np.mean(gray)
                        std_intensity = np.std(gray)

                        # Count edge pixels (potential drawings have more edges)
                        edges = cv2.Canny(gray, 50, 150)
                        edge_ratio = np.sum(edges > 0) / (gray.shape[0] * gray.shape[1])

                        # Score based on:
                        # - Lower mean intensity (drawings are darker)
                        # - Higher std deviation (more variation in intensity)
                        # - Higher edge ratio (more complex shapes)
                        # - Non-text patterns (shapes vs text)

                        print(f"[DEBUG] Col {col_idx}, Row pair {row_idx}-{row_idx+1}: intensity={mean_intensity:.1f}, std={std_intensity:.1f}, edges={edge_ratio:.4f}")

                        if mean_intensity < 245:  # Not empty/white (slightly more lenient)
                            # Enhanced scoring for drawing detection
                            intensity_score = (255 - mean_intensity) / 255  # Lower intensity = higher score
                            complexity_score = min(std_intensity / 30, 2.0)  # Higher std = higher score (more sensitive)
                            edge_score = min(edge_ratio * 20, 2.0)  # More edges = higher score (more sensitive)

                            # Additional checks for drawing-like content
                            contour_bonus = 0
                            if edge_ratio > 0.01:  # Has significant edges
                                # Find contours to detect shapes
                                contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
                                if len(contours) > 2:  # Multiple shapes/objects
                                    contour_bonus = 1.0

                            # Penalize very uniform content (likely text or solid fills)
                            uniformity_penalty = 0
                            if std_intensity < 5:  # Very uniform = likely text or solid
                                uniformity_penalty = -1.0

                            cell_score = intensity_score + complexity_score + edge_score + contour_bonus + uniformity_penalty
                            column_score += cell_score
                            samples += 1

                            print(f"[DEBUG]   -> Score components: intensity={intensity_score:.2f}, complexity={complexity_score:.2f}, edges={edge_score:.2f}, contours={contour_bonus:.2f}, penalty={uniformity_penalty:.2f}, total={cell_score:.2f}")

                if samples > 0:
                    column_scores[col_idx] = column_score / samples
                    print(f"[DEBUG] Column {col_idx} FINAL SCORE: {column_scores[col_idx]:.3f} (samples={samples})")
                    logger.debug(f"[{self.name.upper()}] Column {col_idx}: score={column_scores[col_idx]:.3f} (samples={samples})")

            if not column_scores:
                logger.warning(f"[{self.name.upper()}] No valid columns found for analysis")
                print(f"[DEBUG] Trying to analyze all columns for drawing content...")
                # Force analysis of the widest column since it likely contains drawings
                widest_col = None
                max_width = 0
                for col_idx in range(len(vertical_lines) - 1):
                    width = vertical_lines[col_idx + 1] - vertical_lines[col_idx]
                    if width > max_width and width > 500:  # Minimum reasonable width
                        max_width = width
                        widest_col = col_idx

                if widest_col is not None:
                    print(f"[DEBUG] Forcing selection of widest column {widest_col} (width={max_width}px) as fallback")
                    return widest_col
                else:
                    print(f"[DEBUG] Forcing selection of Column 10 as last resort")
                    return 10

            # Show all available columns for user to verify
            print(f"[DEBUG] === AVAILABLE COLUMNS ===")
            for col_idx in range(len(vertical_lines) - 1):
                left_x = vertical_lines[col_idx]
                right_x = vertical_lines[col_idx + 1]
                width = right_x - left_x
                line_nums = f"lines {col_idx+1}-{col_idx+2}"
                print(f"[DEBUG] Column {col_idx} (between {line_nums}): x={left_x} to x={right_x}, width={width}px")

            # Find the column with the highest score (likely contains drawings)
            best_column = max(column_scores.items(), key=lambda x: x[1])[0]
            best_score = column_scores[best_column]

            # Additional check: prefer the widest column if scores are very close
            sorted_scores = sorted(column_scores.items(), key=lambda x: x[1], reverse=True)
            if len(sorted_scores) >= 2:
                score_diff = sorted_scores[0][1] - sorted_scores[1][1]
                if score_diff < 0.3:  # Very close scores
                    # Check column widths and prefer the wider one
                    top_columns = [col for col, score in sorted_scores[:3]]
                    widest_col = None
                    max_width = 0
                    for col in top_columns:
                        if col + 1 < len(vertical_lines):
                            width = vertical_lines[col + 1] - vertical_lines[col]
                            if width > max_width and width > 500:  # Minimum reasonable width
                                max_width = width
                                widest_col = col

                    if widest_col is not None:
                        best_column = widest_col
                        best_score = column_scores[widest_col]
                        print(f"[DEBUG] Selected wider column {best_column} (width={max_width}px) due to close scores")

            left_boundary = vertical_lines[best_column]
            right_boundary = vertical_lines[best_column + 1]
            logger.info(f"[{self.name.upper()}] Auto-detected drawing column {best_column}: x={left_boundary} to x={right_boundary}")
            print(f"[DEBUG] SELECTED: Column {best_column}: x={left_boundary} to x={right_boundary}, width={right_boundary-left_boundary}px")

            # Show all column scores for debugging
            print(f"[DEBUG] === COLUMN SCORES ===")
            for col_idx, score in sorted(column_scores.items()):
                star = " <-- SELECTED" if col_idx == best_column else ""
                x_start = vertical_lines[col_idx]
                x_end = vertical_lines[col_idx + 1] if col_idx + 1 < len(vertical_lines) else vertical_lines[-1]
                print(f"[DEBUG] Column {col_idx}: score={score:.3f}, x={x_start}-{x_end}, width={x_end-x_start}px{star}")

            logger.info(f"[{self.name.upper()}] Drawing column detected: Column {best_column} (score: {best_score:.3f})")
            print(f"[DEBUG] Selected column {best_column} with highest score: {best_score:.3f}")

            # If top scores are very close, let user know
            sorted_scores = sorted(column_scores.items(), key=lambda x: x[1], reverse=True)
            if len(sorted_scores) >= 2:
                score_diff = sorted_scores[0][1] - sorted_scores[1][1]
                if score_diff < 0.5:  # Very close scores
                    print(f"[DEBUG] WARNING: Top column scores are very close (diff={score_diff:.3f})")
                    print(f"[DEBUG] Consider manual verification. Top 3 columns:")
                    for i in range(min(3, len(sorted_scores))):
                        col_idx, score = sorted_scores[i]
                        print(f"[DEBUG]   Column {col_idx}: {score:.3f}")

            return best_column

        except Exception as e:
            logger.error(f"[{self.name.upper()}] Error finding drawing column: {str(e)}")
            return None

    def filter_major_rows(self, horizontal_lines, tolerance=10):
        """
        Filter horizontal lines to keep only major row separators by grouping
        closely spaced lines and keeping representative ones.

        Args:
            horizontal_lines: Sorted list of horizontal line positions
            tolerance: Maximum distance between lines to be considered the same row

        Returns:
            List of major row separator positions
        """
        if len(horizontal_lines) <= 8:
            return horizontal_lines  # Already looks reasonable

        # Group lines that are close together
        groups = []
        current_group = [horizontal_lines[0]]

        for i in range(1, len(horizontal_lines)):
            if horizontal_lines[i] - horizontal_lines[i-1] <= tolerance:
                current_group.append(horizontal_lines[i])
            else:
                groups.append(current_group)
                current_group = [horizontal_lines[i]]

        groups.append(current_group)

        # Take the first line from each group as the representative (top border of row)
        major_lines = []
        for group in groups:
            major_lines.append(group[0])  # Use first (top) line instead of middle

        logger.info(f"[{self.name.upper()}] Initial filtering: {len(horizontal_lines)} lines to {len(major_lines)} major rows")
        print(f"[DEBUG] Initial row filtering: {len(horizontal_lines)} -> {len(major_lines)} rows")
        print(f"[DEBUG] Initial major row lines: {major_lines}")

        # Apply additional constraints to get exactly 8 data rows
        filtered_lines = self.apply_data_row_constraints(major_lines)

        logger.info(f"[{self.name.upper()}] Final filtering: {len(major_lines)} lines to {len(filtered_lines)} major rows")
        print(f"[DEBUG] Final row filtering: {len(major_lines)} -> {len(filtered_lines)} rows")
        print(f"[DEBUG] Final major row lines: {filtered_lines}")

        return filtered_lines

    def apply_data_row_constraints(self, major_lines):
        """
        Apply additional constraints to identify data rows.
        No longer enforces a fixed count - allows adaptive row detection.

        Args:
            major_lines: List of major row line y-coordinates

        Returns:
            List of filtered lines representing the correct table structure
        """
        # For adaptive row detection, return all major lines without aggressive filtering
        # The dynamic height filtering in the main extraction will handle small rows
        return major_lines

        print(f"[DEBUG] Applying data row constraints to {len(major_lines)} lines...")

        # Calculate distances between consecutive lines
        distances = []
        for i in range(1, len(major_lines)):
            distances.append(major_lines[i] - major_lines[i-1])

        print(f"[DEBUG] Distances between lines: {distances}")

        # Identify minimum row height for actual data rows
        # Data rows should be significantly taller than border/spacing lines
        min_data_row_height = 100  # Minimum height for a valid data row

        # Find lines that form valid data rows (have sufficient height to next line)
        valid_lines = [major_lines[0]]  # Always keep first line (table top)

        for i in range(len(distances)):
            if distances[i] >= min_data_row_height:
                # This forms a valid row, keep the bottom line
                if major_lines[i+1] not in valid_lines:
                    valid_lines.append(major_lines[i+1])
            elif i == len(distances) - 1:
                # Always keep the last line (table bottom)
                if major_lines[i+1] not in valid_lines:
                    valid_lines.append(major_lines[i+1])

        # If we still have too many lines, use height-based filtering
        if len(valid_lines) > 11:  # More than expected (header + 8 data + bottom)
            print(f"[DEBUG] Still too many lines ({len(valid_lines)}), applying height-based filtering...")

            # Calculate row heights and keep the 8 tallest data rows plus header/footer
            row_heights = []
            for i in range(len(valid_lines) - 1):
                height = valid_lines[i+1] - valid_lines[i]
                row_heights.append((height, i, valid_lines[i]))

            # Sort by height descending and take header + 8 tallest + footer
            row_heights.sort(reverse=True)

            # Keep header (first line) and footer (last line)
            final_lines = [valid_lines[0], valid_lines[-1]]

            # Add the 8 tallest middle rows
            middle_rows = [item for item in row_heights if item[1] > 0 and item[1] < len(valid_lines)-2]
            middle_rows = middle_rows[:8]  # Take top 8

            for height, idx, y_coord in middle_rows:
                if y_coord not in final_lines:
                    final_lines.append(y_coord)
                # Also add the bottom boundary of this row
                if valid_lines[idx+1] not in final_lines:
                    final_lines.append(valid_lines[idx+1])

            final_lines.sort()
            valid_lines = final_lines

        print(f"[DEBUG] Applied constraints: {len(major_lines)} -> {len(valid_lines)} lines")
        return valid_lines

    def create_row_boundary_table(self, major_horizontal_lines):
        """
        Create and display a table showing line numbers and upper boundary heights for each row.

        Args:
            major_horizontal_lines: List of y-coordinates for major horizontal lines
        """
        try:
            print(f"\n[DEBUG] === ROW BOUNDARY TABLE ===")
            print(f"{'Line #':<8} | {'Upper Boundary (Y-coord)':<25} | {'Row Type':<15}")
            print(f"{'-'*8}-+-{'-'*25}-+-{'-'*15}")

            for i, y_coord in enumerate(major_horizontal_lines):
                if i == 0:
                    row_type = "Header Top"
                elif i == 1:
                    row_type = "Header Bottom"
                elif i == len(major_horizontal_lines) - 1:
                    row_type = "Table Bottom"
                else:
                    data_row_num = i - 1  # Subtract 1 to account for header
                    row_type = f"Data Row {data_row_num}"

                print(f"{i+1:<8} | {y_coord:<25} | {row_type:<15}")

            print(f"{'-'*8}-+-{'-'*25}-+-{'-'*15}")
            print(f"Total lines: {len(major_horizontal_lines)}")
            print(f"Data rows: {len(major_horizontal_lines) - 2} (excluding header and bottom)")

            logger.info(f"[{self.name.upper()}] Row boundary table created with {len(major_horizontal_lines)} lines")

        except Exception as e:
            logger.error(f"[{self.name.upper()}] Error creating row boundary table: {str(e)}")

    def extract_drawing_cells_full_image(self, full_image, horizontal_lines, vertical_lines):
        """
        Extract drawing cells from the 6th column (between 6th and 7th vertical lines) as per requirements.

        Args:
            full_image: The full image with green grid lines
            horizontal_lines: Sorted list of horizontal line y-positions (full image coordinates)
            vertical_lines: Sorted list of vertical line x-positions (full image coordinates)

        Returns:
            List of dictionaries containing cell info and cropped images
        """
        try:
            extracted_cells = []

            # Check if we have enough lines
            if len(vertical_lines) < 2:
                logger.warning(f"[{self.name.upper()}] Not enough vertical lines detected. Found {len(vertical_lines)}, need at least 2")
                return extracted_cells

            if len(horizontal_lines) < 3:
                logger.warning(f"[{self.name.upper()}] Not enough horizontal lines detected. Found {len(horizontal_lines)}, need at least 3")
                return extracted_cells

            # Filter to get major row separators only (should reduce to ~8 rows)
            major_horizontal_lines = self.filter_major_rows(horizontal_lines)

            # Find which column contains drawings automatically
            drawing_column_idx = self.find_drawing_column(full_image, major_horizontal_lines, vertical_lines)

            if drawing_column_idx is None:
                logger.warning(f"[{self.name.upper()}] Could not automatically detect drawing column")
                # Fallback: try all columns and show scores
                print("[DEBUG] Trying to analyze all columns for drawing content...")
                return extracted_cells

            # Get the drawing column boundaries
            left_x = vertical_lines[drawing_column_idx]
            right_x = vertical_lines[drawing_column_idx + 1]

            logger.info(f"[{self.name.upper()}] Detected drawing column {drawing_column_idx}: x={left_x} to x={right_x} (width={right_x-left_x})")
            print(f"[DEBUG] Auto-detected drawing column {drawing_column_idx}: x={left_x} to x={right_x}, width={right_x-left_x}px")

            # Extract cells between specific line pairs for actual data rows
            # Calculate dynamic minimum height based on average row height
            total_table_height = major_horizontal_lines[-1] - major_horizontal_lines[0]
            estimated_rows = len(major_horizontal_lines) - 2  # Exclude header and footer
            avg_row_height = total_table_height / max(estimated_rows, 1) if estimated_rows > 0 else 100
            min_row_height = max(20, avg_row_height * 0.3)  # Dynamic minimum: 30% of average or 20px minimum

            print(f"[DEBUG] Dynamic row height analysis: avg={avg_row_height:.1f}px, min_threshold={min_row_height:.1f}px")

            sequential_row_num = 1  # Sequential counter for file naming
            # Process all data rows dynamically (from row 1 to second-last row)
            for row_idx in range(1, len(major_horizontal_lines) - 1):
                top_y = major_horizontal_lines[row_idx]
                bottom_y = major_horizontal_lines[row_idx + 1]
                row_height = bottom_y - top_y

                print(f"[DEBUG] Processing row {row_idx} (sequential #{sequential_row_num}): from line {top_y} to line {bottom_y} (height={row_height})")

                # Skip rows that are too small (likely table boundaries or spacing)
                if row_height < min_row_height:
                    print(f"[DEBUG] Skipping row {row_idx} - too small (height={row_height}px < {min_row_height:.1f}px)")
                    logger.warning(f"[{self.name.upper()}] Skipping row {row_idx} - height too small: {row_height}px < {min_row_height:.1f}px")
                    continue

                # Add margin to avoid grid lines but preserve content
                cell_left = left_x + self.margin
                cell_right = right_x - self.margin
                cell_top = top_y + self.margin
                cell_bottom = bottom_y - self.margin

                # Ensure we don't go out of bounds
                cell_left = max(0, cell_left)
                cell_right = min(full_image.shape[1], cell_right)
                cell_top = max(0, cell_top)
                cell_bottom = min(full_image.shape[0], cell_bottom)

                # Check if the cell dimensions are valid
                if cell_right <= cell_left or cell_bottom <= cell_top:
                    logger.warning(f"[{self.name.upper()}] Invalid cell dimensions for row {row_idx}: left={cell_left}, right={cell_right}, top={cell_top}, bottom={cell_bottom}")
                    continue

                # Crop the cell from the full image
                cell_image = full_image[cell_top:cell_bottom, cell_left:cell_right]

                # Check if cell is empty (high mean intensity indicates white/empty cell)
                mean_intensity = np.mean(cv2.cvtColor(cell_image, cv2.COLOR_BGR2GRAY))

                print(f"[DEBUG] Row {row_idx} (sequential #{sequential_row_num}): cell {cell_image.shape}, intensity {mean_intensity:.1f}")

                if mean_intensity > 252:  # Lowered threshold to include more rows
                    logger.debug(f"[{self.name.upper()}] Skipping empty cell in row {row_idx} (mean intensity: {mean_intensity:.1f})")
                    sequential_row_num += 1  # Still increment counter even for skipped rows
                    continue

                cell_info = {
                    "row_index": sequential_row_num,  # Use sequential numbering for file naming
                    "coordinates": {
                        "left": int(cell_left),
                        "right": int(cell_right),
                        "top": int(cell_top),
                        "bottom": int(cell_bottom)
                    },
                    "dimensions": {
                        "width": int(cell_right - cell_left),
                        "height": int(cell_bottom - cell_top)
                    },
                    "mean_intensity": float(mean_intensity),
                    "cell_image": cell_image
                }

                extracted_cells.append(cell_info)
                logger.info(f"[{self.name.upper()}] Extracted drawing cell #{sequential_row_num} from table row {row_idx}: {cell_info['dimensions']['width']}x{cell_info['dimensions']['height']} px, intensity: {mean_intensity:.1f}")

                sequential_row_num += 1  # Increment sequential counter

            logger.info(f"[{self.name.upper()}] Successfully extracted {len(extracted_cells)} drawing cells")

            # Create table with line numbers and upper boundary heights
            self.create_row_boundary_table(major_horizontal_lines)

            return extracted_cells

        except Exception as e:
            logger.error(f"[{self.name.upper()}] Error extracting drawing cells: {str(e)}")
            return []

    def extract_cells_from_shape_column(self, column_image, horizontal_lines):
        """
        Extract individual shape cells from a shape column image.

        Args:
            column_image: The shape column image
            horizontal_lines: Sorted list of horizontal line y-positions

        Returns:
            List of dictionaries containing cell info and cropped images
        """
        try:
            extracted_cells = []
            height, width = column_image.shape[:2]

            print(f"[DEBUG] Shape column dimensions: {width}x{height}")
            print(f"[DEBUG] Horizontal lines: {horizontal_lines}")

            # Calculate minimum row height based on image size and number of lines
            if len(horizontal_lines) > 2:
                avg_row_height = height / (len(horizontal_lines) - 1)
                min_row_height = max(20, avg_row_height * 0.3)
            else:
                min_row_height = 50

            print(f"[DEBUG] Minimum row height threshold: {min_row_height}")

            sequential_row_num = 1

            # Process all rows including first and last rows
            all_rows = []

            # First row: from image top to first green line
            if len(horizontal_lines) > 0:
                all_rows.append((0, horizontal_lines[0]))

            # Middle rows: between consecutive horizontal lines
            for i in range(len(horizontal_lines) - 1):
                all_rows.append((horizontal_lines[i], horizontal_lines[i + 1]))

            # Last row: from last green line to image bottom
            if len(horizontal_lines) > 0:
                all_rows.append((horizontal_lines[-1], height))

            print(f"[DEBUG] Total rows to process: {len(all_rows)} (including first and last rows)")

            # Process all rows
            for row_idx, (top_y, bottom_y) in enumerate(all_rows):
                row_height = bottom_y - top_y

                print(f"[DEBUG] Processing row {row_idx+1}: from y={top_y} to y={bottom_y} (height={row_height})")

                # Skip rows that are too small
                if row_height < min_row_height:
                    print(f"[DEBUG] Skipping row {row_idx+1} - too small (height={row_height}px < {min_row_height}px)")
                    continue

                # Add margin to avoid grid lines
                cell_left = self.margin
                cell_right = width - self.margin
                cell_top = top_y + self.margin
                cell_bottom = bottom_y - self.margin

                # Ensure valid bounds
                cell_left = max(0, cell_left)
                cell_right = min(width, cell_right)
                cell_top = max(0, cell_top)
                cell_bottom = min(height, cell_bottom)

                # Check if dimensions are valid
                if cell_right <= cell_left or cell_bottom <= cell_top:
                    print(f"[DEBUG] Invalid cell dimensions for row {row_idx+1}")
                    continue

                # Crop the cell
                cell_image = column_image[cell_top:cell_bottom, cell_left:cell_right]

                # Check if cell is empty by looking for actual content (drawings, text, etc.)
                gray_cell = cv2.cvtColor(cell_image, cv2.COLOR_BGR2GRAY)
                mean_intensity = np.mean(gray_cell)

                # Calculate variance to detect if there's actual content (drawings have variation)
                intensity_variance = np.var(gray_cell)

                print(f"[DEBUG] Row {row_idx+1}: cell {cell_image.shape}, intensity {mean_intensity:.1f}, variance {intensity_variance:.1f}")

                # Skip cells that are both very white AND have very low variance (truly empty)
                if mean_intensity > 248 and intensity_variance < 50:
                    print(f"[DEBUG] Skipping empty cell in row {row_idx+1} (intensity: {mean_intensity:.1f}, variance: {intensity_variance:.1f})")
                    sequential_row_num += 1
                    continue

                cell_info = {
                    "row_index": sequential_row_num,
                    "coordinates": {
                        "left": int(cell_left),
                        "right": int(cell_right),
                        "top": int(cell_top),
                        "bottom": int(cell_bottom)
                    },
                    "dimensions": {
                        "width": int(cell_right - cell_left),
                        "height": int(cell_bottom - cell_top)
                    },
                    "mean_intensity": float(mean_intensity),
                    "cell_image": cell_image
                }

                extracted_cells.append(cell_info)
                logger.info(f"[{self.name.upper()}] Extracted shape cell #{sequential_row_num}: {cell_info['dimensions']['width']}x{cell_info['dimensions']['height']} px, intensity: {mean_intensity:.1f}")

                sequential_row_num += 1

            logger.info(f"[{self.name.upper()}] Successfully extracted {len(extracted_cells)} shape cells from column")
            return extracted_cells

        except Exception as e:
            logger.error(f"[{self.name.upper()}] Error extracting cells from shape column: {str(e)}")
            return []

    def save_drawing_cells(self, extracted_cells, output_dir, input_file_path=None):
        """
        Save extracted drawing cells as PNG files.

        Args:
            extracted_cells: List of cell dictionaries from extract_drawing_cells
            output_dir: Directory to save the PNG files
            input_file_path: Input file path to extract page number from

        Returns:
            List of saved file paths
        """
        try:
            os.makedirs(output_dir, exist_ok=True)
            saved_files = []

            # Extract order name and page number from input file path
            base_name = os.path.basename(input_file_path)
            # Extract from patterns like CO25S006375_shape_column_page1.png
            order_name = "unknown"
            page_num = "1"

            if "_shape_column_" in base_name:
                order_name = base_name.split("_shape_column_")[0]
                if "_page" in base_name:
                    try:
                        page_part = base_name.split("_page")[1]
                        page_num = page_part.split(".")[0]  # Remove file extension
                    except:
                        page_num = "1"

            for cell in extracted_cells:
                row_index = cell["row_index"]
                cell_image = cell["cell_image"]

                # Generate filename with order name and page number
                filename = f"{order_name}_drawing_row_{row_index}_page{page_num}.png"
                file_path = os.path.join(output_dir, filename)

                # Save the image
                cv2.imwrite(file_path, cell_image)
                saved_files.append(file_path)

                logger.info(f"[{self.name.upper()}] Saved drawing cell: {filename} ({cell['dimensions']['width']}x{cell['dimensions']['height']} px)")

            logger.info(f"[{self.name.upper()}] Saved {len(saved_files)} drawing cell files to {output_dir}")
            return saved_files

        except Exception as e:
            logger.error(f"[{self.name.upper()}] Error saving drawing cells: {str(e)}")
            return []

    def process_image(self, input_image_path):
        """
        Main processing function that extracts drawing cells from shape column.

        Args:
            input_image_path: Path to the input image (shape_column_page.png from form1s4_1)

        Returns:
            Dictionary with processing results
        """
        try:
            logger.info(f"[{self.name.upper()}] Starting drawing cell extraction process")

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
            print(f"[DEBUG] Image loaded successfully: {image.shape}")

            # Step 1: For shape column images, detect green horizontal lines specifically
            print(f"[DEBUG] Processing shape column image - detecting green horizontal grid lines...")

            # Convert to HSV for better green detection
            hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)

            # Define range for green color (same as Form1S4_1)
            lower_green = np.array([35, 50, 50])
            upper_green = np.array([85, 255, 255])

            # Create mask for green pixels
            green_mask = cv2.inRange(hsv, lower_green, upper_green)

            # Find horizontal green lines by scanning each row
            horizontal_positions = []
            height, width = image.shape[:2]

            for y in range(height):
                green_pixel_count = np.sum(green_mask[y, :] > 0)
                # If more than 40% of the row is green, it's likely a horizontal line
                if green_pixel_count > width * 0.4:
                    horizontal_positions.append(y)

            # Group consecutive horizontal lines (lines within 10 pixels of each other)
            horizontal_line_groups = []
            if horizontal_positions:
                current_group = [horizontal_positions[0]]

                for i in range(1, len(horizontal_positions)):
                    if horizontal_positions[i] - horizontal_positions[i-1] <= 10:
                        current_group.append(horizontal_positions[i])
                    else:
                        if len(current_group) > 0:
                            horizontal_line_groups.append(current_group)
                        current_group = [horizontal_positions[i]]

                # Add the last group
                if len(current_group) > 0:
                    horizontal_line_groups.append(current_group)

            # Get representative line from each group (use middle line)
            horizontal_lines = []
            for group in horizontal_line_groups:
                horizontal_lines.append(int(np.mean(group)))

            horizontal_lines = sorted(horizontal_lines)
            print(f"[DEBUG] Detected {len(horizontal_lines)} horizontal lines in shape column")

            if len(horizontal_lines) < 2:
                error_msg = "Not enough horizontal lines detected to extract cells"
                logger.error(f"[{self.name.upper()}] {error_msg}")
                return {"status": "error", "error": error_msg}

            # Step 2: Extract drawing cells directly from the shape column
            extracted_cells = self.extract_cells_from_shape_column(image, horizontal_lines)

            if not extracted_cells:
                logger.warning(f"[{self.name.upper()}] No drawing cells extracted")

            # Step 6: Save the extracted cells
            # Use absolute path relative to project root
            project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
            output_dir = os.path.join(project_root, "io", "fullorder_output", "table_detection", "shapes")

            saved_files = self.save_drawing_cells(extracted_cells, output_dir, input_image_path)

            # Prepare result
            result = {
                "status": "success",
                "input_file": input_image_path,
                "grid_structure": {
                    "horizontal_lines": len(horizontal_lines),
                    "vertical_lines": 0,  # Shape column has no vertical lines
                    "horizontal_positions": horizontal_lines,
                    "vertical_positions": []
                },
                "extraction_results": {
                    "total_cells_extracted": len(extracted_cells),
                    "saved_files": saved_files,
                    "output_directory": output_dir
                },
                "cell_details": [
                    {
                        "row_index": cell["row_index"],
                        "coordinates": cell["coordinates"],
                        "dimensions": cell["dimensions"],
                        "mean_intensity": cell["mean_intensity"]
                    }
                    for cell in extracted_cells
                ],
                "method": "shape_column_horizontal_line_extraction"
            }

            logger.info(f"[{self.name.upper()}] Drawing cell extraction completed successfully")
            return result

        except Exception as e:
            error_msg = f"Error processing image: {str(e)}"
            logger.error(f"[{self.name.upper()}] {error_msg}")
            return {"status": "error", "error": error_msg}


def main():
    """
    Test function to run the form1s4 agent independently.
    """
    try:
        agent = Form1S4Agent()

        # Look for the output from form1s4_1 (shape_column_page.png) in shape_column folder with page number
        input_path = "../../../io/fullorder_output/table_detection/shape_column/CO25S006375_shape_column_page1.png"

        if not os.path.exists(input_path):
            print(f"Input file not found: {input_path}")
            print(f"Current working directory: {os.getcwd()}")
            print("Please run form1s4_1 first to generate the shape column image.")
            return

        print(f"Processing file: {os.path.abspath(input_path)}")
        print(f"File size: {os.path.getsize(input_path)} bytes")

        # Process the image
        result = agent.process_image(input_path)

        print("=== FORM1S4 RESULTS ===")
        print(json.dumps(result, indent=2))

        if result["status"] == "success":
            extraction_results = result["extraction_results"]
            print(f"Successfully extracted {extraction_results['total_cells_extracted']} drawing cells")
            print(f"Files saved to: {extraction_results['output_directory']}")

            for file_path in extraction_results["saved_files"]:
                print(f"  - {os.path.basename(file_path)}")
        else:
            print(f"Error: {result.get('error', 'Unknown error')}")

    except Exception as e:
        print(f"Error in main: {e}")


if __name__ == "__main__":
    main()
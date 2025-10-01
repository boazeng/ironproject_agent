import os
import logging
import cv2
import numpy as np
from PIL import Image
import json
from pathlib import Path
from datetime import datetime
import base64
from openai import OpenAI

logger = logging.getLogger(__name__)

class Shape1S1Agent:
    """
    Shape1S1 Agent - Shape Detection and Catalog Matching

    Responsibilities:
    1. Get shape drawing from extracted images
    2. Detect catalog shape number corresponding to the drawing
    3. Detect length and angle of the shape with order of catalog shape ribs and angles
    4. Analyze shape geometry and dimensions
    """

    def __init__(self):
        self.name = "shape1s1"
        self.short_name = "SHAPE1S1"
        self.shapes_dir = "io/fullorder_output/table_detection/shapes"
        self.output_dir = "io/fullorder_output/shape_detection"

        # Create output directory
        os.makedirs(self.output_dir, exist_ok=True)

        logger.info(f"[{self.short_name}] Agent initialized - Shape Detection and Catalog Matching")

        # Initialize OpenAI client (for advanced shape analysis)
        try:
            self.client = OpenAI()
            logger.info(f"[{self.short_name}] OpenAI client initialized")
        except Exception as e:
            logger.warning(f"[{self.short_name}] OpenAI client not available: {str(e)}")
            self.client = None

        # Define catalog shapes (basic bent iron shapes)
        self.catalog_shapes = {
            "L_SHAPE": {
                "description": "L-shaped bent iron",
                "ribs": 2,
                "angles": [90],
                "pattern": "horizontal_vertical"
            },
            "U_SHAPE": {
                "description": "U-shaped bent iron",
                "ribs": 3,
                "angles": [90, 90],
                "pattern": "horizontal_vertical_horizontal"
            },
            "STRAIGHT": {
                "description": "Straight iron bar",
                "ribs": 1,
                "angles": [],
                "pattern": "horizontal"
            },
            "Z_SHAPE": {
                "description": "Z-shaped bent iron",
                "ribs": 3,
                "angles": [90, 90],
                "pattern": "horizontal_vertical_horizontal_offset"
            }
        }

    def process_single_shape(self, shape_file_path):
        """
        Process a single shape file for shape detection and catalog matching

        Args:
            shape_file_path (str): Path to the shape image file

        Returns:
            dict: Processing results for the single shape
        """
        try:
            filename = os.path.basename(shape_file_path)
            logger.info(f"[{self.short_name}] Processing single shape: {filename}")

            # Check if file exists
            if not os.path.exists(shape_file_path):
                error_msg = f"Shape file not found: {shape_file_path}"
                logger.error(f"[{self.short_name}] {error_msg}")
                return {"status": "error", "message": error_msg}

            # Analyze the shape
            shape_result = self.analyze_shape(shape_file_path)

            # Create result structure
            result = {
                "status": "completed",
                "timestamp": datetime.now().isoformat(),
                "shape_file": shape_file_path,
                "shape_analysis": shape_result
            }

            # Save individual result
            output_file = os.path.join(self.output_dir, f"shape_analysis_{filename}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json")
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(result, f, indent=2, ensure_ascii=False)

            logger.info(f"[{self.short_name}] Single shape analysis completed. Results saved to: {output_file}")
            return result

        except Exception as e:
            error_msg = f"Error processing single shape {shape_file_path}: {str(e)}"
            logger.error(f"[{self.short_name}] {error_msg}")
            return {"status": "error", "message": error_msg}

    def get_next_shape_file(self):
        """
        Get the next shape file from the shapes directory

        Returns:
            str: Path to the next shape file, or None if no files found
        """
        try:
            if not os.path.exists(self.shapes_dir):
                logger.warning(f"[{self.short_name}] Shapes directory not found: {self.shapes_dir}")
                return None

            # Get all PNG files in the shapes directory
            shape_files = []
            for file in os.listdir(self.shapes_dir):
                if file.endswith('.png'):
                    shape_files.append(os.path.join(self.shapes_dir, file))

            if not shape_files:
                logger.info(f"[{self.short_name}] No shape files found in directory")
                return None

            # Sort by modification time to get most recent first
            shape_files.sort(key=lambda x: os.path.getmtime(x), reverse=True)

            next_file = shape_files[0]
            logger.info(f"[{self.short_name}] Next shape file: {os.path.basename(next_file)}")
            return next_file

        except Exception as e:
            logger.error(f"[{self.short_name}] Error getting next shape file: {str(e)}")
            return None

    def process_shape_files(self, order_name=None):
        """
        Process all shape files for shape detection and catalog matching
        (Kept for backward compatibility)

        Args:
            order_name (str): Specific order to process, if None processes all

        Returns:
            dict: Processing results with detected shapes
        """
        try:
            logger.info(f"[{self.short_name}] Starting shape detection process")

            # Get list of shape files
            if not os.path.exists(self.shapes_dir):
                logger.warning(f"[{self.short_name}] Shapes directory not found: {self.shapes_dir}")
                return {"status": "error", "message": "Shapes directory not found"}

            shape_files = []
            for file in os.listdir(self.shapes_dir):
                if file.endswith('.png') and (order_name is None or order_name in file):
                    shape_files.append(os.path.join(self.shapes_dir, file))

            if not shape_files:
                logger.warning(f"[{self.short_name}] No shape files found")
                return {"status": "warning", "message": "No shape files found"}

            logger.info(f"[{self.short_name}] Found {len(shape_files)} shape files to process")

            results = {
                "status": "processing",
                "timestamp": datetime.now().isoformat(),
                "total_shapes": len(shape_files),
                "processed_shapes": [],
                "errors": []
            }

            # Process each shape file
            for shape_file in shape_files:
                try:
                    shape_result = self.analyze_shape(shape_file)
                    results["processed_shapes"].append(shape_result)
                    logger.info(f"[{self.short_name}] Shape analyzed: {shape_result['filename']}")
                except Exception as e:
                    error_msg = f"Error processing {shape_file}: {str(e)}"
                    logger.error(f"[{self.short_name}] {error_msg}")
                    results["errors"].append(error_msg)

            results["status"] = "completed" if not results["errors"] else "completed_with_errors"

            # Save results
            output_file = os.path.join(self.output_dir, f"shape_detection_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json")
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(results, f, indent=2, ensure_ascii=False)

            logger.info(f"[{self.short_name}] Shape detection completed. Results saved to: {output_file}")
            return results

        except Exception as e:
            error_msg = f"Error in shape detection process: {str(e)}"
            logger.error(f"[{self.short_name}] {error_msg}")
            return {"status": "error", "message": error_msg}

    def analyze_shape(self, shape_file_path):
        """
        Analyze a single shape image to detect catalog shape and dimensions

        Args:
            shape_file_path (str): Path to the shape image file

        Returns:
            dict: Shape analysis results
        """
        try:
            filename = os.path.basename(shape_file_path)
            logger.info(f"[{self.short_name}] Analyzing shape: {filename}")

            # Load and process image
            image = cv2.imread(shape_file_path)
            if image is None:
                raise ValueError(f"Could not load image: {shape_file_path}")

            # Basic image analysis
            height, width = image.shape[:2]

            # Extract dimensions from image (look for text/numbers)
            dimensions = self.extract_dimensions(image)

            # Detect shape geometry
            geometry = self.detect_geometry(image)

            # Match with catalog shapes
            catalog_match = self.match_catalog_shape(geometry, dimensions)

            # Advanced analysis using OpenAI if available
            ai_analysis = None
            if self.client:
                try:
                    ai_analysis = self.ai_shape_analysis(shape_file_path)
                except Exception as e:
                    logger.warning(f"[{self.short_name}] AI analysis failed: {str(e)}")

            result = {
                "filename": filename,
                "file_path": shape_file_path,
                "image_size": {"width": width, "height": height},
                "extracted_dimensions": dimensions,
                "detected_geometry": geometry,
                "catalog_match": catalog_match,
                "ai_analysis": ai_analysis,
                "timestamp": datetime.now().isoformat()
            }

            # Send message to user
            self.send_user_message(result)

            return result

        except Exception as e:
            logger.error(f"[{self.short_name}] Error analyzing shape {shape_file_path}: {str(e)}")
            return {
                "filename": os.path.basename(shape_file_path),
                "file_path": shape_file_path,
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }

    def extract_dimensions(self, image):
        """
        Extract numerical dimensions from the shape image using OCR

        Args:
            image: OpenCV image array

        Returns:
            dict: Extracted dimensions
        """
        try:
            # Convert to grayscale
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

            # Apply threshold to get better text recognition
            _, thresh = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)

            # Find contours to locate text regions
            contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

            # Extract text using simple pattern matching (looking for numbers)
            dimensions = {"lengths": [], "angles": [], "text_found": []}

            # Look for red numbers (dimensions are often in red)
            hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)

            # Red color range
            lower_red1 = np.array([0, 50, 50])
            upper_red1 = np.array([10, 255, 255])
            lower_red2 = np.array([170, 50, 50])
            upper_red2 = np.array([180, 255, 255])

            mask1 = cv2.inRange(hsv, lower_red1, upper_red1)
            mask2 = cv2.inRange(hsv, lower_red2, upper_red2)
            red_mask = mask1 + mask2

            # Find red regions (likely dimensions)
            red_contours, _ = cv2.findContours(red_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

            # Basic dimension extraction (this could be enhanced with proper OCR)
            if len(red_contours) > 0:
                dimensions["has_red_markings"] = True
                dimensions["red_regions_count"] = len(red_contours)

            return dimensions

        except Exception as e:
            logger.error(f"[{self.short_name}] Error extracting dimensions: {str(e)}")
            return {"error": str(e)}

    def detect_geometry(self, image):
        """
        Detect the geometric shape and structure

        Args:
            image: OpenCV image array

        Returns:
            dict: Detected geometry information
        """
        try:
            # Convert to grayscale
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

            # Apply edge detection
            edges = cv2.Canny(gray, 50, 150, apertureSize=3)

            # Find lines using Hough Line Transform
            lines = cv2.HoughLines(edges, 1, np.pi/180, threshold=100)

            geometry = {
                "lines_detected": 0,
                "horizontal_lines": 0,
                "vertical_lines": 0,
                "diagonal_lines": 0,
                "estimated_shape": "unknown"
            }

            if lines is not None:
                geometry["lines_detected"] = len(lines)

                for line in lines:
                    rho, theta = line[0]
                    angle = np.degrees(theta)

                    # Classify line orientation
                    if 85 <= angle <= 95 or -5 <= angle <= 5 or 175 <= angle <= 185:
                        geometry["horizontal_lines"] += 1
                    elif 40 <= angle <= 50 or 130 <= angle <= 140:
                        geometry["vertical_lines"] += 1
                    else:
                        geometry["diagonal_lines"] += 1

                # Estimate shape based on line analysis
                if geometry["horizontal_lines"] >= 2 and geometry["vertical_lines"] >= 1:
                    geometry["estimated_shape"] = "L_SHAPE_OR_U_SHAPE"
                elif geometry["horizontal_lines"] >= 1 and geometry["vertical_lines"] == 0:
                    geometry["estimated_shape"] = "STRAIGHT"
                elif geometry["horizontal_lines"] >= 3 and geometry["vertical_lines"] >= 2:
                    geometry["estimated_shape"] = "COMPLEX_BENT"

            return geometry

        except Exception as e:
            logger.error(f"[{self.short_name}] Error detecting geometry: {str(e)}")
            return {"error": str(e)}

    def match_catalog_shape(self, geometry, dimensions):
        """
        Match detected geometry with catalog shapes

        Args:
            geometry (dict): Detected geometry information
            dimensions (dict): Extracted dimensions

        Returns:
            dict: Catalog matching results
        """
        try:
            matches = []

            for shape_id, shape_info in self.catalog_shapes.items():
                confidence = 0

                # Match based on estimated shape
                if geometry.get("estimated_shape") == "STRAIGHT" and shape_id == "STRAIGHT":
                    confidence = 0.8
                elif geometry.get("estimated_shape") == "L_SHAPE_OR_U_SHAPE":
                    if shape_id in ["L_SHAPE", "U_SHAPE"]:
                        confidence = 0.6
                elif geometry.get("estimated_shape") == "COMPLEX_BENT":
                    if shape_id in ["Z_SHAPE", "U_SHAPE"]:
                        confidence = 0.4

                # Adjust confidence based on line counts
                expected_lines = shape_info["ribs"]
                detected_lines = geometry.get("lines_detected", 0)
                if detected_lines > 0:
                    line_match_ratio = min(expected_lines, detected_lines) / max(expected_lines, detected_lines)
                    confidence *= line_match_ratio

                if confidence > 0.3:  # Minimum confidence threshold
                    matches.append({
                        "shape_id": shape_id,
                        "shape_info": shape_info,
                        "confidence": confidence,
                        "match_reason": f"Geometry match with {confidence:.2f} confidence"
                    })

            # Sort by confidence
            matches.sort(key=lambda x: x["confidence"], reverse=True)

            return {
                "best_match": matches[0] if matches else None,
                "all_matches": matches,
                "match_count": len(matches)
            }

        except Exception as e:
            logger.error(f"[{self.short_name}] Error matching catalog shape: {str(e)}")
            return {"error": str(e)}

    def ai_shape_analysis(self, shape_file_path):
        """
        Use OpenAI Vision API for advanced shape analysis

        Args:
            shape_file_path (str): Path to the shape image

        Returns:
            dict: AI analysis results
        """
        try:
            if not self.client:
                return {"error": "OpenAI client not available"}

            # Encode image to base64
            with open(shape_file_path, "rb") as image_file:
                base64_image = base64.b64encode(image_file.read()).decode('utf-8')

            response = self.client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "text",
                                "text": """Analyze this bent iron shape drawing and provide:
1. Shape type (L-shape, U-shape, straight, Z-shape, etc.)
2. Number of ribs/segments
3. Angles between segments
4. Dimensions visible in the image
5. Catalog shape classification

Return as JSON format."""
                            },
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:image/png;base64,{base64_image}"
                                }
                            }
                        ]
                    }
                ],
                max_tokens=500
            )

            ai_result = response.choices[0].message.content

            # Try to parse as JSON, fallback to text
            try:
                ai_analysis = json.loads(ai_result)
            except:
                ai_analysis = {"text_response": ai_result}

            return ai_analysis

        except Exception as e:
            logger.error(f"[{self.short_name}] AI analysis error: {str(e)}")
            return {"error": str(e)}

    def send_user_message(self, shape_result):
        """
        Send a message to the user about the detected shape

        Args:
            shape_result (dict): Shape analysis results
        """
        try:
            filename = shape_result.get("filename", "unknown")
            catalog_match = shape_result.get("catalog_match", {})
            best_match = catalog_match.get("best_match")

            if best_match:
                shape_id = best_match["shape_id"]
                confidence = best_match["confidence"]
                description = best_match["shape_info"]["description"]

                message = f"[SHAPE DETECTED] {filename}:\n"
                message += f"   Catalog: {shape_id}\n"
                message += f"   Type: {description}\n"
                message += f"   Confidence: {confidence:.1%}\n"

                # Add dimension info if available
                dimensions = shape_result.get("extracted_dimensions", {})
                if dimensions.get("has_red_markings"):
                    message += f"   Dimensions: Found markings in image\n"

                # Add AI analysis if available
                ai_analysis = shape_result.get("ai_analysis")
                if ai_analysis and not ai_analysis.get("error"):
                    message += f"   AI Analysis: Available\n"

            else:
                message = f"[SHAPE UNKNOWN] {filename}: Could not match with catalog shapes"

            logger.info(f"[{self.short_name}] {message}")
            print(f"\n{message}")

        except Exception as e:
            logger.error(f"[{self.short_name}] Error sending user message: {str(e)}")


if __name__ == "__main__":
    # Test the agent with single shape processing
    agent = Shape1S1Agent()

    # Get next shape file
    next_shape = agent.get_next_shape_file()
    if next_shape:
        print(f"Processing single shape: {os.path.basename(next_shape)}")
        result = agent.process_single_shape(next_shape)
        print("Single shape analysis completed:", result.get("status"))
    else:
        print("No shape files found to process")
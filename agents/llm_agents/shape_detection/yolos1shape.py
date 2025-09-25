import os
import json
import torch
from PIL import Image
import numpy as np
from datetime import datetime
from pathlib import Path
import cv2
import math
from typing import Dict, List, Tuple, Optional

class YoloS1ShapeAgent:
    """
    YOLO-based Shape Detection Agent
    Detects shapes and extracts rib lengths and angles using a pre-trained YOLO model
    """

    def __init__(self, model_path: str = None, output_dir: str = None):
        """
        Initialize the YOLO Shape Detection Agent

        Args:
            model_path: Path to the YOLO model file
            output_dir: Directory to save output files
        """
        self.model_path = model_path or r"C:\Users\User\Aiprojects\Iron-Projects\Agents\data\yolo_model\yolo.pt"
        self.output_dir = output_dir or r"C:\Users\User\Aiprojects\Iron-Projects\Agents\data\yolo_model"
        self.model = None
        self.device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')

        self._load_model()

    def _load_model(self):
        """Load the YOLO model"""
        try:
            # Check if model file exists
            if not os.path.exists(self.model_path):
                raise FileNotFoundError(f"Model file not found at {self.model_path}")

            # Load YOLO model using ultralytics
            try:
                from ultralytics import YOLO
                self.model = YOLO(self.model_path)
                print(f"Successfully loaded YOLO model from {self.model_path}")
            except ImportError:
                # Fallback to torch hub if ultralytics not available
                self.model = torch.hub.load('ultralytics/yolov5', 'custom',
                                           path=self.model_path, force_reload=False)
                print(f"Loaded model using torch hub from {self.model_path}")

        except Exception as e:
            print(f"Error loading YOLO model: {str(e)}")
            raise

    def detect_shape(self, image_path: str) -> Dict:
        """
        Detect shape in the image and extract properties

        Args:
            image_path: Path to the input image

        Returns:
            Dictionary containing shape detection results
        """
        if not os.path.exists(image_path):
            return {"error": f"Image file not found: {image_path}"}

        try:
            # Read image
            image = cv2.imread(image_path)
            if image is None:
                return {"error": f"Failed to read image: {image_path}"}

            # Run YOLO inference
            results = self.model(image)

            # Process detection results
            shape_info = self._process_detections(results, image)

            # Extract ribs and angles
            if shape_info.get("detections"):
                shape_info["ribs"] = self._extract_ribs(shape_info["detections"], image)
                shape_info["angles"] = self._calculate_angles(shape_info["ribs"])

                # Draw detections on image and save annotated version
                annotated_path = self.draw_detections(image_path, shape_info["detections"])
                if annotated_path:
                    shape_info["annotated_image"] = annotated_path

            # Add metadata
            shape_info["image_path"] = image_path
            shape_info["timestamp"] = datetime.now().isoformat()
            shape_info["model_path"] = self.model_path

            # Save results to file
            output_path = self._save_results(shape_info, image_path)
            shape_info["output_file"] = output_path

            return shape_info

        except Exception as e:
            return {"error": f"Detection failed: {str(e)}", "image_path": image_path}

    def _process_detections(self, results, image) -> Dict:
        """
        Process YOLO detection results

        Args:
            results: YOLO model output
            image: Original image

        Returns:
            Processed detection information
        """
        shape_info = {
            "detections": [],
            "shape_count": 0,
            "confidence_scores": []
        }

        try:
            # Extract detections based on model type
            if hasattr(results, 'pandas'):
                # YOLOv5 style results
                detections = results.pandas().xyxy[0].to_dict('records')
            else:
                # YOLOv8+ style results
                detections = []
                for r in results:
                    if r.boxes:
                        for box in r.boxes:
                            detection = {
                                'xmin': float(box.xyxy[0][0]),
                                'ymin': float(box.xyxy[0][1]),
                                'xmax': float(box.xyxy[0][2]),
                                'ymax': float(box.xyxy[0][3]),
                                'confidence': float(box.conf),
                                'class': int(box.cls) if hasattr(box, 'cls') else 0,
                                'name': r.names[int(box.cls)] if hasattr(r, 'names') and hasattr(box, 'cls') else 'shape'
                            }
                            detections.append(detection)

            # Process each detection
            for i, det in enumerate(detections):
                processed_det = {
                    "shape_number": i + 1,
                    "bbox": {
                        "x1": det.get('xmin', 0),
                        "y1": det.get('ymin', 0),
                        "x2": det.get('xmax', 0),
                        "y2": det.get('ymax', 0)
                    },
                    "confidence": det.get('confidence', 0),
                    "class_name": det.get('name', 'unknown'),
                    "center": {
                        "x": (det.get('xmin', 0) + det.get('xmax', 0)) / 2,
                        "y": (det.get('ymin', 0) + det.get('ymax', 0)) / 2
                    }
                }

                shape_info["detections"].append(processed_det)
                shape_info["confidence_scores"].append(det.get('confidence', 0))

            shape_info["shape_count"] = len(shape_info["detections"])

            if shape_info["confidence_scores"]:
                shape_info["avg_confidence"] = np.mean(shape_info["confidence_scores"])
                shape_info["max_confidence"] = max(shape_info["confidence_scores"])

        except Exception as e:
            print(f"Error processing detections: {str(e)}")

        return shape_info

    def _extract_ribs(self, detections: List[Dict], image: np.ndarray) -> List[Dict]:
        """
        Extract rib information from detected shapes

        Args:
            detections: List of detected shapes
            image: Original image

        Returns:
            List of rib information
        """
        ribs = []

        for det in detections:
            bbox = det["bbox"]

            # Extract region of interest
            x1, y1 = int(bbox["x1"]), int(bbox["y1"])
            x2, y2 = int(bbox["x2"]), int(bbox["y2"])

            # Basic rib calculation (simplified - would need actual contour analysis)
            width = x2 - x1
            height = y2 - y1

            # Estimate ribs based on bounding box
            rib_info = {
                "shape_number": det["shape_number"],
                "estimated_ribs": [
                    {"name": "horizontal", "length": width, "unit": "pixels"},
                    {"name": "vertical", "length": height, "unit": "pixels"},
                    {"name": "diagonal", "length": math.sqrt(width**2 + height**2), "unit": "pixels"}
                ],
                "perimeter": 2 * (width + height),
                "area": width * height
            }

            ribs.append(rib_info)

        return ribs

    def _calculate_angles(self, ribs: List[Dict]) -> List[Dict]:
        """
        Calculate angles from rib information

        Args:
            ribs: List of rib information

        Returns:
            List of angle information
        """
        angles = []

        for rib_info in ribs:
            if "estimated_ribs" in rib_info and len(rib_info["estimated_ribs"]) >= 2:
                # Calculate angle between horizontal and vertical ribs
                horizontal = rib_info["estimated_ribs"][0]["length"]
                vertical = rib_info["estimated_ribs"][1]["length"]

                # Calculate angle in degrees
                angle_rad = math.atan2(vertical, horizontal)
                angle_deg = math.degrees(angle_rad)

                angle_info = {
                    "shape_number": rib_info["shape_number"],
                    "angles": [
                        {"name": "corner_angle", "value": 90.0, "unit": "degrees"},
                        {"name": "diagonal_angle", "value": angle_deg, "unit": "degrees"},
                        {"name": "complementary_angle", "value": 90.0 - angle_deg, "unit": "degrees"}
                    ]
                }

                angles.append(angle_info)

        return angles

    def draw_detections(self, image_path: str, detections: List[Dict]) -> str:
        """
        Draw bounding boxes and labels on the image

        Args:
            image_path: Path to the original image
            detections: List of detection results

        Returns:
            Path to the annotated image file
        """
        try:
            # Read the image
            image = cv2.imread(image_path)
            if image is None:
                print(f"Failed to read image for drawing: {image_path}")
                return None

            # Define colors for different classes (BGR format)
            colors = {
                "U-shape": (0, 255, 0),      # Green
                "complex": (255, 0, 0),       # Blue
                "L-shape": (0, 0, 255),       # Red
                "T-shape": (255, 255, 0),     # Cyan
                "rectangle": (255, 0, 255),   # Magenta
                "default": (0, 255, 255)      # Yellow
            }

            # Draw each detection
            for detection in detections:
                # Get bounding box coordinates
                x1 = int(detection["bbox"]["x1"])
                y1 = int(detection["bbox"]["y1"])
                x2 = int(detection["bbox"]["x2"])
                y2 = int(detection["bbox"]["y2"])

                # Get class name and confidence
                class_name = detection["class_name"]
                confidence = detection["confidence"]

                # Choose color based on class
                color = colors.get(class_name, colors["default"])

                # Draw bounding box
                cv2.rectangle(image, (x1, y1), (x2, y2), color, 3)

                # Prepare label text
                label = f"{class_name}: {confidence:.2%}"

                # Calculate label position
                label_size, _ = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.8, 2)
                label_y = y1 - 10 if y1 > 30 else y2 + 25

                # Draw label background
                cv2.rectangle(image,
                            (x1, label_y - label_size[1] - 5),
                            (x1 + label_size[0], label_y + 5),
                            color, -1)

                # Draw label text
                cv2.putText(image, label, (x1, label_y),
                          cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 255), 2)

                # Draw shape number
                shape_num = f"Shape {detection['shape_number']}"
                cv2.putText(image, shape_num, (x1 + 5, y1 + 25),
                          cv2.FONT_HERSHEY_SIMPLEX, 0.6, color, 2)

            # Create output filename for annotated image
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            base_name = Path(image_path).stem
            output_filename = f"yolo_annotated_{base_name}_{timestamp}.png"
            output_path = os.path.join(self.output_dir, output_filename)

            # Save the annotated image
            cv2.imwrite(output_path, image)
            print(f"Annotated image saved to: {output_path}")

            return output_path

        except Exception as e:
            print(f"Error drawing detections: {str(e)}")
            return None

    def _save_results(self, results: Dict, image_path: str) -> str:
        """
        Save detection results to file

        Args:
            results: Detection results dictionary
            image_path: Path to the original image

        Returns:
            Path to the saved results file
        """
        # Create output filename
        image_name = Path(image_path).stem
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_filename = f"yolo_detection_{image_name}_{timestamp}.json"
        output_path = os.path.join(self.output_dir, output_filename)

        # Save results as JSON
        with open(output_path, 'w') as f:
            json.dump(results, f, indent=2, default=str)

        print(f"Results saved to: {output_path}")
        return output_path

    def process_shape(self, image_path: str) -> Dict:
        """
        Main method to process a shape image

        Args:
            image_path: Path to the shape image

        Returns:
            Complete shape analysis results
        """
        print(f"Processing shape image: {image_path}")
        results = self.detect_shape(image_path)

        if "error" not in results:
            print(f"Successfully detected {results.get('shape_count', 0)} shapes")
            if results.get("ribs"):
                print(f"Extracted {len(results['ribs'])} rib sets")
            if results.get("angles"):
                print(f"Calculated {len(results['angles'])} angle sets")
        else:
            print(f"Error: {results['error']}")

        return results


# Test function
def test_agent():
    """Test the YOLO Shape Detection Agent"""
    agent = YoloS1ShapeAgent()

    # Test with the provided test image
    test_image = r"C:\Users\User\Aiprojects\Iron-Projects\Agents\data\yolo_model\testshape"

    # Check if test image exists (try with common extensions)
    test_paths = [
        test_image,
        test_image + ".jpg",
        test_image + ".png",
        test_image + ".jpeg"
    ]

    for path in test_paths:
        if os.path.exists(path):
            print(f"Testing with: {path}")
            results = agent.process_shape(path)
            print("\nDetection Results:")
            print(json.dumps(results, indent=2, default=str))
            return results

    print(f"Test image not found. Tried: {test_paths}")
    return None


if __name__ == "__main__":
    test_agent()
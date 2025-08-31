import os
import cv2
import numpy as np
import base64
import json
from typing import Dict, List, Tuple, Optional
from openai import OpenAI
import math

class PathFinderAgent:
    """
    Specialized agent for finding and extracting path vectors from bent iron drawings.
    Converts geometric shapes into sequences of vectors with lengths and angles.
    """
    
    def __init__(self, api_key):
        """
        Initialize the PathFinder agent
        
        Args:
            api_key: OpenAI API key for vision analysis
        """
        self.client = OpenAI(api_key=api_key)
        self.api_key = api_key
        print("[PATHFINDER] Agent initialized - Vector path extraction specialist")
    
    def encode_image(self, image_path):
        """
        Encode image to base64 for API transmission
        
        Args:
            image_path: Path to the image file
            
        Returns:
            Base64 encoded string
        """
        with open(image_path, "rb") as image_file:
            return base64.b64encode(image_file.read()).decode('utf-8')
    
    def extract_contours(self, image_path: str) -> List[np.ndarray]:
        """
        Extract contours from the drawing using OpenCV
        
        Args:
            image_path: Path to the drawing image
            
        Returns:
            List of contours (each contour is an array of points)
        """
        try:
            # Read the image
            img = cv2.imread(image_path)
            if img is None:
                print(f"[PATHFINDER] Error: Could not read image {image_path}")
                return []
            
            # Convert to grayscale
            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
            
            # Apply threshold to get binary image
            _, binary = cv2.threshold(gray, 127, 255, cv2.THRESH_BINARY_INV)
            
            # Find contours
            contours, _ = cv2.findContours(binary, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            
            print(f"[PATHFINDER] Found {len(contours)} contours in image")
            
            # Filter out very small contours (noise)
            min_area = 100  # Minimum contour area
            filtered_contours = [c for c in contours if cv2.contourArea(c) > min_area]
            
            print(f"[PATHFINDER] Filtered to {len(filtered_contours)} significant contours")
            
            return filtered_contours
            
        except Exception as e:
            print(f"[PATHFINDER] Error extracting contours: {e}")
            return []
    
    def approximate_polygon(self, contour: np.ndarray, epsilon_factor: float = 0.02) -> np.ndarray:
        """
        Approximate contour with polygon using Douglas-Peucker algorithm
        
        Args:
            contour: Input contour points
            epsilon_factor: Factor for approximation accuracy (lower = more accurate)
            
        Returns:
            Approximated polygon points
        """
        # Calculate epsilon based on contour perimeter
        epsilon = epsilon_factor * cv2.arcLength(contour, True)
        
        # Approximate polygon
        approx = cv2.approxPolyDP(contour, epsilon, True)
        
        return approx
    
    def extract_vertices_from_vision(self, image_path: str, rib_count: int, shape_pattern: str = None, rib_lengths: List[float] = None, shape_type: str = None) -> List[Tuple[float, float]]:
        """
        Extract vertices using GPT-4 Vision API with context from other agents
        
        Args:
            image_path: Path to the drawing image
            rib_count: Expected number of ribs
            shape_pattern: Shape pattern from RibFinder (optional)
            rib_lengths: Rib lengths from CHATAN (optional)
            shape_type: Shape type from CHATAN (optional)
            
        Returns:
            List of vertices (x, y) coordinates
        """
        try:
            base64_image = self.encode_image(image_path)
            
            # Build context information from other agents
            context_info = f"The drawing shows a bent iron shape with exactly {rib_count} ribs (straight segments).\n"
            
            if shape_pattern:
                context_info += f"RibFinder detected pattern: {shape_pattern}\n"
            if shape_type:
                context_info += f"CHATAN identified shape type: {shape_type}\n"
            if rib_lengths:
                context_info += f"CHATAN measured rib lengths: {rib_lengths} cm\n"
            
            response = self.client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {
                        "role": "system",
                        "content": f"""You are an expert at analyzing bent iron technical drawings.
                        
                        {context_info}
                        
                        Your task is to identify the VERTICES (corner points) of the shape.
                        There should be {rib_count + 1} vertices for an open shape or {rib_count} for closed.
                        
                        IMPORTANT: 
                        - Start from one end of the shape
                        - List vertices in order along the path
                        - Use relative coordinates where the first vertex is (0, 0)
                        - Scale based on the dimensions shown in the drawing
                        - Use the known rib lengths to ensure accurate scaling
                        
                        Return ONLY a JSON object:
                        {{
                            "vertices": [[x1, y1], [x2, y2], ...],
                            "is_closed": boolean,
                            "dimensions_detected": [list of dimension values found]
                        }}"""
                    },
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "text",
                                "text": f"Extract the vertices for this {rib_count}-rib bent iron shape. Start from one end and trace the path."
                            },
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:image/jpeg;base64,{base64_image}",
                                    "detail": "high"
                                }
                            }
                        ]
                    }
                ],
                max_tokens=1000,
                temperature=0.1
            )
            
            result_text = response.choices[0].message.content
            
            # Parse JSON response
            if "```json" in result_text:
                result_text = result_text.split("```json")[1].split("```")[0]
            elif "```" in result_text:
                result_text = result_text.split("```")[1].split("```")[0]
            
            result = json.loads(result_text.strip())
            vertices = [(v[0], v[1]) for v in result.get("vertices", [])]
            
            print(f"[PATHFINDER] Extracted {len(vertices)} vertices from vision analysis")
            return vertices
            
        except Exception as e:
            print(f"[PATHFINDER] Vision extraction failed: {e}")
            return []
    
    def calculate_vectors(self, vertices: List[Tuple[float, float]]) -> List[Dict]:
        """
        Calculate vectors between consecutive vertices
        
        Args:
            vertices: List of (x, y) vertex coordinates
            
        Returns:
            List of vector dictionaries with properties
        """
        vectors = []
        
        for i in range(len(vertices) - 1):
            x1, y1 = vertices[i]
            x2, y2 = vertices[i + 1]
            
            # Calculate vector components
            dx = x2 - x1
            dy = y2 - y1
            
            # Calculate length
            length = math.sqrt(dx**2 + dy**2)
            
            # Calculate angle (in degrees)
            angle_rad = math.atan2(dy, dx)
            angle_deg = math.degrees(angle_rad)
            
            # Calculate normalized direction vector
            if length > 0:
                dir_x = dx / length
                dir_y = dy / length
            else:
                dir_x, dir_y = 0, 0
            
            vector_info = {
                "rib_number": i + 1,
                "start_point": {"x": x1, "y": y1},
                "end_point": {"x": x2, "y": y2},
                "vector": {"dx": dx, "dy": dy},
                "length": round(length, 2),
                "angle_degrees": round(angle_deg, 2),
                "angle_radians": round(angle_rad, 4),
                "direction": {"x": round(dir_x, 4), "y": round(dir_y, 4)}
            }
            
            # Calculate bend angle to next rib (if not last)
            if i < len(vertices) - 2:
                x3, y3 = vertices[i + 2]
                dx_next = x3 - x2
                dy_next = y3 - y2
                angle_next = math.atan2(dy_next, dx_next)
                bend_angle = math.degrees(angle_next - angle_rad)
                
                # Normalize bend angle to [-180, 180]
                while bend_angle > 180:
                    bend_angle -= 360
                while bend_angle < -180:
                    bend_angle += 360
                    
                vector_info["bend_angle_to_next"] = round(bend_angle, 2)
            
            vectors.append(vector_info)
        
        return vectors
    
    def find_path(self, image_path: str, rib_count: int, all_straight: bool = True, ribfinder_data: Dict = None, chatan_data: Dict = None) -> Dict:
        """
        Main method to find the path vectors of a bent iron shape
        
        Args:
            image_path: Path to the drawing image
            rib_count: Number of ribs in the shape
            all_straight: Whether all ribs are straight lines (True) or may have curves (False)
            ribfinder_data: Data from RibFinder agent (optional)
            chatan_data: Data from CHATAN agent with rib lengths (optional)
            
        Returns:
            Dictionary with complete path analysis
        """
        try:
            print(f"[PATHFINDER] Analyzing path for {rib_count}-rib shape")
            print(f"[PATHFINDER] All ribs straight: {all_straight}")
            
            # Extract data from other agents
            ribfinder_shape_pattern = None
            chatan_rib_lengths = []
            chatan_shape_type = None
            
            if ribfinder_data:
                ribfinder_shape_pattern = ribfinder_data.get('shape_pattern')
                print(f"[PATHFINDER] RibFinder pattern: {ribfinder_shape_pattern}")
            
            if chatan_data:
                chatan_shape_type = chatan_data.get('shape_type')
                sides = chatan_data.get('sides', [])
                chatan_rib_lengths = [side.get('length', 0) for side in sides if side.get('length', 0) > 0]
                print(f"[PATHFINDER] CHATAN shape: {chatan_shape_type}")
                print(f"[PATHFINDER] CHATAN rib lengths: {chatan_rib_lengths} cm")
            
            # Check if file exists
            if not os.path.exists(image_path):
                return {"error": f"Image file not found: {image_path}"}
            
            # Method 1: Try vision-based vertex extraction with context from other agents
            vertices = self.extract_vertices_from_vision(image_path, rib_count, ribfinder_shape_pattern, chatan_rib_lengths, chatan_shape_type)
            
            # Method 2: If vision fails, try contour-based extraction
            if not vertices or len(vertices) < 2:
                print("[PATHFINDER] Attempting contour-based extraction...")
                contours = self.extract_contours(image_path)
                
                if contours:
                    # Use the largest contour
                    largest_contour = max(contours, key=cv2.contourArea)
                    
                    # Approximate to polygon
                    approx = self.approximate_polygon(largest_contour)
                    
                    # Convert to vertices list
                    vertices = [(point[0][0], point[0][1]) for point in approx]
                    
                    # Ensure we have the expected number of vertices
                    if len(vertices) > rib_count + 1:
                        # Simplify further
                        approx = self.approximate_polygon(largest_contour, epsilon_factor=0.05)
                        vertices = [(point[0][0], point[0][1]) for point in approx]
                    
                    print(f"[PATHFINDER] Extracted {len(vertices)} vertices from contours")
            
            if not vertices or len(vertices) < 2:
                return {
                    "error": "Failed to extract vertices",
                    "rib_count": rib_count,
                    "vertices": [],
                    "vectors": []
                }
            
            # Calculate vectors from vertices
            vectors = self.calculate_vectors(vertices)
            
            # Calculate total path length
            total_length = sum(v["length"] for v in vectors)
            
            # Determine shape type based on vectors
            shape_type = self.classify_shape(vectors, rib_count)
            
            # Build complete result
            result = {
                "status": "Path analysis complete",
                "rib_count": rib_count,
                "vertex_count": len(vertices),
                "vertices": [{"x": v[0], "y": v[1], "index": i} for i, v in enumerate(vertices)],
                "vectors": vectors,
                "total_path_length": round(total_length, 2),
                "shape_type": shape_type,
                "is_closed": self.is_closed_shape(vertices),
                "all_ribs_straight": all_straight,
                "path_summary": {
                    "start_point": {"x": vertices[0][0], "y": vertices[0][1]},
                    "end_point": {"x": vertices[-1][0], "y": vertices[-1][1]},
                    "bounding_box": self.calculate_bounding_box(vertices)
                }
            }
            
            print(f"[PATHFINDER] Path analysis complete: {len(vectors)} vectors extracted")
            return result
            
        except Exception as e:
            print(f"[PATHFINDER] Path finding failed: {e}")
            return {
                "error": f"Path finding failed: {str(e)}",
                "rib_count": rib_count,
                "vertices": [],
                "vectors": []
            }
    
    def classify_shape(self, vectors: List[Dict], rib_count: int) -> str:
        """
        Classify the shape based on vectors and angles
        
        Args:
            vectors: List of vector dictionaries
            rib_count: Number of ribs
            
        Returns:
            Shape classification string
        """
        if rib_count == 2:
            # Check if L-shape (90-degree bend)
            if vectors and "bend_angle_to_next" in vectors[0]:
                angle = abs(vectors[0]["bend_angle_to_next"])
                if 85 <= angle <= 95:
                    return "L-shape"
        elif rib_count == 3:
            # Check for U-shape or Z-shape
            if len(vectors) >= 2:
                if all("bend_angle_to_next" in v and abs(v["bend_angle_to_next"]) > 85 
                       and abs(v["bend_angle_to_next"]) < 95 for v in vectors[:2]):
                    # Check if both bends are in same direction (U) or opposite (Z)
                    if vectors[0]["bend_angle_to_next"] * vectors[1]["bend_angle_to_next"] > 0:
                        return "U-shape"
                    else:
                        return "Z-shape"
        
        return f"Complex-{rib_count}-rib"
    
    def is_closed_shape(self, vertices: List[Tuple[float, float]], threshold: float = 10.0) -> bool:
        """
        Check if the shape is closed (start and end points are close)
        
        Args:
            vertices: List of vertex coordinates
            threshold: Distance threshold for considering points as same
            
        Returns:
            True if closed shape, False otherwise
        """
        if len(vertices) < 3:
            return False
        
        start = vertices[0]
        end = vertices[-1]
        distance = math.sqrt((end[0] - start[0])**2 + (end[1] - start[1])**2)
        
        return distance < threshold
    
    def calculate_bounding_box(self, vertices: List[Tuple[float, float]]) -> Dict:
        """
        Calculate bounding box of the shape
        
        Args:
            vertices: List of vertex coordinates
            
        Returns:
            Bounding box dictionary
        """
        if not vertices:
            return {"min_x": 0, "min_y": 0, "max_x": 0, "max_y": 0, "width": 0, "height": 0}
        
        x_coords = [v[0] for v in vertices]
        y_coords = [v[1] for v in vertices]
        
        min_x, max_x = min(x_coords), max(x_coords)
        min_y, max_y = min(y_coords), max(y_coords)
        
        return {
            "min_x": round(min_x, 2),
            "min_y": round(min_y, 2),
            "max_x": round(max_x, 2),
            "max_y": round(max_y, 2),
            "width": round(max_x - min_x, 2),
            "height": round(max_y - min_y, 2)
        }


def create_pathfinder_agent(api_key):
    """
    Factory function to create a PathFinder agent
    
    Args:
        api_key: OpenAI API key
        
    Returns:
        PathFinderAgent instance
    """
    return PathFinderAgent(api_key)
import os
import base64
import json
import autogen
from openai import OpenAI
from typing import Dict
import requests
from google.cloud import vision
import io
import anthropic
import cv2
import numpy as np
from skimage import filters, morphology, measure, feature
import skimage.io as skio
from scipy.ndimage import label

class RibFinderAgent:
    """
    Specialized agent that uses high-end ChatGPT to accurately count ribs in bent iron drawings
    """
    
    def __init__(self, api_key, google_vision_api_key=None, anthropic_api_key=None):
        """
        Initialize the RibFinder agent with premium models from OpenAI, Google, and Anthropic
        
        Args:
            api_key: OpenAI API key
            google_vision_api_key: Google Vision API key (optional)
            anthropic_api_key: Anthropic Claude API key (optional)
        """
        # Initialize OpenAI client
        self.client = OpenAI(api_key=api_key)
        self.api_key = api_key
        
        # Initialize Google Vision API
        self.google_vision_api_key = google_vision_api_key or os.getenv("GOOGLE_VISION_API_KEY")
        self.google_credentials_path = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
        
        # Claude Vision API disabled by user request
        self.claude_client = None
        print("[RIBFINDER] Claude Vision API disabled")
        
        # Initialize Google Vision client if credentials available
        self.vision_client = None
        if self.google_credentials_path and os.path.exists(self.google_credentials_path):
            self.vision_client = vision.ImageAnnotatorClient()
            print("[RIBFINDER] Google Vision API initialized with service account")
        elif self.google_vision_api_key:
            print("[RIBFINDER] Google Vision API initialized with API key")
        else:
            print("[RIBFINDER] Google Vision API not configured - using ChatGPT only")
        
        # Configuration for highest quality GPT model
        config_list = [
            {
                "model": "gpt-4o",  # Use premium model for accuracy
                "api_key": api_key,
                "max_tokens": 300,  # Focused response
            }
        ]
        
        # LLM configuration for maximum accuracy
        llm_config = {
            "config_list": config_list,
            "temperature": 0.1,  # Very low temperature for consistent counting
            "timeout": 180,
        }
        
        # Create the rib counting specialist agent
        self.agent = autogen.AssistantAgent(
            name="RIBFINDER_Specialist",
            llm_config=llm_config,
            system_message="""You are a specialist in counting ribs (straight segments) in bent iron drawings.
            
            Your ONLY task is to count ribs accurately. Nothing else.
            
            DEFINITION: A rib = any straight segment of iron between two bends (or ends).
            
            COUNTING METHOD:
            1. Start from one end of the iron
            2. Follow the path segment by segment  
            3. Each straight section = 1 rib
            4. Count systematically
            
            Return ONLY the number as integer.
            """
        )
    
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
    
    def analyze_with_google_vision(self, image_path: str) -> int:
        """
        Analyze image with Google Vision API to count ribs
        
        Args:
            image_path: Path to the drawing image
            
        Returns:
            Number of ribs detected by Google Vision
        """
        try:
            if not self.vision_client:
                return None
                
            with io.open(image_path, 'rb') as image_file:
                content = image_file.read()
            
            image = vision.Image(content=content)
            
            # Perform text detection to help identify dimensions and structure
            response = self.vision_client.text_detection(image=image)
            texts = response.text_annotations
            
            # Perform object detection
            objects_response = self.vision_client.object_localization(image=image)
            objects = objects_response.localized_object_annotations
            
            # Simple heuristic: count detected text groups as potential rib indicators
            # This is a simplified approach - you might need more sophisticated logic
            if texts:
                # Count dimension indicators (numbers) as potential ribs
                dimension_count = len([t for t in texts if any(char.isdigit() for char in t.description)])
                # Basic heuristic: if we see 3 dimension groups, likely 3 ribs
                if dimension_count >= 3:
                    return 3
                elif dimension_count == 2:
                    return 2
                else:
                    return 1
            
            return None
            
        except Exception as e:
            print(f"[RIBFINDER] Google Vision analysis failed: {e}")
            return None
    
    def analyze_with_claude_vision(self, image_path: str) -> int:
        """
        Analyze image with Claude Vision API to count ribs
        
        Args:
            image_path: Path to the drawing image
            
        Returns:
            Number of ribs detected by Claude Vision
        """
        try:
            if not self.claude_client:
                return None
                
            # Read and encode the image
            with open(image_path, 'rb') as image_file:
                image_data = base64.b64encode(image_file.read()).decode('utf-8')
            
            # Get image MIME type
            mime_type = "image/png" if image_path.endswith('.png') else "image/jpeg"
            
            # Send to Claude Vision API
            response = self.claude_client.messages.create(
                model="claude-3-haiku-20240307",  # Claude model with vision
                max_tokens=1024,
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "text",
                                "text": """You are an expert at analyzing bent iron construction drawings.
                                
                                Your ONLY task is to count the number of ribs (straight segments) in this bent iron shape.
                                
                                CRITICAL INSTRUCTIONS:
                                1. A rib is ANY straight segment between bends
                                2. Count ALL straight segments systematically
                                3. Common patterns:
                                   - L-shape = 2 ribs
                                   - U-shape = 3 ribs
                                   - Z-shape = 3 ribs
                                   - Complex shapes = 4+ ribs
                                
                                Look for vertical segments on BOTH ends of horizontal segments.
                                If you see |___| pattern, that's 3 ribs (U-shape).
                                
                                Return ONLY a JSON object: {"rib_count": number}"""
                            },
                            {
                                "type": "image",
                                "source": {
                                    "type": "base64",
                                    "media_type": mime_type,
                                    "data": image_data
                                }
                            }
                        ]
                    }
                ]
            )
            
            # Parse response
            result_text = response.content[0].text
            
            # Try to parse JSON
            try:
                if "```json" in result_text:
                    result_text = result_text.split("```json")[1].split("```")[0]
                elif "```" in result_text:
                    result_text = result_text.split("```")[1].split("```")[0]
                
                result = json.loads(result_text.strip())
                return result.get("rib_count", None)
                
            except json.JSONDecodeError:
                # Try to extract number from text
                import re
                numbers = re.findall(r'\b(\d+)\b', result_text)
                if numbers:
                    return int(numbers[0])
                return None
                
        except Exception as e:
            print(f"[RIBFINDER] Claude Vision analysis failed: {e}")
            return None
    
    def analyze_with_opencv_vertices(self, image_path: str) -> int:
        """
        Use OpenCV to detect vertices (bend points) in the bent iron drawing
        
        Args:
            image_path: Path to the drawing image
            
        Returns:
            Number of ribs detected based on vertices (or None if failed)
        """
        try:
            # Normalize path for OpenCV (handle Windows paths and spaces)
            normalized_path = os.path.normpath(image_path)
            
            # Check if file exists first
            if not os.path.exists(normalized_path):
                print(f"[RIBFINDER] OpenCV error: File not found - {normalized_path}")
                return None
            
            # Try multiple approaches to read the image
            image = None
            
            # Method 1: Direct imread
            image = cv2.imread(normalized_path)
            
            # Method 2: If direct fails, try with forward slashes
            if image is None:
                forward_slash_path = normalized_path.replace('\\', '/')
                image = cv2.imread(forward_slash_path)
                
            # Method 3: If still fails, use numpy to read and convert
            if image is None:
                print(f"[RIBFINDER] OpenCV imread failed, trying numpy approach...")
                try:
                    # Read as bytes and decode with cv2
                    with open(normalized_path, 'rb') as f:
                        file_bytes = np.frombuffer(f.read(), dtype=np.uint8)
                        image = cv2.imdecode(file_bytes, cv2.IMREAD_COLOR)
                except Exception as e:
                    print(f"[RIBFINDER] Numpy approach also failed: {e}")
            
            if image is None:
                print(f"[RIBFINDER] All methods failed to read image: {normalized_path}")
                return None
            else:
                print(f"[RIBFINDER] OpenCV successfully loaded image")
                
            # Convert to grayscale
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            
            # Apply Gaussian blur to reduce noise
            blurred = cv2.GaussianBlur(gray, (5, 5), 0)
            
            # Use edge detection
            edges = cv2.Canny(blurred, 50, 150, apertureSize=3)
            
            # Find contours
            contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            
            if not contours:
                return None
            
            # Find the largest contour (presumably the main iron shape)
            main_contour = max(contours, key=cv2.contourArea)
            
            # Approximate the contour to reduce points
            epsilon = 0.02 * cv2.arcLength(main_contour, True)
            approx_contour = cv2.approxPolyDP(main_contour, epsilon, True)
            
            # Count vertices (corners)
            vertices = len(approx_contour)
            
            print(f"[RIBFINDER] OpenCV detected {vertices} vertices")
            
            # Analyze the shape geometry to determine ribs more accurately
            if vertices < 3:
                print(f"[RIBFINDER] OpenCV insufficient vertices: {vertices} (need at least 3)")
                return None
            
            # For bent iron shapes, the number of ribs depends on shape type:
            # We need to analyze the actual geometry, not just count vertices
            
            # Simple heuristic: check if it's more likely L-shape or U-shape
            # by analyzing the bounding rectangle
            x, y, w, h = cv2.boundingRect(approx_contour)
            aspect_ratio = max(w, h) / min(w, h)
            
            # If very rectangular (high aspect ratio), likely L-shape
            # If more square-ish, could be U-shape
            if aspect_ratio > 10:  # Very long and thin - likely L-shape
                ribs = 2
                print(f"[RIBFINDER] OpenCV: High aspect ratio ({aspect_ratio:.1f}) suggests L-shape = 2 ribs")
            elif vertices == 3:
                ribs = 2  # True L-shape
                print(f"[RIBFINDER] OpenCV: 3 vertices = L-shape = 2 ribs")
            elif vertices == 4:
                # Could be L-shape with 4 corner points or true U-shape
                # For now, assume L-shape (more common in this context)
                ribs = 2
                print(f"[RIBFINDER] OpenCV: 4 vertices, assuming L-shape = 2 ribs")
            else:
                # For more complex shapes
                ribs = min(vertices - 1, 4)  # Cap at 4 ribs max
                print(f"[RIBFINDER] OpenCV: {vertices} vertices = {ribs} ribs (complex shape)")
            
            return ribs
                
        except Exception as e:
            print(f"[RIBFINDER] OpenCV analysis failed: {e}")
            return None
    
    def analyze_with_scikit_image(self, image_path: str) -> int:
        """
        Use Scikit-image to detect ribs through improved line detection and geometric analysis
        
        Args:
            image_path: Path to the drawing image
            
        Returns:
            Number of ribs detected based on advanced analysis (or None if failed)
        """
        try:
            # Normalize path (same as OpenCV)
            normalized_path = os.path.normpath(image_path)
            
            if not os.path.exists(normalized_path):
                print(f"[RIBFINDER] Scikit-image error: File not found - {normalized_path}")
                return None
            
            # Read image with scikit-image
            try:
                # First try skimage.io
                import skimage.io as skio
                image = skio.imread(normalized_path)
            except Exception:
                # Fallback to opencv + conversion
                cv_image = cv2.imread(normalized_path)
                if cv_image is None:
                    # Use numpy approach
                    with open(normalized_path, 'rb') as f:
                        file_bytes = np.frombuffer(f.read(), dtype=np.uint8)
                        cv_image = cv2.imdecode(file_bytes, cv2.IMREAD_COLOR)
                
                if cv_image is None:
                    print(f"[RIBFINDER] Scikit-image failed to load image")
                    return None
                    
                # Convert BGR to RGB for skimage
                image = cv2.cvtColor(cv_image, cv2.COLOR_BGR2RGB)
            
            print(f"[RIBFINDER] Scikit-image loaded image with shape: {image.shape}")
            
            # Handle different image formats (RGB, RGBA, grayscale)
            if len(image.shape) == 3:
                if image.shape[2] == 4:  # RGBA image
                    # Convert RGBA to RGB by removing alpha channel
                    image = image[:, :, :3]
                    print(f"[RIBFINDER] Converted RGBA to RGB")
                
                # Convert to grayscale
                from skimage.color import rgb2gray
                gray = rgb2gray(image)
            else:
                gray = image
            
            # Enhanced preprocessing for better line detection
            from skimage import restoration, morphology as morph, segmentation
            
            # Apply bilateral filter to preserve edges while reducing noise
            denoised = restoration.denoise_bilateral(gray, sigma_color=0.1, sigma_spatial=15)
            
            # Multiple edge detection approaches
            # Method 1: Enhanced Canny with adaptive thresholds
            edges_canny = feature.canny(denoised, sigma=1.5, low_threshold=0.05, high_threshold=0.15)
            
            # Method 2: Sobel edge detection 
            from skimage import filters as filt
            edges_sobel = filt.sobel(denoised) > 0.1
            
            # Method 3: Ridge detection for line-like structures
            ridges = filt.meijering(denoised, sigmas=[1, 2, 3])
            ridge_binary = ridges > np.percentile(ridges, 85)
            
            # Combine edge detection methods
            combined_edges = np.logical_or(np.logical_or(edges_canny, edges_sobel), ridge_binary)
            
            # Clean up edges with morphological operations
            # Remove small noise
            cleaned_edges = morph.remove_small_objects(combined_edges, min_size=20)
            # Fill small gaps in lines
            cleaned_edges = morph.binary_closing(cleaned_edges, morph.disk(2))
            
            # Use Hough Line Transform for robust line detection
            from skimage.transform import hough_line, hough_line_peaks
            
            # Detect lines using Hough transform
            tested_angles = np.linspace(-np.pi/2, np.pi/2, 180, endpoint=False)
            hough_space, angles, dists = hough_line(cleaned_edges, theta=tested_angles)
            
            # Find peaks in Hough space (detected lines)
            hspace_peaks = hough_line_peaks(hough_space, angles, dists, 
                                          min_distance=20,   # Minimum distance between lines
                                          threshold=0.3 * np.max(hough_space))  # Threshold for peak detection
            
            # Analyze detected lines
            detected_lines = list(zip(*hspace_peaks))
            
            print(f"[RIBFINDER] Scikit-image Hough transform detected {len(detected_lines)} lines")
            
            # Group lines by orientation to identify distinct ribs
            line_angles = [angle for _, angle, _ in detected_lines]
            
            # Group similar angles (within 10 degrees)
            angle_groups = []
            tolerance = np.pi / 18  # 10 degrees in radians
            
            for angle in line_angles:
                # Normalize angle to [0, pi)
                norm_angle = angle % np.pi
                
                # Find existing group or create new one
                grouped = False
                for group in angle_groups:
                    group_angle = group[0]
                    if abs(norm_angle - group_angle) < tolerance or abs(norm_angle - group_angle - np.pi) < tolerance:
                        group.append(norm_angle)
                        grouped = True
                        break
                
                if not grouped:
                    angle_groups.append([norm_angle])
            
            # Count distinct orientations (each represents a potential rib direction)
            num_orientations = len(angle_groups)
            
            print(f"[RIBFINDER] Scikit-image found {num_orientations} distinct line orientations")
            
            # Advanced geometric analysis using contour detection
            from skimage import measure
            contours = measure.find_contours(cleaned_edges, level=0.5)
            
            # Analyze main contour structure
            main_contour_length = 0
            main_contour = None
            
            for contour in contours:
                if len(contour) > main_contour_length:
                    main_contour_length = len(contour)
                    main_contour = contour
            
            # Analyze the main contour for corners/vertices
            if main_contour is not None and len(main_contour) > 10:
                # Simplify contour to find vertices
                from skimage.measure import approximate_polygon
                simplified = approximate_polygon(main_contour, tolerance=5)
                vertices = len(simplified) - 1  # Subtract 1 because first and last point are the same
                
                print(f"[RIBFINDER] Scikit-image contour analysis: {vertices} vertices detected")
                
                # Use vertex count to determine ribs
                if vertices >= 3:
                    # For bent iron: vertices - 1 = ribs (approximately)
                    # But we need to be smart about it
                    if vertices == 3:  # Triangle-like = L-shape = 2 ribs
                        contour_ribs = 2
                    elif vertices == 4:  # Rectangle-like could be L-shape (2) or U-shape (3)
                        # Use additional analysis
                        # Check if it's more square (U-shape) or rectangular (L-shape)
                        bbox = np.array([np.min(main_contour, axis=0), np.max(main_contour, axis=0)])
                        width = bbox[1][1] - bbox[0][1]  # width
                        height = bbox[1][0] - bbox[0][0]  # height
                        aspect_ratio = max(width, height) / max(min(width, height), 1)
                        
                        if aspect_ratio < 2.5:  # More square-ish = U-shape
                            contour_ribs = 3
                        else:  # More rectangular = L-shape  
                            contour_ribs = 2
                    elif vertices == 5:  # Pentagon-like = U-shape = 3 ribs
                        contour_ribs = 3
                    else:
                        contour_ribs = min(vertices - 1, 4)  # Cap at 4 ribs max
                else:
                    contour_ribs = 2  # Default fallback
            else:
                contour_ribs = 2  # Default fallback
            
            # Combine all methods for final decision
            print(f"[RIBFINDER] Scikit-image analysis summary:")
            print(f"  → Hough lines: {len(detected_lines)} detected")
            print(f"  → Line orientations: {num_orientations}")  
            print(f"  → Contour vertices: {vertices if 'vertices' in locals() else 'N/A'}")
            print(f"  → Contour suggested ribs: {contour_ribs}")
            
            # Decision logic: combine multiple methods
            method_votes = []
            
            # Vote from line orientations (each orientation suggests segments in that direction)
            if num_orientations == 2:  # Two orientations = likely L-shape (2 ribs)
                method_votes.append(2)
            elif num_orientations >= 3:  # Three+ orientations = likely U-shape or more complex
                method_votes.append(3)
            else:
                method_votes.append(2)  # Default to L-shape for single orientation
            
            # Vote from contour analysis
            method_votes.append(contour_ribs)
            
            # Vote from number of detected lines
            if len(detected_lines) <= 2:
                method_votes.append(2)  # Few lines = L-shape
            elif len(detected_lines) >= 3:
                method_votes.append(3)  # More lines = U-shape
            else:
                method_votes.append(2)
            
            # Take majority vote or average
            from collections import Counter
            vote_counts = Counter(method_votes)
            most_common_vote = vote_counts.most_common(1)[0][0]
            
            print(f"[RIBFINDER] Scikit-image method votes: {method_votes}")
            print(f"[RIBFINDER] Scikit-image final decision: {most_common_vote} ribs")
            
            return most_common_vote
                
        except Exception as e:
            print(f"[RIBFINDER] Scikit-image analysis failed: {e}")
            return None
    
    def count_ribs(self, image_path: str) -> Dict:
        """
        Count ribs in a bent iron drawing using both Google Vision and ChatGPT
        
        Args:
            image_path: Path to the drawing image
            
        Returns:
            Dictionary with rib count results including match percentage
        """
        try:
            # Check if file exists
            if not os.path.exists(image_path):
                return {"error": f"Image file not found: {image_path}"}
            
            # Prepare the image for analysis
            base64_image = self.encode_image(image_path)
            
            print(f"[RIBFINDER] Analyzing ribs in: {os.path.basename(image_path)}")
            
            # First, try Google Vision API if available
            google_vision_count = None
            if self.vision_client:
                print("[RIBFINDER] Using Google Vision API...")
                google_vision_count = self.analyze_with_google_vision(image_path)
                if google_vision_count:
                    print(f"[RIBFINDER] Google Vision detected: {google_vision_count} ribs")
            
            # Try OpenCV vertex detection
            print("[RIBFINDER] Using OpenCV vertex detection...")
            opencv_count = self.analyze_with_opencv_vertices(image_path)
            if opencv_count:
                print(f"[RIBFINDER] OpenCV detected: {opencv_count} ribs")
            
            # Try Scikit-image line detection
            print("[RIBFINDER] Using Scikit-image line detection...")
            scikit_count = self.analyze_with_scikit_image(image_path)
            if scikit_count:
                print(f"[RIBFINDER] Scikit-image detected: {scikit_count} ribs")
            
            # Then use ChatGPT Vision
            print("[RIBFINDER] Using ChatGPT Vision (GPT-4o)...")
            
            # Call premium GPT-4 Vision API
            response = self.client.chat.completions.create(
                model="gpt-4o",  # Premium model for best accuracy
                messages=[
                    {
                        "role": "system",
                        "content": """You are THE EXPERT in counting ribs in bent iron construction drawings.
                        
                        CRITICAL MISSION: Count the exact number of ribs (straight segments) in this drawing.
                        
                        **STEP-BY-STEP COUNTING METHOD**:
                        1. **Visual Inspection**: Look at the COMPLETE drawing from end to end
                        2. **Path Tracing**: Follow the iron path from one end to the other
                        3. **Segment Identification**: Identify each straight section
                        4. **Systematic Counting**: Count each straight segment as 1 rib
                        
                        **SHAPE-SPECIFIC COUNTING**:
                        - **L-shape**: 2 ribs (vertical + horizontal)
                        - **U-shape**: 3 ribs (left vertical + base + right vertical)  
                        - **Z-shape**: 3 ribs (first segment + middle + last segment)
                        - **Complex shapes**: Count every straight segment
                        
                        **CRITICAL RULES**:
                        - A rib = any straight segment between bends or ends
                        - If you see vertical segments on BOTH ends = U-shape = 3 ribs
                        - If you see vertical segment on ONE end = L-shape = 2 ribs
                        - Each bend separates ribs
                        
                        **VISUAL PATTERN GUIDE**:
                        - |___| pattern = 3 ribs (U-shape)
                        - |___ pattern = 2 ribs (L-shape)  
                        - ___| pattern = 2 ribs (L-shape)
                        - |___| with dimensions on both ends = definitely 3 ribs
                        
                        **DIMENSION CLUES**:
                        - If you see dimensions at both vertical ends = count both verticals as ribs
                        - Pattern like "20-405-20" indicates 3 segments = 3 ribs
                        
                        Return ONLY valid JSON:
                        {
                            "rib_count": number,
                            "shape_pattern": "description of what you see (e.g., 'vertical-horizontal-vertical')",
                            "confidence": number (0-100),
                            "reasoning": "brief explanation of counting method"
                        }"""
                    },
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "text",
                                "text": "Count the ribs (straight segments) in this bent iron drawing. Be extremely careful to count ALL segments. Look for vertical segments on both ends - if present, this indicates a U-shape with 3 ribs. Trace the complete path and count systematically."
                            },
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:image/jpeg;base64,{base64_image}",
                                    "detail": "high"  # Use high detail for accurate counting
                                }
                            }
                        ]
                    }
                ],
                max_tokens=300,
                temperature=0.1  # Very low for consistent counting
            )
            
            # Parse the response
            result_text = response.choices[0].message.content
            
            # Try to parse JSON from response
            try:
                # Remove markdown code blocks if present
                if "```json" in result_text:
                    result_text = result_text.split("```json")[1].split("```")[0]
                elif "```" in result_text:
                    result_text = result_text.split("```")[1].split("```")[0]
                
                result = json.loads(result_text.strip())
                result["status"] = "Rib counting complete"
                
            except json.JSONDecodeError:
                # If JSON parsing fails, try to extract number
                try:
                    # Look for number in response
                    import re
                    numbers = re.findall(r'\b(\d+)\b', result_text)
                    if numbers:
                        rib_count = int(numbers[0])
                        result = {
                            "rib_count": rib_count,
                            "shape_pattern": "extracted from text",
                            "confidence": 80,
                            "reasoning": "Extracted from text response",
                            "raw_response": result_text
                        }
                    else:
                        result = {
                            "rib_count": 0,
                            "shape_pattern": "unknown",
                            "confidence": 0,
                            "reasoning": "Failed to parse response",
                            "raw_response": result_text
                        }
                except:
                    result = {
                        "rib_count": 0,
                        "shape_pattern": "unknown", 
                        "confidence": 0,
                        "reasoning": "Complete parsing failure",
                        "raw_response": result_text
                    }
            
            # Get ChatGPT rib count
            chatgpt_count = result.get("rib_count", 0)
            print(f"[RIBFINDER] ChatGPT detected: {chatgpt_count} ribs")
            
            
            # Create list of available counts for analysis
            counts = {}
            if google_vision_count is not None:
                counts['google'] = google_vision_count
            if opencv_count is not None:
                counts['opencv'] = opencv_count
            if scikit_count is not None:
                counts['scikit'] = scikit_count
            counts['chatgpt'] = chatgpt_count
            
            # Claude Vision disabled by user request
            
            # Analyze agreement patterns among all available methods
            method_names = list(counts.keys())
            method_counts = list(counts.values())
            
            # Count how many methods agree on each value
            from collections import Counter
            count_frequency = Counter(method_counts)
            most_common_count, frequency = count_frequency.most_common(1)[0]
            
            total_methods = len(method_counts)
            agreement_percentage = (frequency / total_methods) * 100
            
            # Determine final result and confidence
            result["rib_count"] = most_common_count
            
            if frequency == total_methods:
                # Perfect agreement
                match_percentage = 100
                result["vision_agreement"] = "PERFECT_AGREEMENT"
                print(f"[RIBFINDER] ✓ PERFECT AGREEMENT: All {total_methods} methods detected {most_common_count} ribs")
                
            elif frequency >= (total_methods / 2):
                # Majority agreement
                match_percentage = int(agreement_percentage)
                result["vision_agreement"] = "MAJORITY_AGREEMENT"
                agreeing_methods = [method for method, count in counts.items() if count == most_common_count]
                print(f"[RIBFINDER] ✓ MAJORITY AGREEMENT: {', '.join(agreeing_methods)} agree on {most_common_count} ribs ({match_percentage}%)")
                
            else:
                # No clear majority - use ChatGPT as default
                result["rib_count"] = chatgpt_count
                match_percentage = 25  # Low confidence
                result["vision_agreement"] = "NO_MAJORITY"
                print(f"[RIBFINDER] ⚠ NO CLEAR MAJORITY: Using ChatGPT default ({chatgpt_count} ribs) with low confidence")
                
                # Show all disagreements
                method_details = [f"{method}={count}" for method, count in counts.items()]
                print(f"[RIBFINDER]   All results: {', '.join(method_details)}")
            
            # Store all counts for transparency
            if google_vision_count is not None:
                result["google_vision_count"] = google_vision_count
            if opencv_count is not None:
                result["opencv_count"] = opencv_count
            if scikit_count is not None:
                result["scikit_count"] = scikit_count
            result["chatgpt_count"] = chatgpt_count
            
            # Add match percentage to result
            result["match_percentage"] = match_percentage
            
            print(f"[RIBFINDER] Analysis complete - Match: {match_percentage}%")
            
            return result
            
        except Exception as e:
            return {"error": f"Rib counting failed: {str(e)}"}
    
    def validate_rib_count(self, image_path: str, expected_count: int = None) -> Dict:
        """
        Validate rib count with additional checks
        
        Args:
            image_path: Path to the drawing image
            expected_count: Expected rib count for validation
            
        Returns:
            Dictionary with validation results
        """
        result = self.count_ribs(image_path)
        
        if "error" not in result:
            rib_count = result.get("rib_count", 0)
            
            # Add validation logic
            if expected_count and rib_count != expected_count:
                print(f"[RIBFINDER] WARNING: Found {rib_count} ribs, expected {expected_count}")
                result["validation_warning"] = f"Count mismatch: found {rib_count}, expected {expected_count}"
            
            # Add confidence assessment
            confidence = result.get("confidence", 0)
            if confidence >= 90:
                result["quality"] = "EXCELLENT"
            elif confidence >= 70:
                result["quality"] = "GOOD"
            elif confidence >= 50:
                result["quality"] = "FAIR"
            else:
                result["quality"] = "POOR"
                
        return result
    
    def get_agent(self):
        """
        Return the AutoGen agent for integration with orchestrator
        
        Returns:
            AutoGen AssistantAgent
        """
        return self.agent


def create_rib_finder_agent(api_key):
    """
    Factory function to create a RibFinder agent
    
    Args:
        api_key: OpenAI API key
        
    Returns:
        RibFinderAgent instance
    """
    return RibFinderAgent(api_key)
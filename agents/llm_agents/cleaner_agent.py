"""
CLEANER Agent - Phase 2: Enhanced text detection and removal
Removes text, numbers, and annotations from bent iron drawings using advanced techniques
Outputs clean drawings with only the iron ribs visible
"""

import os
import cv2
import numpy as np
from typing import Dict, Optional, Tuple, List
import base64
from PIL import Image
from google.cloud import vision
from skimage import morphology

class CleanerAgent:
    def __init__(self):
        """Initialize the CLEANER agent with Phase 2 enhancements"""
        self.name = "CLEANER"
        
        # Initialize Google Vision API for text detection
        try:
            self.vision_client = vision.ImageAnnotatorClient()
            print("[CLEANER] Google Vision API initialized for text detection")
        except Exception as e:
            print(f"[CLEANER] Warning: Google Vision API failed to initialize: {e}")
            self.vision_client = None
            
        print("[CLEANER] Phase 2 Agent initialized - Enhanced drawing cleaning specialist")
        
    def clean_drawing(self, image_path: str, output_dir: str = "io/cleaned") -> Dict:
        """
        Main method to clean a drawing - removes text and keeps only ribs
        
        Args:
            image_path: Path to the original drawing
            output_dir: Directory to save cleaned images
            
        Returns:
            Dictionary with cleaned image path and processing info
        """
        try:
            print(f"[CLEANER] Processing: {os.path.basename(image_path)}")
            
            # Ensure output directory exists
            os.makedirs(output_dir, exist_ok=True)
            
            # Load image
            image = self._load_image(image_path)
            if image is None:
                return {"error": f"Failed to load image: {image_path}"}
            
            print(f"[CLEANER] Image loaded: {image.shape}")
            
            # Phase 2: Enhanced cleaning with text detection
            cleaned_image = self._clean_with_text_detection(image, image_path)
            
            # Generate output filename (sanitize special characters)
            base_name = os.path.splitext(os.path.basename(image_path))[0]
            # Replace problematic characters in filename
            base_name = base_name.replace('\u202f', ' ')  # Replace narrow no-break space
            base_name = base_name.replace(':', '_').replace('/', '_').replace('\\', '_')
            output_path = os.path.join(output_dir, f"{base_name}_cleaned.png")
            
            # Save cleaned image
            success = cv2.imwrite(output_path, cleaned_image)
            
            if success:
                print(f"[CLEANER] ✓ Cleaned image saved: {output_path}")
                
                # Calculate cleaning metrics
                metrics = self._calculate_metrics(image, cleaned_image)
                
                # Get detailed Phase 2 statistics
                text_regions = getattr(self, '_last_text_regions', [])
                dimension_lines = getattr(self, '_last_dimension_lines', [])
                
                return {
                    "status": "success",
                    "original_path": image_path,
                    "cleaned_path": output_path,
                    "cleaning_method": "phase2_enhanced",
                    "pixels_removed": metrics["pixels_removed"],
                    "cleaning_percentage": metrics["cleaning_percentage"],
                    "text_regions_detected": len(text_regions),
                    "dimension_lines_detected": len(dimension_lines),
                    "google_vision_used": self.vision_client is not None,
                    "output_size": os.path.getsize(output_path)
                }
            else:
                return {"error": "Failed to save cleaned image"}
                
        except Exception as e:
            print(f"[CLEANER] Error: {str(e)}")
            return {"error": f"Cleaning failed: {str(e)}"}
    
    def _load_image(self, image_path: str) -> Optional[np.ndarray]:
        """Load image with multiple fallback methods"""
        try:
            # Normalize path
            normalized_path = os.path.normpath(image_path)
            
            # Try standard OpenCV load
            image = cv2.imread(normalized_path)
            if image is not None:
                return image
            
            # Fallback: numpy approach
            with open(normalized_path, 'rb') as f:
                file_bytes = np.frombuffer(f.read(), dtype=np.uint8)
                image = cv2.imdecode(file_bytes, cv2.IMREAD_COLOR)
                
            if image is not None:
                return image
                
            # Fallback: PIL approach
            pil_image = Image.open(normalized_path)
            if pil_image.mode == 'RGBA':
                pil_image = pil_image.convert('RGB')
            image = np.array(pil_image)
            image = cv2.cvtColor(image, cv2.COLOR_RGB2BGR)
            
            return image
            
        except Exception as e:
            print(f"[CLEANER] Failed to load image: {e}")
            return None
    
    def _clean_with_text_detection(self, image: np.ndarray, image_path: str) -> np.ndarray:
        """
        Phase 2: Enhanced cleaning using text detection and intelligent line classification
        """
        print("[CLEANER] Starting Phase 2 enhanced cleaning...")
        
        # Step 1: Detect text regions using Google Vision
        text_regions = self._detect_text_regions(image_path)
        self._last_text_regions = text_regions
        
        # Step 2: Detect dimension lines and arrows
        dimension_lines = self._detect_dimension_lines(image)
        self._last_dimension_lines = dimension_lines
        
        # Step 3: Classify and preserve iron ribs
        iron_mask = self._extract_iron_ribs(image, text_regions, dimension_lines)
        
        # Step 4: Create final clean image
        cleaned_image = self._apply_advanced_cleaning(image, text_regions, dimension_lines, iron_mask)
        
        # Step 5: Normalize rib widths (remove small interferences)
        normalized_image = self._normalize_rib_widths(cleaned_image)
        
        return normalized_image
    
    def _detect_text_regions(self, image_path: str) -> List[Tuple]:
        """
        Use Google Vision API to detect all text regions with precise bounding boxes
        
        Returns:
            List of (x, y, width, height) tuples for text regions
        """
        text_regions = []
        
        if not self.vision_client:
            print("[CLEANER] Google Vision not available, using fallback text detection")
            return self._detect_text_fallback(image_path)
        
        try:
            print("[CLEANER] Phase 2.1: Using Google Vision for precise text detection")
            
            # Load image for Vision API
            with open(image_path, 'rb') as image_file:
                content = image_file.read()
            
            image_vision = vision.Image(content=content)
            response = self.vision_client.text_detection(image=image_vision)
            
            if response.error.message:
                raise Exception(f'{response.error.message}')
            
            texts = response.text_annotations
            
            if texts:
                # Skip the first annotation (full text) and process individual words/numbers
                for text in texts[1:]:  # Skip full text annotation
                    vertices = text.bounding_poly.vertices
                    
                    # Get bounding box coordinates
                    x_coords = [vertex.x for vertex in vertices]
                    y_coords = [vertex.y for vertex in vertices]
                    
                    x = min(x_coords)
                    y = min(y_coords)
                    width = max(x_coords) - x
                    height = max(y_coords) - y
                    
                    # Expand bounding box to ensure complete removal
                    margin = 5
                    x = max(0, x - margin)
                    y = max(0, y - margin)
                    width += 2 * margin
                    height += 2 * margin
                    
                    text_regions.append((x, y, width, height))
                    
                print(f"[CLEANER] Google Vision detected {len(text_regions)} text regions")
            else:
                print("[CLEANER] No text detected by Google Vision")
                
        except Exception as e:
            print(f"[CLEANER] Google Vision text detection failed: {e}")
            return self._detect_text_fallback(image_path)
        
        return text_regions
    
    def _detect_text_fallback(self, image_path: str) -> List[Tuple]:
        """
        Fallback text detection using OpenCV when Google Vision is unavailable
        """
        print("[CLEANER] Using OpenCV fallback for text detection")
        
        image = cv2.imread(image_path)
        if image is None:
            return []
        
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        
        # Use MSER (Maximally Stable Extremal Regions) for text detection
        mser = cv2.MSER_create(
            _min_area=50,
            _max_area=2000,
            _delta=5
        )
        
        regions, _ = mser.detectRegions(gray)
        text_regions = []
        
        for region in regions:
            x, y, w, h = cv2.boundingRect(region.reshape(-1, 1, 2))
            
            # Filter by aspect ratio and size to identify text-like regions
            aspect_ratio = w / h if h > 0 else 0
            if 0.1 < aspect_ratio < 10 and 100 < w * h < 5000:
                text_regions.append((x, y, w, h))
        
        print(f"[CLEANER] OpenCV fallback detected {len(text_regions)} potential text regions")
        return text_regions
    
    def _detect_dimension_lines(self, image: np.ndarray) -> List[Tuple]:
        """
        Phase 2.2: Detect dimension lines, arrows, and measurement annotations
        
        Returns:
            List of dimension line coordinates and types
        """
        print("[CLEANER] Phase 2.2: Detecting dimension lines and arrows")
        
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        dimension_lines = []
        
        # Detect thin lines (likely dimension lines)
        edges = cv2.Canny(gray, 50, 150, apertureSize=3)
        
        # Use Hough Lines with parameters tuned for thin dimension lines
        lines = cv2.HoughLinesP(
            edges, 
            rho=1, 
            theta=np.pi/180, 
            threshold=30,  # Lower threshold for thin lines
            minLineLength=20,  # Shorter minimum length
            maxLineGap=5
        )
        
        if lines is not None:
            for line in lines:
                x1, y1, x2, y2 = line[0]
                length = np.sqrt((x2-x1)**2 + (y2-y1)**2)
                
                # Classify line type based on characteristics
                line_type = self._classify_line_type(gray, x1, y1, x2, y2, length)
                
                if line_type == "dimension":
                    dimension_lines.append(("line", x1, y1, x2, y2))
        
        # Detect arrow heads (triangular shapes)
        arrow_heads = self._detect_arrows(gray)
        for arrow in arrow_heads:
            dimension_lines.append(("arrow", *arrow))
        
        print(f"[CLEANER] Detected {len(dimension_lines)} dimension elements")
        return dimension_lines
    
    def _classify_line_type(self, gray: np.ndarray, x1: int, y1: int, x2: int, y2: int, length: float) -> str:
        """
        Intelligent line classification to distinguish iron ribs from dimension lines
        """
        # Sample pixels along the line to check thickness
        num_samples = max(5, int(length // 10))
        thickness_samples = []
        
        for i in range(num_samples):
            t = i / (num_samples - 1)
            x = int(x1 + t * (x2 - x1))
            y = int(y1 + t * (y2 - y1))
            
            # Check perpendicular thickness at this point
            angle = np.arctan2(y2 - y1, x2 - x1)
            perp_angle = angle + np.pi/2
            
            # Sample perpendicular to line
            thickness = 0
            for offset in range(1, 10):
                px = int(x + offset * np.cos(perp_angle))
                py = int(y + offset * np.sin(perp_angle))
                
                if 0 <= px < gray.shape[1] and 0 <= py < gray.shape[0]:
                    if gray[py, px] < 200:  # Dark pixel (part of line)
                        thickness = offset
                    else:
                        break
                        
            thickness_samples.append(thickness)
        
        avg_thickness = np.mean(thickness_samples) if thickness_samples else 0
        
        # Classification criteria
        if avg_thickness > 3 and length > 50:
            return "iron_rib"  # Thick, long lines are likely iron
        elif avg_thickness <= 2 and length < 100:
            return "dimension"  # Thin, shorter lines are likely dimensions
        else:
            return "unknown"
    
    def _detect_arrows(self, gray: np.ndarray) -> List[Tuple]:
        """
        Detect arrow heads using template matching and contour analysis
        """
        arrows = []
        
        # Find small triangular contours (arrow heads)
        edges = cv2.Canny(gray, 50, 150)
        contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        for contour in contours:
            area = cv2.contourArea(contour)
            if 10 < area < 200:  # Small triangular shapes
                # Approximate contour
                epsilon = 0.02 * cv2.arcLength(contour, True)
                approx = cv2.approxPolyDP(contour, epsilon, True)
                
                # Check if it's triangular (3-4 vertices) and small
                if len(approx) in [3, 4]:
                    x, y, w, h = cv2.boundingRect(approx)
                    arrows.append((x, y, w, h))
        
        return arrows
    
    def _extract_iron_ribs(self, image: np.ndarray, text_regions: List, dimension_lines: List) -> np.ndarray:
        """
        Conservative iron extraction - preserve original iron, only remove text
        """
        print("[CLEANER] Phase 2.2: Conservative iron extraction")
        
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        
        # Create a conservative text-only removal mask
        text_only_mask = np.zeros(gray.shape, dtype=np.uint8)
        
        # Only mask text regions (be very conservative with dimensions)
        for x, y, w, h in text_regions:
            # Make text mask slightly smaller to avoid iron damage
            margin = 2
            x_safe = x + margin
            y_safe = y + margin  
            w_safe = max(1, w - 2*margin)
            h_safe = max(1, h - 2*margin)
            cv2.rectangle(text_only_mask, (x_safe, y_safe), (x_safe+w_safe, y_safe+h_safe), 255, -1)
        
        # Start with original image thresholding (preserve as much as possible)
        # Use only conservative threshold to maintain iron structure
        _, iron_thresh = cv2.threshold(gray, 180, 255, cv2.THRESH_BINARY_INV)
        
        # Remove ONLY text areas from the iron (not dimension lines)
        iron_mask = cv2.bitwise_and(iron_thresh, cv2.bitwise_not(text_only_mask))
        
        # Minimal cleanup - just connect obvious breaks
        kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (2, 2))
        iron_mask = cv2.morphologyEx(iron_mask, cv2.MORPH_CLOSE, kernel, iterations=1)
        
        # Fill small holes only
        kernel_small = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3, 3))
        iron_mask = cv2.morphologyEx(iron_mask, cv2.MORPH_CLOSE, kernel_small, iterations=1)
        
        print(f"[CLEANER] Conservative extraction - preserving maximum iron structure")
        
        return iron_mask
    
    def _apply_advanced_cleaning(self, image: np.ndarray, text_regions: List, dimension_lines: List, iron_mask: np.ndarray) -> np.ndarray:
        """
        Apply conservative cleaning - preserve as much original structure as possible
        """
        print("[CLEANER] Phase 2: Applying conservative cleaning")
        
        # Method 1: Try minimal intervention approach
        result = self._apply_minimal_cleaning(image, text_regions)
        
        # Check if minimal cleaning was sufficient
        text_remaining = self._check_text_removal(result, text_regions)
        
        if text_remaining < 0.3:  # Less than 30% text remaining
            print("[CLEANER] Minimal cleaning successful")
            return result
        else:
            print("[CLEANER] Minimal cleaning insufficient, using mask approach")
            # Fallback to mask approach but with enhanced preservation
            return self._apply_mask_cleaning(image, iron_mask)
    
    def _apply_minimal_cleaning(self, image: np.ndarray, text_regions: List) -> np.ndarray:
        """
        Minimal intervention - only remove text, preserve everything else
        """
        result = image.copy()
        
        # For each text region, use inpainting to remove text
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        
        for x, y, w, h in text_regions:
            # Create mask for this text region only
            text_mask = np.zeros(gray.shape, dtype=np.uint8)
            cv2.rectangle(text_mask, (x, y), (x+w, y+h), 255, -1)
            
            # Use inpainting to fill the text region
            try:
                gray_inpainted = cv2.inpaint(gray, text_mask, 3, cv2.INPAINT_TELEA)
                result_gray = cv2.cvtColor(result, cv2.COLOR_BGR2GRAY)
                result_gray[text_mask > 0] = gray_inpainted[text_mask > 0]
                result = cv2.cvtColor(result_gray, cv2.COLOR_GRAY2BGR)
            except:
                # Fallback: fill with white
                result[text_mask > 0] = 255
        
        return result
    
    def _apply_mask_cleaning(self, image: np.ndarray, iron_mask: np.ndarray) -> np.ndarray:
        """
        Mask-based cleaning but with better preservation
        """
        # Create white background
        result = np.ones_like(image) * 255
        
        # Apply iron mask
        iron_mask_3ch = cv2.cvtColor(iron_mask, cv2.COLOR_GRAY2BGR)
        result[iron_mask_3ch > 0] = 0
        
        return result
    
    def _check_text_removal(self, image: np.ndarray, text_regions: List) -> float:
        """
        Check how much text remains in the cleaned image
        Returns ratio of remaining text (0.0 = all removed, 1.0 = none removed)
        """
        if not text_regions:
            return 0.0
        
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        
        total_text_pixels = 0
        remaining_text_pixels = 0
        
        for x, y, w, h in text_regions:
            region = gray[y:y+h, x:x+w]
            total_text_pixels += region.size
            # Count dark pixels (likely remaining text)
            remaining_text_pixels += np.sum(region < 200)
        
        if total_text_pixels == 0:
            return 0.0
        
        return remaining_text_pixels / total_text_pixels
    
    def _clean_with_opencv(self, image: np.ndarray) -> np.ndarray:
        """
        Basic OpenCV cleaning - Phase 1 implementation
        Removes text while preserving iron rib lines
        """
        print("[CLEANER] Starting OpenCV cleaning process...")
        
        # Convert to grayscale
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        
        # Step 1: Detect main iron lines (thick, continuous)
        # Apply bilateral filter to reduce noise while keeping edges
        filtered = cv2.bilateralFilter(gray, 9, 75, 75)
        
        # Adaptive threshold to get binary image
        binary = cv2.adaptiveThreshold(
            filtered, 255, 
            cv2.ADAPTIVE_THRESH_GAUSSIAN_C, 
            cv2.THRESH_BINARY_INV, 
            11, 2
        )
        
        # Step 2: Morphological operations to isolate iron ribs
        # Use larger kernel for horizontal/vertical lines (iron ribs)
        kernel_size = 3
        kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (kernel_size, kernel_size))
        
        # Close gaps in lines
        closed = cv2.morphologyEx(binary, cv2.MORPH_CLOSE, kernel, iterations=2)
        
        # Remove small noise (text/numbers are usually smaller)
        cleaned = cv2.morphologyEx(closed, cv2.MORPH_OPEN, kernel, iterations=1)
        
        # Step 3: Find and filter contours
        contours, _ = cv2.findContours(cleaned, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        # Create mask for iron ribs only
        mask = np.zeros_like(gray)
        
        # Filter contours by size and aspect ratio
        for contour in contours:
            area = cv2.contourArea(contour)
            if area < 50:  # Skip small contours (likely text/noise)
                continue
                
            # Get bounding box
            x, y, w, h = cv2.boundingRect(contour)
            aspect_ratio = max(w, h) / min(w, h) if min(w, h) > 0 else 1
            
            # Iron ribs are typically long and thin
            if aspect_ratio > 3 or area > 500:
                cv2.drawContours(mask, [contour], -1, 255, -1)
        
        # Step 4: Apply additional filtering for line detection
        # Detect lines using HoughLinesP
        lines = cv2.HoughLinesP(
            mask, 1, np.pi/180, 
            threshold=50, 
            minLineLength=30, 
            maxLineGap=10
        )
        
        # Create final clean image
        result = np.ones_like(image) * 255  # White background
        
        if lines is not None:
            # Draw detected lines (iron ribs) in black
            for line in lines:
                x1, y1, x2, y2 = line[0]
                cv2.line(result, (x1, y1), (x2, y2), (0, 0, 0), 2)
        
        # Alternative: use the filtered mask directly
        if lines is None or len(lines) < 2:
            print("[CLEANER] Using contour-based approach")
            # Convert mask to 3-channel
            mask_3ch = cv2.cvtColor(mask, cv2.COLOR_GRAY2BGR)
            # Invert to get black lines on white background
            result = cv2.bitwise_not(mask_3ch)
        
        print(f"[CLEANER] Cleaning complete - Found {len(lines) if lines is not None else 0} line segments")
        
        return result
    
    def _calculate_metrics(self, original: np.ndarray, cleaned: np.ndarray) -> Dict:
        """Calculate cleaning metrics"""
        try:
            # Convert to grayscale for comparison
            orig_gray = cv2.cvtColor(original, cv2.COLOR_BGR2GRAY)
            clean_gray = cv2.cvtColor(cleaned, cv2.COLOR_BGR2GRAY)
            
            # Count non-white pixels (content)
            orig_content = np.sum(orig_gray < 250)
            clean_content = np.sum(clean_gray < 250)
            
            pixels_removed = max(0, orig_content - clean_content)
            cleaning_percentage = (pixels_removed / orig_content * 100) if orig_content > 0 else 0
            
            return {
                "pixels_removed": int(pixels_removed),
                "cleaning_percentage": round(cleaning_percentage, 2)
            }
        except:
            return {
                "pixels_removed": 0,
                "cleaning_percentage": 0
            }
    
    def validate_cleaning(self, cleaned_path: str) -> Dict:
        """
        Validate the quality of cleaning
        Check if text is removed and ribs are preserved
        """
        try:
            image = cv2.imread(cleaned_path)
            if image is None:
                return {"valid": False, "reason": "Cannot load cleaned image"}
            
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            
            # Check for presence of lines (ribs should be present)
            edges = cv2.Canny(gray, 50, 150)
            line_pixels = np.sum(edges > 0)
            
            if line_pixels < 100:
                return {"valid": False, "reason": "Too few lines detected - ribs might be lost"}
            
            # Basic validation passed
            return {
                "valid": True,
                "line_pixels": int(line_pixels),
                "quality": "GOOD" if line_pixels > 500 else "FAIR"
            }
            
        except Exception as e:
            return {"valid": False, "reason": str(e)}
    
    def _normalize_rib_widths(self, image: np.ndarray) -> np.ndarray:
        """
        Phase 2.5: Normalize rib widths and remove small interferences
        Makes all ribs uniform thickness by removing small bumps and inconsistencies
        
        Args:
            image: Cleaned image with ribs
            
        Returns:
            Image with normalized rib widths
        """
        print("[CLEANER] Phase 2.5: Normalizing rib widths and removing interferences")
        
        # Convert to grayscale for processing
        if len(image.shape) == 3:
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        else:
            gray = image.copy()
        
        # Create binary image (iron ribs are dark)
        _, binary = cv2.threshold(gray, 200, 255, cv2.THRESH_BINARY_INV)
        
        # Step 1: Find the skeleton of ribs to identify centerlines
        skeleton = morphology.skeletonize(binary > 0).astype(np.uint8) * 255
        
        # Step 2: Detect main rib lines using Hough transform
        lines = cv2.HoughLinesP(
            skeleton,
            rho=1,
            theta=np.pi/180,
            threshold=20,
            minLineLength=30,
            maxLineGap=10
        )
        
        if lines is None or len(lines) == 0:
            print("[CLEANER] No lines detected for normalization, returning original")
            return image
        
        # Step 3: Analyze existing rib widths to determine target width
        target_width = self._calculate_target_rib_width(binary, lines)
        print(f"[CLEANER] Target rib width determined: {target_width} pixels")
        
        # Step 4: Create normalized ribs image
        normalized = self._create_normalized_ribs(lines, gray.shape, target_width)
        
        # Step 5: Post-process to smooth connections
        normalized = self._smooth_rib_connections(normalized)
        
        # Convert back to 3-channel if needed
        if len(image.shape) == 3:
            normalized = cv2.cvtColor(normalized, cv2.COLOR_GRAY2BGR)
        
        print("[CLEANER] Rib width normalization complete")
        return normalized
    
    def _calculate_target_rib_width(self, binary: np.ndarray, lines: np.ndarray) -> int:
        """
        Calculate the target width for rib normalization by analyzing existing ribs
        
        Args:
            binary: Binary image with ribs
            lines: Detected lines from Hough transform
            
        Returns:
            Target width in pixels
        """
        width_samples = []
        
        for line in lines[:10]:  # Sample first 10 lines to avoid processing too many
            x1, y1, x2, y2 = line[0]
            
            # Calculate line direction and perpendicular
            line_vec = np.array([x2 - x1, y2 - y1])
            line_length = np.linalg.norm(line_vec)
            
            if line_length < 1:
                continue
                
            # Normalize line direction
            line_dir = line_vec / line_length
            perp_dir = np.array([-line_dir[1], line_dir[0]])
            
            # Sample width at multiple points along the line
            num_samples = max(3, int(line_length // 20))
            for i in range(num_samples):
                t = i / max(1, num_samples - 1)
                sample_x = int(x1 + t * (x2 - x1))
                sample_y = int(y1 + t * (y2 - y1))
                
                # Measure perpendicular width at this point
                width = self._measure_width_at_point(binary, sample_x, sample_y, perp_dir)
                if width > 0:
                    width_samples.append(width)
        
        if not width_samples:
            return 3  # Default width
        
        # Use median width as target to avoid outliers
        target_width = max(2, int(np.median(width_samples)))
        return min(target_width, 8)  # Cap at reasonable maximum
    
    def _measure_width_at_point(self, binary: np.ndarray, x: int, y: int, perp_dir: np.ndarray) -> int:
        """
        Measure the width of a rib at a specific point in perpendicular direction
        
        Args:
            binary: Binary image
            x, y: Point to measure from
            perp_dir: Perpendicular direction vector
            
        Returns:
            Width in pixels
        """
        if not (0 <= x < binary.shape[1] and 0 <= y < binary.shape[0]):
            return 0
        
        if binary[y, x] == 0:  # Not on a rib
            return 0
        
        width = 0
        max_search = 15
        
        # Search in both perpendicular directions
        for direction in [-1, 1]:
            for offset in range(1, max_search):
                px = int(x + direction * offset * perp_dir[0])
                py = int(y + direction * offset * perp_dir[1])
                
                if not (0 <= px < binary.shape[1] and 0 <= py < binary.shape[0]):
                    break
                
                if binary[py, px] > 0:  # Still on rib
                    width += 1
                else:
                    break
        
        return width
    
    def _create_normalized_ribs(self, lines: np.ndarray, image_shape: Tuple, target_width: int) -> np.ndarray:
        """
        Create a new image with normalized width ribs
        
        Args:
            lines: Detected lines
            image_shape: Shape of output image
            target_width: Target width for all ribs
            
        Returns:
            Image with normalized ribs
        """
        # Create white background
        result = np.ones(image_shape, dtype=np.uint8) * 255
        
        # Draw each line with consistent width
        for line in lines:
            x1, y1, x2, y2 = line[0]
            
            # Draw line with target thickness
            cv2.line(result, (x1, y1), (x2, y2), 0, thickness=target_width)
        
        return result
    
    def _smooth_rib_connections(self, image: np.ndarray) -> np.ndarray:
        """
        Smooth connections between rib segments to create natural joints
        
        Args:
            image: Image with normalized ribs
            
        Returns:
            Image with smoothed connections
        """
        # Apply minimal morphological operations to smooth connections
        kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3, 3))
        
        # Convert to binary for morphology
        _, binary = cv2.threshold(image, 128, 255, cv2.THRESH_BINARY_INV)
        
        # Close small gaps
        smoothed = cv2.morphologyEx(binary, cv2.MORPH_CLOSE, kernel, iterations=1)
        
        # Convert back to grayscale
        result = cv2.bitwise_not(smoothed)
        
        return result
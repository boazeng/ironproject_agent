import os
import json
import base64
from typing import Dict, List, Optional
from datetime import datetime
from pathlib import Path
from openai import OpenAI
from PIL import Image, ImageDraw, ImageFont
import io
import cv2
import numpy as np
from dotenv import load_dotenv

class Shape1S2Agent:
    """
    Shape Detection Agent using ChatGPT Vision API
    Analyzes shapes in images and extracts rib lengths and angles
    """

    def __init__(self, input_dir: str = None, output_dir: str = None):
        """
        Initialize the Shape1S2 Agent

        Args:
            input_dir: Directory containing input images
            output_dir: Directory to save analysis results
        """
        load_dotenv()

        self.input_dir = input_dir or r"C:\Users\User\Aiprojects\Iron-Projects\Agents\io\temp_shape"
        self.output_dir = output_dir or r"C:\Users\User\Aiprojects\Iron-Projects\Agents\io\temp_shape"

        # Initialize OpenAI client
        api_key = os.getenv('OPENAI_API_KEY')
        if not api_key:
            raise ValueError("OPENAI_API_KEY not found in environment variables")

        self.client = OpenAI(api_key=api_key)
        self.model = "gpt-4o"  # Updated model that supports vision

        # Create directories if they don't exist
        Path(self.input_dir).mkdir(parents=True, exist_ok=True)
        Path(self.output_dir).mkdir(parents=True, exist_ok=True)

    def encode_image(self, image_path: str) -> str:
        """
        Encode image to base64 string for API request

        Args:
            image_path: Path to the image file

        Returns:
            Base64 encoded string of the image
        """
        try:
            with open(image_path, "rb") as image_file:
                return base64.b64encode(image_file.read()).decode('utf-8')
        except Exception as e:
            print(f"Error encoding image: {str(e)}")
            raise

    def detect_lines_with_opencv(self, image_path: str) -> int:
        """
        Use OpenCV to detect the number of drawn lines before calling ChatGPT

        Args:
            image_path: Path to the image file

        Returns:
            Number of detected drawn lines
        """
        try:
            # Load the image
            cv_img = cv2.imread(image_path)
            if cv_img is None:
                print(f"Could not load image: {image_path}")
                return 0

            # Convert to grayscale
            gray = cv2.cvtColor(cv_img, cv2.COLOR_BGR2GRAY)

            # Apply threshold to get black lines
            _, thresh = cv2.threshold(gray, 127, 255, cv2.THRESH_BINARY_INV)

            # Use Hough line detection to find actual drawn lines
            edges = cv2.Canny(gray, 50, 150)
            lines = cv2.HoughLinesP(edges, 1, np.pi/180, threshold=30, minLineLength=20, maxLineGap=5)

            detected_lines = len(lines) if lines is not None else 0

            # Filter out very similar lines (parallel and close together)
            if lines is not None and len(lines) > 0:
                unique_lines = []
                for line in lines:
                    x1, y1, x2, y2 = line[0]
                    is_unique = True

                    for existing in unique_lines:
                        ex1, ey1, ex2, ey2 = existing[0]
                        # Check if lines are very similar (same direction and close)
                        if (abs(x1-ex1) < 10 and abs(y1-ey1) < 10 and
                            abs(x2-ex2) < 10 and abs(y2-ey2) < 10):
                            is_unique = False
                            break

                    if is_unique:
                        unique_lines.append(line)

                detected_lines = len(unique_lines)

            raw_count = len(lines) if lines is not None else 0
            print(f"OpenCV detected: {raw_count} raw lines -> {detected_lines} unique drawn lines")

            return detected_lines

        except Exception as e:
            print(f"Error in OpenCV line detection: {str(e)}")
            return 0

    def create_analysis_prompt(self, detected_lines: int = None) -> str:
        """
        Create a simplified prompt for ChatGPT to analyze shapes

        Returns:
            Formatted prompt string
        """
        line_info = f"\n\nIMPORTANT: OpenCV pre-analysis detected {detected_lines} drawn lines in this image. Please confirm this count and provide the measurements for exactly {detected_lines} drawn lines." if detected_lines else ""

        prompt = f"""IMPORTANT: Analyze the image directly and return the actual data, not code or instructions.

The image contains engineering shapes made of straight drawn lines.
The information is encoded in two ways:
1. Drawn lines – the visible black lines forming the shape.
2. Numbers – indicating either:
   - The line length (in millimeters), written next to a line.
   - The angle between two lines (if given explicitly).{line_info}
________________________________________
Your Tasks
1. Detect all drawn lines in the image
   - Identify each visible black line segment that is actually drawn.
   - Count only the lines that are physically drawn, not implied or missing lines.
2. Count the number of drawn lines
   - Return the actual total count of drawn lines from this specific image.
   - Cross-check with the OpenCV pre-analysis if provided.
3. Extract line lengths
   - For each drawn line, read the length number written near it (in millimeters).
   - Associate each line with its detected length value.
4. Extract angles
   - For each junction between two drawn lines:
     • If an angle number is written, return that specific number.
     • If no number is written but the angle appears to be 90°, mark it as 90°.
     • If not determinable, return "unknown".
________________________________________
IMPORTANT:
• Look at the actual image and extract the real values.
• Count ONLY the black lines that are actually drawn (visible).
• Do NOT count missing or implied lines.
• Do NOT provide code or processing steps.
• Return the actual measurements and counts from THIS image.

Output format in JSON:
{{
    "total_lines": number,
    "lines": [
        {{
            "line_number": 1,
            "length": number (in mm),
            "angle_to_next": number or "90°" or "unknown"
        }},
        {{
            "line_number": 2,
            "length": number (in mm),
            "angle_to_next": number or "90°" or "unknown"
        }}
    ]
}}

Output Requirements:
1. Return the JSON data as specified above
2. Also create an annotated version of the image with:
   - Green lines overlaid on each detected drawn line
   - Length labels next to each line
   - Angle labels at each junction
3. Return both the JSON data and indicate that an annotated image should be created"""

        return prompt

    def analyze_shape(self, image_path: str) -> Dict:
        """
        Analyze a shape image using ChatGPT Vision API

        Args:
            image_path: Path to the shape image

        Returns:
            Dictionary containing the analysis results
        """
        if not os.path.exists(image_path):
            return {"error": f"Image file not found: {image_path}"}

        try:
            # First, use OpenCV to detect the number of drawn lines
            detected_lines = self.detect_lines_with_opencv(image_path)

            # Encode the image
            base64_image = self.encode_image(image_path)

            # Create the analysis prompt with detected line count
            prompt = self.create_analysis_prompt(detected_lines)

            # Call ChatGPT Vision API
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": prompt},
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:image/jpeg;base64,{base64_image}"
                                }
                            }
                        ]
                    }
                ],
                max_tokens=2000,
                temperature=0.2  # Lower temperature for more consistent analysis
            )

            # Extract and parse the response
            content = response.choices[0].message.content

            # Try to extract JSON from the response
            try:
                # Find JSON content in the response
                import re
                json_match = re.search(r'\{.*\}', content, re.DOTALL)
                if json_match:
                    analysis_result = json.loads(json_match.group())
                else:
                    # If no JSON found, create a structured response
                    analysis_result = {
                        "raw_response": content,
                        "error": "Could not parse JSON from response"
                    }
            except json.JSONDecodeError:
                analysis_result = {
                    "raw_response": content,
                    "error": "Invalid JSON in response"
                }

            # Add metadata
            analysis_result["metadata"] = {
                "image_path": image_path,
                "image_name": Path(image_path).name,
                "timestamp": datetime.now().isoformat(),
                "model_used": self.model,
                "agent": "shape1s2",
                "opencv_detected_lines": detected_lines
            }

            return analysis_result

        except Exception as e:
            return {
                "error": f"Analysis failed: {str(e)}",
                "image_path": image_path,
                "timestamp": datetime.now().isoformat()
            }

    def create_annotated_image(self, image_path: str, analysis_results: Dict) -> str:
        """
        Create an annotated image with green lines on ribs and labels

        Args:
            image_path: Path to the original image
            analysis_results: Analysis results from ChatGPT

        Returns:
            Path to the saved annotated image
        """
        try:
            # Load the image using OpenCV for line detection
            cv_img = cv2.imread(image_path)
            if cv_img is None:
                print(f"Could not load image: {image_path}")
                return None

            # Convert to grayscale for line detection
            gray = cv2.cvtColor(cv_img, cv2.COLOR_BGR2GRAY)

            # Apply threshold to get black lines
            _, thresh = cv2.threshold(gray, 127, 255, cv2.THRESH_BINARY_INV)

            # Find contours (which represent the lines/ribs)
            contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

            # Draw green lines over the detected contours
            contour_count = 0
            for contour in contours:
                # Only draw contours that are likely to be ribs (reasonable size)
                area = cv2.contourArea(contour)
                if area > 50:  # Reduced threshold to catch more lines
                    cv2.drawContours(cv_img, [contour], -1, (0, 255, 0), 3)
                    contour_count += 1

            # Also try Hough line detection for straight lines
            edges = cv2.Canny(gray, 50, 150)
            lines = cv2.HoughLinesP(edges, 1, np.pi/180, threshold=30, minLineLength=20, maxLineGap=5)

            line_count = 0
            if lines is not None:
                for line in lines:
                    x1, y1, x2, y2 = line[0]
                    cv2.line(cv_img, (x1, y1), (x2, y2), (0, 255, 0), 3)
                    line_count += 1

            print(f"Detected {contour_count} contours and {line_count} Hough lines")

            # Convert back to PIL for text annotation
            cv_img_rgb = cv2.cvtColor(cv_img, cv2.COLOR_BGR2RGB)
            img = Image.fromarray(cv_img_rgb)
            draw = ImageDraw.Draw(img)

            # Try to use a font, fall back to default if not available
            try:
                font = ImageFont.truetype("arial.ttf", 20)
            except:
                font = ImageFont.load_default()

            # If we have rib data, draw text annotations
            if "ribs" in analysis_results and analysis_results["ribs"]:
                y_offset = 30

                # Draw title
                draw.text((10, 10), f"Total Ribs: {analysis_results.get('total_ribs', 0)}",
                         fill="green", font=font)

                # Draw rib information
                for rib in analysis_results["ribs"]:
                    rib_num = rib.get("rib_number", "?")
                    length = rib.get("length", "?")
                    angle = rib.get("angle_to_next", "?")

                    text = f"Rib {rib_num}: {length}mm, Angle: {angle}"
                    draw.text((10, y_offset + (rib_num * 25)), text, fill="green", font=font)

            # Create output filename for annotated image (no timestamp)
            output_filename = f"annotated_{Path(image_path).stem}.png"
            output_path = os.path.join(self.output_dir, output_filename)

            # Delete old annotated image if it exists
            if os.path.exists(output_path):
                os.remove(output_path)
                print(f"Deleted old annotated image: {output_path}")

            # Save the annotated image
            img.save(output_path)
            print(f"Annotated image saved to: {output_path}")

            return output_path

        except Exception as e:
            print(f"Error creating annotated image: {str(e)}")
            return None

    def save_results(self, results: Dict, image_name: str) -> str:
        """
        Save analysis results to JSON file

        Args:
            results: Analysis results dictionary
            image_name: Name of the analyzed image

        Returns:
            Path to the saved JSON file
        """
        # Create output filename (no timestamp)
        output_filename = f"shape_analysis_{Path(image_name).stem}.json"
        output_path = os.path.join(self.output_dir, output_filename)

        # Delete old JSON file if it exists
        if os.path.exists(output_path):
            os.remove(output_path)
            print(f"Deleted old JSON file: {output_path}")

        # Save results as JSON
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, ensure_ascii=False)

        print(f"Results saved to: {output_path}")
        return output_path

    def process_image(self, image_name: str = None) -> Dict:
        """
        Process a shape image from the temp_shape folder

        Args:
            image_name: Name of the image file. If None, processes the first image found

        Returns:
            Complete analysis results with saved file path
        """
        # If no specific image provided, find the first image in the folder
        if image_name is None:
            image_files = []
            for ext in ['.jpg', '.jpeg', '.png', '.bmp', '.gif']:
                image_files.extend(Path(self.input_dir).glob(f'*{ext}'))
                image_files.extend(Path(self.input_dir).glob(f'*{ext.upper()}'))

            if not image_files:
                return {"error": f"No image files found in {self.input_dir}"}

            image_path = str(image_files[0])
            image_name = image_files[0].name
        else:
            image_path = os.path.join(self.input_dir, image_name)

            # Check if file exists, try with common extensions if not
            if not os.path.exists(image_path):
                for ext in ['.jpg', '.jpeg', '.png', '.bmp']:
                    test_path = f"{image_path}{ext}"
                    if os.path.exists(test_path):
                        image_path = test_path
                        image_name = Path(test_path).name
                        break
                else:
                    return {"error": f"Image file not found: {image_path}"}

        print(f"Processing shape image: {image_path}")

        # Analyze the shape
        results = self.analyze_shape(image_path)

        # Save results
        if "error" not in results or results.get("raw_response"):
            output_path = self.save_results(results, image_name)
            results["output_file"] = output_path

            # Create annotated image if analysis was successful
            if "total_ribs" in results:
                annotated_path = self.create_annotated_image(image_path, results)
                if annotated_path:
                    results["annotated_image"] = annotated_path

            # Print summary
            if "error" not in results:
                if "total_lines" in results:
                    print(f"Successfully analyzed shape")
                    print(f"Found {results.get('total_lines', 0)} drawn lines")
                elif "total_ribs" in results:  # Fallback for old format
                    print(f"Successfully analyzed shape")
                    print(f"Found {results.get('total_ribs', 0)} ribs")
            else:
                print(f"Analysis completed with notes: {results.get('error', '')}")
        else:
            print(f"Error: {results['error']}")

        return results

    def batch_process(self) -> List[Dict]:
        """
        Process all images in the temp_shape folder

        Returns:
            List of analysis results for all images
        """
        results = []

        # Find all image files
        image_files = []
        for ext in ['.jpg', '.jpeg', '.png', '.bmp', '.gif']:
            image_files.extend(Path(self.input_dir).glob(f'*{ext}'))
            image_files.extend(Path(self.input_dir).glob(f'*{ext.upper()}'))

        if not image_files:
            print(f"No image files found in {self.input_dir}")
            return results

        print(f"Found {len(image_files)} images to process")

        # Process each image
        for i, image_file in enumerate(image_files, 1):
            print(f"\nProcessing image {i}/{len(image_files)}: {image_file.name}")
            result = self.process_image(image_file.name)
            results.append(result)

        # Save batch summary
        summary = {
            "total_processed": len(results),
            "successful": sum(1 for r in results if "error" not in r),
            "failed": sum(1 for r in results if "error" in r and not r.get("raw_response")),
            "timestamp": datetime.now().isoformat(),
            "results": results
        }

        summary_path = os.path.join(self.output_dir, f"batch_analysis_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json")
        with open(summary_path, 'w', encoding='utf-8') as f:
            json.dump(summary, f, indent=2, ensure_ascii=False)

        print(f"\nBatch processing complete. Summary saved to: {summary_path}")
        return results


# Test function
def test_agent():
    """Test the Shape1S2 Agent"""
    print("Initializing Shape1S2 Agent...")

    try:
        agent = Shape1S2Agent()
        print("Agent initialized successfully")

        # Process any image in the temp_shape folder
        results = agent.process_image()

        if results:
            print("\nAnalysis Results:")
            print(json.dumps(results, indent=2, ensure_ascii=False))

        return results

    except Exception as e:
        print(f"Error during test: {str(e)}")
        return None


if __name__ == "__main__":
    test_agent()
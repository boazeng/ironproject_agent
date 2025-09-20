import base64
import json
import os
import logging
import cv2
import numpy as np
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

class Form1S2Agent:
    def __init__(self):
        self.name = "form1s2"
        self.api_key = os.getenv('OPENAI_API_KEY')
        if not self.api_key:
            logger.error(f"[{self.name.upper()}] OpenAI API key not found")
            raise ValueError("OpenAI API key not configured")

        self.client = OpenAI(api_key=self.api_key)

        self.PROMPT = """You are given an image of a steel order form in a predefined format ("Format 1").

The order form contains two sections:
1. A header with general metadata (project name, order number, contact person, etc.).
2. A structured table of order items.

Your task is to detect the **full outer boundary of the table**, including:
- The **table header row** (column titles)
- All the **order item rows**

Detection Instructions:
You must detect the table **based on its visible horizontal and vertical lines** (grid structure). **Do not rely on visual estimation or hardcoded coordinates.**
Use **OpenCV-based image processing** for precise detection.

Processing Steps:
1. Convert the image to **grayscale**
2. Apply **adaptive thresholding** to enhance contrast
3. Use **morphological operations** to extract horizontal and vertical lines separately
4. Combine the lines to form a **binary mask** of the table
5. Use cv2.findContours to detect the **largest outer rectangle** enclosing the table grid
6. Create the 4 point of the table coordination
7. Draw a red rectangle on the original image to represent the detected boundary

Output Requirements:
- The red rectangle must:
  - Match the **actual table borders** precisely (no visual guesswork)
  - Include the table header row and all item rows
  - **Not include whitespace**, extra margins, or anything outside the grid
  - Be drawn directly over the real grid lines of the table

- The output should be:
  - A single image showing the original input with the **red bounding box** clearly marked
  - No explanations or debug overlays  only the red box output is needed

Final output:
return the rectangular coordination x,y
return a base64 file"""

    def detect_table_boundary_opencv(self, image_path: str):
        """
        Detect table boundary using OpenCV following the exact specifications:
        1. Convert to grayscale
        2. Apply adaptive thresholding
        3. Use morphological operations to extract lines
        4. Combine lines to form binary mask
        5. Use cv2.findContours to detect largest outer rectangle
        6. Return coordinates and image with red rectangle
        """
        try:
            logger.info(f"[{self.name.upper()}] Starting OpenCV table detection: {image_path}")

            # Load the image
            image = cv2.imread(image_path)
            if image is None:
                logger.error(f"[{self.name.upper()}] Failed to load image: {image_path}")
                return None, None

            original = image.copy()
            height, width = image.shape[:2]

            # Step 1: Convert to grayscale
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            logger.info(f"[{self.name.upper()}] Converted to grayscale")

            # Step 2: Apply adaptive thresholding to enhance contrast
            thresh = cv2.adaptiveThreshold(gray, 255, cv2.ADAPTIVE_THRESH_MEAN_C, cv2.THRESH_BINARY_INV, 15, 10)
            logger.info(f"[{self.name.upper()}] Applied adaptive thresholding")

            # Step 3: Use morphological operations to extract horizontal and vertical lines separately

            # Extract horizontal lines
            horizontal_kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (40, 1))
            horizontal_lines = cv2.morphologyEx(thresh, cv2.MORPH_OPEN, horizontal_kernel)

            # Extract vertical lines
            vertical_kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (1, 40))
            vertical_lines = cv2.morphologyEx(thresh, cv2.MORPH_OPEN, vertical_kernel)

            logger.info(f"[{self.name.upper()}] Extracted horizontal and vertical lines")

            # Step 4: Combine the lines to form a binary mask of the table
            table_mask = cv2.addWeighted(horizontal_lines, 0.5, vertical_lines, 0.5, 0.0)
            table_mask = cv2.morphologyEx(table_mask, cv2.MORPH_CLOSE, np.ones((3,3), np.uint8))

            logger.info(f"[{self.name.upper()}] Combined lines to form table mask")

            # Step 5: Use cv2.findContours to detect the largest outer rectangle enclosing the table grid
            contours, _ = cv2.findContours(table_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

            if not contours:
                logger.warning(f"[{self.name.upper()}] No contours found")
                return None, None

            # Find the largest contour (should be the table)
            largest_contour = max(contours, key=cv2.contourArea)

            # Get bounding rectangle of the largest contour
            x, y, w, h = cv2.boundingRect(largest_contour)

            # Add some padding and ensure we're within image bounds
            padding = 5
            x = max(0, x - padding)
            y = max(0, y - padding)
            w = min(width - x, w + 2*padding)
            h = min(height - y, h + 2*padding)

            logger.info(f"[{self.name.upper()}] Detected table boundary: x={x}, y={y}, w={w}, h={h}")

            # Step 6: Create the 4 point coordinates
            coordinates = {
                "x": int(x),
                "y": int(y),
                "width": int(w),
                "height": int(h)
            }

            # Step 7: Draw a red rectangle on the original image
            result_image = original.copy()
            cv2.rectangle(result_image, (x, y), (x + w, y + h), (0, 0, 255), 2)

            logger.info(f"[{self.name.upper()}] Drew red rectangle on image")

            # Save the result image in fullorder_output/table_detection/grid folder
            # Use absolute path relative to project root
            project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
            output_dir = os.path.join(project_root, "io", "fullorder_output", "table_detection", "grid")
            os.makedirs(output_dir, exist_ok=True)

            # Extract page number from input filename (e.g., CO25S006375_page2.png -> CO25S006375_ordertable_page2.png)
            input_filename = os.path.basename(image_path)
            import re
            page_match = re.search(r'_page(\d+)\.png$', input_filename)
            if page_match:
                page_num = page_match.group(1)
                base_name = input_filename.replace(f"_page{page_num}.png", "")
                output_filename = f"{base_name}_ordertable_page{page_num}.png"
            else:
                output_filename = "ordertable.png"

            output_path = os.path.join(output_dir, output_filename)
            cv2.imwrite(output_path, result_image)
            logger.info(f"[{self.name.upper()}] Saved result image: {output_path}")

            logger.info(f"[{self.name.upper()}] OpenCV table detection completed successfully")
            return coordinates, output_path

        except Exception as e:
            logger.error(f"[{self.name.upper()}] Error in OpenCV table detection: {str(e)}")
            return None, None

    def analyze_order(self, image_path: str, example_path: str = None):
        try:
            logger.info(f"[{self.name.upper()}] Processing image: {image_path}")

            with open(image_path, "rb") as f:
                order_bytes = f.read()

            messages = [
                {"role": "system", "content": "You are an expert in image processing and OpenCV."},
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": self.PROMPT},
                        {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{base64.b64encode(order_bytes).decode()}"}},
                    ]
                }
            ]

            if example_path and os.path.exists(example_path):
                logger.info(f"[{self.name.upper()}] Including example image: {example_path}")
                with open(example_path, "rb") as f:
                    example_bytes = f.read()

                messages[1]["content"].append({
                    "type": "image_url",
                    "image_url": {"url": f"data:image/jpeg;base64,{base64.b64encode(example_bytes).decode()}"}
                })

            logger.info(f"[{self.name.upper()}] Calling ChatGPT API...")
            response = self.client.chat.completions.create(
                model="gpt-4o",
                messages=messages,
                temperature=0
            )

            result_text = response.choices[0].message.content
            logger.info(f"[{self.name.upper()}] Received response from ChatGPT")

            print("Raw Response:", result_text[:500] + "..." if len(result_text) > 500 else result_text)

            try:
                result_json = json.loads(result_text)
                coords = result_json.get("coordinates")
                img_b64 = result_json.get("image_base64")

                if img_b64:
                    output_path = "ordertable.png"
                    with open(output_path, "wb") as f:
                        f.write(base64.b64decode(img_b64))
                    logger.info(f"[{self.name.upper()}] Annotated image saved as {output_path}")

                return coords, img_b64

            except json.JSONDecodeError as e:
                logger.warning(f"[{self.name.upper()}] Could not parse JSON: {e}")
                return self._parse_text_response(result_text)

        except Exception as e:
            logger.error(f"[{self.name.upper()}] Error analyzing order: {str(e)}")
            return None, None

    def _parse_text_response(self, text):
        import re

        coords = None
        img_b64 = None

        coord_patterns = [
            r'coordinates?:\s*(\d+),\s*(\d+),\s*(\d+),\s*(\d+)',
            r'x:\s*(\d+).*?y:\s*(\d+).*?width:\s*(\d+).*?height:\s*(\d+)',
            r'(\d+),\s*(\d+),\s*(\d+),\s*(\d+)'
        ]

        for pattern in coord_patterns:
            match = re.search(pattern, text, re.IGNORECASE | re.DOTALL)
            if match:
                coords = {
                    "x": int(match.group(1)),
                    "y": int(match.group(2)),
                    "width": int(match.group(3)),
                    "height": int(match.group(4))
                }
                break

        base64_patterns = [
            r'image_base64["\']?\s*:\s*["\']?([A-Za-z0-9+/]{100,}={0,2})',
            r'base64["\']?\s*:\s*["\']?([A-Za-z0-9+/]{100,}={0,2})',
            r'([A-Za-z0-9+/]{500,}={0,2})'
        ]

        for pattern in base64_patterns:
            match = re.search(pattern, text)
            if match:
                img_b64 = match.group(1)
                break

        if img_b64:
            try:
                output_path = "ordertable.png"
                with open(output_path, "wb") as f:
                    f.write(base64.b64decode(img_b64))
                logger.info(f"[{self.name.upper()}] Annotated image saved from text parsing")
            except Exception as e:
                logger.error(f"[{self.name.upper()}] Failed to decode base64: {e}")
                img_b64 = None

        return coords, img_b64

    def process_image(self, input_image_path, example_image_path=None):
        try:
            logger.info(f"[{self.name.upper()}] Starting table detection process")

            if not os.path.exists(input_image_path):
                error_msg = f"Input image not found: {input_image_path}"
                logger.error(f"[{self.name.upper()}] {error_msg}")
                return {"status": "error", "error": error_msg}

            # Use OpenCV implementation instead of ChatGPT
            coords, output_image_path = self.detect_table_boundary_opencv(input_image_path)

            if coords or output_image_path:
                result = {
                    "status": "success",
                    "input_file": input_image_path,
                    "coordinates": coords,
                    "output_image_path": output_image_path,
                    "method": "opencv_local"
                }
                logger.info(f"[{self.name.upper()}] Table detection completed successfully")
                return result
            else:
                error_msg = "Failed to detect table boundary using OpenCV"
                logger.error(f"[{self.name.upper()}] {error_msg}")
                return {"status": "error", "error": error_msg}

        except Exception as e:
            error_msg = f"Error processing image: {str(e)}"
            logger.error(f"[{self.name.upper()}] {error_msg}")
            return {"status": "error", "error": error_msg}


def main():
    try:
        agent = Form1S2Agent()

        input_path = "../../temp/CO25S006348_page1.png"
        example_path = "../../input/example/form1/example0.jpg"

        result = agent.process_image(input_path, example_path)
        print("=== FORM1S2 RESULTS ===")
        print(json.dumps(result, indent=2))

        if result["status"] == "success":
            print("Detected Coordinates:", result.get("coordinates"))
            if result.get("output_image_path"):
                print("Output image saved:", result["output_image_path"])

    except Exception as e:
        print(f"Error in main: {e}")


if __name__ == "__main__":
    main()
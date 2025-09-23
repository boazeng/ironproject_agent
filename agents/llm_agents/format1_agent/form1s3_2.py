"""
Form1S3.2 Agent - Order Line Count Analysis
Analyzes the table body image using ChatGPT to determine the number of order lines.
"""

import cv2
import numpy as np
import os
import json
import logging
import base64
from typing import Optional, Dict, Any
from openai import OpenAI
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class Form1S32Agent:
    """Agent for counting order lines in table body using ChatGPT vision."""

    def __init__(self, name: str = "form1s3_2"):
        """
        Initialize the Form1S3.2 agent.

        Args:
            name: Agent name for logging
        """
        self.name = name
        self.client = None
        self._initialize_openai_client()

    def _initialize_openai_client(self):
        """Initialize OpenAI client with API key."""
        try:
            api_key = os.getenv('OPENAI_API_KEY')
            if not api_key:
                raise ValueError("OPENAI_API_KEY not found in environment variables")

            self.client = OpenAI(api_key=api_key)
            logger.info(f"[{self.name.upper()}] OpenAI client initialized successfully")

        except Exception as e:
            logger.error(f"[{self.name.upper()}] Failed to initialize OpenAI client: {str(e)}")
            self.client = None

    def encode_image_to_base64(self, image_path: str) -> str:
        """
        Encode image to base64 string for OpenAI API.

        Args:
            image_path: Path to the image file

        Returns:
            Base64 encoded image string
        """
        try:
            with open(image_path, "rb") as image_file:
                encoded_string = base64.b64encode(image_file.read()).decode('utf-8')
            return encoded_string
        except Exception as e:
            logger.error(f"[{self.name.upper()}] Error encoding image: {str(e)}")
            raise

    def analyze_table_rows_with_chatgpt(self, image_path: str) -> Dict[str, Any]:
        """
        Analyze table body image using ChatGPT to count order lines.

        Args:
            image_path: Path to the table body image

        Returns:
            Dictionary with analysis results
        """
        try:
            if not self.client:
                raise ValueError("OpenAI client not initialized")

            logger.info(f"[{self.name.upper()}] Analyzing table image with ChatGPT")
            print(f"[DEBUG] Encoding image: {image_path}")

            # Encode image to base64
            base64_image = self.encode_image_to_base64(image_path)

            # Prepare the prompt for ChatGPT
            prompt = """
            Analyze this table image and count the number of data rows that contain order information.

            Please:
            1. Look for horizontal grid lines that separate table rows
            2. Count only the data rows (exclude header rows)
            3. Each data row should contain order/item information
            4. Ignore empty rows or very small spacing rows
            5. For each data row, estimate the Y coordinates (top and bottom) based on the image pixel coordinates
            6. Return ONLY a JSON object with the count and coordinates

            Expected format:
            {
                "number_of_rows": <count>,
                "analysis": "Brief description of what you observed",
                "row_coordinates": [
                    {
                        "row_number": 1,
                        "high_y": <top_y_coordinate>,
                        "low_y": <bottom_y_coordinate>
                    },
                    {
                        "row_number": 2,
                        "high_y": <top_y_coordinate>,
                        "low_y": <bottom_y_coordinate>
                    }
                    // ... continue for all rows
                ]
            }

            Be precise and count carefully. Focus on actual data-containing rows.
            Estimate Y coordinates based on the pixel positions in the image (0 = top, increasing downward).
            """

            print(f"[DEBUG] Sending request to ChatGPT...")

            # Make API call to ChatGPT
            response = self.client.chat.completions.create(
                model="gpt-4o",  # Use GPT-4 with vision capabilities
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "text",
                                "text": prompt
                            },
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:image/png;base64,{base64_image}",
                                    "detail": "high"
                                }
                            }
                        ]
                    }
                ],
                max_tokens=500,
                temperature=0.1
            )

            # Extract response content
            response_content = response.choices[0].message.content.strip()
            print(f"[DEBUG] ChatGPT Response: {response_content}")

            # Try to parse JSON response
            try:
                # Check if response is wrapped in markdown code block
                if response_content.strip().startswith('```json') and response_content.strip().endswith('```'):
                    # Extract JSON from markdown code block
                    json_content = response_content.strip()[7:-3].strip()  # Remove ```json and ```
                    analysis_result = json.loads(json_content)
                else:
                    analysis_result = json.loads(response_content)
            except json.JSONDecodeError:
                # If not valid JSON, extract number and create structured response
                import re
                numbers = re.findall(r'\d+', response_content)
                if numbers:
                    analysis_result = {
                        "number_of_rows": int(numbers[0]),
                        "analysis": response_content,
                        "row_coordinates": [],
                        "parsing_note": "Extracted number from text response"
                    }
                else:
                    raise ValueError("Could not extract row count from ChatGPT response")

            logger.info(f"[{self.name.upper()}] ChatGPT analysis completed")
            logger.info(f"[{self.name.upper()}] Detected rows: {analysis_result.get('number_of_rows', 'Unknown')}")

            return {
                "status": "success",
                "chatgpt_response": analysis_result,
                "raw_response": response_content
            }

        except Exception as e:
            logger.error(f"[{self.name.upper()}] Error in ChatGPT analysis: {str(e)}")
            return {
                "status": "error",
                "error": str(e),
                "chatgpt_response": None
            }

    def count_order_lines(self, input_file: str, output_dir: str) -> Dict[str, Any]:
        """
        Count order lines in table body image using ChatGPT.

        Args:
            input_file: Path to table_body.png from form1s3.1
            output_dir: Directory to save the analysis results

        Returns:
            Dictionary with counting results
        """
        try:
            logger.info(f"[{self.name.upper()}] Starting order line counting process")
            logger.info(f"[{self.name.upper()}] Input file: {input_file}")

            # Verify input file exists
            if not os.path.exists(input_file):
                raise FileNotFoundError(f"Input file not found: {input_file}")

            # Analyze with ChatGPT
            analysis_result = self.analyze_table_rows_with_chatgpt(input_file)

            if analysis_result["status"] != "success":
                raise ValueError(f"ChatGPT analysis failed: {analysis_result.get('error', 'Unknown error')}")

            # Extract row count and coordinates
            chatgpt_data = analysis_result["chatgpt_response"]
            row_count = chatgpt_data.get("number_of_rows", 0)
            row_coordinates = chatgpt_data.get("row_coordinates", [])

            # Prepare output data
            output_data = {
                "number_of_rows": row_count,
                "analysis_method": "ChatGPT Vision API",
                "model_used": "gpt-4o",
                "input_file": os.path.basename(input_file),
                "chatgpt_analysis": chatgpt_data.get("analysis", ""),
                "row_coordinates": row_coordinates,
                "timestamp": "2025-09-20",
                "agent": self.name
            }

            # Save results to JSON file
            os.makedirs(output_dir, exist_ok=True)

            # Extract page number from input filename (e.g., CO25S006375_table_bodyonly_page2.png -> CO25S006375_order_line_count_page2.json)
            input_filename = os.path.basename(input_file)
            import re
            page_match = re.search(r'_table_bodyonly_page(\d+)\.png$', input_filename)
            if page_match:
                page_num = page_match.group(1)
                base_name = input_filename.replace(f"_table_bodyonly_page{page_num}.png", "")
                output_filename = f"{base_name}_order_line_count_page{page_num}.json"
            else:
                output_filename = "order_line_count.json"

            output_file = os.path.join(output_dir, output_filename)

            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(output_data, f, indent=2, ensure_ascii=False)

            result = {
                "status": "success",
                "input_file": input_file,
                "output_file": output_file,
                "row_count": row_count,
                "analysis": chatgpt_data.get("analysis", ""),
                "row_coordinates": row_coordinates,
                "output_data": output_data
            }

            logger.info(f"[{self.name.upper()}] Order line counting completed")
            logger.info(f"[{self.name.upper()}] Detected {row_count} order lines")
            if row_coordinates:
                logger.info(f"[{self.name.upper()}] Extracted Y coordinates for {len(row_coordinates)} rows")
            logger.info(f"[{self.name.upper()}] Results saved to: {output_file}")

            return result

        except Exception as e:
            logger.error(f"[{self.name.upper()}] Error counting order lines: {str(e)}")
            return {
                "status": "error",
                "error": str(e),
                "input_file": input_file
            }

    def process_file(self, input_file: str, output_dir: str) -> Dict[str, Any]:
        """
        Process a single file for order line counting.

        Args:
            input_file: Path to input table body image
            output_dir: Directory to save counting results

        Returns:
            Processing result dictionary
        """
        return self.count_order_lines(input_file, output_dir)


def main():
    """Main function for testing the Form1S3.2 agent."""
    # Initialize agent
    agent = Form1S32Agent()

    # Test file paths
    input_file = "io/fullorder_output/table_detection/table/CO25S006375_table_bodyonly_page1.png"
    output_dir = "io/fullorder_output/table_detection/table"

    # Process the file
    result = agent.process_file(input_file, output_dir)

    # Print results
    if result["status"] == "success":
        print(f"✅ Order line counting successful!")
        print(f"📊 Row count: {result['row_count']}")
        print(f"📁 Output: {result['output_file']}")
        print(f"🤖 Analysis: {result['analysis']}")
    else:
        print(f"❌ Order line counting failed: {result['error']}")


if __name__ == "__main__":
    main()
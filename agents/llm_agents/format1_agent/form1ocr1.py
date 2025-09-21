import os
import logging
import json
import base64
from pathlib import Path
from PIL import Image
from openai import OpenAI
from dotenv import load_dotenv
from .form1dat1 import Form1Dat1Agent

# Load environment variables
load_env_path = Path(__file__).parent.parent.parent.parent / '.env'
load_dotenv(dotenv_path=load_env_path)

logger = logging.getLogger(__name__)

class Form1OCR1Agent:
    """
    Form1OCR1 Agent - Order Header OCR Processing
    Performs OCR on order header page 1 image using ChatGPT Vision API
    Extracts specific Hebrew fields and saves results to JSON
    """

    def __init__(self):
        self.name = "form1ocr1"
        self.short_name = "OCR1"
        self.output_dir = "io/fullorder_output"
        self.json_output_dir = "io/fullorder_output/json_output"
        self.order_header_dir = "io/fullorder_output/table_detection/order_header"

        # Required fields to extract (Hebrew)
        self.required_fields = [
            "לקוח/פרויקט",
            "איש קשר באתר",
            "טלפון",
            "כתובת האתר",
            "תאריך הזמנה",
            "מס הזמנה",
            "תאריך אספקה",
            "שם התוכנית",
            "סה\"כ משקל"
        ]

        logger.info(f"[{self.short_name.upper()}] Agent initialized - Order Header OCR processor")

        # Create output directories if they don't exist
        os.makedirs(self.output_dir, exist_ok=True)
        os.makedirs(self.json_output_dir, exist_ok=True)

        # Initialize form1dat1 agent for data storage
        self.form1dat1 = Form1Dat1Agent()

        # Initialize OpenAI client
        self.openai_api_key = os.getenv('OPENAI_API_KEY')
        if not self.openai_api_key:
            logger.error(f"[{self.short_name.upper()}] OpenAI API key not found in environment variables")
            raise ValueError("OpenAI API key is required")

        self.client = OpenAI(api_key=self.openai_api_key)

    def encode_image_to_base64(self, image_path):
        """Encode image to base64 for API submission"""
        try:
            with open(image_path, "rb") as image_file:
                encoded_string = base64.b64encode(image_file.read()).decode('utf-8')
            return encoded_string
        except Exception as e:
            logger.error(f"[{self.short_name.upper()}] Error encoding image: {e}")
            return None

    def find_order_header_page1_image(self):
        """Find the order header page 1 image file"""
        try:
            # Look for page 1 order header image
            pattern_variations = [
                "*_order_title_page1_order_header.png",
                "*_page1_order_header.png",
                "*_order_header_page1.png"
            ]

            for pattern in pattern_variations:
                files = list(Path(self.order_header_dir).glob(pattern))
                if files:
                    image_path = files[0]  # Take the first match
                    logger.info(f"[{self.short_name.upper()}] Found order header page 1 image: {image_path}")
                    return str(image_path)

            # If no specific pattern found, look for any file with "page1" in name
            all_files = list(Path(self.order_header_dir).glob("*.png"))
            for file in all_files:
                if "page1" in file.name.lower():
                    logger.info(f"[{self.short_name.upper()}] Found page 1 image: {file}")
                    return str(file)

            logger.error(f"[{self.short_name.upper()}] No order header page 1 image found in {self.order_header_dir}")
            return None

        except Exception as e:
            logger.error(f"[{self.short_name.upper()}] Error finding order header image: {e}")
            return None

    def perform_ocr_with_chatgpt(self, image_path):
        """Perform OCR using ChatGPT Vision API"""
        try:
            logger.info(f"[{self.short_name.upper()}] Performing OCR on {image_path}")

            # Encode image to base64
            image_base64 = self.encode_image_to_base64(image_path)
            if not image_base64:
                return None

            # Create the prompt for field extraction
            fields_list = "\n".join([f"• {field}" for field in self.required_fields])

            prompt = f"""
אתה מבצע OCR על תמונה של כותרת הזמנה בעברית.
אנא זהה וחלץ את השדות הבאים מהתמונה:

{fields_list}

החזר את התוצאה בפורמט JSON בדיוק כפי שמוצג כאן:
{{
    "לקוח/פרויקט": "ערך שנמצא או empty",
    "איש קשר באתר": "ערך שנמצא או empty",
    "טלפון": "ערך שנמצא או empty",
    "כתובת האתר": "ערך שנמצא או empty",
    "תאריך הזמנה": "ערך שנמצא או empty",
    "מס הזמנה": "ערך שנמצא או empty",
    "תאריך אספקה": "ערך שנמצא או empty",
    "שם התוכנית": "ערך שנמצא או empty",
    "סה\\"כ משקל": "ערך שנמצא או empty"
}}

אם שדה לא נמצא, השתמש במילה "empty".
אנא החזר רק את ה-JSON, ללא טקסט נוסף.
            """

            # Make API call to ChatGPT
            response = self.client.chat.completions.create(
                model="gpt-4o",
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
                                    "url": f"data:image/png;base64,{image_base64}"
                                }
                            }
                        ]
                    }
                ],
                max_tokens=500,
                temperature=0
            )

            # Extract the response
            ocr_result = response.choices[0].message.content.strip()
            logger.info(f"[{self.short_name.upper()}] OCR result received from ChatGPT")

            return ocr_result

        except Exception as e:
            logger.error(f"[{self.short_name.upper()}] Error performing OCR with ChatGPT: {e}")
            return None

    def parse_and_validate_json(self, ocr_result):
        """Parse and validate the JSON response from ChatGPT"""
        try:
            # Try to extract JSON from the response
            if '```json' in ocr_result:
                # Extract JSON from code block
                start = ocr_result.find('```json') + 7
                end = ocr_result.find('```', start)
                json_str = ocr_result[start:end].strip()
            elif '{' in ocr_result and '}' in ocr_result:
                # Extract JSON from braces
                start = ocr_result.find('{')
                end = ocr_result.rfind('}') + 1
                json_str = ocr_result[start:end]
            else:
                json_str = ocr_result

            # Parse JSON
            parsed_data = json.loads(json_str)

            # Validate that all required fields are present
            validated_data = {}
            for field in self.required_fields:
                validated_data[field] = parsed_data.get(field, "empty")

            logger.info(f"[{self.short_name.upper()}] Successfully parsed and validated JSON data")
            return validated_data

        except json.JSONDecodeError as e:
            logger.error(f"[{self.short_name.upper()}] JSON parsing error: {e}")
            logger.error(f"[{self.short_name.upper()}] Raw response: {ocr_result}")

            # Return empty data structure
            return {field: "empty" for field in self.required_fields}
        except Exception as e:
            logger.error(f"[{self.short_name.upper()}] Error validating JSON: {e}")
            return {field: "empty" for field in self.required_fields}

    def save_results_to_json(self, data, base_filename):
        """Save extracted data to JSON file"""
        try:
            # Create output filename
            output_filename = f"{base_filename}_order_header_ocr.json"
            output_path = os.path.join(self.json_output_dir, output_filename)

            # Add metadata
            result_data = {
                "agent": self.name,
                "version": "1.0",
                "extracted_fields": data,
                "field_count": len([v for v in data.values() if v != "empty"]),
                "timestamp": Path(output_path).stat().st_mtime if os.path.exists(output_path) else None
            }

            # Save to JSON file
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(result_data, f, ensure_ascii=False, indent=2)

            logger.info(f"[{self.short_name.upper()}] Results saved to {output_path}")
            return output_path

        except Exception as e:
            logger.error(f"[{self.short_name.upper()}] Error saving results: {e}")
            return None

    def create_website_analysis_file(self, extracted_data, image_path, base_filename):
        """Create the main analysis file that the website expects"""
        try:
            # Create the analysis file for the website
            analysis_filename = f"{base_filename}_analysis.json"
            analysis_path = os.path.join(self.output_dir, analysis_filename)

            # Create analysis data structure
            analysis_data = {
                "file": f"{base_filename}.pdf",
                "order_header_image_path": image_path.replace("\\", "/"),
                "ocr_data": extracted_data,
                "sections": {
                    "header": {
                        "found": True,
                        "order_number": extracted_data.get("מס הזמנה", "-"),
                        "customer": extracted_data.get("לקוח/פרויקט", "-")
                    }
                }
            }

            # Save to analysis file
            with open(analysis_path, 'w', encoding='utf-8') as f:
                json.dump(analysis_data, f, ensure_ascii=False, indent=2)

            logger.info(f"[{self.short_name.upper()}] Website analysis file created: {analysis_path}")
            return analysis_path

        except Exception as e:
            logger.error(f"[{self.short_name.upper()}] Error creating website analysis file: {e}")
            return None

    def process(self, pdf_path=None):
        """Main processing function"""
        try:
            logger.info(f"[{self.short_name.upper()}] Starting order header OCR processing")

            # Find the order header page 1 image
            image_path = self.find_order_header_page1_image()
            if not image_path:
                logger.error(f"[{self.short_name.upper()}] No order header page 1 image found")
                return {
                    'success': False,
                    'error': 'No order header page 1 image found',
                    'agent_result': None
                }

            # Perform OCR with ChatGPT
            ocr_result = self.perform_ocr_with_chatgpt(image_path)
            if not ocr_result:
                logger.error(f"[{self.short_name.upper()}] OCR failed")
                return {
                    'success': False,
                    'error': 'OCR processing failed',
                    'agent_result': None
                }

            # Parse and validate the JSON response
            extracted_data = self.parse_and_validate_json(ocr_result)

            # Get base filename for output (extract PDF name from image filename)
            image_filename = Path(image_path).stem
            # Extract the PDF filename (e.g., "CO25S006375" from "CO25S006375_order_title_page1_order_header")
            base_filename = image_filename.split("_")[0]

            # Save results to JSON
            output_path = self.save_results_to_json(extracted_data, base_filename)

            # Store OCR data in form1dat1 database (Section 2) - only extracted fields
            ocr_data = extracted_data
            self.form1dat1.store_ocr_data(base_filename, ocr_data)
            logger.info(f"[{self.short_name.upper()}] OCR data stored in form1dat1 database")

            # Create website analysis file for immediate display
            analysis_path = self.create_website_analysis_file(extracted_data, image_path, base_filename)

            # Prepare result
            result = {
                'success': True,
                'agent_result': {
                    'extracted_fields': extracted_data,
                    'field_count': len([v for v in extracted_data.values() if v != "empty"]),
                    'output_file': output_path,
                    'analysis_file': analysis_path,
                    'source_image': image_path
                }
            }

            logger.info(f"[{self.short_name.upper()}] OCR processing completed successfully")
            logger.info(f"[{self.short_name.upper()}] Extracted {result['agent_result']['field_count']} fields")

            return result

        except Exception as e:
            logger.error(f"[{self.short_name.upper()}] Error in processing: {e}")
            return {
                'success': False,
                'error': str(e),
                'agent_result': None
            }

def main():
    """Test function"""
    agent = Form1OCR1Agent()
    result = agent.process()
    print(f"OCR Agent Result: {result}")

if __name__ == "__main__":
    main()
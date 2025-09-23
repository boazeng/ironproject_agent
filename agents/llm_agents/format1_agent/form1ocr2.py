import os
import logging
import json
import base64
import time
from pathlib import Path
from PIL import Image
from openai import OpenAI
from dotenv import load_dotenv

# Load environment variables
load_env_path = Path(__file__).parent.parent.parent.parent / '.env'
load_dotenv(dotenv_path=load_env_path)

logger = logging.getLogger(__name__)

class Form1OCR2Agent:
    """
    Form1OCR2 Agent - Table Body OCR Processing
    Performs OCR on table body images using ChatGPT Vision API
    Extracts table data according to format1 column structure and saves results to JSON
    """

    def __init__(self):
        self.name = "form1ocr2"
        self.short_name = "OCR2"
        self.table_input_dir = "io/fullorder_output/table_detection/table"
        self.table_ocr_output_dir = "io/fullorder_output/table_detection/table_ocr"
        self.format_definition_path = "agents/llm_agents/format1_agent/table_format_definition.json"

        logger.info(f"[{self.short_name.upper()}] Agent initialized - Table Body OCR processor")

        # Create output directory if it doesn't exist
        os.makedirs(self.table_ocr_output_dir, exist_ok=True)

        # Load table format definition
        self.table_format = self.load_table_format_definition()

        # Initialize OpenAI client
        self.openai_api_key = os.getenv('OPENAI_API_KEY')
        if not self.openai_api_key:
            logger.error(f"[{self.short_name.upper()}] OpenAI API key not found in environment variables")
            raise ValueError("OpenAI API key is required")

        self.client = OpenAI(api_key=self.openai_api_key)

    def load_table_format_definition(self):
        """Load table format definition from JSON file"""
        try:
            with open(self.format_definition_path, 'r', encoding='utf-8') as f:
                format_data = json.load(f)

            logger.info(f"[{self.short_name.upper()}] Loaded table format: {format_data['format']}")
            logger.info(f"[{self.short_name.upper()}] Number of columns: {format_data['number_of_columns']}")

            return format_data
        except Exception as e:
            logger.error(f"[{self.short_name.upper()}] Error loading table format definition: {e}")
            # Return default format if file not found
            return {
                "format": "format 1",
                "number_of_columns": 7,
                "columns": {
                    f"column_{i}": {"number": i, "name": f"Column {i}"}
                    for i in range(1, 8)
                }
            }

    def encode_image_to_base64(self, image_path):
        """Encode image to base64 for API submission"""
        try:
            with open(image_path, "rb") as image_file:
                encoded_string = base64.b64encode(image_file.read()).decode('utf-8')
            return encoded_string
        except Exception as e:
            logger.error(f"[{self.short_name.upper()}] Error encoding image: {e}")
            return None

    def find_table_body_image(self, order_number, page_number):
        """Find the table body image file for specific order and page"""
        try:
            # Look for table body image: {ordernumber}_table_bodyonly_page{pagenumber}.png
            image_filename = f"{order_number}_table_bodyonly_page{page_number}.png"
            image_path = os.path.join(self.table_input_dir, image_filename)

            if os.path.exists(image_path):
                logger.info(f"[{self.short_name.upper()}] Found table body image: {image_path}")
                return image_path
            else:
                logger.error(f"[{self.short_name.upper()}] Table body image not found: {image_path}")
                return None

        except Exception as e:
            logger.error(f"[{self.short_name.upper()}] Error finding table body image: {e}")
            return None

    def create_table_ocr_prompt(self):
        """Create the OCR prompt based on table format definition"""
        try:
            # Extract column information from format definition
            columns_info = []
            for col_key, col_data in self.table_format["columns"].items():
                columns_info.append(f"עמודה {col_data['number']}: {col_data['name']}")

            columns_text = "\n".join(columns_info)

            prompt = f"""
אתה מבצע OCR על תמונה של טבלה בעברית.

הטבלה מכילה {self.table_format['number_of_columns']} עמודות:
{columns_text}

אנא חלץ את כל הנתונים מהטבלה והחזר אותם בפורמט JSON כפי שמוצג:

{{
  "table_data": {{
    "format": "{self.table_format['format']}",
    "page_number": "מספר העמוד",
    "total_rows": מספר השורות,
    "rows": [
      {{
        "row_number": 1,
        "מס": "ערך",
        "shape": "ערך",
        "קוטר": "ערך",
        "סהכ יחידות": "ערך",
        "אורך": "ערך",
        "משקל": "ערך",
        "הערות": "ערך"
      }}
    ]
  }}
}}

הוראות חשובות:
1. חלץ את כל השורות מהטבלה
2. אם תא ריק, השתמש במחרוזת "empty"
3. שמור על הסדר המדויק של העמודות
4. אם יש ציורים או צורות בעמודת ה-shape, תאר אותם בקצרה
5. החזר רק את ה-JSON, ללא טקסט נוסף

            """

            return prompt

        except Exception as e:
            logger.error(f"[{self.short_name.upper()}] Error creating OCR prompt: {e}")
            return None

    def perform_table_ocr_with_chatgpt(self, image_path, page_number):
        """Perform table OCR using ChatGPT Vision API"""
        try:
            logger.info(f"[{self.short_name.upper()}] Performing table OCR on {image_path}")

            # Encode image to base64
            image_base64 = self.encode_image_to_base64(image_path)
            if not image_base64:
                return None

            # Create the prompt for table OCR
            prompt = self.create_table_ocr_prompt()
            if not prompt:
                return None

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
                max_tokens=2000,
                temperature=0
            )

            # Extract the response
            ocr_result = response.choices[0].message.content.strip()
            logger.info(f"[{self.short_name.upper()}] Table OCR result received from ChatGPT")

            return ocr_result

        except Exception as e:
            logger.error(f"[{self.short_name.upper()}] Error performing table OCR with ChatGPT: {e}")
            return None

    def parse_and_validate_table_json(self, ocr_result, page_number):
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

            # Clean up escape sequences before parsing JSON
            json_str = json_str.replace('\\', '/')

            # Parse JSON
            parsed_data = json.loads(json_str)

            # Validate and ensure proper structure
            if "table_data" not in parsed_data:
                # If direct structure, wrap it
                table_data = parsed_data
            else:
                table_data = parsed_data["table_data"]

            # Ensure page number is set
            if "page_number" not in table_data or not table_data["page_number"]:
                table_data["page_number"] = str(page_number)

            # Ensure format is set
            if "format" not in table_data:
                table_data["format"] = self.table_format["format"]

            # Validate rows structure
            if "rows" not in table_data:
                table_data["rows"] = []

            if "total_rows" not in table_data:
                table_data["total_rows"] = len(table_data["rows"])

            logger.info(f"[{self.short_name.upper()}] Successfully parsed table JSON data")
            logger.info(f"[{self.short_name.upper()}] Found {table_data['total_rows']} rows")

            return {"table_data": table_data}

        except json.JSONDecodeError as e:
            logger.error(f"[{self.short_name.upper()}] JSON parsing error: {e}")
            logger.error(f"[{self.short_name.upper()}] Raw response: {ocr_result}")

            # Return empty structure
            return {
                "table_data": {
                    "format": self.table_format["format"],
                    "page_number": str(page_number),
                    "total_rows": 0,
                    "rows": [],
                    "error": "JSON parsing failed"
                }
            }
        except Exception as e:
            logger.error(f"[{self.short_name.upper()}] Error validating table JSON: {e}")
            return {
                "table_data": {
                    "format": self.table_format["format"],
                    "page_number": str(page_number),
                    "total_rows": 0,
                    "rows": [],
                    "error": str(e)
                }
            }

    def save_table_ocr_results(self, table_data, order_number, page_number):
        """Save table OCR results to JSON file"""
        try:
            # Create output filename: {ordernumber}_table_ocr_page{pagenumber}.json
            output_filename = f"{order_number}_table_ocr_page{page_number}.json"
            output_path = os.path.join(self.table_ocr_output_dir, output_filename)

            # Add metadata
            result_data = {
                "agent": self.name,
                "version": "1.0",
                "order_number": order_number,
                "page_number": page_number,
                "timestamp": time.time(),
                "table_data": table_data["table_data"]
            }

            # Save to JSON file
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(result_data, f, ensure_ascii=False, indent=2)

            logger.info(f"[{self.short_name.upper()}] Table OCR results saved to {output_path}")
            return output_path

        except Exception as e:
            logger.error(f"[{self.short_name.upper()}] Error saving table OCR results: {e}")
            return None

    def process_page(self, order_number, page_number):
        """Process a single page table OCR"""
        try:
            logger.info(f"[{self.short_name.upper()}] Processing table OCR for {order_number} page {page_number}")

            # Find the table body image
            image_path = self.find_table_body_image(order_number, page_number)
            if not image_path:
                return {
                    'success': False,
                    'error': f'Table body image not found for {order_number} page {page_number}',
                    'agent_result': None
                }

            # Perform table OCR with ChatGPT
            ocr_result = self.perform_table_ocr_with_chatgpt(image_path, page_number)
            if not ocr_result:
                return {
                    'success': False,
                    'error': 'Table OCR processing failed',
                    'agent_result': None
                }

            # Parse and validate the JSON response
            table_data = self.parse_and_validate_table_json(ocr_result, page_number)

            # Save results to JSON
            output_path = self.save_table_ocr_results(table_data, order_number, page_number)

            # Prepare result
            result = {
                'success': True,
                'agent_result': {
                    'table_data': table_data["table_data"],
                    'total_rows': table_data["table_data"]["total_rows"],
                    'output_file': output_path,
                    'source_image': image_path
                }
            }

            logger.info(f"[{self.short_name.upper()}] Table OCR processing completed successfully")
            logger.info(f"[{self.short_name.upper()}] Extracted {result['agent_result']['total_rows']} rows")

            return result

        except Exception as e:
            logger.error(f"[{self.short_name.upper()}] Error in processing: {e}")
            return {
                'success': False,
                'error': str(e),
                'agent_result': None
            }

    def find_all_table_images(self, order_number):
        """Find all table body images for an order"""
        try:
            table_images = []
            for file in os.listdir(self.table_input_dir):
                if file.startswith(f"{order_number}_table_bodyonly_page") and file.endswith('.png'):
                    # Extract page number from filename
                    page_part = file.replace(f"{order_number}_table_bodyonly_page", "").replace(".png", "")
                    table_images.append({
                        'page_number': page_part,
                        'file_path': os.path.join(self.table_input_dir, file)
                    })

            # Sort by page number
            table_images.sort(key=lambda x: int(x['page_number']))
            logger.info(f"[{self.short_name.upper()}] Found {len(table_images)} table images for {order_number}")
            return table_images

        except Exception as e:
            logger.error(f"[{self.short_name.upper()}] Error finding table images: {e}")
            return []

    def process_all_pages(self, order_number):
        """Process all table pages for an order"""
        try:
            logger.info(f"[{self.short_name.upper()}] Processing all table pages for {order_number}")

            # Find all table images
            table_images = self.find_all_table_images(order_number)
            if not table_images:
                return {
                    'success': False,
                    'error': f'No table images found for {order_number}',
                    'agent_result': None
                }

            results = []
            total_rows = 0

            for image_info in table_images:
                page_number = image_info['page_number']
                logger.info(f"[{self.short_name.upper()}] Processing page {page_number}")

                result = self.process_page(order_number, page_number)
                if result['success']:
                    results.append(result['agent_result'])
                    total_rows += result['agent_result']['total_rows']
                else:
                    logger.error(f"[{self.short_name.upper()}] Failed to process page {page_number}: {result['error']}")

            # Prepare combined result
            combined_result = {
                'success': len(results) > 0,
                'agent_result': {
                    'order_number': order_number,
                    'total_pages_processed': len(results),
                    'total_rows_extracted': total_rows,
                    'pages': results,
                    'output_files': [r['output_file'] for r in results if r.get('output_file')]
                }
            }

            if len(results) == 0:
                combined_result['error'] = 'Failed to process any table pages'
                combined_result['agent_result'] = None

            logger.info(f"[{self.short_name.upper()}] Completed processing {len(results)} pages with {total_rows} total rows")
            return combined_result

        except Exception as e:
            logger.error(f"[{self.short_name.upper()}] Error in process_all_pages: {e}")
            return {
                'success': False,
                'error': str(e),
                'agent_result': None
            }

    def process(self, order_number=None, page_number=None):
        """Main processing function"""
        if not order_number:
            logger.error(f"[{self.short_name.upper()}] Order number is required")
            return {
                'success': False,
                'error': 'Order number is required',
                'agent_result': None
            }

        if page_number:
            # Process single page
            return self.process_page(order_number, page_number)
        else:
            # Process all pages
            return self.process_all_pages(order_number)

def main():
    """Test function"""
    agent = Form1OCR2Agent()
    # Test with existing order - process all pages
    result = agent.process(order_number="CO25S006375")

    # Print results safely (avoiding unicode issues)
    print("Table OCR Agent Result:")
    print(f"Success: {result.get('success', False)}")
    if result.get('success'):
        agent_result = result.get('agent_result', {})
        print(f"Order: {agent_result.get('order_number', 'N/A')}")
        print(f"Pages processed: {agent_result.get('total_pages_processed', 0)}")
        print(f"Total rows: {agent_result.get('total_rows_extracted', 0)}")
        print(f"Output files: {len(agent_result.get('output_files', []))}")
    else:
        print(f"Error: {result.get('error', 'Unknown error')}")

if __name__ == "__main__":
    main()
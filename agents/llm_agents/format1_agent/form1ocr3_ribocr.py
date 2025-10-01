"""
Form1OCR3 Rib-OCR Agent (form1ocr2)
Agent for mapping catalog shape letters to order drawing dimensions using ChatGPT API.
"""

import os
import json
import base64
import logging
from typing import Dict, List, Any, Optional, Tuple
import requests
from PIL import Image
import io
from datetime import datetime

class Form1OCR3RibOCRAgent:
    """
    Agent that maps catalog shape letters to order drawing dimensions using ChatGPT vision API.
    Handles ribs and angles with special treatment for 90-degree angles.
    """

    def __init__(self, api_key: Optional[str] = None):
        """Initialize the agent with OpenAI API key."""
        self.api_key = api_key or os.getenv('OPENAI_API_KEY')
        if not self.api_key:
            raise ValueError("OpenAI API key not found. Set OPENAI_API_KEY environment variable.")

        self.api_url = "https://api.openai.com/v1/chat/completions"
        self.model = "gpt-4o"  # Updated model that supports vision
        self.logger = self._setup_logger()

        # Prompt template
        self.prompt_template = """
CONTEXT:
You are given two images:
- "catalog_image": a schematic/catalog drawing where ribs and angles are labeled with letters (A, B, C, ...).
- "order_image": a measured drawing of the same part, where numeric dimensions are printed near the ribs/angles.

ADDITIONAL INPUT (new):
- "letter_list": a JSON array supplied with the request that enumerates which catalog letters are ribs or angles and — for angles — whether the user declares them to be 90°. Example:
  [
    {{"letter":"A","type":"rib"}},
    {{"letter":"C","type":"angle","is_90":true}},
    {{"letter":"E","type":"rib"}}
  ]
- Behavior rule for angles: **If an entry has `"type":"angle"` and `"is_90": true`, the assistant must treat that letter as an angle of 90° and must NOT change or convert that value (i.e., map the letter to 90 and set confidence high).** For angles where `"is_90"` is false or omitted, detect numeric angle labels from the order image as usual.

GOAL:
Look at both images and map each letter from the catalog image to its corresponding numeric dimension in the order image.

YOUR TASK:
1. Look at the catalog_image and identify where each letter from the letter_list appears
2. Look at the order_image and find the numeric dimensions
3. Match each letter to its corresponding number based on position:
   - Letters on straight segments (ribs) should map to length dimensions
   - Letters at corners (angles) should map to angle measurements
   - If a letter is marked as an angle with "is_90": true, ALWAYS return 90 as its value
4. Return the mappings in JSON format

IMPORTANT:
- DO NOT try to execute code. Just analyze the images visually.
- For angles marked with "is_90": true, you MUST return 90 regardless of what you see
- Base your mappings on the visual correspondence between the two images
- The shapes in both images are identical, just labeled differently

RESPONSE FORMAT:
Return ONLY a JSON object with this structure (no additional text or explanation):

{{
  "mappings": [
    {{
      "letter": "A",
      "type": "rib",
      "number": 70,
      "confidence": 0.95
    }},
    {{
      "letter": "B",
      "type": "angle",
      "is_90": true,
      "number": 90,
      "confidence": 0.99
    }},
    {{
      "letter": "C",
      "type": "rib",
      "number": 14,
      "confidence": 0.90
    }}
    // ... more mappings for each letter in letter_list
  ],
  "summary": {{
    "success": true,
    "notes": "Successfully mapped X letters"
  }}
}}

CRITICAL RULES:
- Return ONLY the JSON - no explanations, no code, no instructions
- For any angle with "is_90": true, you MUST set number to 90
- Include ALL letters from the letter_list in your response
- If you cannot find a letter, set its number to null and confidence to 0.0

Letter list for this analysis: {letter_list}
"""

    def _setup_logger(self) -> logging.Logger:
        """Setup logging for the agent."""
        logger = logging.getLogger('Form1OCR3RibOCR')
        logger.setLevel(logging.INFO)

        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            handler.setFormatter(formatter)
            logger.addHandler(handler)

        return logger

    def encode_image(self, image_path: str) -> str:
        """Encode image to base64 string."""
        try:
            with open(image_path, "rb") as image_file:
                return base64.b64encode(image_file.read()).decode('utf-8')
        except Exception as e:
            self.logger.error(f"Error encoding image {image_path}: {e}")
            raise

    def validate_letter_list(self, letter_list: List[Dict[str, Any]]) -> bool:
        """Validate the letter list format."""
        required_fields = ['letter', 'type']

        for idx, item in enumerate(letter_list):
            if not isinstance(item, dict):
                self.logger.error(f"Letter list item {idx} is not a dict: {type(item)}")
                return False

            for field in required_fields:
                if field not in item:
                    self.logger.error(f"Letter list item {idx} missing field '{field}': {item}")
                    return False

            if item['type'] not in ['rib', 'angle']:
                self.logger.error(f"Letter list item {idx} has invalid type '{item['type']}': {item}")
                return False

            # Check is_90 field for angles
            if item['type'] == 'angle' and 'is_90' in item:
                if not isinstance(item['is_90'], bool):
                    self.logger.error(f"Letter list item {idx} has non-boolean is_90 field: {item}")
                    return False

        return True

    def save_response_to_temp(self, content: str, shape_number: Optional[str] = None,
                             line_order: Optional[int] = None) -> str:
        """
        Save ChatGPT response to temp folder.
        If files exist for the same shape/line combination, delete them first.

        Args:
            content: Raw ChatGPT response content
            shape_number: Shape number for filename
            line_order: Line order for filename

        Returns:
            Path to saved file
        """
        # File saving disabled to prevent temp folder clutter
        self.logger.info(f"Response saving disabled - not saving to temp folder")
        return ""

    def save_input_images_to_temp(self, catalog_image_path: str, order_image_path: str,
                                  shape_number: Optional[str] = None,
                                  line_order: Optional[int] = None) -> Tuple[str, str]:
        """
        Save input catalog and order images to temp folder.
        File saving disabled to prevent temp folder clutter.

        Args:
            catalog_image_path: Path to catalog image
            order_image_path: Path to order image
            shape_number: Shape number for filename
            line_order: Line order for filename

        Returns:
            Tuple of (temp_catalog_path, temp_order_path) - returns empty strings
        """
        # File saving disabled to prevent temp folder clutter
        self.logger.info(f"Input image saving disabled - not saving catalog and order images to temp folder")
        return "", ""

    def save_rib_to_find_json(self, letter_list: List[Dict], shape_number: str, line_order: int) -> str:
        """
        Save the rib_to_find JSON file to temp folder.
        File saving disabled to prevent temp folder clutter.

        Args:
            letter_list: List of letters with their types (rib/angle)
            shape_number: Shape catalog number
            line_order: Line order number

        Returns:
            str: Path to the saved rib_to_find JSON file - returns empty string
        """
        # File saving disabled to prevent temp folder clutter
        self.logger.info(f"Rib_to_find JSON saving disabled - not saving to temp folder for shape {shape_number}, line {line_order}")
        return ""

    def map_catalog_to_order(
        self,
        catalog_image_path: str,
        order_image_path: str,
        letter_list: List[Dict[str, Any]],
        shape_number: Optional[str] = None,
        line_order: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Map catalog shape letters to order drawing dimensions.

        Args:
            catalog_image_path: Path to catalog shape image
            order_image_path: Path to order drawing image
            letter_list: List of letters with type (rib/angle) and is_90 flag
            shape_number: Shape number for reference
            line_order: Line order number for reference

        Returns:
            Dictionary containing mappings and analysis results
        """
        try:
            self.logger.info(f"Starting mapping for shape {shape_number}, line {line_order}")

            # Validate inputs
            if not os.path.exists(catalog_image_path):
                raise FileNotFoundError(f"Catalog image not found: {catalog_image_path}")

            if not os.path.exists(order_image_path):
                raise FileNotFoundError(f"Order image not found: {order_image_path}")

            if not self.validate_letter_list(letter_list):
                raise ValueError("Invalid letter_list format")

            # Save input images to temp folder
            temp_catalog_path, temp_order_path = self.save_input_images_to_temp(
                catalog_image_path, order_image_path, shape_number, line_order
            )

            # Save rib_to_find JSON file to temp folder
            rib_to_find_path = self.save_rib_to_find_json(letter_list, shape_number, line_order)

            # Encode images
            catalog_base64 = self.encode_image(catalog_image_path)
            order_base64 = self.encode_image(order_image_path)

            # Prepare prompt with letter list
            prompt = self.prompt_template.format(
                letter_list=json.dumps(letter_list, indent=2)
            )

            # Prepare API request
            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self.api_key}"
            }

            payload = {
                "model": self.model,
                "messages": [
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
                                    "url": f"data:image/jpeg;base64,{catalog_base64}",
                                    "detail": "high"
                                }
                            },
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:image/jpeg;base64,{order_base64}",
                                    "detail": "high"
                                }
                            }
                        ]
                    }
                ],
                "max_tokens": 4000,
                "temperature": 0.1
            }

            # Make API request
            self.logger.info("Sending request to ChatGPT API...")
            response = requests.post(self.api_url, headers=headers, json=payload)

            if response.status_code != 200:
                raise Exception(f"API request failed: {response.status_code} - {response.text}")

            response_data = response.json()

            # Extract content from response
            if 'choices' not in response_data or not response_data['choices']:
                raise Exception("No response content from API")

            content = response_data['choices'][0]['message']['content']

            # Save raw response to temp folder
            temp_file_path = self.save_response_to_temp(content, shape_number, line_order)

            # Parse JSON response
            try:
                self.logger.info(f"Raw response content: {content[:500]}...")  # Log first 500 chars
                result = json.loads(content)
            except json.JSONDecodeError as e:
                self.logger.error(f"Failed to parse JSON response: {e}")
                self.logger.error(f"Raw content: {content}")
                # Try to extract JSON from content if it's wrapped in text
                import re
                json_match = re.search(r'(\{.*\})', content, re.DOTALL)
                if json_match:
                    try:
                        result = json.loads(json_match.group(1))
                    except json.JSONDecodeError as e2:
                        self.logger.error(f"Failed to parse extracted JSON: {e2}")
                        raise Exception(f"JSON parsing failed: {e2}")
                else:
                    raise Exception(f"Could not find valid JSON in response: {content}")

            # Add metadata
            result['metadata'] = {
                'shape_number': shape_number,
                'line_order': line_order,
                'catalog_image_path': catalog_image_path,
                'order_image_path': order_image_path,
                'letter_list': letter_list,
                'api_model': self.model,
                'agent_name': 'form1ocr2',
                'temp_file_path': temp_file_path,
                'temp_catalog_image_path': temp_catalog_path,
                'temp_order_image_path': temp_order_path,
                'rib_to_find_path': rib_to_find_path
            }

            self.logger.info(f"Successfully completed mapping with {len(result.get('mappings', []))} mappings")

            # Print simple summary of letters and values
            print("\n" + "="*50)
            print("LETTER MAPPING RESULTS:")
            print("="*50)
            for mapping in result.get('mappings', []):
                letter = mapping.get('letter', '?')
                value = mapping.get('number', 'null')
                mapping_type = mapping.get('type', '?')
                print(f"{letter}: {value} ({mapping_type})")
            print("="*50 + "\n")

            return result

        except Exception as e:
            import traceback
            self.logger.error(f"Error in map_catalog_to_order: {e}")
            self.logger.error(f"Error type: {type(e).__name__}")
            self.logger.error(f"Traceback: {traceback.format_exc()}")
            return {
                'mappings': [],
                'summary': {
                    'success': False,
                    'notes': f"Error: {str(e)}",
                    'annotated_catalog_path': None,
                    'annotated_order_path': None,
                    'masks': []
                },
                'metadata': {
                    'shape_number': shape_number,
                    'line_order': line_order,
                    'catalog_image_path': catalog_image_path,
                    'order_image_path': order_image_path,
                    'letter_list': letter_list,
                    'api_model': self.model,
                    'agent_name': 'form1ocr2',
                    'error': str(e),
                    'temp_file_path': None,
                    'temp_catalog_image_path': None,
                    'temp_order_image_path': None,
                    'rib_to_find_path': None
                }
            }

    def process_shape_line(
        self,
        shape_data: Dict[str, Any],
        catalog_image_path: str,
        order_image_path: str
    ) -> Dict[str, Any]:
        """
        Process a specific shape line using the mapping agent.

        Args:
            shape_data: Shape data containing letter information
            catalog_image_path: Path to catalog image
            order_image_path: Path to order drawing image

        Returns:
            Mapping results
        """
        try:
            # Extract letter list from shape_data
            letter_list = []

            if 'ribs' in shape_data:
                for rib_letter in shape_data['ribs']:
                    letter_list.append({
                        'letter': rib_letter,
                        'type': 'rib'
                    })

            if 'angles' in shape_data:
                for angle_data in shape_data['angles']:
                    if isinstance(angle_data, dict):
                        letter_entry = {
                            'letter': angle_data.get('letter'),
                            'type': 'angle'
                        }

                        # Check for 90-degree angle flag
                        if angle_data.get('is_90_degree', False) or angle_data.get('value') == 90:
                            letter_entry['is_90'] = True
                        else:
                            letter_entry['is_90'] = False

                        letter_list.append(letter_entry)
                    else:
                        # Simple letter format
                        letter_list.append({
                            'letter': angle_data,
                            'type': 'angle',
                            'is_90': False
                        })

            # Get shape number and line order if available
            shape_number = shape_data.get('shape_number')
            line_order = shape_data.get('line_order')

            return self.map_catalog_to_order(
                catalog_image_path=catalog_image_path,
                order_image_path=order_image_path,
                letter_list=letter_list,
                shape_number=shape_number,
                line_order=line_order
            )

        except Exception as e:
            self.logger.error(f"Error in process_shape_line: {e}")
            return {
                'mappings': [],
                'summary': {
                    'success': False,
                    'notes': f"Error processing shape line: {str(e)}",
                    'annotated_catalog_path': None,
                    'annotated_order_path': None,
                    'masks': []
                },
                'metadata': {
                    'error': str(e),
                    'agent_name': 'form1ocr2'
                }
            }

# Convenience function for easy usage
def create_form1ocr2_agent(api_key: Optional[str] = None) -> Form1OCR3RibOCRAgent:
    """Create and return a Form1OCR2 agent instance."""
    return Form1OCR3RibOCRAgent(api_key)

# Example usage and testing
if __name__ == "__main__":
    # Example usage
    agent = create_form1ocr2_agent()

    # Example letter list
    example_letter_list = [
        {"letter": "A", "type": "rib"},
        {"letter": "B", "type": "rib"},
        {"letter": "C", "type": "angle", "is_90": True},
        {"letter": "D", "type": "angle", "is_90": False}
    ]

    print("Form1OCR2 agent initialized successfully!")
    print("Example letter list format:")
    print(json.dumps(example_letter_list, indent=2))
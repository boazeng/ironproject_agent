"""
OrderHeader Agent - Specialized field detection for iron order headers
This agent extracts specific required fields from Hebrew iron/steel order header images using ChatGPT Vision.
It focuses on finding these exact fields: מספר הזמנה, לקוח/פרויקט, שם התוכנית, איש קשר, טלפון, כתובת האתר, משקל כולל
"""

import os
import json
import base64
import requests
import re
import glob
from typing import Dict, Any, Optional, List
from dotenv import load_dotenv
import datetime

load_dotenv()

class OrderHeaderAgent:
    def __init__(self, ocr_provider: str = "chatgpt"):
        self.name = "ORDERHEADER"
        self.ocr_provider = ocr_provider.lower()
        
        # Initialize logging
        self.log_folder = "logs"
        os.makedirs(self.log_folder, exist_ok=True)
        
        # Initialize based on selected provider
        if self.ocr_provider == "chatgpt":
            self.openai_api_key = os.getenv('OPENAI_API_KEY')
            if not self.openai_api_key:
                print(f"[{self.name}] Warning: ChatGPT API key not found, falling back to Google Vision")
                self.ocr_provider = "google"
        
        if self.ocr_provider == "google":
            self.google_api_key = os.getenv('GOOGLE_VISION_API_KEY')
            if not self.google_api_key:
                raise ValueError("No OCR provider available - missing API keys")
    
    def log_chatgpt_request(self, payload: Dict[str, Any]) -> None:
        """
        Log ChatGPT request data to single file (overwrites previous)

        Args:
            payload: The request payload sent to ChatGPT API
        """
        try:
            log_filename = "chatgpt_orderheader_request.json"
            log_path = os.path.join(self.log_folder, log_filename)
            
            # Create a sanitized version of the payload for logging (remove base64 image data)
            sanitized_payload = json.loads(json.dumps(payload))
            
            # Replace base64 image data with placeholder to reduce file size
            for message in sanitized_payload.get("messages", []):
                if isinstance(message.get("content"), list):
                    for content_item in message["content"]:
                        if content_item.get("type") == "image_url":
                            image_url = content_item.get("image_url", {})
                            if "data:image" in image_url.get("url", ""):
                                # Extract just the format info, not the full base64 data
                                data_prefix = image_url["url"].split(",")[0]
                                content_item["image_url"]["url"] = f"{data_prefix},[BASE64_IMAGE_DATA_REMOVED]"
                                content_item["image_url"]["size_info"] = f"Original size: {len(image_url.get('url', ''))} characters"
            
            # Add logging metadata
            log_data = {
                "timestamp": datetime.datetime.now().isoformat(),
                "agent": self.name,
                "request_type": "chatgpt_vision",
                "log_type": "REQUEST",
                "payload": sanitized_payload
            }
            
            with open(log_path, 'w', encoding='utf-8') as f:
                json.dump(log_data, f, indent=2, ensure_ascii=False)
            
            print(f"[{self.name}] Request logged to: {log_path}")

        except Exception as e:
            print(f"[{self.name}] Error logging request: {str(e)}")
    
    def log_chatgpt_response(self, response: Dict[str, Any]) -> None:
        """
        Log ChatGPT response data to single file (overwrites previous)

        Args:
            response: The complete response from ChatGPT API
        """
        try:
            log_filename = "chatgpt_orderheader_response.json"
            log_path = os.path.join(self.log_folder, log_filename)
            
            # Add logging metadata
            log_data = {
                "timestamp": datetime.datetime.now().isoformat(),
                "agent": self.name,
                "response_type": "chatgpt_vision",
                "log_type": "RESPONSE",
                "response": response
            }
            
            with open(log_path, 'w', encoding='utf-8') as f:
                json.dump(log_data, f, indent=2, ensure_ascii=False)

            print(f"[{self.name}] Response logged to: {log_path}")

        except Exception as e:
            print(f"[{self.name}] Error logging response: {str(e)}")

    def log_extracted_fields(self, extracted_fields: List[Dict[str, str]], raw_text: str) -> None:
        """
        Log the specific fields extracted by OrderHeader agent in a clean, readable format
        
        Args:
            extracted_fields: List of extracted field dictionaries
            raw_text: The raw OCR text from ChatGPT
        """
        try:
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            log_filename = f"orderheader_extracted_fields_{timestamp}.json"
            log_path = os.path.join(self.log_folder, log_filename)
            
            # Create clean, readable log data
            clean_fields = {}
            for field_obj in extracted_fields:
                for key, value in field_obj.items():
                    clean_fields[key] = value
            
            log_data = {
                "timestamp": datetime.datetime.now().isoformat(),
                "agent": "OrderHeader Specialist",
                "mission": "Extract specific fields from Hebrew iron order headers",
                "target_fields": [
                    "מספר הזמנה",
                    "לקוח/פרויקט", 
                    "שם התוכנית",
                    "איש קשר",
                    "טלפון",
                    "כתובת האתר",
                    "משקל כולל"
                ],
                "extracted_data": clean_fields,
                "field_count": len(clean_fields),
                "raw_ocr_text": raw_text,
                "notes": f"Found {len(clean_fields)} out of 7 target fields"
            }
            
            with open(log_path, 'w', encoding='utf-8') as f:
                json.dump(log_data, f, indent=2, ensure_ascii=False)
            
            print(f"[{self.name}] OrderHeader extracted fields logged to: {log_path}")
            
            # Also create a simple summary for quick viewing
            summary_filename = f"orderheader_summary_{timestamp}.txt"
            summary_path = os.path.join(self.log_folder, summary_filename)
            
            with open(summary_path, 'w', encoding='utf-8') as f:
                f.write("=== OrderHeader Agent Results ===\n")
                f.write(f"Timestamp: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write(f"Fields Found: {len(clean_fields)}/7\n\n")
                
                for key, value in clean_fields.items():
                    status = "✓ FOUND" if value and value.strip() else "✗ EMPTY"
                    f.write(f"{status}: {key} = '{value}'\n")
                
                f.write(f"\nRaw OCR Text:\n{raw_text}\n")
            
            print(f"[{self.name}] OrderHeader summary logged to: {summary_path}")
            
        except Exception as e:
            print(f"[{self.name}] Error logging extracted fields: {str(e)}")
            
    def analyze_with_google_vision(self, image_path: str) -> Dict[str, Any]:
        """
        Analyze header image using Google Vision API
        
        Args:
            image_path: Path to the order header image
            
        Returns:
            Dictionary containing extracted header fields
        """
        try:
            print(f"[{self.name}] Using Google Vision API for OCR analysis")
            
            if not os.path.exists(image_path):
                return {"success": False, "error": "Image file not found"}
            
            # Encode image to base64
            with open(image_path, "rb") as image_file:
                base64_image = base64.b64encode(image_file.read()).decode('utf-8')
            
            # Google Vision API request
            url = f"https://vision.googleapis.com/v1/images:annotate?key={self.google_api_key}"
            
            payload = {
                "requests": [
                    {
                        "image": {
                            "content": base64_image
                        },
                        "features": [
                            {
                                "type": "TEXT_DETECTION",
                                "maxResults": 50
                            }
                        ]
                    }
                ]
            }
            
            print(f"[{self.name}] Sending request to Google Vision API...")
            response = requests.post(url, json=payload, timeout=30)
            
            if response.status_code == 200:
                result = response.json()
                
                if 'responses' in result and len(result['responses']) > 0:
                    vision_response = result['responses'][0]
                    
                    if 'error' in vision_response:
                        return {
                            "success": False,
                            "error": f"Google Vision error: {vision_response['error'].get('message', 'Unknown error')}",
                            "extracted_fields": [],
                            "raw_text": "",
                            "field_count": 0
                        }
                    
                    # Extract text from response
                    full_text = ""
                    if 'fullTextAnnotation' in vision_response:
                        full_text = vision_response['fullTextAnnotation']['text']
                    elif 'textAnnotations' in vision_response and len(vision_response['textAnnotations']) > 0:
                        full_text = vision_response['textAnnotations'][0]['description']
                    
                    print(f"[{self.name}] Extracted text from Google Vision:")
                    print(f"[{self.name}] Full text:\n{full_text}")
                    print(f"[{self.name}] Text preview: {full_text[:200]}...")
                    
                    # Parse the extracted text to find field-value pairs
                    extracted_fields = self.parse_header_fields(full_text)
                    
                    return {
                        "success": True,
                        "extracted_fields": extracted_fields,
                        "raw_text": full_text,
                        "field_count": len(extracted_fields),
                        "ocr_provider": "google_vision"
                    }
                else:
                    return {
                        "success": False,
                        "error": "No text detected by Google Vision",
                        "extracted_fields": [],
                        "raw_text": "",
                        "field_count": 0
                    }
            else:
                return {
                    "success": False,
                    "error": f"Google Vision API error: {response.status_code} - {response.text}",
                    "extracted_fields": [],
                    "raw_text": "",
                    "field_count": 0
                }
                
        except Exception as e:
            print(f"[{self.name}] Exception in Google Vision analysis: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "extracted_fields": [],
                "raw_text": "",
                "field_count": 0
            }
    
    def parse_header_fields(self, text: str) -> List[Dict[str, str]]:
        """
        Parse header text and extract field-value pairs
        
        Args:
            text: OCR extracted text
            
        Returns:
            List of field-value dictionaries
        """
        extracted_fields = []
        
        # Common field patterns to look for
        field_patterns = [
            (r'לקוח\s*[/:]?\s*פרויקט\s*[:]\s*([^\n\r\t]+)', 'לקוח/פרויקט'),
            (r'איש\s+הקשר\s+באתר\s*[:]\s*([^\n\r\t]+)', 'איש הקשר באתר'),
            (r'טלפון\s*[:]\s*([^\n\r\t]+)', 'טלפון'),
            (r'מס[\'\']\s*הזמנה\s*[:]\s*([^\n\r\t]+)', 'מס\' הזמנה'),
            (r'אתר\s*[:]\s*([^\n\r\t]+)', 'אתר'),
            (r'כתובת\s+האתר\s*[:]\s*([^\n\r\t]+)', 'כתובת האתר'),
            (r'אזור\s+אספקה\s*[:]\s*([^\n\r\t]+)', 'אזור אספקה'),
            (r'תאריך\s*[:]\s*([^\n\r\t]+)', 'תאריך'),
            (r'שם\s+התוכנית\s*[:]\s*([^\n\r\t]+)', 'שם התוכנית'),
            (r'סה["\']כ\s+משקל\s*[:]\s*([^\n\r\t]+)', 'סה"כ משקל'),
            (r'משקל\s*[:]\s*([^\n\r\t]+)', 'משקל'),
            (r'לקוח\s*[:]\s*([^\n\r\t]+)', 'לקוח'),
            # Additional patterns for better detection
            (r'אזור\s*אספקה\s*[:]\s*([^\n\r\t]+)', 'אזור אספקה'),
            (r'כתובת\s*האתר\s*[:]\s*([^\n\r\t]+)', 'כתובת האתר'),
            # More flexible patterns
            (r'(?:^|\s)אתר\s*:\s*([^\n\r\t]+)', 'אתר'),
            (r'(?:^|\s)אזור\s+אספקה\s*:\s*([^\n\r\t]+)', 'אזור אספקה')
        ]
        
        print(f"[{self.name}] Parsing fields from text...")
        print(f"[{self.name}] Text lines for debugging:")
        for i, line in enumerate(text.split('\n')):
            print(f"[{self.name}] Line {i}: '{line}'")
        
        for pattern, field_name in field_patterns:
            matches = re.finditer(pattern, text, re.IGNORECASE | re.MULTILINE | re.UNICODE)
            for match in matches:
                value = match.group(1).strip()
                if value and len(value) > 0:
                    extracted_fields.append({field_name: value})
                    print(f"[{self.name}] Found field: {field_name} = {value}")
        
        # If we didn't find אזור אספקה with patterns, try manual search
        if not any('אזור אספקה' in str(field) for field in extracted_fields):
            print(f"[{self.name}] Trying manual search for אזור אספקה...")
            lines = text.split('\n')
            for line in lines:
                if 'אזור' in line and 'אספקה' in line:
                    print(f"[{self.name}] Found line with אזור אספקה: '{line}'")
                    # Try to extract value after colon
                    parts = line.split(':')
                    if len(parts) >= 2:
                        value = parts[1].strip()
                        if value:
                            extracted_fields.append({'אזור אספקה': value})
                            print(f"[{self.name}] Manually extracted אזור אספקה = {value}")
                    break
        
        # Remove duplicates while preserving order
        seen = set()
        unique_fields = []
        for field in extracted_fields:
            field_key = list(field.keys())[0]
            if field_key not in seen:
                seen.add(field_key)
                unique_fields.append(field)
        
        print(f"[{self.name}] Extracted {len(unique_fields)} unique fields")
        return unique_fields

    def analyze_header_image(self, image_path: str) -> Dict[str, Any]:
        """
        Analyze order header image and extract detailed field information
        
        Args:
            image_path: Path to the order header image
            
        Returns:
            Dictionary containing extracted header fields
        """
        try:
            print(f"\n[{self.name}] Starting header image analysis using {self.ocr_provider}")
            print(f"[{self.name}] Image path: {image_path}")
            
            if not os.path.exists(image_path):
                print(f"[{self.name}] Error: Image file not found at {image_path}")
                return {"success": False, "error": "Image file not found", "extracted_fields": [], "raw_text": "", "field_count": 0}
            
            # Route to appropriate OCR provider (ChatGPT is now primary)
            if self.ocr_provider == "chatgpt":
                return self.analyze_with_chatgpt(image_path)
            else:
                return self.analyze_with_google_vision(image_path)
                
        except Exception as e:
            print(f"[{self.name}] Exception during analysis: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "extracted_fields": [],
                "raw_text": "",
                "field_count": 0
            }
    
    def analyze_with_chatgpt(self, image_path: str) -> Dict[str, Any]:
        """
        Analyze header image using ChatGPT Vision API (fallback method)
        
        Args:
            image_path: Path to the order header image
            
        Returns:
            Dictionary containing extracted header fields
        """
        try:
            print(f"[{self.name}] Using ChatGPT Vision API for OCR analysis")
            
            # Encode image to base64
            with open(image_path, "rb") as image_file:
                base64_image = base64.b64encode(image_file.read()).decode('utf-8')
            
            # Create specialized header analysis prompt for specific fields
            prompt = f"""You are a specialized OrderHeader agent for iron/steel order documents. Your mission is to extract SPECIFIC fields from the Hebrew order header image.

You must find and extract these EXACT fields from the header:

🎯 REQUIRED FIELDS TO FIND:
1. מספר הזמנה (Order Number)
2. לקוח/פרויקט (Customer/Project)
3. שם התוכנית (Program Name) - VERY IMPORTANT: Look carefully for this field, it may appear as "שם התוכנית:", "תוכנית:", or similar
4. איש קשר (Contact Person) - may appear as "איש הקשר באתר"
5. טלפון (Phone)
6. כתובת האתר (Site Address)
7. משקל כולל (Total Weight) - may appear as "סה״כ משקל"

CRITICAL INSTRUCTIONS:
- Extract the EXACT field names as they appear in Hebrew
- For each field, extract its corresponding value
- If a field is visible but empty, include it with empty string ""
- Pay special attention to Hebrew text - be very precise
- Look in table format or key-value pairs
- Some fields may be split across lines
- SCAN THE ENTIRE IMAGE carefully - שם התוכנית might be in a different location
- Look for any text that mentions תוכנית, project name, or program details
- Check corners, edges, and different sections of the header

Return ONLY this JSON format:
{{
    "success": true,
    "extracted_fields": [
        {{"מספר הזמנה": "value_or_empty"}},
        {{"לקוח/פרויקט": "value_or_empty"}},
        {{"שם התוכנית": "value_or_empty"}},
        {{"איש קשר": "value_or_empty"}},
        {{"טלפון": "value_or_empty"}},
        {{"כתובת האתר": "value_or_empty"}},
        {{"משקל כולל": "value_or_empty"}}
    ],
    "raw_text": "Complete OCR text from the image",
    "field_count": 7,
    "notes": "Observations about field detection"
}}

If OCR fails, return:
{{
    "success": false,
    "error": "OCR error description",
    "extracted_fields": [],
    "raw_text": "",
    "field_count": 0
}}

Focus on these 7 fields only. Be extremely accurate with Hebrew text."""

            # Call ChatGPT Vision API
            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self.openai_api_key}"
            }
            
            payload = {
                "model": "gpt-4o",
                "messages": [
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": prompt},
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
                "max_tokens": 2000,
                "temperature": 0.1
            }
            
            print(f"[{self.name}] Sending request to ChatGPT Vision API...")
            
            # Log the request data
            self.log_chatgpt_request(payload)
            
            response = requests.post(
                "https://api.openai.com/v1/chat/completions",
                headers=headers,
                json=payload,
                timeout=60
            )
            
            if response.status_code == 200:
                result = response.json()
                content = result.get('choices', [{}])[0].get('message', {}).get('content', '{}')
                
                # Log the complete response data
                self.log_chatgpt_response(result)
                
                try:
                    print(f"[{self.name}] Raw response length: {len(content)} characters")
                except UnicodeEncodeError:
                    print(f"[{self.name}] Raw response received (Unicode content)")
                
                # Try to parse JSON response
                try:
                    analysis_data = json.loads(content)
                    print(f"[{self.name}] Successfully parsed JSON response")
                    print(f"[{self.name}] Extracted {len(analysis_data.get('extracted_fields', []))} fields")
                    return analysis_data
                    
                except json.JSONDecodeError:
                    # If JSON parsing fails, try to extract JSON from the response
                    import re
                    json_match = re.search(r'\{.*\}', content, re.DOTALL)
                    if json_match:
                        try:
                            analysis_data = json.loads(json_match.group())
                            print(f"[{self.name}] Successfully extracted JSON from response")
                            return analysis_data
                        except json.JSONDecodeError:
                            pass
                    
                    # Fallback: create structured response from raw content
                    print(f"[{self.name}] JSON parsing failed, creating fallback response")
                    return {
                        "success": True,
                        "extracted_fields": [],
                        "raw_text": content,
                        "field_count": 0,
                        "notes": "Response was not in JSON format, raw text provided",
                        "raw_response": content
                    }
                    
            else:
                print(f"[{self.name}] API request failed with status {response.status_code}")
                print(f"[{self.name}] Error: {response.text}")
                return {
                    "success": False,
                    "error": f"API request failed: {response.status_code} - {response.text}",
                    "extracted_fields": [],
                    "raw_text": "",
                    "field_count": 0
                }
                
        except Exception as e:
            print(f"[{self.name}] Exception during analysis: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "extracted_fields": [],
                "raw_text": "",
                "field_count": 0
            }
    
    def process_header_analysis(self, image_filename: str) -> Dict[str, Any]:
        """
        Main method to process header analysis for a given filename
        
        Args:
            image_filename: Name of the header image file (e.g., "CO25S006348_order_header.png")
            
        Returns:
            Complete analysis results
        """
        print(f"\n[{self.name}] Processing header analysis for: {image_filename}")
        
        # Construct full path to header image
        header_folder = "io/fullorder_output/table_detection/order_header"
        image_path = os.path.join(header_folder, image_filename)
        
        if not os.path.exists(image_path):
            print(f"[{self.name}] Error: Header image not found at {image_path}")
            return {
                "success": False,
                "error": f"Header image not found: {image_filename}",
                "extracted_fields": [],
                "raw_text": "",
                "field_count": 0
            }
        
        # Perform the analysis
        analysis_result = self.analyze_header_image(image_path)
        
        # Add metadata
        analysis_result.update({
            "agent": self.name,
            "image_filename": image_filename,
            "image_path": image_path,
            "timestamp": datetime.datetime.now().isoformat(),
            "ocr_provider": self.ocr_provider
        })
        
        print(f"[{self.name}] Analysis complete")
        if analysis_result.get("success"):
            print(f"[{self.name}] Successfully extracted {analysis_result.get('field_count', 0)} fields")
        else:
            print(f"[{self.name}] Analysis failed: {analysis_result.get('error', 'Unknown error')}")
            
        return analysis_result

if __name__ == "__main__":
    # Test the agent with ChatGPT Vision
    print("Testing OrderHeader Agent with ChatGPT Vision API...")
    agent = OrderHeaderAgent(ocr_provider="chatgpt")
    result = agent.process_header_analysis("CO25S006348_order_header.png")
    print(json.dumps(result, indent=2, ensure_ascii=False))
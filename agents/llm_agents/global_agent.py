"""
GLOBAL Agent - Full Order Page Analysis with Hebrew OCR Support
Analyzes complete order documents to extract:
1. Header and header table information
2. Main order table with rows
3. Footer information
"""

import os
import base64
import json
import glob
from typing import Dict, List, Any, Optional
import requests
from PIL import Image
import io
import fitz  # PyMuPDF for PDF handling
from google.cloud import vision
from google.oauth2 import service_account
import numpy as np
import cv2

class GlobalAgent:
    def __init__(self, api_key: str):
        """
        Initialize GLOBAL agent for full order page analysis
        
        Args:
            api_key: OpenAI API key for ChatGPT Vision
        """
        self.api_key = api_key
        self.name = "GLOBAL"
        self.google_vision_client = None
        self.init_google_vision()
        print(f"[{self.name}] Agent initialized - Full order page analysis specialist")
        
    def init_google_vision(self):
        """Initialize Google Vision API for Hebrew OCR"""
        try:
            # Try to load Google Vision credentials
            creds_path = os.getenv("GOOGLE_VISION_CREDENTIALS")
            if creds_path and os.path.exists(creds_path):
                credentials = service_account.Credentials.from_service_account_file(creds_path)
                self.google_vision_client = vision.ImageAnnotatorClient(credentials=credentials)
                print(f"[{self.name}] Google Vision API initialized with Hebrew OCR support")
            else:
                print(f"[{self.name}] Google Vision credentials not found - Hebrew OCR disabled")
        except Exception as e:
            print(f"[{self.name}] Google Vision initialization failed: {e}")
            self.google_vision_client = None
    
    def pdf_to_images(self, pdf_path: str) -> List[np.ndarray]:
        """
        Convert PDF pages to images
        
        Args:
            pdf_path: Path to PDF file
            
        Returns:
            List of images (numpy arrays) for each page
        """
        images = []
        try:
            pdf_document = fitz.open(pdf_path)
            for page_num in range(len(pdf_document)):
                page = pdf_document[page_num]
                # Render at higher resolution for better OCR
                mat = fitz.Matrix(2, 2)  # 2x zoom
                pix = page.get_pixmap(matrix=mat)
                img_data = pix.tobytes("png")
                img = Image.open(io.BytesIO(img_data))
                images.append(np.array(img))
            pdf_document.close()
            print(f"[{self.name}] Converted PDF to {len(images)} images")
        except Exception as e:
            print(f"[{self.name}] Error converting PDF: {e}")
        return images
    
    def extract_hebrew_text(self, image_path: str) -> Dict[str, Any]:
        """
        Extract Hebrew text using Google Vision OCR
        
        Args:
            image_path: Path to image file
            
        Returns:
            Dictionary with extracted text and bounding boxes
        """
        if not self.google_vision_client:
            return {"error": "Google Vision not initialized", "text": "", "blocks": []}
        
        try:
            # Read image
            with open(image_path, 'rb') as image_file:
                content = image_file.read()
            
            image = vision.Image(content=content)
            
            # Perform text detection with Hebrew language hint
            response = self.google_vision_client.document_text_detection(
                image=image,
                image_context={"language_hints": ["he", "en"]}
            )
            
            if response.error.message:
                return {"error": response.error.message, "text": "", "blocks": []}
            
            # Extract full text
            full_text = response.full_text_annotation.text if response.full_text_annotation else ""
            
            # Extract text blocks with positions
            blocks = []
            for page in response.full_text_annotation.pages:
                for block in page.blocks:
                    block_text = ""
                    for paragraph in block.paragraphs:
                        for word in paragraph.words:
                            word_text = ''.join([symbol.text for symbol in word.symbols])
                            block_text += word_text + " "
                    
                    # Get bounding box
                    vertices = block.bounding_box.vertices
                    bbox = {
                        "top": min(v.y for v in vertices),
                        "bottom": max(v.y for v in vertices),
                        "left": min(v.x for v in vertices),
                        "right": max(v.x for v in vertices)
                    }
                    
                    blocks.append({
                        "text": block_text.strip(),
                        "bbox": bbox,
                        "confidence": block.confidence if hasattr(block, 'confidence') else None
                    })
            
            print(f"[{self.name}] Extracted {len(blocks)} text blocks via Hebrew OCR")
            return {
                "text": full_text,
                "blocks": blocks,
                "language": "hebrew/english"
            }
            
        except Exception as e:
            print(f"[{self.name}] Hebrew OCR error: {e}")
            return {"error": str(e), "text": "", "blocks": []}
    
    def analyze_with_chatgpt(self, image_path: str, ocr_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Use ChatGPT Vision to analyze the document structure
        
        Args:
            image_path: Path to image file
            ocr_data: OCR extraction results
            
        Returns:
            Analysis results with identified sections
        """
        try:
            # Encode image
            with open(image_path, "rb") as image_file:
                base64_image = base64.b64encode(image_file.read()).decode('utf-8')
            
            # Prepare OCR context for ChatGPT
            ocr_context = ""
            if ocr_data.get("text"):
                ocr_context = f"\n\nOCR extracted text (Hebrew/English):\n{ocr_data['text'][:2000]}"  # Limit for token size
            
            # Create analysis prompt
            prompt = f"""You are analyzing a full order document page that may contain Hebrew and English text.
            
{ocr_context}

Please analyze this document and identify the following sections:

1. HEADER SECTION:
   - Company name/logo area
   - Order number, date, customer details
   - Extract ALL key-value pairs from header tables, including: לקוח/פרויקט, איש הקשר באתר, טלפון, מס' הזמנה, אתר, כתובת האתר, אזור אספקה, סה"כ משקל
   - Look for both explicit labels and implicit field-value relationships
   - Any header table with metadata

2. MAIN TABLE SECTION:
   - Identify the main order table (the large structured table in the middle)
   - Count ALL DATA ROWS: Include every single row with numbers/data - do NOT exclude any
   - The table should have approximately 6-7 rows of data including the top row
   - EXACT column structure from left to right should be: מס' (number), סה"כ משקל [kg] (total weight), אורך [m] (length), סה"כ יח' (total units), קוטר [mm] (diameter), הערות (notes)
   - CRITICAL: The first data row starts with values like "1, 24.0, 1.5, 18, 12, 150" - do NOT miss this row
   - Extract ALL table data rows completely with correct column mapping
   - Each row should have 6 values corresponding to the 6 columns
   - Note if there are any iron/metal order specifications

3. FOOTER SECTION:
   - Total amounts, summaries
   - Terms and conditions
   - Signatures or approval areas
   - Contact information

For each section, provide:
- Location on page (top/middle/bottom)
- Approximate bounding box if visible
- Key information extracted
- Whether text is in Hebrew, English, or mixed

Return the analysis in this JSON format:
{{
    "document_type": "order_page",
    "language": "hebrew/english/mixed",
    "sections": {{
        "header": {{
            "found": true/false,
            "location": "top",
            "company_name": "",
            "order_number": "",
            "date": "",
            "customer": "",
            "header_table": {{
                "found": true/false,
                "rows": 0,
                "key_values": [
                    {{"field_name": "value"}},
                    "Extract ALL visible key-value pairs including: לקוח/פרויקט, איש הקשר באתר, טלפון, מס' הזמנה, אתר, כתובת האתר, אזור אספקה, סה"כ משקל"
                ]
            }}
        }},
        "main_table": {{
            "found": true/false,
            "location": "middle",
            "row_count": 0,
            "columns": [],
            "contains_iron_orders": true/false,
            "all_items": []
        }},
        "footer": {{
            "found": true/false,
            "location": "bottom",
            "total_amount": "",
            "terms": "",
            "signatures": true/false,
            "contact_info": ""
        }}
    }},
    "summary": "Brief description of the document"
}}"""

            # Call ChatGPT Vision API
            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self.api_key}"
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
            
            response = requests.post(
                "https://api.openai.com/v1/chat/completions",
                headers=headers,
                json=payload,
                timeout=60
            )
            
            if response.status_code == 200:
                result = response.json()
                content = result['choices'][0]['message']['content']
                
                # Try to parse JSON from response
                try:
                    # Extract JSON from the response
                    import re
                    json_match = re.search(r'\{.*\}', content, re.DOTALL)
                    if json_match:
                        analysis = json.loads(json_match.group())
                    else:
                        analysis = {"error": "Could not parse JSON", "raw_response": content}
                except:
                    analysis = {"error": "JSON parsing failed", "raw_response": content}
                
                print(f"[{self.name}] ChatGPT Vision analysis complete")
                return analysis
            else:
                print(f"[{self.name}] ChatGPT API error: {response.status_code}")
                return {"error": f"API error: {response.status_code}", "details": response.text}
                
        except Exception as e:
            print(f"[{self.name}] Error in ChatGPT analysis: {e}")
            return {"error": str(e)}
    
    def analyze_order_page(self, file_path: str) -> Dict[str, Any]:
        """
        Main method to analyze a full order page
        
        Args:
            file_path: Path to order document (PDF or image)
            
        Returns:
            Complete analysis results
        """
        print(f"\n[{self.name}] Starting full order page analysis")
        print(f"[{self.name}] File: {os.path.basename(file_path)}")
        
        results = {
            "file": os.path.basename(file_path),
            "file_type": "pdf" if file_path.lower().endswith('.pdf') else "image",
            "sections": {},
            "ocr_data": {},
            "analysis": {}
        }
        
        try:
            # Handle PDF files
            if file_path.lower().endswith('.pdf'):
                print(f"[{self.name}] Processing PDF document")
                images = self.pdf_to_images(file_path)
                
                if not images:
                    return {"error": "Failed to convert PDF to images"}
                
                # For now, analyze first page only
                # Save first page as temporary image
                temp_image_path = file_path.replace('.pdf', '_page1.png')
                Image.fromarray(images[0]).save(temp_image_path)
                analysis_path = temp_image_path
                
                results["pdf_pages"] = len(images)
                results["analyzing_page"] = 1
            else:
                analysis_path = file_path
            
            # Step 1: Extract Hebrew text using Google Vision OCR
            print(f"[{self.name}] Step 1: Extracting text with Hebrew OCR")
            ocr_data = self.extract_hebrew_text(analysis_path)
            results["ocr_data"] = ocr_data
            
            # Step 2: Analyze document structure with ChatGPT
            print(f"[{self.name}] Step 2: Analyzing document structure with ChatGPT Vision")
            analysis = self.analyze_with_chatgpt(analysis_path, ocr_data)
            results["analysis"] = analysis
            
            # Step 3: Combine results
            if "sections" in analysis:
                results["sections"] = analysis["sections"]
                
            # Step 3.5: Add area position information for detected sections
            results = self.add_area_positions(analysis_path, results)
            
            # Step 4: Extract table images if main table is found
            table_image_path = self.extract_table_image(file_path, results)
            if table_image_path:
                results["table_image_path"] = os.path.relpath(table_image_path)
            
            # Step 5: Extract table header row image
            header_image_path = self.extract_table_header_image(file_path, results)
            if header_image_path:
                results["table_header_image_path"] = os.path.relpath(header_image_path)
            
            # Step 6: Extract order header image
            order_header_image_path = self.extract_order_header_image(file_path, results)
            if order_header_image_path:
                results["order_header_image_path"] = os.path.relpath(order_header_image_path)
            
            # Step 7: Extract shape cells from each table row
            shape_cell_info = self.extract_shape_cells(file_path, results)
            if shape_cell_info:
                # Store both detailed info and path list for backward compatibility
                results["shape_cells"] = shape_cell_info
                results["shape_cell_paths"] = [info["path"] for info in shape_cell_info]
            
            # Clean up temporary file if created
            if file_path.lower().endswith('.pdf') and os.path.exists(temp_image_path):
                os.remove(temp_image_path)
            
            print(f"[{self.name}] Analysis complete")
            return results
            
        except Exception as e:
            print(f"[{self.name}] Error in order page analysis: {e}")
            return {"error": str(e), "file": file_path}
    
    def extract_table_image(self, file_path: str, analysis_results: Dict[str, Any]) -> Optional[str]:
        """
        Extract and save the main table area as an image
        
        Args:
            file_path: Path to the source document
            analysis_results: Results from the analysis containing table information
            
        Returns:
            Path to saved table image or None if extraction failed
        """
        try:
            if not analysis_results.get("analysis", {}).get("sections", {}).get("main_table", {}).get("found"):
                print(f"[{self.name}] No main table found to extract")
                return None
            
            print(f"[{self.name}] Extracting main table image")
            
            # Create output directory
            output_dir = "io/fullorder_output/table_detection"
            os.makedirs(output_dir, exist_ok=True)
            
            # Determine source image
            source_image_path = None
            if file_path.lower().endswith('.pdf'):
                # Convert PDF first page to image
                images = self.pdf_to_images(file_path)
                if images:
                    temp_image_path = file_path.replace('.pdf', '_temp_table_extract.png')
                    Image.fromarray(images[0]).save(temp_image_path)
                    source_image_path = temp_image_path
            else:
                source_image_path = file_path
            
            if not source_image_path or not os.path.exists(source_image_path):
                print(f"[{self.name}] Source image not available for table extraction")
                return None
            
            # Load image with OpenCV
            image = cv2.imread(source_image_path)
            if image is None:
                print(f"[{self.name}] Failed to load image with OpenCV")
                return None
            
            # Convert to grayscale for processing
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            
            # Get image dimensions
            img_height, img_width = image.shape[:2]
            
            # Use more conservative region estimation to avoid cutting off table content
            # Start slightly below the header but leave more room for table content
            
            header_end = int(img_height * 0.15)  # Reduced from 25% to 15% to include more content
            footer_start = int(img_height * 0.95)  # Increased from 85% to 95% to include more content
            
            # Focus on larger section for table detection to capture complete table
            table_region = gray[header_end:footer_start, :]
            
            print(f"[{self.name}] Focusing on expanded table region: rows {header_end}-{footer_start}")
            
            # Apply morphological operations to detect table structure
            kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (3, 3))
            opened = cv2.morphologyEx(table_region, cv2.MORPH_OPEN, kernel)
            
            # Detect horizontal and vertical lines in the table region
            horizontal_kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (40, 1))
            vertical_kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (1, 40))
            
            horizontal_lines = cv2.morphologyEx(opened, cv2.MORPH_OPEN, horizontal_kernel)
            vertical_lines = cv2.morphologyEx(opened, cv2.MORPH_OPEN, vertical_kernel)
            
            # Combine lines to find table structure
            table_structure = cv2.addWeighted(horizontal_lines, 0.5, vertical_lines, 0.5, 0.0)
            
            # Find contours in the table region
            contours, _ = cv2.findContours(table_structure, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            
            if not contours:
                print(f"[{self.name}] No table contours found in region, using estimated bounds")
                # Fallback: use estimated table area with more conservative margins
                x = int(img_width * 0.03)  # Smaller left margin to capture more content
                y = header_end + 10  # Smaller top margin to include first row
                w = int(img_width * 0.94)  # Wider to capture full table
                h = footer_start - header_end - 20  # Smaller bottom margin
            else:
                # Find the largest contour (likely the main table)
                largest_contour = max(contours, key=cv2.contourArea)
                
                # Get bounding rectangle relative to table region
                x_rel, y_rel, w, h = cv2.boundingRect(largest_contour)
                
                # Convert back to full image coordinates
                x = x_rel
                y = header_end + y_rel
                
                # Expand horizontally to capture full table width
                x = max(0, int(img_width * 0.02))  # Small left margin
                w = min(img_width - x, int(img_width * 0.96))  # Almost full width
            
            # Add generous padding around the detected table to ensure nothing is cut off
            padding = 20
            x = max(0, x - padding)
            y = max(0, y - padding)  # Allow padding to extend above header_end if needed
            w = min(img_width - x, w + 2 * padding)
            h = min(img_height - y, h + 2 * padding)  # Allow padding to extend below footer_start if needed
            
            # Extract table area
            table_image = image[y:y+h, x:x+w]
            
            # Save table image to table subfolder
            base_filename = os.path.splitext(os.path.basename(file_path))[0]
            table_filename = f"{base_filename}_main_table.png"
            table_subfolder = os.path.join(output_dir, "table")
            os.makedirs(table_subfolder, exist_ok=True)
            table_path = os.path.join(table_subfolder, table_filename)
            
            cv2.imwrite(table_path, table_image)
            
            # Clean up temporary file if created
            if file_path.lower().endswith('.pdf') and source_image_path.endswith('_temp_table_extract.png'):
                if os.path.exists(source_image_path):
                    os.remove(source_image_path)
            
            print(f"[{self.name}] Table image saved: {table_path}")
            return table_path
            
        except Exception as e:
            print(f"[{self.name}] Error extracting table image: {e}")
            return None
    
    def extract_table_header_image(self, file_path: str, analysis_results: Dict[str, Any]) -> Optional[str]:
        """
        Extract and save only the table header row as an image
        
        Args:
            file_path: Path to the source document
            analysis_results: Results from the analysis containing table information
            
        Returns:
            Path to saved table header image or None if extraction failed
        """
        try:
            if not analysis_results.get("analysis", {}).get("sections", {}).get("main_table", {}).get("found"):
                print(f"[{self.name}] No main table found to extract header from")
                return None
            
            print(f"[{self.name}] Extracting table header row image")
            
            # Create output directory
            output_dir = "io/fullorder_output/table_detection"
            os.makedirs(output_dir, exist_ok=True)
            
            # Determine source image
            source_image_path = None
            if file_path.lower().endswith('.pdf'):
                # Convert PDF first page to image
                images = self.pdf_to_images(file_path)
                if images:
                    temp_image_path = file_path.replace('.pdf', '_temp_header_extract.png')
                    Image.fromarray(images[0]).save(temp_image_path)
                    source_image_path = temp_image_path
            else:
                source_image_path = file_path
            
            if not source_image_path or not os.path.exists(source_image_path):
                print(f"[{self.name}] Source image not available for header extraction")
                return None
            
            # Load image with OpenCV
            image = cv2.imread(source_image_path)
            if image is None:
                print(f"[{self.name}] Failed to load image with OpenCV for header extraction")
                return None
            
            # Convert to grayscale for processing
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            
            # Get image dimensions
            img_height, img_width = image.shape[:2]
            
            # Use same region calculation as main table extraction (updated values)
            header_end = int(img_height * 0.15)  # Top 15% for header (same as main table)
            footer_start = int(img_height * 0.95)  # Bottom 5% for footer (same as main table)
            
            # Focus on the table region first
            table_region = gray[header_end:footer_start, :]
            
            print(f"[{self.name}] Searching for table header in rows {header_end}-{footer_start}")
            
            # Simplified approach: assume header row is at the top of the table area
            print(f"[{self.name}] Using estimated header position at top of table region")
            
            # Capture the complete header row with Hebrew column names
            # Based on the main table image, we need to start higher to get the complete text
            
            # Calculate header row with 10% padding above and below
            # Estimate header row height (typical table row is about 50-60 pixels)
            estimated_header_row_height = 50  # Base header row height
            padding_percentage = 0.10  # 10% padding
            
            # Calculate padding above and below
            vertical_padding = int(estimated_header_row_height * padding_percentage)
            
            # Start position: slightly above table region minus top padding
            header_y_start = header_end - vertical_padding
            # Total height: header row + top padding + bottom padding
            header_row_height = estimated_header_row_height + (2 * vertical_padding)
            header_y_end = header_y_start + header_row_height
            
            print(f"[{self.name}] Header calculation: base_height={estimated_header_row_height}, padding={vertical_padding}")
            print(f"[{self.name}] Extracting header from rows {header_y_start}-{header_y_end} (total height: {header_row_height})")
            
            # Ensure header stays within image bounds but allow starting above header_end
            header_y_start = max(0, header_y_start)  # Don't go above image top
            header_y_end = min(img_height, header_y_end)  # Don't go below image bottom
            
            # Set horizontal bounds to capture full table width
            header_x_start = int(img_width * 0.02)  # Small left margin
            header_x_end = int(img_width * 0.98)    # Small right margin
            
            # Extract header area
            header_image = image[header_y_start:header_y_end, header_x_start:header_x_end]
            
            if header_image.size == 0:
                print(f"[{self.name}] Header extraction resulted in empty image")
                return None
            
            # Save header image to table_header subfolder
            base_filename = os.path.splitext(os.path.basename(file_path))[0]
            header_filename = f"{base_filename}_table_header.png"
            header_subfolder = os.path.join(output_dir, "table_header")
            os.makedirs(header_subfolder, exist_ok=True)
            header_path = os.path.join(header_subfolder, header_filename)
            
            cv2.imwrite(header_path, header_image)
            
            # Clean up temporary file if created
            if file_path.lower().endswith('.pdf') and source_image_path.endswith('_temp_header_extract.png'):
                if os.path.exists(source_image_path):
                    os.remove(source_image_path)
            
            print(f"[{self.name}] Table header image saved: {header_path}")
            print(f"[{self.name}] Header dimensions: {header_image.shape[1]}x{header_image.shape[0]}")
            return header_path
            
        except Exception as e:
            print(f"[{self.name}] Error extracting table header image: {e}")
            return None

    def extract_order_header_image(self, file_path: str, analysis_results: Dict[str, Any]) -> Optional[str]:
        """
        Extract and save the order header (everything above table header) as an image
        
        Args:
            file_path: Path to the source document
            analysis_results: Results from the analysis containing table information
            
        Returns:
            Path to saved order header image or None if extraction failed
        """
        try:
            if not analysis_results.get("analysis", {}).get("sections", {}).get("main_table", {}).get("found"):
                print(f"[{self.name}] No main table found to determine order header region")
                return None
            
            print(f"[{self.name}] Extracting order header image")
            
            # Create output directory
            output_dir = "io/fullorder_output/table_detection"
            os.makedirs(output_dir, exist_ok=True)
            
            # Determine source image
            source_image_path = None
            if file_path.lower().endswith('.pdf'):
                # Convert PDF first page to image
                images = self.pdf_to_images(file_path)
                if images:
                    temp_image_path = file_path.replace('.pdf', '_temp_order_header_extract.png')
                    Image.fromarray(images[0]).save(temp_image_path)
                    source_image_path = temp_image_path
            else:
                source_image_path = file_path
            
            if not source_image_path or not os.path.exists(source_image_path):
                print(f"[{self.name}] Source image not available for order header extraction")
                return None
            
            # Load image with OpenCV
            image = cv2.imread(source_image_path)
            if image is None:
                print(f"[{self.name}] Failed to load image with OpenCV for order header extraction")
                return None
            
            # Get image dimensions
            img_height, img_width = image.shape[:2]
            
            # Use same region calculation as table header extraction to find table start
            header_end = int(img_height * 0.15)  # Same as main table extraction
            
            # Calculate table header position (same as table header extraction logic)
            estimated_header_row_height = 50
            padding_percentage = 0.10
            vertical_padding = int(estimated_header_row_height * padding_percentage)
            table_header_start = header_end - vertical_padding
            
            # Order header is everything from top of document to start of table header
            order_header_start = 0
            order_header_end = max(0, table_header_start)
            
            print(f"[{self.name}] Extracting order header from rows {order_header_start}-{order_header_end}")
            
            # Ensure we have a reasonable height
            if order_header_end - order_header_start < 50:
                order_header_end = order_header_start + 200  # Minimum height for order header
                print(f"[{self.name}] Adjusted order header height to: {order_header_start}-{order_header_end}")
            
            # Set horizontal bounds to capture full width
            order_header_x_start = 0
            order_header_x_end = img_width
            
            # Extract order header area
            order_header_image = image[order_header_start:order_header_end, order_header_x_start:order_header_x_end]
            
            if order_header_image.size == 0:
                print(f"[{self.name}] Order header extraction resulted in empty image")
                return None
            
            # Save order header image to order_header subfolder
            base_filename = os.path.splitext(os.path.basename(file_path))[0]
            header_filename = f"{base_filename}_order_header.png"
            header_subfolder = os.path.join(output_dir, "order_header")
            os.makedirs(header_subfolder, exist_ok=True)
            header_path = os.path.join(header_subfolder, header_filename)
            
            cv2.imwrite(header_path, order_header_image)
            
            # Clean up temporary file if created
            if file_path.lower().endswith('.pdf') and source_image_path.endswith('_temp_order_header_extract.png'):
                if os.path.exists(source_image_path):
                    os.remove(source_image_path)
            
            print(f"[{self.name}] Order header image saved: {header_path}")
            print(f"[{self.name}] Order header dimensions: {order_header_image.shape[1]}x{order_header_image.shape[0]}")
            return header_path
            
        except Exception as e:
            print(f"[{self.name}] Error extracting order header image: {e}")
            return None

    def extract_shape_cells(self, file_path: str, analysis_results: Dict[str, Any]) -> Optional[List[Dict[str, Any]]]:
        """
        Extract shape drawings from each table row and save as individual PNG files
        Now with automatic shape column detection based on column headers

        Args:
            file_path: Path to the source document
            analysis_results: Results from the analysis containing table information

        Returns:
            List of dictionaries containing shape information (path, row_number, column_position) or None if extraction failed
        """
        try:
            # Get user sections if available
            user_sections = analysis_results.get("user_sections", {})

            # We'll now attempt extraction either with user selection or automatic detection
            if user_sections and user_sections.get("shape_column"):
                print(f"[{self.name}] Found user-selected shape column, will use it for extraction")
            else:
                print(f"[{self.name}] No user-selected shape column. Will attempt automatic detection with ChatGPT Vision...")

            main_table = analysis_results.get("analysis", {}).get("sections", {}).get("main_table", {})
            if not main_table.get("found"):
                print(f"[{self.name}] No main table found to extract shape cells")
                return None

            row_count = main_table.get("row_count", 0)
            if row_count == 0:
                print(f"[{self.name}] No table rows found to extract shapes")
                return None

            print(f"[{self.name}] Extracting shape cells from {row_count} table rows using user-selected column")
            
            # Create output directory
            output_dir = "io/fullorder_output/table_detection"
            shapes_subfolder = os.path.join(output_dir, "shapes")
            os.makedirs(shapes_subfolder, exist_ok=True)
            
            # Determine source image
            source_image_path = None
            if file_path.lower().endswith('.pdf'):
                # Convert PDF first page to image
                images = self.pdf_to_images(file_path)
                if images:
                    temp_image_path = file_path.replace('.pdf', '_temp_shapes_extract.png')
                    Image.fromarray(images[0]).save(temp_image_path)
                    source_image_path = temp_image_path
            else:
                source_image_path = file_path
            
            if not source_image_path or not os.path.exists(source_image_path):
                print(f"[{self.name}] Source image not available for shape extraction")
                return None
            
            # Load image with OpenCV
            image = cv2.imread(source_image_path)
            if image is None:
                print(f"[{self.name}] Failed to load image with OpenCV for shape extraction")
                return None
            
            # Get image dimensions
            img_height, img_width = image.shape[:2]
            
            # Use same table region calculation as main table extraction
            header_end = int(img_height * 0.15)
            footer_start = int(img_height * 0.95)
            
            # Calculate table region
            table_y_start = header_end
            table_y_end = footer_start
            table_height = table_y_end - table_y_start
            
            # Estimate row height (divide table height by number of rows + header)
            estimated_row_height = table_height // (row_count + 1)  # +1 for header row
            
            # Skip the header row and start from first data row
            first_data_row_start = table_y_start + estimated_row_height
            
            # Extract table region for line detection
            table_region = image[table_y_start:table_y_end, :]
            
            print(f"[{self.name}] Table region: rows {table_y_start}-{table_y_end}, estimated row height: {estimated_row_height}")
            
            # Convert table region to grayscale for line detection
            gray_table = cv2.cvtColor(table_region, cv2.COLOR_BGR2GRAY)
            
            # Apply threshold to enhance line detection
            _, thresh = cv2.threshold(gray_table, 127, 255, cv2.THRESH_BINARY_INV)
            
            # Detect horizontal lines (table row separators)
            horizontal_kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (gray_table.shape[1] // 20, 1))
            horizontal_lines = cv2.morphologyEx(thresh, cv2.MORPH_OPEN, horizontal_kernel)
            
            # Detect vertical lines (table column separators)
            vertical_kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (1, gray_table.shape[0] // 20))
            vertical_lines = cv2.morphologyEx(thresh, cv2.MORPH_OPEN, vertical_kernel)
            
            # Find horizontal line positions
            horizontal_contours, _ = cv2.findContours(horizontal_lines, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            h_lines = []
            for contour in horizontal_contours:
                x, y, w, h = cv2.boundingRect(contour)
                if w > gray_table.shape[1] * 0.4:  # Lines spanning at least 40% of width
                    h_lines.append(y)
            h_lines = sorted(set(h_lines))
            
            # Find vertical line positions
            vertical_contours, _ = cv2.findContours(vertical_lines, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            v_lines = []
            for contour in vertical_contours:
                x, y, w, h = cv2.boundingRect(contour)
                if h > gray_table.shape[0] * 0.2:  # Lines spanning at least 20% of height
                    v_lines.append(x)
                    # Also add the right edge of the line
                    v_lines.append(x + w)
            v_lines = sorted(set(v_lines))
            
            print(f"[{self.name}] Detected {len(h_lines)} horizontal lines and {len(v_lines)} vertical lines")
            if h_lines:
                print(f"[{self.name}] Horizontal line positions: {h_lines[:10]}{'...' if len(h_lines) > 10 else ''}")
            
            # Determine shape column coordinates
            shape_column_start = None
            shape_column_end = None

            # First check for user-selected shape column
            if user_sections and user_sections.get("shape_column"):
                shape_column_info = user_sections.get("shape_column", {})
                shape_selection = shape_column_info.get("selection", {})

                if shape_selection:
                    # Use user-selected coordinates
                    shape_column_start = int(shape_selection.get("x", 0))
                    shape_column_width = int(shape_selection.get("width", 100))
                    shape_column_end = shape_column_start + shape_column_width
                    print(f"[{self.name}] Using user-selected shape column: x {shape_column_start}-{shape_column_end} (width: {shape_column_width})")

            # If no user selection, try automatic detection with ChatGPT Vision
            if shape_column_start is None:
                print(f"[{self.name}] No user selection, attempting automatic detection with ChatGPT Vision...")

                # Use ChatGPT Vision to detect shape column
                detected_coords = self.detect_shape_column_with_vision(
                    source_image_path,
                    (table_y_start, table_y_end)
                )

                if detected_coords:
                    shape_column_start, shape_column_end = detected_coords
                    print(f"[{self.name}] ChatGPT Vision detected shape column at x: {shape_column_start}-{shape_column_end}")
                else:
                    # Last fallback - estimate middle area
                    print(f"[{self.name}] Automatic detection failed, using estimated middle area")
                    shape_column_start = int(gray_table.shape[1] * 0.3)
                    shape_column_end = int(gray_table.shape[1] * 0.7)
            
            # Ensure we have enough horizontal lines for all rows
            if len(h_lines) < row_count + 1:
                print(f"[{self.name}] Not enough horizontal lines detected ({len(h_lines)}), estimating missing rows")
                # Add estimated positions for missing lines
                if len(h_lines) >= 2:
                    avg_row_height = (h_lines[-1] - h_lines[0]) / (len(h_lines) - 1)
                else:
                    avg_row_height = gray_table.shape[0] / (row_count + 2)
                
                # Fill in missing lines
                while len(h_lines) < row_count + 2:  # +2 for header and bottom
                    if len(h_lines) == 0:
                        h_lines.append(int(avg_row_height * 0.8))  # Header bottom
                    else:
                        h_lines.append(int(h_lines[-1] + avg_row_height))
                h_lines = sorted(h_lines)
            
            shape_paths = []
            base_filename = os.path.splitext(os.path.basename(file_path))[0]
            
            # Extract each row's shape cell using detected boundaries
            for row_num in range(row_count):
                # Calculate proper row boundaries
                if len(h_lines) >= row_count + 1:  # Need at least row_count + 1 lines for row_count data rows
                    # We have enough detected lines (including header)
                    # Skip the first line (header separator) and use subsequent lines for data rows
                    line_index = row_num + 1  # +1 to skip header line
                    if line_index < len(h_lines):
                        row_y_start = h_lines[line_index - 1] if line_index > 0 else 0
                        row_y_end = h_lines[line_index]
                    else:
                        # Last row - from last detected line to bottom
                        row_y_start = h_lines[-1]
                        row_y_end = gray_table.shape[0]
                else:
                    # Not enough lines detected - use estimated row positions
                    # Account for header row in calculations
                    estimated_header_height = gray_table.shape[0] // (row_count + 2)  # +2 for header and padding
                    data_area_start = estimated_header_height
                    data_area_height = gray_table.shape[0] - data_area_start
                    avg_row_height = data_area_height / row_count

                    row_y_start = int(data_area_start + (avg_row_height * row_num))
                    row_y_end = int(data_area_start + (avg_row_height * (row_num + 1)))

                    # Ensure we don't exceed table bounds
                    row_y_end = min(row_y_end, gray_table.shape[0])
                
                print(f"[{self.name}] Row {row_num + 1}: y {row_y_start}-{row_y_end} (height: {row_y_end - row_y_start})")
                
                # Use precise cell boundaries without padding to avoid cutting content
                # Ensure we capture the complete cell content
                cell_y_start = max(0, row_y_start)
                cell_y_end = min(gray_table.shape[0], row_y_end)

                # For x coordinates, we need to handle the coordinate system properly
                # The shape_column coordinates are from the full image, but we're working with table_region
                # So we need to adjust them or extract from the full image

                # Convert table region coordinates back to full image coordinates
                full_img_y_start = table_y_start + cell_y_start
                full_img_y_end = table_y_start + cell_y_end

                # Use the precise shape column coordinates from the full image
                cell_x_start = max(0, shape_column_start)
                cell_x_end = min(img_width, shape_column_end)

                # Extract shape cell from the full image with precise coordinates
                shape_cell = image[full_img_y_start:full_img_y_end, cell_x_start:cell_x_end]
                
                if shape_cell.size == 0:
                    print(f"[{self.name}] Shape cell {row_num + 1} extraction resulted in empty image")
                    continue
                
                # Save shape cell image
                shape_filename = f"{base_filename}_shape_row_{row_num + 1}.png"
                shape_path = os.path.join(shapes_subfolder, shape_filename)
                
                cv2.imwrite(shape_path, shape_cell)
                shape_paths.append(shape_path)
                
                print(f"[{self.name}] Shape cell {row_num + 1} saved: {shape_filename} (dimensions: {shape_cell.shape[1]}x{shape_cell.shape[0]}) at full img y: {full_img_y_start}-{full_img_y_end}, x: {cell_x_start}-{cell_x_end}")
            
            # Clean up temporary file if created
            if file_path.lower().endswith('.pdf') and source_image_path.endswith('_temp_shapes_extract.png'):
                if os.path.exists(source_image_path):
                    os.remove(source_image_path)
            
            # Create shape information with column details
            shape_info_list = []
            for i, shape_path in enumerate(shape_paths):
                shape_info = {
                    "path": os.path.relpath(shape_path),
                    "row_number": i + 1,
                    "column_position": {
                        "start": int(shape_column_start),
                        "end": int(shape_column_end),
                        "width": int(shape_column_end - shape_column_start),
                        "description": "Shape column (צורה)"
                    }
                }
                shape_info_list.append(shape_info)
            
            print(f"[{self.name}] Extracted {len(shape_paths)} shape cells using precise cell boundary detection")
            print(f"[{self.name}] Shape column position: {shape_column_start}-{shape_column_end} pixels")
            return shape_info_list
            
        except Exception as e:
            print(f"[{self.name}] Error extracting shape cells: {e}")
            return None

    def regenerate_shapes_from_column(self, shape_column_filename: str, column_name: str = 'צורה') -> Dict[str, Any]:
        """
        Regenerate individual shape files from the shape column image
        New approach: Extract cells based on table structure, not content detection

        Args:
            shape_column_filename: Filename of the shape column image
            column_name: Name of the column containing shapes (default: 'צורה')

        Returns:
            Dictionary with success status, shapes_generated count, and any errors
        """
        try:
            print(f"[{self.name}] Starting shape regeneration from column: {shape_column_filename} (Column: {column_name})")
            print(f"[{self.name}] Using table-structure-based extraction (no content detection)")

            # Find the shape column image path
            shape_column_path = None
            possible_paths = [
                f"io/fullorder_output/table_detection/shape_column/{shape_column_filename}",
                f"io/fullorder_output/table_detection/shapes/{shape_column_filename}",
                f"io/fullorder_output/{shape_column_filename}"
            ]

            for path in possible_paths:
                if os.path.exists(path):
                    shape_column_path = path
                    break

            if not shape_column_path:
                return {
                    'success': False,
                    'error': f'Shape column image not found: {shape_column_filename}'
                }

            print(f"[{self.name}] Found shape column at: {shape_column_path}")

            # Load the shape column image
            image = cv2.imread(shape_column_path)
            if image is None:
                return {
                    'success': False,
                    'error': f'Could not load image: {shape_column_path}'
                }

            # Create output directory
            shapes_output_dir = "io/fullorder_output/table_detection/shapes"
            os.makedirs(shapes_output_dir, exist_ok=True)

            # Get base filename without extension for output naming
            base_name = os.path.splitext(shape_column_filename)[0].replace('_shape_column', '')

            # Clean up old shape files for this document to avoid confusion
            print(f"[{self.name}] Cleaning up old shape files for {base_name}")
            for filename in os.listdir(shapes_output_dir):
                if filename.startswith(f"{base_name}_shape_row_") and filename.endswith('.png'):
                    old_file_path = os.path.join(shapes_output_dir, filename)
                    try:
                        os.remove(old_file_path)
                        print(f"[{self.name}] Removed old shape file: {filename}")
                    except Exception as e:
                        print(f"[{self.name}] Could not remove old file {filename}: {e}")

            # Use precise cell boundary detection instead of estimated division
            image_height, image_width = image.shape[:2]

            # Convert to grayscale for better line detection
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

            # Detect horizontal lines (table row borders)
            horizontal_lines = self._detect_horizontal_lines(gray)

            if not horizontal_lines:
                print(f"[{self.name}] No horizontal lines detected, falling back to estimated division")
                # Fallback to estimated division
                estimated_rows = 6
                row_height = image_height // estimated_rows
                horizontal_lines = [i * row_height for i in range(estimated_rows + 1)]
                if horizontal_lines[-1] != image_height:
                    horizontal_lines.append(image_height)

            print(f"[{self.name}] Detected {len(horizontal_lines)-1} cells to extract")

            # NEW APPROACH: Simply extract ALL cells without content detection
            # The shape_column image should already contain only the shape column
            # We'll extract every cell and let the user see all of them

            shapes_generated = 0

            # Get expected number of rows from analysis file if available
            expected_rows = 6  # Default
            try:
                # Try to read the most recent analysis file to get actual row count
                analysis_files = glob.glob(os.path.join("io/fullorder_output", "*_ironman_analysis.json"))
                if analysis_files:
                    analysis_files.sort(key=os.path.getmtime, reverse=True)
                    with open(analysis_files[0], 'r', encoding='utf-8') as f:
                        analysis_data = json.load(f)
                        if 'sections' in analysis_data:
                            table_data = analysis_data['sections'].get('main_table', {})
                            if 'row_count' in table_data:
                                expected_rows = table_data['row_count']
                                print(f"[{self.name}] Found {expected_rows} rows in table from analysis")
            except Exception as e:
                print(f"[{self.name}] Could not read row count from analysis: {e}")

            # Extract cells based on uniform division (simple and reliable)
            if len(horizontal_lines) < 2:
                # If no lines detected, divide uniformly
                print(f"[{self.name}] Using uniform division for {expected_rows} rows")
                row_height = image_height // expected_rows

                for i in range(expected_rows):
                    y_start = i * row_height
                    y_end = (i + 1) * row_height if i < expected_rows - 1 else image_height

                    # Small padding to avoid borders
                    padding = 2
                    y_start_padded = max(0, y_start + padding)
                    y_end_padded = min(image_height, y_end - padding)

                    # Extract cell
                    shape_cell = image[y_start_padded:y_end_padded, :]

                    # Save cell
                    row_num = i + 1
                    output_filename = f"{base_name}_shape_row_{row_num}.png"
                    output_path = os.path.join(shapes_output_dir, output_filename)

                    if cv2.imwrite(output_path, shape_cell):
                        shapes_generated += 1
                        print(f"[{self.name}] Saved cell {row_num}: {output_filename} (y: {y_start_padded}-{y_end_padded})")
            else:
                # Use detected lines but extract ALL cells (no content filtering)
                cells_to_extract = min(len(horizontal_lines) - 1, expected_rows)

                for i in range(cells_to_extract):
                    y_start = horizontal_lines[i]
                    y_end = horizontal_lines[i + 1]

                    # Small padding to avoid borders
                    padding = 2
                    y_start_padded = max(0, y_start + padding)
                    y_end_padded = min(image_height, y_end - padding)

                    # Skip very small cells (likely borders)
                    if y_end_padded - y_start_padded < 15:
                        continue

                    # Extract cell
                    shape_cell = image[y_start_padded:y_end_padded, :]

                    # Save cell
                    row_num = shapes_generated + 1
                    output_filename = f"{base_name}_shape_row_{row_num}.png"
                    output_path = os.path.join(shapes_output_dir, output_filename)

                    if cv2.imwrite(output_path, shape_cell):
                        shapes_generated += 1
                        print(f"[{self.name}] Saved cell {row_num}: {output_filename} (y: {y_start_padded}-{y_end_padded})")

            print(f"[{self.name}] Shape regeneration completed: {shapes_generated} shapes generated")

            return {
                'success': True,
                'shapes_generated': shapes_generated,
                'output_directory': shapes_output_dir,
                'message': f'Successfully generated {shapes_generated} shape files from {shape_column_filename}'
            }

        except Exception as e:
            error_msg = f"Error regenerating shapes: {str(e)}"
            print(f"[{self.name}] {error_msg}")
            return {
                'success': False,
                'error': error_msg,
                'shapes_generated': 0
            }

    def _detect_horizontal_lines(self, gray_image):
        """
        Detect horizontal lines in a grayscale image to find table row boundaries

        Args:
            gray_image: Grayscale image (numpy array)

        Returns:
            List of y-coordinates where horizontal lines are detected, sorted from top to bottom
        """
        try:
            height, width = gray_image.shape

            # Apply Gaussian blur to reduce noise
            blurred = cv2.GaussianBlur(gray_image, (3, 3), 0)

            # Detect edges using Canny
            edges = cv2.Canny(blurred, 50, 150)

            # Create a horizontal kernel to detect horizontal lines
            horizontal_kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (width//4, 1))

            # Apply morphological operations to enhance horizontal lines
            horizontal_lines_img = cv2.morphologyEx(edges, cv2.MORPH_OPEN, horizontal_kernel)

            # Find contours of horizontal lines
            contours, _ = cv2.findContours(horizontal_lines_img, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

            # Extract y-coordinates of horizontal lines
            line_positions = []

            for contour in contours:
                # Get bounding rectangle
                x, y, w, h = cv2.boundingRect(contour)

                # Only consider lines that span a significant portion of the width
                if w > width * 0.3 and h <= 5:  # Horizontal line criteria
                    line_positions.append(y)

            # Remove duplicates and sort
            line_positions = sorted(list(set(line_positions)))

            # Add top and bottom boundaries if not present
            if not line_positions or line_positions[0] > 5:
                line_positions.insert(0, 0)
            if not line_positions or line_positions[-1] < height - 5:
                line_positions.append(height)

            # Filter out lines that are too close to each other (merge nearby lines)
            filtered_lines = []
            min_distance = 20  # Minimum distance between lines

            for pos in line_positions:
                if not filtered_lines or pos - filtered_lines[-1] >= min_distance:
                    filtered_lines.append(pos)

            print(f"[{self.name}] Detected horizontal line positions: {filtered_lines}")
            return filtered_lines

        except Exception as e:
            print(f"[{self.name}] Error detecting horizontal lines: {e}")
            return []

    def detect_shape_column_with_vision(self, image_path: str, table_region: tuple) -> Optional[tuple]:
        """
        Use ChatGPT Vision to detect which column contains shape drawings

        Args:
            image_path: Path to the document image
            table_region: Tuple of (y_start, y_end) for table area

        Returns:
            Tuple of (column_start, column_end) or None if detection failed
        """
        try:
            print(f"[{self.name}] Using ChatGPT Vision to detect shape column...")

            # Load the image
            image = cv2.imread(image_path)
            if image is None:
                print(f"[{self.name}] Failed to load image for shape column detection")
                return None

            # Extract table region
            y_start, y_end = table_region
            table_image = image[y_start:y_end, :]

            # Get image dimensions
            height, width = table_image.shape[:2]

            # Sample multiple columns (divide table into vertical strips)
            num_samples = 6  # Check up to 6 columns
            column_width = width // num_samples

            # Create a composite image showing all column samples
            samples = []
            for i in range(num_samples):
                x_start = i * column_width
                x_end = min((i + 1) * column_width, width)

                # Take a sample from middle of table (avoid header)
                sample_y_start = height // 4
                sample_y_end = 3 * height // 4

                column_sample = table_image[sample_y_start:sample_y_end, x_start:x_end]
                samples.append((i, x_start, x_end, column_sample))

            # Create composite image for ChatGPT
            composite_height = max(s[3].shape[0] for s in samples)
            composite_width = sum(s[3].shape[1] for s in samples) + (len(samples) - 1) * 10  # 10px spacing
            composite = np.ones((composite_height, composite_width, 3), dtype=np.uint8) * 255

            x_offset = 0
            for i, (idx, _, _, sample) in enumerate(samples):
                h, w = sample.shape[:2]
                composite[0:h, x_offset:x_offset+w] = sample

                # Add column number
                cv2.putText(composite, f"Col {idx+1}", (x_offset + 5, 20),
                           cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 0), 2)

                x_offset += w + 10

            # Save composite temporarily
            temp_path = "temp_column_detection.png"
            cv2.imwrite(temp_path, composite)

            # Encode image for ChatGPT
            with open(temp_path, "rb") as img_file:
                base64_image = base64.b64encode(img_file.read()).decode('utf-8')

            # Ask ChatGPT to identify the shape column
            prompt = """Look at these table columns from an iron/steel order document.
Which column contains technical drawings or shapes (bent iron shapes)?
The shapes typically look like lines, rectangles, or bent shapes with measurements.

Please respond with ONLY the column number (1-6) that contains the drawings/shapes.
If you see simple lines or geometric shapes for bent iron, that's the shape column.
If no column contains drawings, respond with 0.

Just the number, nothing else."""

            response = requests.post(
                "https://api.openai.com/v1/chat/completions",
                headers={
                    "Content-Type": "application/json",
                    "Authorization": f"Bearer {self.api_key}"
                },
                json={
                    "model": "gpt-4o",
                    "messages": [
                        {
                            "role": "user",
                            "content": [
                                {"type": "text", "text": prompt},
                                {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{base64_image}"}}
                            ]
                        }
                    ],
                    "max_tokens": 10,
                    "temperature": 0
                }
            )

            if response.status_code == 200:
                result = response.json()
                column_num = int(result['choices'][0]['message']['content'].strip())

                if column_num > 0 and column_num <= len(samples):
                    _, x_start, x_end, _ = samples[column_num - 1]
                    print(f"[{self.name}] ChatGPT detected shape column {column_num} at x: {x_start}-{x_end}")

                    # Clean up temp file
                    if os.path.exists(temp_path):
                        os.remove(temp_path)

                    return (x_start, x_end)
                else:
                    print(f"[{self.name}] ChatGPT could not identify shape column")
            else:
                print(f"[{self.name}] ChatGPT Vision API error: {response.status_code}")

            # Clean up temp file
            if os.path.exists(temp_path):
                os.remove(temp_path)

        except Exception as e:
            print(f"[{self.name}] Error in ChatGPT shape column detection: {e}")

        return None

    def _has_drawing_content(self, cell_image):
        """
        Simple and fast check if a cell contains drawing content

        Args:
            cell_image: Cell image (numpy array)

        Returns:
            Boolean indicating whether the cell contains drawing content
        """
        try:
            if cell_image.size == 0:
                return False

            # Convert to grayscale
            gray = cv2.cvtColor(cell_image, cv2.COLOR_BGR2GRAY) if len(cell_image.shape) == 3 else cell_image
            height, width = gray.shape

            # Skip very small cells
            if height < 30 or width < 30:
                return False

            # Simple threshold to detect dark content (drawings) - more sensitive for line drawings
            _, binary = cv2.threshold(gray, 250, 255, cv2.THRESH_BINARY_INV)
            content_pixels = cv2.countNonZero(binary)
            total_pixels = height * width
            content_ratio = content_pixels / total_pixels

            # A cell has content if at least 0.05% of pixels are dark (very sensitive for line drawings)
            has_content = content_ratio >= 0.0005

            print(f"[{self.name}] Cell ({width}x{height}): {content_pixels} dark pixels, ratio {content_ratio:.6f} -> {'HAS DRAWING' if has_content else 'EMPTY'}")

            return has_content

        except Exception as e:
            print(f"[{self.name}] Error analyzing cell content: {e}")
            return False

    def add_area_positions(self, image_path: str, results: Dict[str, Any]) -> Dict[str, Any]:
        """
        Add area positions for detected sections, using stored user selections if available
        
        Args:
            image_path: Path to analyzed image
            results: Analysis results to enhance
            
        Returns:
            Enhanced results with area position information
        """
        try:
            # Load image to get dimensions
            image = cv2.imread(image_path)
            if image is None:
                return results
            
            img_height, img_width = image.shape[:2]
            
            # Check if we have user-defined area positions from previous selections
            user_sections = results.get("user_sections", {})
            
            # Add area positions to sections if they exist
            if "sections" in results:
                sections = results["sections"]
                
                # Order Header Area - use user selection if available, otherwise estimate
                if sections.get("header", {}).get("found"):
                    if "order_header" in user_sections and "selection" in user_sections["order_header"]:
                        # Use user-defined area position
                        user_sel = user_sections["order_header"]["selection"]
                        # Scale from canvas coordinates to original image coordinates
                        # User coordinates are in canvas pixels, need to scale to image pixels
                        # Assume the canvas was scaled to fit in a typical PDF viewer (~600px wide)
                        canvas_scale_x = img_width / 600  # Estimate based on typical canvas size
                        canvas_scale_y = img_height / 800  # Estimate based on typical canvas size
                        
                        sections["header"]["area_position"] = {
                            "x": int(user_sel["x"] * canvas_scale_x),
                            "y": int(user_sel["y"] * canvas_scale_y),
                            "width": int(user_sel["width"] * canvas_scale_x),
                            "height": int(user_sel["height"] * canvas_scale_y),
                            "description": "Order Header Area - User defined",
                            "original_image_width": img_width,
                            "original_image_height": img_height,
                            "source": "user_selection"
                        }
                    else:
                        # Fallback to conservative estimate
                        header_height = int(img_height * 0.08)
                        sections["header"]["area_position"] = {
                            "x": int(img_width * 0.05),
                            "y": int(img_height * 0.01),
                            "width": int(img_width * 0.90),
                            "height": header_height,
                            "description": "Order Header Area - Estimated",
                            "original_image_width": img_width,
                            "original_image_height": img_height,
                            "source": "estimated"
                        }
                
                # Table Header Area - use user selection if available, otherwise estimate
                if sections.get("main_table", {}).get("found"):
                    # Add table header area position
                    if "table_header" not in sections:
                        sections["table_header"] = {"found": True}
                    
                    if "table_header" in user_sections and "selection" in user_sections["table_header"]:
                        # Use user-defined area position
                        user_sel = user_sections["table_header"]["selection"]
                        canvas_scale_x = img_width / 600
                        canvas_scale_y = img_height / 800
                        
                        sections["table_header"]["area_position"] = {
                            "x": int(user_sel["x"] * canvas_scale_x),
                            "y": int(user_sel["y"] * canvas_scale_y),
                            "width": int(user_sel["width"] * canvas_scale_x),
                            "height": int(user_sel["height"] * canvas_scale_y),
                            "description": "Table Header Area - User defined",
                            "original_image_width": img_width,
                            "original_image_height": img_height,
                            "source": "user_selection"
                        }
                    else:
                        # Fallback to estimated positioning
                        header_area_end = int(img_height * 0.08) + int(img_height * 0.01)
                        table_header_start = header_area_end + int(img_height * 0.01)
                        table_header_height = int(img_height * 0.03)
                        sections["table_header"]["area_position"] = {
                            "x": int(img_width * 0.05),
                            "y": table_header_start,
                            "width": int(img_width * 0.90),
                            "height": table_header_height,
                            "description": "Table Header Area - Estimated",
                            "original_image_width": img_width,
                            "original_image_height": img_height,
                            "source": "estimated"
                        }
                    
                    # Main Table Area - use user selection if available, otherwise estimate
                    if "table_area" in user_sections and "selection" in user_sections["table_area"]:
                        # Use user-defined area position
                        user_sel = user_sections["table_area"]["selection"]
                        canvas_scale_x = img_width / 600
                        canvas_scale_y = img_height / 800
                        
                        sections["main_table"]["area_position"] = {
                            "x": int(user_sel["x"] * canvas_scale_x),
                            "y": int(user_sel["y"] * canvas_scale_y),
                            "width": int(user_sel["width"] * canvas_scale_x),
                            "height": int(user_sel["height"] * canvas_scale_y),
                            "description": "Main Table Area - User defined",
                            "original_image_width": img_width,
                            "original_image_height": img_height,
                            "source": "user_selection"
                        }
                    else:
                        # Fallback to estimated positioning
                        # Need to get table_header_start and height from above
                        header_area_end = int(img_height * 0.08) + int(img_height * 0.01)
                        table_header_start = header_area_end + int(img_height * 0.01)
                        table_header_height = int(img_height * 0.03)
                        table_data_start = table_header_start + table_header_height + int(img_height * 0.005)
                        table_data_height = int(img_height * 0.45)
                        
                        sections["main_table"]["area_position"] = {
                            "x": int(img_width * 0.05),
                            "y": table_data_start,
                            "width": int(img_width * 0.90),
                            "height": table_data_height,
                            "description": "Main Table Area - Estimated",
                            "original_image_width": img_width,
                            "original_image_height": img_height,
                            "source": "estimated"
                        }
            
            # Log which areas used user selections vs estimates
            used_user_selections = []
            if "sections" in results:
                for section_name, section_data in results["sections"].items():
                    if section_data.get("area_position", {}).get("source") == "user_selection":
                        used_user_selections.append(section_name)
            
            if used_user_selections:
                print(f"[{self.name}] Using user selections for: {', '.join(used_user_selections)}")
            else:
                print(f"[{self.name}] Using estimated positions for all areas")
                
            print(f"[{self.name}] Added area positions to detected sections")
            return results
            
        except Exception as e:
            print(f"[{self.name}] Error adding area positions: {e}")
            return results


def create_global_agent(api_key: str) -> GlobalAgent:
    """
    Factory function to create GLOBAL agent
    
    Args:
        api_key: OpenAI API key
        
    Returns:
        GlobalAgent instance
    """
    return GlobalAgent(api_key)
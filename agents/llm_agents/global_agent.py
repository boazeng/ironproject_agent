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
   - Any header table with metadata

2. MAIN TABLE SECTION:
   - Identify the main order table
   - Count the number of rows (excluding header row)
   - Identify columns (item number, description, quantity, dimensions, etc.)
   - Extract ALL table items/rows with their complete data, not just samples
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
                "key_values": []
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
            
            # Step 4: Extract table images if main table is found
            table_image_path = self.extract_table_image(file_path, results)
            if table_image_path:
                results["table_image_path"] = os.path.relpath(table_image_path)
            
            # Step 5: Extract table header row image
            header_image_path = self.extract_table_header_image(file_path, results)
            if header_image_path:
                results["table_header_image_path"] = os.path.relpath(header_image_path)
            
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
            
            # Use analysis results to estimate table location
            # Header typically occupies top 20-25% of document
            # Footer typically occupies bottom 10-15% of document  
            # Main table is in the middle section
            
            header_end = int(img_height * 0.25)  # Top 25% for header
            footer_start = int(img_height * 0.85)  # Bottom 15% for footer
            
            # Focus on the middle section for table detection
            table_region = gray[header_end:footer_start, :]
            
            print(f"[{self.name}] Focusing on table region: rows {header_end}-{footer_start}")
            
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
                print(f"[{self.name}] No table contours found in middle region, using estimated bounds")
                # Fallback: use estimated table area
                x = int(img_width * 0.05)  # 5% margin from left
                y = header_end + 20  # Start after header with small margin
                w = int(img_width * 0.90)  # 90% width
                h = footer_start - header_end - 40  # Height between header and footer
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
            
            # Add minimal padding around the detected table
            padding = 10
            x = max(0, x - padding)
            y = max(header_end, y - padding)
            w = min(img_width - x, w + 2 * padding)
            h = min(footer_start - y, h + 2 * padding)
            
            # Extract table area
            table_image = image[y:y+h, x:x+w]
            
            # Save table image
            base_filename = os.path.splitext(os.path.basename(file_path))[0]
            table_filename = f"{base_filename}_main_table.png"
            table_path = os.path.join(output_dir, table_filename)
            
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
            
            # Use similar region calculation as main table extraction
            header_end = int(img_height * 0.25)  # Top 25% for header
            footer_start = int(img_height * 0.85)  # Bottom 15% for footer
            
            # Focus on the table region first
            table_region = gray[header_end:footer_start, :]
            
            print(f"[{self.name}] Searching for table header in rows {header_end}-{footer_start}")
            
            # Simplified approach: assume header row is at the top of the table area
            print(f"[{self.name}] Using estimated header position at top of table region")
            
            # Estimate header row position
            # Header typically starts shortly after the document header ends
            header_y_start = header_end + 20  # Small margin after document header
            header_row_height = 45  # Estimated height for table header row
            header_y_end = header_y_start + header_row_height
            
            # Additional fallback: try to find text density to identify header row
            try:
                # Look for areas with high horizontal contrast (indicating text/borders)
                table_region_top = table_region[:80, :]  # Focus on top part of table region
                
                # Apply threshold to find text areas
                _, thresh = cv2.threshold(table_region_top, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
                
                # Find horizontal projection (sum pixels in each row)
                horizontal_projection = cv2.reduce(255 - thresh, 1, cv2.REDUCE_SUM, dtype=cv2.CV_32SC1)
                horizontal_projection = horizontal_projection.flatten()
                
                if len(horizontal_projection) > 0:
                    # Find the row with highest content (likely header)
                    max_content_row = np.argmax(horizontal_projection)
                    
                    # Adjust header position based on content detection
                    if max_content_row > 10:  # If found content is reasonable
                        header_y_start = header_end + max_content_row - 10
                        header_y_end = header_y_start + header_row_height
                        print(f"[{self.name}] Adjusted header position based on content at row {max_content_row}")
                
            except Exception as e:
                print(f"[{self.name}] Content-based header detection failed: {e}, using default position")
            
            # Ensure header stays within bounds
            header_y_start = max(header_end, header_y_start)
            header_y_end = min(footer_start, header_y_end)
            
            # Set horizontal bounds to capture full table width
            header_x_start = int(img_width * 0.02)  # Small left margin
            header_x_end = int(img_width * 0.98)    # Small right margin
            
            # Extract header area
            header_image = image[header_y_start:header_y_end, header_x_start:header_x_end]
            
            if header_image.size == 0:
                print(f"[{self.name}] Header extraction resulted in empty image")
                return None
            
            # Save header image
            base_filename = os.path.splitext(os.path.basename(file_path))[0]
            header_filename = f"{base_filename}_table_header.png"
            header_path = os.path.join(output_dir, header_filename)
            
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


def create_global_agent(api_key: str) -> GlobalAgent:
    """
    Factory function to create GLOBAL agent
    
    Args:
        api_key: OpenAI API key
        
    Returns:
        GlobalAgent instance
    """
    return GlobalAgent(api_key)
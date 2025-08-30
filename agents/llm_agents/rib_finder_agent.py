import os
import base64
import json
import autogen
from openai import OpenAI
from typing import Dict
import requests
from google.cloud import vision
import io

class RibFinderAgent:
    """
    Specialized agent that uses high-end ChatGPT to accurately count ribs in bent iron drawings
    """
    
    def __init__(self, api_key, google_vision_api_key=None):
        """
        Initialize the RibFinder agent with premium model and Google Vision
        
        Args:
            api_key: OpenAI API key
            google_vision_api_key: Google Vision API key (optional)
        """
        # Initialize OpenAI client
        self.client = OpenAI(api_key=api_key)
        self.api_key = api_key
        
        # Initialize Google Vision API
        self.google_vision_api_key = google_vision_api_key or os.getenv("GOOGLE_VISION_API_KEY")
        self.google_credentials_path = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
        
        # Initialize Google Vision client if credentials available
        self.vision_client = None
        if self.google_credentials_path and os.path.exists(self.google_credentials_path):
            self.vision_client = vision.ImageAnnotatorClient()
            print("[RIBFINDER] Google Vision API initialized with service account")
        elif self.google_vision_api_key:
            print("[RIBFINDER] Google Vision API initialized with API key")
        else:
            print("[RIBFINDER] Google Vision API not configured - using ChatGPT only")
        
        # Configuration for highest quality GPT model
        config_list = [
            {
                "model": "gpt-4o",  # Use premium model for accuracy
                "api_key": api_key,
                "max_tokens": 300,  # Focused response
            }
        ]
        
        # LLM configuration for maximum accuracy
        llm_config = {
            "config_list": config_list,
            "temperature": 0.1,  # Very low temperature for consistent counting
            "timeout": 180,
        }
        
        # Create the rib counting specialist agent
        self.agent = autogen.AssistantAgent(
            name="RIBFINDER_Specialist",
            llm_config=llm_config,
            system_message="""You are a specialist in counting ribs (straight segments) in bent iron drawings.
            
            Your ONLY task is to count ribs accurately. Nothing else.
            
            DEFINITION: A rib = any straight segment of iron between two bends (or ends).
            
            COUNTING METHOD:
            1. Start from one end of the iron
            2. Follow the path segment by segment  
            3. Each straight section = 1 rib
            4. Count systematically
            
            Return ONLY the number as integer.
            """
        )
    
    def encode_image(self, image_path):
        """
        Encode image to base64 for API transmission
        
        Args:
            image_path: Path to the image file
            
        Returns:
            Base64 encoded string
        """
        with open(image_path, "rb") as image_file:
            return base64.b64encode(image_file.read()).decode('utf-8')
    
    def analyze_with_google_vision(self, image_path: str) -> int:
        """
        Analyze image with Google Vision API to count ribs
        
        Args:
            image_path: Path to the drawing image
            
        Returns:
            Number of ribs detected by Google Vision
        """
        try:
            if not self.vision_client:
                return None
                
            with io.open(image_path, 'rb') as image_file:
                content = image_file.read()
            
            image = vision.Image(content=content)
            
            # Perform text detection to help identify dimensions and structure
            response = self.vision_client.text_detection(image=image)
            texts = response.text_annotations
            
            # Perform object detection
            objects_response = self.vision_client.object_localization(image=image)
            objects = objects_response.localized_object_annotations
            
            # Simple heuristic: count detected text groups as potential rib indicators
            # This is a simplified approach - you might need more sophisticated logic
            if texts:
                # Count dimension indicators (numbers) as potential ribs
                dimension_count = len([t for t in texts if any(char.isdigit() for char in t.description)])
                # Basic heuristic: if we see 3 dimension groups, likely 3 ribs
                if dimension_count >= 3:
                    return 3
                elif dimension_count == 2:
                    return 2
                else:
                    return 1
            
            return None
            
        except Exception as e:
            print(f"[RIBFINDER] Google Vision analysis failed: {e}")
            return None
    
    def count_ribs(self, image_path: str) -> Dict:
        """
        Count ribs in a bent iron drawing using both Google Vision and ChatGPT
        
        Args:
            image_path: Path to the drawing image
            
        Returns:
            Dictionary with rib count results including match percentage
        """
        try:
            # Check if file exists
            if not os.path.exists(image_path):
                return {"error": f"Image file not found: {image_path}"}
            
            # Prepare the image for analysis
            base64_image = self.encode_image(image_path)
            
            print(f"[RIBFINDER] Analyzing ribs in: {os.path.basename(image_path)}")
            
            # First, try Google Vision API if available
            google_vision_count = None
            if self.vision_client:
                print("[RIBFINDER] Using Google Vision API...")
                google_vision_count = self.analyze_with_google_vision(image_path)
                if google_vision_count:
                    print(f"[RIBFINDER] Google Vision detected: {google_vision_count} ribs")
            
            # Then use ChatGPT Vision
            print("[RIBFINDER] Using ChatGPT Vision (GPT-4o)...")
            
            # Call premium GPT-4 Vision API
            response = self.client.chat.completions.create(
                model="gpt-4o",  # Premium model for best accuracy
                messages=[
                    {
                        "role": "system",
                        "content": """You are THE EXPERT in counting ribs in bent iron construction drawings.
                        
                        CRITICAL MISSION: Count the exact number of ribs (straight segments) in this drawing.
                        
                        **STEP-BY-STEP COUNTING METHOD**:
                        1. **Visual Inspection**: Look at the COMPLETE drawing from end to end
                        2. **Path Tracing**: Follow the iron path from one end to the other
                        3. **Segment Identification**: Identify each straight section
                        4. **Systematic Counting**: Count each straight segment as 1 rib
                        
                        **SHAPE-SPECIFIC COUNTING**:
                        - **L-shape**: 2 ribs (vertical + horizontal)
                        - **U-shape**: 3 ribs (left vertical + base + right vertical)  
                        - **Z-shape**: 3 ribs (first segment + middle + last segment)
                        - **Complex shapes**: Count every straight segment
                        
                        **CRITICAL RULES**:
                        - A rib = any straight segment between bends or ends
                        - If you see vertical segments on BOTH ends = U-shape = 3 ribs
                        - If you see vertical segment on ONE end = L-shape = 2 ribs
                        - Each bend separates ribs
                        
                        **VISUAL PATTERN GUIDE**:
                        - |___| pattern = 3 ribs (U-shape)
                        - |___ pattern = 2 ribs (L-shape)  
                        - ___| pattern = 2 ribs (L-shape)
                        - |___| with dimensions on both ends = definitely 3 ribs
                        
                        **DIMENSION CLUES**:
                        - If you see dimensions at both vertical ends = count both verticals as ribs
                        - Pattern like "20-405-20" indicates 3 segments = 3 ribs
                        
                        Return ONLY valid JSON:
                        {
                            "rib_count": number,
                            "shape_pattern": "description of what you see (e.g., 'vertical-horizontal-vertical')",
                            "confidence": number (0-100),
                            "reasoning": "brief explanation of counting method"
                        }"""
                    },
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "text",
                                "text": "Count the ribs (straight segments) in this bent iron drawing. Be extremely careful to count ALL segments. Look for vertical segments on both ends - if present, this indicates a U-shape with 3 ribs. Trace the complete path and count systematically."
                            },
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:image/jpeg;base64,{base64_image}",
                                    "detail": "high"  # Use high detail for accurate counting
                                }
                            }
                        ]
                    }
                ],
                max_tokens=300,
                temperature=0.1  # Very low for consistent counting
            )
            
            # Parse the response
            result_text = response.choices[0].message.content
            
            # Try to parse JSON from response
            try:
                # Remove markdown code blocks if present
                if "```json" in result_text:
                    result_text = result_text.split("```json")[1].split("```")[0]
                elif "```" in result_text:
                    result_text = result_text.split("```")[1].split("```")[0]
                
                result = json.loads(result_text.strip())
                result["status"] = "Rib counting complete"
                
            except json.JSONDecodeError:
                # If JSON parsing fails, try to extract number
                try:
                    # Look for number in response
                    import re
                    numbers = re.findall(r'\b(\d+)\b', result_text)
                    if numbers:
                        rib_count = int(numbers[0])
                        result = {
                            "rib_count": rib_count,
                            "shape_pattern": "extracted from text",
                            "confidence": 80,
                            "reasoning": "Extracted from text response",
                            "raw_response": result_text
                        }
                    else:
                        result = {
                            "rib_count": 0,
                            "shape_pattern": "unknown",
                            "confidence": 0,
                            "reasoning": "Failed to parse response",
                            "raw_response": result_text
                        }
                except:
                    result = {
                        "rib_count": 0,
                        "shape_pattern": "unknown", 
                        "confidence": 0,
                        "reasoning": "Complete parsing failure",
                        "raw_response": result_text
                    }
            
            # Get ChatGPT rib count
            chatgpt_count = result.get("rib_count", 0)
            print(f"[RIBFINDER] ChatGPT detected: {chatgpt_count} ribs")
            
            # Calculate match percentage
            if google_vision_count is not None:
                if google_vision_count == chatgpt_count:
                    match_percentage = 100
                    print(f"[RIBFINDER] ✓ AGREEMENT: Both systems detected {chatgpt_count} ribs (100% match)")
                else:
                    match_percentage = 50
                    print(f"[RIBFINDER] ⚠ DISAGREEMENT: Google Vision={google_vision_count}, ChatGPT={chatgpt_count} (50% match)")
                    # Use ChatGPT's count as primary but note the disagreement
                    result["google_vision_count"] = google_vision_count
                    result["chatgpt_count"] = chatgpt_count
            else:
                # Only ChatGPT available
                match_percentage = 75  # Single source confidence
                print(f"[RIBFINDER] ChatGPT only: {chatgpt_count} ribs (75% - single source)")
            
            # Add match percentage to result
            result["match_percentage"] = match_percentage
            result["vision_agreement"] = "AGREE" if match_percentage == 100 else "DISAGREE" if match_percentage == 50 else "SINGLE_SOURCE"
            
            print(f"[RIBFINDER] Analysis complete - Match: {match_percentage}%")
            
            return result
            
        except Exception as e:
            return {"error": f"Rib counting failed: {str(e)}"}
    
    def validate_rib_count(self, image_path: str, expected_count: int = None) -> Dict:
        """
        Validate rib count with additional checks
        
        Args:
            image_path: Path to the drawing image
            expected_count: Expected rib count for validation
            
        Returns:
            Dictionary with validation results
        """
        result = self.count_ribs(image_path)
        
        if "error" not in result:
            rib_count = result.get("rib_count", 0)
            
            # Add validation logic
            if expected_count and rib_count != expected_count:
                print(f"[RIBFINDER] WARNING: Found {rib_count} ribs, expected {expected_count}")
                result["validation_warning"] = f"Count mismatch: found {rib_count}, expected {expected_count}"
            
            # Add confidence assessment
            confidence = result.get("confidence", 0)
            if confidence >= 90:
                result["quality"] = "EXCELLENT"
            elif confidence >= 70:
                result["quality"] = "GOOD"
            elif confidence >= 50:
                result["quality"] = "FAIR"
            else:
                result["quality"] = "POOR"
                
        return result
    
    def get_agent(self):
        """
        Return the AutoGen agent for integration with orchestrator
        
        Returns:
            AutoGen AssistantAgent
        """
        return self.agent


def create_rib_finder_agent(api_key):
    """
    Factory function to create a RibFinder agent
    
    Args:
        api_key: OpenAI API key
        
    Returns:
        RibFinderAgent instance
    """
    return RibFinderAgent(api_key)
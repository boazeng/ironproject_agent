import os
import base64
import json
import autogen
from openai import OpenAI
from typing import Dict
import requests
from google.cloud import vision
import io
import anthropic

class RibFinderAgent:
    """
    Specialized agent that uses high-end ChatGPT to accurately count ribs in bent iron drawings
    """
    
    def __init__(self, api_key, google_vision_api_key=None, anthropic_api_key=None):
        """
        Initialize the RibFinder agent with premium models from OpenAI, Google, and Anthropic
        
        Args:
            api_key: OpenAI API key
            google_vision_api_key: Google Vision API key (optional)
            anthropic_api_key: Anthropic Claude API key (optional)
        """
        # Initialize OpenAI client
        self.client = OpenAI(api_key=api_key)
        self.api_key = api_key
        
        # Initialize Google Vision API
        self.google_vision_api_key = google_vision_api_key or os.getenv("GOOGLE_VISION_API_KEY")
        self.google_credentials_path = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
        
        # Initialize Anthropic Claude client
        self.anthropic_api_key = anthropic_api_key or os.getenv("ANTHROPIC_API_KEY")
        self.claude_client = None
        if self.anthropic_api_key and self.anthropic_api_key != "your_anthropic_api_key_here":
            try:
                self.claude_client = anthropic.Anthropic(api_key=self.anthropic_api_key)
                print("[RIBFINDER] Claude Vision API initialized")
            except Exception as e:
                print(f"[RIBFINDER] Claude Vision API initialization failed: {e}")
                self.claude_client = None
        
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
    
    def analyze_with_claude_vision(self, image_path: str) -> int:
        """
        Analyze image with Claude Vision API to count ribs
        
        Args:
            image_path: Path to the drawing image
            
        Returns:
            Number of ribs detected by Claude Vision
        """
        try:
            if not self.claude_client:
                return None
                
            # Read and encode the image
            with open(image_path, 'rb') as image_file:
                image_data = base64.b64encode(image_file.read()).decode('utf-8')
            
            # Get image MIME type
            mime_type = "image/png" if image_path.endswith('.png') else "image/jpeg"
            
            # Send to Claude Vision API
            response = self.claude_client.messages.create(
                model="claude-3-5-sonnet-20241022",  # Latest Claude model with vision
                max_tokens=1024,
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "text",
                                "text": """You are an expert at analyzing bent iron construction drawings.
                                
                                Your ONLY task is to count the number of ribs (straight segments) in this bent iron shape.
                                
                                CRITICAL INSTRUCTIONS:
                                1. A rib is ANY straight segment between bends
                                2. Count ALL straight segments systematically
                                3. Common patterns:
                                   - L-shape = 2 ribs
                                   - U-shape = 3 ribs
                                   - Z-shape = 3 ribs
                                   - Complex shapes = 4+ ribs
                                
                                Look for vertical segments on BOTH ends of horizontal segments.
                                If you see |___| pattern, that's 3 ribs (U-shape).
                                
                                Return ONLY a JSON object: {"rib_count": number}"""
                            },
                            {
                                "type": "image",
                                "source": {
                                    "type": "base64",
                                    "media_type": mime_type,
                                    "data": image_data
                                }
                            }
                        ]
                    }
                ]
            )
            
            # Parse response
            result_text = response.content[0].text
            
            # Try to parse JSON
            try:
                if "```json" in result_text:
                    result_text = result_text.split("```json")[1].split("```")[0]
                elif "```" in result_text:
                    result_text = result_text.split("```")[1].split("```")[0]
                
                result = json.loads(result_text.strip())
                return result.get("rib_count", None)
                
            except json.JSONDecodeError:
                # Try to extract number from text
                import re
                numbers = re.findall(r'\b(\d+)\b', result_text)
                if numbers:
                    return int(numbers[0])
                return None
                
        except Exception as e:
            print(f"[RIBFINDER] Claude Vision analysis failed: {e}")
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
            
            # Initialize Claude count
            claude_count = None
            
            # Check if Google Vision and ChatGPT disagree - if so, use Claude as tie-breaker
            if google_vision_count is not None and google_vision_count != chatgpt_count:
                print(f"[RIBFINDER] ⚠ DISAGREEMENT: Google={google_vision_count}, ChatGPT={chatgpt_count}")
                
                # Use Claude Vision as tie-breaker if available
                if self.claude_client:
                    print("[RIBFINDER] Using Claude Vision as tie-breaker...")
                    claude_count = self.analyze_with_claude_vision(image_path)
                    if claude_count:
                        print(f"[RIBFINDER] Claude detected: {claude_count} ribs")
                        
                        # Determine final count based on agreement
                        if claude_count == chatgpt_count:
                            print(f"[RIBFINDER] ✓ RESOLUTION: Claude agrees with ChatGPT ({chatgpt_count} ribs)")
                            result["rib_count"] = chatgpt_count
                            match_percentage = 67  # 2 out of 3 agree
                            result["vision_agreement"] = "MAJORITY_CHATGPT_CLAUDE"
                        elif claude_count == google_vision_count:
                            print(f"[RIBFINDER] ✓ RESOLUTION: Claude agrees with Google ({google_vision_count} ribs)")
                            result["rib_count"] = google_vision_count
                            match_percentage = 67  # 2 out of 3 agree
                            result["vision_agreement"] = "MAJORITY_GOOGLE_CLAUDE"
                        else:
                            print(f"[RIBFINDER] ⚠ NO CONSENSUS: All three systems disagree!")
                            print(f"  Google={google_vision_count}, ChatGPT={chatgpt_count}, Claude={claude_count}")
                            # Use ChatGPT as default but with low confidence
                            result["rib_count"] = chatgpt_count
                            match_percentage = 33  # All disagree
                            result["vision_agreement"] = "ALL_DISAGREE"
                        
                        # Store all counts for transparency
                        result["google_vision_count"] = google_vision_count
                        result["chatgpt_count"] = chatgpt_count
                        result["claude_count"] = claude_count
                    else:
                        # Claude failed, stick with original disagreement
                        match_percentage = 50
                        result["vision_agreement"] = "DISAGREE_NO_TIEBREAKER"
                        result["google_vision_count"] = google_vision_count
                        result["chatgpt_count"] = chatgpt_count
                else:
                    # No Claude available for tie-breaking
                    match_percentage = 50
                    result["vision_agreement"] = "DISAGREE_NO_TIEBREAKER"
                    result["google_vision_count"] = google_vision_count
                    result["chatgpt_count"] = chatgpt_count
                    
            elif google_vision_count is not None and google_vision_count == chatgpt_count:
                # Google and ChatGPT agree - perfect!
                match_percentage = 100
                print(f"[RIBFINDER] ✓ AGREEMENT: Both systems detected {chatgpt_count} ribs (100% match)")
                result["vision_agreement"] = "AGREE"
                
            elif google_vision_count is None:
                # Only ChatGPT available
                match_percentage = 75  # Single source confidence
                print(f"[RIBFINDER] ChatGPT only: {chatgpt_count} ribs (75% - single source)")
                result["vision_agreement"] = "SINGLE_SOURCE"
            
            # Add match percentage to result
            result["match_percentage"] = match_percentage
            
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
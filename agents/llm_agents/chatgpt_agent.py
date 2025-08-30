import os
import base64
import json
import autogen
from openai import OpenAI
from PIL import Image
import io

class ChatGPTVisionAgent:
    """
    Agent that uses ChatGPT with vision capabilities to analyze bent iron drawings
    """
    
    def __init__(self, api_key):
        """
        Initialize the ChatGPT vision agent
        
        Args:
            api_key: OpenAI API key
        """
        # Initialize OpenAI client
        self.client = OpenAI(api_key=api_key)
        self.api_key = api_key
        
        # Configuration for GPT-4o Vision (using latest cost-efficient model)
        config_list = [
            {
                "model": "gpt-4o-mini",  
                "api_key": api_key,
                "max_tokens": 500,  # Limit tokens for cost control
            }
        ]
        
        # LLM configuration
        llm_config = {
            "config_list": config_list,
            "temperature": 0.3,  # Lower temperature for accurate analysis
            "timeout": 120,
        }
        
        # Create the vision analysis agent
        self.agent = autogen.AssistantAgent(
            name="ChatGPT_Vision_Analyzer",
            llm_config=llm_config,
            system_message="""You are a specialized agent for analyzing bent iron order drawings.
            
            Your task is to:
            1. Identify the shape type (L-shape, U-shape, Z-shape, stirrup, etc.)
            2. Extract all visible dimensions in millimeters
            3. Identify bend angles
            4. Determine the iron bar diameter if visible
            5. Count the number of bends
            
            Return results in this format:
            {
                "shape_type": "identified shape",
                "dimensions": {
                    "length_1": value,
                    "length_2": value,
                    "height": value,
                    "width": value
                },
                "bend_angles": [angle1, angle2],
                "bar_diameter": value,
                "number_of_bends": count,
                "confidence": 0-100
            }
            
            Be precise with measurements and indicate if any dimension is unclear.
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
    
    def analyze_drawing(self, image_path):
        """
        Analyze a bent iron drawing using ChatGPT vision
        
        Args:
            image_path: Path to the drawing image
            
        Returns:
            Dictionary with analysis results
        """
        try:
            # Check if file exists
            if not os.path.exists(image_path):
                return {"error": f"Image file not found: {image_path}"}
            
            # Prepare the image for analysis
            base64_image = self.encode_image(image_path)
            
            print(f"Analyzing image: {image_path}")
            print("Sending to ChatGPT Vision API...")
            
            # Call GPT-4 Vision API
            response = self.client.chat.completions.create(
                model="gpt-4o-mini",  # Using cost-efficient model with vision
                messages=[
                    {
                        "role": "system",
                        "content": """You are an expert in deciphering drawings of bent iron shapes for construction.

                        IMPORTANT: Analyze the COMPLETE shape geometry, not just partial segments.

                        For bent iron analysis:
                        1. **Shape Recognition**: 
                           - L-shape: 2 ribs meeting at 90°
                           - U-shape: 3 ribs (left leg + base + right leg)
                           - Z-shape: 3 ribs with alternating directions
                           - Straight: 1 rib with no bends
                        
                        2. **Rib Counting**: Count ALL segments separated by bends:
                           - Each straight segment = 1 rib
                           - Include vertical legs AND horizontal bases
                           - For U-shapes: left leg (rib 1) + base (rib 2) + right leg (rib 3)
                        
                        3. **Dimension Analysis**:
                           - Look for ALL numerical values on the drawing
                           - Measure each rib/segment independently
                           - Include both short legs and long bases
                        
                        4. **Angle Analysis**:
                           - 90° = perpendicular bends
                           - 180° = straight continuation (no bend)
                           - Measure angles between consecutive ribs
                        
                        CRITICAL: If you see a U-shape (vertical-horizontal-vertical), count it as 3 ribs, not 2!
                        
                        Return ONLY valid JSON in this exact format:
                        {
                            "shape_type": "string (L, U, Z, straight iron, etc.)",
                            "number_of_ribs": number,
                            "sides": [
                                {
                                    "side_number": number,
                                    "length": number,
                                    "angle_to_next": number,
                                    "description": "string (e.g., left leg, base, right leg)"
                                }
                            ],
                            "angles_between_ribs": [numbers],
                            "confidence": number (0-100)
                        }"""
                    },
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "text",
                                "text": "Analyze this bent iron drawing. Identify the shape type, count the ribs, find the angles between ribs, and extract the length measurements shown on the drawing."
                            },
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:image/jpeg;base64,{base64_image}",
                                    "detail": "low"  # Use low detail for cost savings
                                }
                            }
                        ]
                    }
                ],
                max_tokens=500,
                temperature=0.3
            )
            
            # Parse the response
            result_text = response.choices[0].message.content
            print(f"API Response: {result_text}")
            
            # Try to parse JSON from response
            try:
                # Remove markdown code blocks if present
                if "```json" in result_text:
                    result_text = result_text.split("```json")[1].split("```")[0]
                elif "```" in result_text:
                    result_text = result_text.split("```")[1].split("```")[0]
                
                result = json.loads(result_text.strip())
                result["status"] = "Analysis complete"
            except json.JSONDecodeError:
                # If JSON parsing fails, return structured error
                result = {
                    "shape_type": "Unknown",
                    "number_of_ribs": 0,
                    "sides": [],
                    "angles_between_ribs": [],
                    "confidence": 0,
                    "status": "JSON parsing failed",
                    "raw_response": result_text
                }
            
            return result
            
        except Exception as e:
            return {"error": f"Analysis failed: {str(e)}"}
    
    def recheck_analysis(self, image_path, previous_result):
        """
        Reanalyze a drawing with more careful attention after user rejection
        
        Args:
            image_path: Path to the drawing image
            previous_result: Previous analysis that was rejected
            
        Returns:
            Dictionary with revised analysis results
        """
        try:
            # Check if file exists
            if not os.path.exists(image_path):
                return {"error": f"Image file not found: {image_path}"}
            
            # Prepare the image for analysis
            base64_image = self.encode_image(image_path)
            
            print(f"Rechecking image: {image_path}")
            print("Sending recheck request to ChatGPT Vision API...")
            
            # Call GPT-4 Vision API with recheck instructions
            response = self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {
                        "role": "system",
                        "content": """You are an expert in deciphering drawings of bent iron shapes for construction.
                        
                        IMPORTANT: Your previous analysis was rejected by the user. Please recheck more carefully.
                        
                        CRITICAL REVIEW POINTS:
                        1. **Complete Shape Analysis**: Don't miss any segments!
                           - U-shape = 3 ribs (left leg + base + right leg)
                           - L-shape = 2 ribs (vertical + horizontal)
                           - Look for VERTICAL-HORIZONTAL-VERTICAL patterns
                        
                        2. **Rib Counting Rules**:
                           - Count EVERY straight segment separated by bends
                           - If you see symmetrical legs on both sides, it's likely U-shape
                           - Don't combine multiple segments into one rib
                        
                        3. **Dimension Detection**:
                           - Find ALL numbers on the drawing
                           - Each rib should have its own length measurement
                           - Look for small dimensions (like 20mm) for legs
                           - Look for large dimensions (like 425mm) for bases
                        
                        4. **Shape Geometry**:
                           - U-shape: Two short verticals + one long horizontal
                           - L-shape: One vertical + one horizontal
                           - Analyze the COMPLETE path of the iron
                        
                        Previous result was: {previous_result}
                        
                        Return ONLY valid JSON in this exact format:
                        {
                            "shape_type": "string (L, U, Z, straight iron, etc.)",
                            "number_of_ribs": number,
                            "sides": [
                                {
                                    "side_number": number,
                                    "length": number,
                                    "angle_to_next": number,
                                    "description": "string (e.g., left leg, base, right leg)"
                                }
                            ],
                            "angles_between_ribs": [numbers],
                            "confidence": number (0-100)
                        }"""
                    },
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "text",
                                "text": f"Please recheck this bent iron drawing more carefully. My previous analysis was: {previous_result}. The user rejected it, so please examine the drawing again with extra attention to detail."
                            },
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:image/jpeg;base64,{base64_image}",
                                    "detail": "high"  # Use high detail for recheck
                                }
                            }
                        ]
                    }
                ],
                max_tokens=500,
                temperature=0.1  # Lower temperature for more consistent recheck
            )
            
            # Parse the response
            result_text = response.choices[0].message.content
            print(f"Recheck API Response: {result_text}")
            
            # Try to parse JSON from response
            try:
                # Remove markdown code blocks if present
                if "```json" in result_text:
                    result_text = result_text.split("```json")[1].split("```")[0]
                elif "```" in result_text:
                    result_text = result_text.split("```")[1].split("```")[0]
                
                result = json.loads(result_text.strip())
                result["status"] = "Recheck complete"
            except json.JSONDecodeError:
                # If JSON parsing fails, return structured error
                result = {
                    "shape_type": "Unknown",
                    "number_of_ribs": 0,
                    "sides": [],
                    "angles_between_ribs": [],
                    "confidence": 0,
                    "status": "Recheck JSON parsing failed",
                    "raw_response": result_text
                }
            
            return result
            
        except Exception as e:
            return {"error": f"Recheck failed: {str(e)}"}
    
    def get_agent(self):
        """
        Return the AutoGen agent for integration with orchestrator
        
        Returns:
            AutoGen AssistantAgent
        """
        return self.agent


def create_chatgpt_vision_agent(api_key):
    """
    Factory function to create a ChatGPT vision agent
    
    Args:
        api_key: OpenAI API key
        
    Returns:
        ChatGPTVisionAgent instance
    """
    return ChatGPTVisionAgent(api_key)
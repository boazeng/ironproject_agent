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
        
        # Create the vision analysis agent (CHATAN)
        self.agent = autogen.AssistantAgent(
            name="CHATAN_Analyser",
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
            
            print(f"[CHATAN] Analyzing image: {os.path.basename(image_path)}")
            print("[CHATAN] Sending to Vision API...")
            
            # Call GPT-4 Vision API
            response = self.client.chat.completions.create(
                model="gpt-4o-mini",  # Using cost-efficient model with vision
                messages=[
                    {
                        "role": "system",
                        "content": """You are an expert in deciphering drawings of bent iron shapes for construction.

                        STEP 1: MANDATORY SHAPE CHECK - LOOK AT THE COMPLETE DRAWING!
                        
                        **CRITICAL ANALYSIS SEQUENCE**:
                        1. Look at the LEFT end of the horizontal line - is there a vertical segment?
                        2. Look at the RIGHT end of the horizontal line - is there a vertical segment?
                        3. If BOTH ends have verticals → U-SHAPE with 3 RIBS
                        4. If only ONE end has vertical → L-SHAPE with 2 RIBS
                        
                        **VISUAL PATTERN RECOGNITION**:
                        - U-shape pattern: |___| or ⎸‾‾‾⎸ (vertical on BOTH sides)
                        - L-shape pattern: |___ or ___| (vertical on ONE side only)
                        
                        **MANDATORY U-SHAPE IDENTIFICATION**:
                        The drawing shows: 20 |_____405_____| 20
                        This is clearly a U-SHAPE with:
                        - Left vertical leg (20mm)
                        - Horizontal base (405mm)  
                        - Right vertical leg (20mm)
                        = 3 RIBS TOTAL
                        
                        COMPREHENSIVE SHAPE IDENTIFICATION:
                        Analyze ANY bent iron shape regardless of complexity. Count ALL segments separated by bends.
                        
                        COMMON SHAPES (but not limited to these):
                        - **Straight bar**: 1 rib, no bends
                        - **L-shape**: 2 ribs (vertical + horizontal) at 90°
                        - **U-shape**: 3 ribs (left leg + base + right leg)
                        - **Z-shape**: 3 ribs with alternating directions
                        - **C-shape**: 3 ribs curved configuration
                        - **S-shape**: Multiple ribs in S-curve
                        - **Step-shape**: Multiple ribs creating steps
                        - **Multi-bend**: 4+ ribs with multiple bends
                        - **Box-shape**: 4 ribs forming rectangle
                        - **H-shape**: Multiple ribs in H configuration
                        - **T-shape**: 3 ribs in T configuration
                        - **Cross-shape**: 4+ ribs crossing
                        - **Spiral**: Multiple ribs in spiral
                        - **Custom**: Any unique bent configuration
                        
                        SHAPE DETECTION RULES:
                        - Count EVERY straight segment as a separate rib
                        - A rib = any straight section between two bends
                        - Complex shapes can have 5, 6, 7, 8+ ribs
                        - Don't limit yourself to simple L/U shapes
                        
                        **UNIVERSAL RIB COUNTING METHOD**:
                        1. Follow the iron path from start to end
                        2. Each straight segment = 1 rib
                        3. Each bend = transition between ribs
                        4. Count systematically: rib1 → bend → rib2 → bend → rib3, etc.
                        
                        **COMPLEX SHAPE ANALYSIS**:
                        - **Multi-bend stirrups**: Can have 6-8+ ribs
                        - **Reinforcement bars**: Various configurations
                        - **Custom brackets**: Unique bent patterns
                        - **Structural elements**: Complex geometries
                        
                        **DIMENSION ANALYSIS**:
                        - Look for ALL numerical values on the drawing
                        - Each rib should have its own dimension
                        - Some ribs may share dimensions (e.g., symmetrical legs)
                        - Measure each segment independently
                        
                        **ANGLE ANALYSIS**:
                        - 90° = perpendicular bends (most common)
                        - 45° = angled bends
                        - 135° = obtuse bends  
                        - 60°, 120° = special angles
                        - Custom angles for specific applications
                        
                        **DESCRIPTION GUIDELINES**:
                        - Name each rib descriptively (e.g., "top horizontal", "left vertical", "diagonal connector")
                        - For complex shapes, use position-based names
                        - Be specific about rib function and orientation
                        
                        CRITICAL: If you see vertical segments on BOTH ends = U-SHAPE with 3 RIBS!
                        
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
                                "text": "Analyze this bent iron drawing. CRITICAL: Look carefully at BOTH ends of the horizontal line - are there vertical segments on both the left AND right sides? If yes, this is a U-shape with 3 ribs. If only one end has a vertical, it's an L-shape with 2 ribs. Count all ribs, find angles, and extract measurements."
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
            print(f"[CHATAN] Analysis complete")
            
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
            
            print(f"[CHATAN] Rechecking image: {os.path.basename(image_path)}")
            print("[CHATAN] Sending recheck request to Vision API...")
            
            # Call GPT-4 Vision API with recheck instructions
            response = self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {
                        "role": "system",
                        "content": """You are an expert in deciphering drawings of bent iron shapes for construction.
                        
                        IMPORTANT: Your previous analysis was rejected. Please recheck more carefully.
                        
                        CRITICAL - COMPREHENSIVE SHAPE RECHECK:
                        Analyze the COMPLETE shape, no matter how complex. Don't limit to simple L/U shapes.
                        
                        **UNIVERSAL RECHECK METHOD**:
                        1. **Trace the iron path completely** from one end to the other
                        2. **Count every straight segment** = separate rib
                        3. **Identify all bends** = transitions between ribs
                        4. **Complex shapes welcome**: 4, 5, 6, 7, 8+ ribs possible
                        
                        **SHAPE COMPLEXITY LEVELS**:
                        - **Simple**: L-shape (2 ribs), U-shape (3 ribs)
                        - **Moderate**: Z-shape (3 ribs), T-shape (3 ribs), Step (4+ ribs)
                        - **Complex**: Multi-bend stirrups (6+ ribs), Custom brackets (4+ ribs)
                        - **Advanced**: Box shapes (4 ribs), H-shapes (5+ ribs), Spirals (many ribs)
                        
                        **RECHECK PRIORITIES**:
                        1. **Don't miss any segments**: Every straight section counts
                        2. **Complex is normal**: Construction uses many multi-bend shapes
                        3. **Systematic counting**: Follow the iron path segment by segment
                        4. **Detailed descriptions**: Name each rib clearly
                        
                        **DIMENSION RECHECK**:
                        - Look for ALL numbers on the drawing
                        - Each rib should have dimensions (some may be identical)
                        - Check for small dimensions (legs) and large dimensions (spans)
                        - Missing dimensions should be identified as 0 for reanalysis
                        
                        **ANGLE VARIETY**:
                        - Not just 90° - look for 45°, 135°, 60°, 120°, custom angles
                        - Each bend angle affects the overall shape classification
                        
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
            print(f"[CHATAN] Recheck analysis complete")
            
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
    
    def analyze_with_rib_count(self, image_path, rib_finder_result):
        """
        Analyze a drawing with pre-determined rib count from RibFinder
        
        Args:
            image_path: Path to the drawing image
            rib_finder_result: Results from RibFinder agent
            
        Returns:
            Dictionary with analysis results using established rib count
        """
        try:
            # Check if file exists
            if not os.path.exists(image_path):
                return {"error": f"Image file not found: {image_path}"}
            
            # Extract RibFinder information
            established_rib_count = rib_finder_result.get("rib_count", 0)
            shape_pattern = rib_finder_result.get("shape_pattern", "unknown")
            ribfinder_confidence = rib_finder_result.get("confidence", 0)
            
            # Prepare the image for analysis
            base64_image = self.encode_image(image_path)
            
            print(f"[CHATAN] Analyzing with established rib count: {established_rib_count}")
            print(f"[CHATAN] RibFinder pattern: {shape_pattern}")
            print("[CHATAN] Sending detailed analysis request...")
            
            # Call GPT-4 Vision API with RibFinder context
            response = self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {
                        "role": "system",
                        "content": f"""You are an expert in analyzing bent iron shapes for construction.
                        
                        IMPORTANT: The rib count has already been established by our premium RibFinder specialist.
                        
                        **ESTABLISHED FACTS** (DO NOT CHANGE):
                        - RIB COUNT: {established_rib_count} ribs (determined by GPT-4o specialist)
                        - SHAPE PATTERN: {shape_pattern}
                        - RIBFINDER CONFIDENCE: {ribfinder_confidence}%
                        
                        **YOUR TASK**: Provide detailed analysis of these {established_rib_count} ribs:
                        1. Extract EXACT dimensions for each of the {established_rib_count} ribs - look carefully at ALL numbers in the drawing
                        2. Each rib may have different dimensions - don't assume they're all the same
                        3. Look for numbers near each segment - horizontal base may differ from vertical legs
                        4. Determine angles between ribs
                        5. Provide descriptive names for each rib
                        6. Identify overall shape type based on the {established_rib_count} ribs
                        
                        **CRITICAL INSTRUCTIONS**:
                        - Use EXACTLY {established_rib_count} ribs in your analysis
                        - Do NOT recount ribs - this has been done by premium model
                        - Focus on extracting dimensions, angles, and descriptions
                        - If {established_rib_count} = 3, expect U-shape pattern
                        - If {established_rib_count} = 2, expect L-shape pattern
                        
                        Return ONLY valid JSON in this exact format:
                        {{
                            "shape_type": "string (based on {established_rib_count} ribs)",
                            "number_of_ribs": {established_rib_count},
                            "sides": [
                                {{
                                    "side_number": number,
                                    "length": number,
                                    "angle_to_next": number,
                                    "description": "string (e.g., left leg, base, right leg)"
                                }}
                            ],
                            "angles_between_ribs": [numbers],
                            "confidence": number (0-100)
                        }}"""
                    },
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "text",
                                "text": f"Analyze this bent iron drawing in detail. RibFinder has already determined this has EXACTLY {established_rib_count} ribs with pattern '{shape_pattern}'. Your job is to extract PRECISE dimensions for these {established_rib_count} ribs. CRITICAL: Look carefully at ALL dimension numbers in the drawing - different ribs may have different lengths. For example, horizontal segments might be labeled differently than vertical segments. Read every number visible in the drawing and match it to the correct rib."
                            },
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:image/jpeg;base64,{base64_image}",
                                    "detail": "high"  # Use high detail for accurate dimension reading
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
            print(f"[CHATAN] Detailed analysis complete")
            
            # Try to parse JSON from response
            try:
                # Remove markdown code blocks if present
                if "```json" in result_text:
                    result_text = result_text.split("```json")[1].split("```")[0]
                elif "```" in result_text:
                    result_text = result_text.split("```")[1].split("```")[0]
                
                result = json.loads(result_text.strip())
                result["status"] = "Analysis with rib count complete"
                result["ribfinder_used"] = True
                result["established_rib_count"] = established_rib_count
            except json.JSONDecodeError:
                # If JSON parsing fails, return structured error with established rib count
                result = {
                    "shape_type": "Unknown",
                    "number_of_ribs": established_rib_count,  # Use established count
                    "sides": [],
                    "angles_between_ribs": [],
                    "confidence": 0,
                    "status": "JSON parsing failed but rib count established",
                    "ribfinder_used": True,
                    "established_rib_count": established_rib_count,
                    "raw_response": result_text
                }
            
            return result
            
        except Exception as e:
            return {
                "error": f"Analysis with rib count failed: {str(e)}",
                "established_rib_count": rib_finder_result.get("rib_count", 0)
            }
    
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
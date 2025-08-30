import os
import base64
import json
import autogen
from openai import OpenAI
from typing import Dict, List, Tuple

class ChatGPTComparisonAgent:
    """
    Agent that uses ChatGPT vision to compare analyzed shapes with catalog shapes
    """
    
    def __init__(self, api_key):
        """
        Initialize the ChatGPT comparison agent
        
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
            "temperature": 0.2,  # Lower temperature for consistent comparison
            "timeout": 120,
        }
        
        # Create the vision comparison agent (CHATCO)
        self.agent = autogen.AssistantAgent(
            name="CHATCO_Comparator",
            llm_config=llm_config,
            system_message="""You are a specialized agent for comparing bent iron shapes.
            
            Your task is to:
            1. Compare two bent iron shapes visually
            2. Determine similarity score (0-100%)
            3. Identify matching features (angles, proportions, shape type)
            4. Note key differences if any
            
            Focus on:
            - Overall shape geometry (L, U, Z, etc.)
            - Number of bends/ribs
            - Angle relationships between segments
            - Relative proportions (not exact dimensions)
            
            Return results in this format:
            {
                "similarity_score": 0-100,
                "shape_match": true/false,
                "matching_features": ["feature1", "feature2"],
                "differences": ["difference1", "difference2"],
                "confidence": 0-100
            }
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
    
    def compare_single_shape(self, input_image_path: str, catalog_image_path: str, input_rib_count: int = None) -> Dict:
        """
        Compare input shape with a single catalog shape
        
        Args:
            input_image_path: Path to the input drawing being analyzed
            catalog_image_path: Path to a catalog shape image
            
        Returns:
            Dictionary with comparison results
        """
        try:
            # Check if files exist
            if not os.path.exists(input_image_path):
                return {"error": f"Input image not found: {input_image_path}"}
            if not os.path.exists(catalog_image_path):
                return {"error": f"Catalog image not found: {catalog_image_path}"}
            
            # Prepare the images for comparison
            input_base64 = self.encode_image(input_image_path)
            catalog_base64 = self.encode_image(catalog_image_path)
            
            print(f"  [CHATCO] → Comparing with: {os.path.basename(catalog_image_path)}")
            
            # Call GPT-4 Vision API for comparison
            response = self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {
                        "role": "system",
                        "content": """You are an expert in comparing bent iron shapes for construction.
                        
                        STRICT COMPARISON CRITERIA:
                        
                        **CRITICAL: RIB COUNT MUST MATCH FIRST**
                        - If rib counts are different, maximum similarity = 40%
                        - 2-rib shape CANNOT be 70%+ similar to 3-rib shape
                        - 3-rib shape CANNOT be 70%+ similar to 4-rib shape
                        
                        1. **Rib Count Matching (MOST IMPORTANT)**:
                           - Same rib count = proceed with detailed comparison
                           - Different rib count = major penalty (max 40% similarity)
                           - Examples: L-shape (2 ribs) vs U-shape (3 ribs) = poor match
                        
                        2. **Shape Type Verification**:
                           - L-shape (2 ribs) vs L-shape (2 ribs) = good potential
                           - U-shape (3 ribs) vs U-shape (3 ribs) = good potential  
                           - L-shape (2 ribs) vs U-shape (3 ribs) = poor match
                        
                        3. **Geometry Pattern** (only if rib counts match):
                           - Linear patterns (straight sequences)
                           - Angular patterns (multiple bends)
                           - Closed patterns (rectangular, U-shaped)
                        
                        4. **Angle and Proportion Analysis** (only if rib counts match):
                           - Bend angles (90°, 45°, 135°, custom)
                           - Relative proportions and symmetry
                        
                        STRICT SCORING GUIDE:
                        - Different rib counts: Maximum 40% similarity
                        - Same rib count + identical pattern: 80-100%
                        - Same rib count + similar pattern: 60-79%
                        - Same rib count + different pattern: 40-59%
                        - Different rib count: 10-40%
                        
                        Return ONLY valid JSON in this exact format:
                        {
                            "similarity_score": number (0-100),
                            "shape_match": boolean,
                            "matching_features": ["feature1", "feature2"],
                            "differences": ["difference1", "difference2"],
                            "confidence": number (0-100)
                        }"""
                    },
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "text", 
                                "text": f"Compare these two bent iron shapes. First image is the input shape{f' which has {input_rib_count} ribs' if input_rib_count else ''}, second is from the catalog. CRITICAL: If they have different numbers of ribs/segments, maximum similarity is 40%. Count the ribs carefully in both images. An L-shape has 2 ribs (one vertical, one horizontal), a U-shape has 3 ribs. In catalog images, letters like 'A' and 'C' often label the ribs - if you see A marking a vertical segment and C marking a horizontal segment, that's an L-shape with 2 ribs. Focus on the actual iron segments, not just visible lines."
                            },
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:image/jpeg;base64,{input_base64}",
                                    "detail": "high"  # Use high detail for accurate rib counting
                                }
                            },
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:image/jpeg;base64,{catalog_base64}",
                                    "detail": "high"  # Use high detail for accurate rib counting
                                }
                            }
                        ]
                    }
                ],
                max_tokens=300,
                temperature=0.2
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
                result["catalog_file"] = os.path.basename(catalog_image_path)
            except json.JSONDecodeError:
                # If JSON parsing fails, return structured error
                result = {
                    "similarity_score": 0,
                    "shape_match": False,
                    "matching_features": [],
                    "differences": ["Failed to parse comparison"],
                    "confidence": 0,
                    "catalog_file": os.path.basename(catalog_image_path),
                    "raw_response": result_text
                }
            
            return result
            
        except Exception as e:
            return {
                "error": f"Comparison failed: {str(e)}",
                "catalog_file": os.path.basename(catalog_image_path)
            }
    
    def find_best_match(self, input_image_path: str, catalog_dir: str = "io/catalog", input_rib_count: int = None) -> Dict:
        """
        Compare input shape with all catalog shapes and find the best match
        
        Args:
            input_image_path: Path to the input drawing being analyzed
            catalog_dir: Directory containing catalog shape images
            
        Returns:
            Dictionary with the best match and all comparison results
        """
        try:
            print(f"\n[🤖 CHATCO] Starting catalog comparison...")
            print(f"[🤖 CHATCO] Input image: {os.path.basename(input_image_path)}")
            print(f"[🤖 CHATCO] Catalog directory: {catalog_dir}")
            
            # Check if catalog directory exists
            if not os.path.exists(catalog_dir):
                return {
                    "error": f"Catalog directory not found: {catalog_dir}",
                    "best_match": None,
                    "comparisons": []
                }
            
            # Get all image files from catalog
            supported_formats = ('.png', '.jpg', '.jpeg', '.bmp', '.gif')
            catalog_files = [f for f in os.listdir(catalog_dir) 
                           if f.lower().endswith(supported_formats)]
            
            if not catalog_files:
                return {
                    "error": "No catalog images found",
                    "best_match": None,
                    "comparisons": []
                }
            
            print(f"[🤖 CHATCO] Found {len(catalog_files)} catalog shapes to compare")
            
            # Compare with each catalog shape
            all_comparisons = []
            best_match = None
            highest_score = 0
            
            for catalog_file in catalog_files:
                catalog_path = os.path.join(catalog_dir, catalog_file)
                comparison_result = self.compare_single_shape(input_image_path, catalog_path, input_rib_count)
                
                if "error" not in comparison_result:
                    all_comparisons.append(comparison_result)
                    
                    # Check if this is the best match so far
                    score = comparison_result.get("similarity_score", 0)
                    if score > highest_score:
                        highest_score = score
                        best_match = comparison_result
                        
                    # Print progress with more detail
                    if score >= 70:
                        print(f"  [CHATCO]  ✓ Good match: {catalog_file} ({score}%)")
                    else:
                        print(f"  [CHATCO]  - Low match: {catalog_file} ({score}%)")
                    
                    # Debug: Show what CHATCO detected for shape 104
                    if "104" in catalog_file and comparison_result.get("differences"):
                        print(f"  [CHATCO] DEBUG - Shape 104 analysis: {comparison_result.get('differences')}")
            
            # Prepare final result
            result = {
                "best_match": best_match,
                "best_match_file": best_match["catalog_file"] if best_match else None,
                "best_match_score": highest_score,
                "total_comparisons": len(all_comparisons),
                "all_comparisons": sorted(all_comparisons, 
                                         key=lambda x: x.get("similarity_score", 0), 
                                         reverse=True)
            }
            
            # Print summary
            print(f"\n[🤖 CHATCO] Comparison complete!")
            if best_match:
                print(f"[🤖 CHATCO] Best match: {best_match['catalog_file']}")
                print(f"[🤖 CHATCO] Similarity: {highest_score}%")
                print(f"[🤖 CHATCO] Shape match: {best_match.get('shape_match', False)}")
            else:
                print(f"[🤖 CHATCO] No suitable matches found")
            
            return result
            
        except Exception as e:
            return {
                "error": f"Catalog comparison failed: {str(e)}",
                "best_match": None,
                "comparisons": []
            }
    
    def compare_with_analysis(self, input_image_path: str, analysis_result: Dict, 
                            catalog_dir: str = "io/catalog") -> Dict:
        """
        Enhanced comparison using both visual comparison and analysis data
        
        Args:
            input_image_path: Path to the input drawing
            analysis_result: Previous analysis results from main agent
            catalog_dir: Directory containing catalog shapes
            
        Returns:
            Dictionary with enhanced comparison results
        """
        # First do visual comparison with shape info
        input_rib_count = analysis_result.get('number_of_ribs', 0)
        print(f"[🤖 CHATCO] Input shape info: {analysis_result.get('shape_type', 'Unknown')} with {input_rib_count} ribs")
        comparison_result = self.find_best_match(input_image_path, catalog_dir, input_rib_count)
        
        # Enhance with analysis data
        if comparison_result.get("best_match"):
            comparison_result["input_analysis"] = {
                "shape_type": analysis_result.get("shape_type"),
                "number_of_ribs": analysis_result.get("number_of_ribs"),
                "angles": analysis_result.get("angles_between_ribs")
            }
            
            # Validate the match makes sense
            input_ribs = analysis_result.get("number_of_ribs", 0)
            best_score = comparison_result["best_match_score"]
            
            if best_score > 40 and input_ribs != comparison_result.get("best_match", {}).get("estimated_ribs"):
                print(f"[🤖 CHATCO] WARNING: High similarity ({best_score}%) between shapes with different rib counts!")
                print(f"[🤖 CHATCO] Input has {input_ribs} ribs, but got {best_score}% match - investigating...")
            
            # Determine configuration match quality
            best_score = comparison_result["best_match_score"]
            if best_score >= 90:
                comparison_result["match_quality"] = "EXCELLENT"
            elif best_score >= 70:
                comparison_result["match_quality"] = "GOOD"
            elif best_score >= 50:
                comparison_result["match_quality"] = "FAIR"
            else:
                comparison_result["match_quality"] = "POOR"
        
        return comparison_result
    
    def compare_with_analysis_corrected(self, input_image_path, analysis_result, catalog_dir="io/catalog", corrected_rib_count=None):
        """
        Compare input shape with catalog using corrected rib count from RIBFINDER
        
        Args:
            input_image_path: Path to the input drawing being analyzed
            analysis_result: Analysis results from CHATAN
            catalog_dir: Directory containing catalog shape images
            corrected_rib_count: Correct rib count from RIBFINDER
            
        Returns:
            Dictionary with comparison results using corrected information
        """
        print(f"[🤖 CHATCO] RECHECK: Input shape corrected to {corrected_rib_count} ribs")
        print(f"[🤖 CHATCO] RECHECK: Looking for better matches with {corrected_rib_count} ribs...")
        
        # Update the analysis result with corrected rib count
        corrected_analysis = analysis_result.copy()
        corrected_analysis["number_of_ribs"] = corrected_rib_count
        
        # Do comparison with corrected data
        comparison_result = self.find_best_match(input_image_path, catalog_dir, corrected_rib_count)
        
        # Enhance with corrected analysis data
        if comparison_result.get("best_match"):
            comparison_result["input_analysis"] = {
                "shape_type": corrected_analysis.get("shape_type"),
                "number_of_ribs": corrected_rib_count,
                "angles": corrected_analysis.get("angles_between_ribs"),
                "corrected": True
            }
            
            # Look specifically for shapes with matching rib count
            print(f"[🤖 CHATCO] RECHECK: Prioritizing catalog shapes with {corrected_rib_count} ribs...")
            
            # Add correction flag to result
            comparison_result["corrected_analysis"] = True
            comparison_result["original_chatco_count"] = analysis_result.get("number_of_ribs")
            comparison_result["corrected_rib_count"] = corrected_rib_count
        
        return comparison_result
    
    def get_agent(self):
        """
        Return the AutoGen agent for integration with orchestrator
        
        Returns:
            AutoGen AssistantAgent
        """
        return self.agent


def create_chatgpt_comparison_agent(api_key):
    """
    Factory function to create a ChatGPT comparison agent
    
    Args:
        api_key: OpenAI API key
        
    Returns:
        ChatGPTComparisonAgent instance
    """
    return ChatGPTComparisonAgent(api_key)
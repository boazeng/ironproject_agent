import os
import sys
from dotenv import load_dotenv
from agents.llm_agents import create_chatgpt_vision_agent, create_chatgpt_comparison_agent, create_rib_finder_agent, create_pathfinder_agent, create_dataoutput_agent
from agents.llm_agents.cleaner_agent import CleanerAgent
from utils.logger import IronManLogger

# Set UTF-8 encoding for Windows
if sys.platform == "win32":
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# Load environment variables
load_dotenv()

def process_drawing(file_path, cleaner, ribfinder, chat_analyse, chat_compare, pathfinder, logger):
    """
    Process a bent iron drawing using CLEANER, RibFinder, CHATAN, CHATCO, and PATHFINDER
    
    Args:
        file_path: Path to the drawing file
        cleaner: Cleaner agent instance (CLEANER)
        ribfinder: RibFinder agent instance (RIBFINDER)
        chat_analyse: ChatGPT vision agent instance (CHATAN) 
        chat_compare: ChatGPT comparison agent instance (CHATCO)
        pathfinder: PathFinder agent instance (PATHFINDER)
        logger: Logger instance for workflow tracking
    
    Returns:
        Dictionary with analysis results and comparison
    """
    
    print("\n" + "="*60)
    print(f"[🦾 IRONMAN] NEW ANALYSIS REQUEST: {os.path.basename(file_path)}")
    print("="*60)
    
    # Step 1: Validate file
    print("\n[🦾 IRONMAN] [STEP 1] Validating file existence...")
    if not os.path.exists(file_path):
        print("[🦾 IRONMAN]   ❌ File not found!")
        return {"error": f"File not found: {file_path}"}
    print(f"[🦾 IRONMAN]   ✓ File found at: {file_path}")
    
    # Step 2: SKIPPING CLEANER - Using original drawing directly
    print("\n[🦾 IRONMAN] [STEP 2] SKIPPING CLEANER - Using original drawing")
    print("[🦾 IRONMAN]   → Bypassing CLEANER agent as requested")
    print("[🦾 IRONMAN]   → Will send original drawing directly to RIBFINDER")
    
    # Use original image path instead of cleaned image
    cleaned_image_path = file_path
    
    # Step 3: Count ribs with RibFinder (using ORIGINAL image)
    print("\n[🦾 IRONMAN] [STEP 3] Counting ribs with RIBFINDER...")
    print("[🦾 IRONMAN]   → Sending ORIGINAL drawing to RIBFINDER (Premium Agent)")
    print("[🦾 IRONMAN]   → Using GPT-4o for maximum rib counting accuracy...")
    print("[🦾 IRONMAN]   → Note: Using uncleaned original image")
    
    logger.log_step_start(3, "Counting ribs with RIBFINDER", "RIBFINDER")
    
    rib_result = ribfinder.count_ribs(file_path)
    
    if "error" in rib_result:
        print(f"[🦾 IRONMAN]   ❌ RIBFINDER Error: {rib_result['error']}")
        return rib_result
    
    rib_count = rib_result.get("rib_count", 0)
    shape_pattern = rib_result.get("shape_pattern", "unknown")
    confidence = rib_result.get("confidence", 0)
    match_percentage = rib_result.get("match_percentage", 0)
    vision_agreement = rib_result.get("vision_agreement", "UNKNOWN")
    
    print(f"[🦾 IRONMAN]   ✓ RIBFINDER found: {rib_count} ribs")
    print(f"[🦾 IRONMAN]   → Pattern: {shape_pattern}")
    print(f"[🦾 IRONMAN]   → Confidence: {confidence}%")
    print(f"[🦾 IRONMAN]   → Vision Match: {match_percentage}% ({vision_agreement})")
    
    # Check if match percentage is low and retry with original image if needed
    if match_percentage < 50:
        print(f"\n[🦾 IRONMAN] [STEP 3.1] Low match detected ({match_percentage}%) - Comparing with original image...")
        print("[🦾 IRONMAN]   → Testing original image to see if cleaning affected accuracy")
        
        logger.log_step_start("3.1", "Comparing RIBFINDER results: cleaned vs original", "RIBFINDER")
        
        original_rib_result = ribfinder.count_ribs(file_path)
        
        if "error" not in original_rib_result:
            original_match_percentage = original_rib_result.get("match_percentage", 0)
            original_rib_count = original_rib_result.get("rib_count", 0)
            original_vision_agreement = original_rib_result.get("vision_agreement", "UNKNOWN")
            
            print(f"[🦾 IRONMAN]   → Original image result: {original_rib_count} ribs")
            print(f"[🦾 IRONMAN]   → Original match: {original_match_percentage}% ({original_vision_agreement})")
            print(f"[🦾 IRONMAN]   → Cleaned match: {match_percentage}% ({vision_agreement})")
            
            # Log both results for comparison in log file
            logger.log_agent_output("RIBFINDER_CLEANED", rib_result)
            logger.log_agent_output("RIBFINDER_ORIGINAL", original_rib_result)
            
            # Use the result with higher match percentage
            if original_match_percentage > match_percentage:
                print(f"[🦾 IRONMAN]   ✓ Using original image result (better match: {original_match_percentage}% vs {match_percentage}%)")
                rib_result = original_rib_result
                rib_count = original_rib_count
                match_percentage = original_match_percentage
                vision_agreement = original_vision_agreement
                shape_pattern = original_rib_result.get("shape_pattern", "unknown")
                confidence = original_rib_result.get("confidence", 0)
                
                logger.log_agent_output("RIBFINDER_FINAL_CHOICE", original_rib_result)
            else:
                print(f"[🦾 IRONMAN]   → Keeping cleaned image result (cleaned: {match_percentage}% vs original: {original_match_percentage}%)")
                logger.log_agent_output("RIBFINDER_FINAL_CHOICE", rib_result)
        else:
            print(f"[🦾 IRONMAN]   ⚠ Original image analysis failed: {original_rib_result['error']}")
    else:
        print(f"[🦾 IRONMAN]   ✓ Good match percentage ({match_percentage}%) - no retry needed")
    
    logger.log_agent_output("RIBFINDER", rib_result)
    
    # Step 4: Prepare for detailed analysis  
    print("\n[🦾 IRONMAN] [STEP 4] Preparing detailed analysis request...")
    print(f"[🦾 IRONMAN]   ✓ File size: {os.path.getsize(file_path) / 1024:.2f} KB")
    print(f"[🦾 IRONMAN]   ✓ Rib count established: {rib_count} ribs")
    
    # Step 5: Send to CHATAN (Chat Analyse Agent) with rib count info
    print("\n[🦾 IRONMAN] [STEP 5] Sending request to CHATAN (Analysis Agent)...")
    print(f"[🦾 IRONMAN]   → Transferring image to CHATAN with established rib count: {rib_count}")
    print(f"[🦾 IRONMAN]   → CHATAN will use RIBFINDER's accurate count ({rib_count} ribs)")
    
    logger.log_step_start(5, "Sending request to CHATAN (Analysis Agent)", "CHATAN")
    
    # Use dual vision analysis for CHATAN with RIBFINDER's established rib count
    result = chat_analyse.analyze_with_rib_count(file_path, rib_result)
    
    print("[🦾 IRONMAN]   ✓ Response received from CHATAN")
    
    logger.log_agent_output("CHATAN", result)
    
    # Add RibFinder results to the main result
    result["ribfinder"] = rib_result
    result["expected_rib_count"] = rib_count
    
    # Step 6: Process and display results
    print("\n[🦾 IRONMAN] [STEP 6] Processing analysis results...")
    print("-"*60)
    print("[🦾 IRONMAN] ANALYSIS RESULTS:")
    print("-"*60)
    
    if "error" in result:
        print(f"[🦾 IRONMAN] ERROR: {result['error']}")
    else:
        print(f"[🦾 IRONMAN] Shape Type:        {result.get('shape_type', 'Unknown')}")
        print(f"[🦾 IRONMAN] Number of Ribs:    {result.get('number_of_ribs', 0)}")
        print(f"[🦾 IRONMAN] Confidence Score:  {result.get('confidence', 0)}%")
        
        # Display angles between ribs
        angles = result.get('angles_between_ribs', [])
        if angles:
            print(f"[🦾 IRONMAN] Angles between Ribs: {angles}°")
        
        # Display each side with its details
        sides = result.get('sides', [])
        if sides:
            print("\n[🦾 IRONMAN] Ribs Details:")
            for side in sides:
                side_num = side.get('side_number', '?')
                length = side.get('length', 0)
                angle = side.get('angle_to_next', 0)
                description = side.get('description', '')
                
                # Build the display line
                rib_info = f"[🦾 IRONMAN]   Rib {side_num}: {length} cm"
                if description:
                    rib_info += f" ({description})"
                print(rib_info)
                
                if angle > 0:
                    print(f"[🦾 IRONMAN]     → Angle to next rib: {angle}°")
        else:
            print("\n[🦾 IRONMAN] No rib details detected")
    
    print("-"*60)
    
    # Check for missing dimensions
    missing_dimensions = False
    if "sides" in result:
        for side in result["sides"]:
            if side.get("length", 0) == 0:
                missing_dimensions = True
                missing_side = side.get("side_number", "?")
                missing_desc = side.get("description", "unknown")
                print(f"\n[🦾 IRONMAN] ⚠️ WARNING: Missing dimension detected!")
                print(f"[🦾 IRONMAN]   → Rib {missing_side} ({missing_desc}) has 0 mm")
                break
    
    # If dimensions are missing, ask CHATAN to reanalyze
    if missing_dimensions:
        print(f"\n[🦾 IRONMAN] [STEP 5.1] Requesting CHATAN to search for missing dimensions...")
        print(f"[🦾 IRONMAN]   → CHATAN, please look more carefully for ALL dimensions")
        print(f"[🦾 IRONMAN]   → Focus on finding the {missing_desc} dimension")
        
        # Reanalyze with CHATAN focusing on missing dimensions
        result = chat_analyse.recheck_analysis(file_path, result)
        
        print(f"[🦾 IRONMAN]   ✓ CHATAN completed dimension search")
        
        # Display updated results
        print("\n" + "-"*60)
        print("[🦾 IRONMAN] UPDATED ANALYSIS RESULTS:")
        print("-"*60)
        print(f"[🦾 IRONMAN] Shape Type:        {result.get('shape_type', 'Unknown')}")
        print(f"[🦾 IRONMAN] Number of Ribs:    {result.get('number_of_ribs', 0)}")
        print(f"[🦾 IRONMAN] Confidence Score:  {result.get('confidence', 0)}%")
        
        angles = result.get('angles_between_ribs', [])
        if angles:
            print(f"[🦾 IRONMAN] Angles between Ribs: {angles}°")
        
        sides = result.get('sides', [])
        if sides:
            print("\n[🦾 IRONMAN] Updated Ribs Details:")
            for side in sides:
                side_num = side.get('side_number', '?')
                length = side.get('length', 0)
                angle = side.get('angle_to_next', 0)
                description = side.get('description', '')
                
                # Highlight if dimension was found
                status = "✅" if length > 0 else "❌ STILL MISSING"
                rib_info = f"[🦾 IRONMAN]   Rib {side_num}: {length} mm"
                if description:
                    rib_info += f" ({description})"
                rib_info += f" {status}"
                print(rib_info)
                
                if angle > 0:
                    print(f"[🦾 IRONMAN]     → Angle to next rib: {angle}°")
        
        print("-"*60)
    
    # Step 5.5: Extract vector path using PATHFINDER
    print("\n[🦾 IRONMAN] [STEP 6.5] Extracting vector path with PATHFINDER...")
    print(f"[🦾 IRONMAN]   → Sending to PATHFINDER (Vector Path Extraction)")
    print(f"[🦾 IRONMAN]   → Using established rib count: {rib_count} ribs")
    
    logger.log_step_start(5.5, "Extracting vector path with PATHFINDER", "PATHFINDER")
    
    pathfinder_result = pathfinder.find_path(
        image_path=file_path,
        rib_count=rib_count,
        all_straight=True,
        ribfinder_data=rib_result,
        chatan_data=result
    )
    
    if "error" in pathfinder_result:
        print(f"[🦾 IRONMAN]   ❌ PATHFINDER Error: {pathfinder_result['error']}")
    else:
        print(f"[🦾 IRONMAN]   ✓ PATHFINDER analysis complete")
        print(f"[🦾 IRONMAN]   → Shape Type: {pathfinder_result.get('shape_type', 'Unknown')}")
        print(f"[🦾 IRONMAN]   → Vertices Found: {pathfinder_result.get('vertex_count', 0)}")
        print(f"[🦾 IRONMAN]   → Total Path Length: {pathfinder_result.get('total_path_length', 0)} units")
        print(f"[🦾 IRONMAN]   → Is Closed Shape: {pathfinder_result.get('is_closed', False)}")
        
        # Display vector information
        vectors = pathfinder_result.get('vectors', [])
        if vectors:
            print(f"\n[🦾 IRONMAN] PATHFINDER Vector Analysis:")
            for vec in vectors:
                rib_num = vec.get('rib_number', '?')
                length = vec.get('length', 0)
                angle = vec.get('angle_degrees', 0)
                print(f"[🦾 IRONMAN]   Vector {rib_num}: Length {length:.1f} units, Angle {angle:.1f}°")
                if 'bend_angle_to_next' in vec:
                    bend_angle = vec['bend_angle_to_next']
                    print(f"[🦾 IRONMAN]     → Bend to next: {bend_angle:.1f}°")
        
        # Display bounding box
        bbox = pathfinder_result.get('path_summary', {}).get('bounding_box', {})
        if bbox:
            print(f"[🦾 IRONMAN]   → Bounding Box: {bbox.get('width', 0):.1f} × {bbox.get('height', 0):.1f} units")
    
    # Add PathFinder results to main result
    result["pathfinder"] = pathfinder_result
    
    if "error" not in pathfinder_result:
        logger.log_agent_output("PATHFINDER", pathfinder_result)
    
    print("-"*60)
    
    # Step 6: Compare with catalog shapes using CHATCO
    print("\n[🦾 IRONMAN] [STEP 7] Comparing with catalog shapes...")
    print("[🦾 IRONMAN]   → Sending to CHATCO (Comparison Agent)")
    print("[🦾 IRONMAN]   → CHATCO analyzing similarity with catalog...")
    
    logger.log_step_start(6, "Comparing with catalog shapes", "CHATCO")
    
    comparison_result = chat_compare.compare_with_analysis(file_path, result, "io/catalog")
    
    # Check for rib count inconsistencies between agents
    ribfinder_count = rib_result.get("rib_count", 0)
    chatan_count = result.get("number_of_ribs", 0)
    
    # Extract CHATCO's detected rib count from differences
    chatco_detected_count = None
    if comparison_result.get("best_match") and comparison_result["best_match"].get("differences"):
        differences = comparison_result["best_match"]["differences"]
        for diff in differences:
            import re
            # Look for various patterns of rib count mentions
            patterns = [
                r'Input shape has (\d+) ribs',
                r'Different rib counts: (\d+) ribs vs',
                r'(\d+) ribs vs \d+ rib'
            ]
            
            for pattern in patterns:
                match = re.search(pattern, diff)
                if match:
                    chatco_detected_count = int(match.group(1))
                    break
            if chatco_detected_count:
                break
    
    # Detect inconsistency
    inconsistency_detected = False
    if chatco_detected_count and chatco_detected_count != ribfinder_count:
        inconsistency_detected = True
        print(f"\n[🦾 IRONMAN] ⚠️ RIB COUNT INCONSISTENCY DETECTED!")
        print(f"[🦾 IRONMAN]   → RIBFINDER found: {ribfinder_count} ribs")
        print(f"[🦾 IRONMAN]   → CHATAN confirmed: {chatan_count} ribs")
        print(f"[🦾 IRONMAN]   → CHATCO detected: {chatco_detected_count} ribs")
        print(f"[🦾 IRONMAN]   → Asking CHATCO to recheck with correct rib count...")
        
        # Ask CHATCO to reanalyze with the correct rib count
        print(f"[🦾 IRONMAN] [STEP 7.1] CHATCO recheck with established {ribfinder_count} ribs...")
        comparison_result = chat_compare.compare_with_analysis_corrected(file_path, result, "io/catalog", ribfinder_count)
    
    if comparison_result.get("best_match"):
        best_match = comparison_result["best_match"]
        print(f"[🦾 IRONMAN]   ✓ Best match found: {best_match['catalog_file']}")
        print(f"[🦾 IRONMAN]   → Similarity: {best_match.get('similarity_score', 0)}%")
        
        # Show CHATCO's detailed analysis
        if best_match.get('matching_features'):
            print(f"[🦾 IRONMAN]   → CHATCO found matching features: {', '.join(best_match['matching_features'])}")
        if best_match.get('differences'):
            print(f"[🦾 IRONMAN]   → CHATCO found differences: {', '.join(best_match['differences'])}")
        if best_match.get('reasoning'):
            print(f"[🦾 IRONMAN]   → CHATCO reasoning: {best_match['reasoning']}")
        
        # Determine match quality based on score
        score = best_match.get('similarity_score', 0)
        if score >= 90:
            match_quality = "EXCELLENT"
        elif score >= 70:
            match_quality = "GOOD"
        elif score >= 50:
            match_quality = "FAIR"
        else:
            match_quality = "POOR"
        
        print(f"[🦾 IRONMAN]   → Match Quality: {match_quality}")
        
        # Add comparison results to main result
        result["comparison"] = {
            "best_match_file": best_match['catalog_file'],
            "similarity_score": best_match.get('similarity_score', 0),
            "shape_match": best_match.get('shape_match', False),
            "match_quality": match_quality,
            "matching_features": best_match.get('matching_features', []),
            "differences": best_match.get('differences', []),
            "reasoning": best_match.get('reasoning', '')
        }
        
        logger.log_agent_output("CHATCO", result["comparison"])
    else:
        print("[🦾 IRONMAN]   ⚠️ No matching catalog shape found")
        result["comparison"] = {
            "best_match_file": None,
            "similarity_score": 0,
            "shape_match": False,
            "match_quality": "NO_MATCH"
        }
        
        logger.log_agent_output("CHATCO", result["comparison"])
    
    print("-"*60)
    
    return result

def validate_results_with_user(result, file_name):
    """
    Ask user to validate the analysis results
    
    Args:
        result: Analysis results from ChatGPT agent
        file_name: Name of the file being analyzed
        
    Returns:
        bool: True if results are accepted, False if rejected
    """
    print("\n" + "?"*60)
    print("USER VALIDATION REQUIRED")
    print("?"*60)
    print(f"File: {file_name}")
    print(f"Shape: {result.get('shape_type', 'Unknown')}")
    print(f"Ribs: {result.get('number_of_ribs', 0)}")
    print(f"Confidence: {result.get('confidence', 0)}%")
    
    # Show comparison results if available
    if result.get('comparison'):
        comp = result['comparison']
        if comp.get('best_match_file'):
            print(f"Best Catalog Match: {comp['best_match_file']}")
            print(f"Match Similarity: {comp['similarity_score']}%")
            print(f"Match Quality: {comp['match_quality']}")
    
    while True:
        try:
            user_input = input("\nAre these results correct? (y/n): ").lower().strip()
            if user_input in ['y', 'yes']:
                print("  ✓ Results accepted by user")
                return True
            elif user_input in ['n', 'no']:
                print("  ❌ Results rejected by user")
                return False
            else:
                print("Please enter 'y' for yes or 'n' for no")
        except EOFError:
            print("\n  ⚠️ No interactive input available - auto-accepting results")
            print("  ✓ Results auto-accepted (non-interactive mode)")
            return True

def reprocess_drawing(file_path, ribfinder, chat_analyse, chat_compare, pathfinder, previous_result, attempt_number):
    """
    Reprocess a drawing with additional instructions for CHATAN to recheck
    
    Args:
        file_path: Path to the drawing file
        ribfinder: RibFinder agent instance (RIBFINDER)
        chat_analyse: ChatGPT vision agent instance (CHATAN)
        chat_compare: ChatGPT comparison agent instance (CHATCO)
        pathfinder: PathFinder agent instance (PATHFINDER)
        previous_result: Previous analysis results that were rejected
        attempt_number: Current attempt number
        
    Returns:
        Dictionary with new analysis results
    """
    print(f"\n[🦾 IRONMAN] [STEP 5.{attempt_number}] Re-sending request to CHATAN...")
    print("[🦾 IRONMAN]   → Asking CHATAN to double-check previous analysis")
    print("[🦾 IRONMAN]   → Requesting more careful examination from CHATAN")
    
    # Create a special recheck method
    result = chat_analyse.recheck_analysis(file_path, previous_result)
    
    print("[🦾 IRONMAN]   ✓ Recheck analysis received from CHATAN")
    
    # Print the new results
    print("\n" + "-"*60)
    print(f"[🦾 IRONMAN] RECHECK RESULTS (Attempt {attempt_number}):")
    print("-"*60)
    
    if "error" in result:
        print(f"[🦾 IRONMAN] ERROR: {result['error']}")
    else:
        print(f"[🦾 IRONMAN] Shape Type:        {result.get('shape_type', 'Unknown')}")
        print(f"[🦾 IRONMAN] Number of Ribs:    {result.get('number_of_ribs', 0)}")
        print(f"[🦾 IRONMAN] Confidence Score:  {result.get('confidence', 0)}%")
        
        # Display angles between ribs
        angles = result.get('angles_between_ribs', [])
        if angles:
            print(f"[🦾 IRONMAN] Angles between Ribs: {angles}°")
        
        # Display each side with its details
        sides = result.get('sides', [])
        if sides:
            print("\n[🦾 IRONMAN] Ribs Details:")
            for side in sides:
                side_num = side.get('side_number', '?')
                length = side.get('length', 0)
                angle = side.get('angle_to_next', 0)
                description = side.get('description', '')
                
                # Build the display line
                rib_info = f"[🦾 IRONMAN]   Rib {side_num}: {length} cm"
                if description:
                    rib_info += f" ({description})"
                print(rib_info)
                
                if angle > 0:
                    print(f"[🦾 IRONMAN]     → Angle to next rib: {angle}°")
        else:
            print("\n[🦾 IRONMAN] No rib details detected")
    
    print("-"*60)
    
    return result

def main():
    """
    Main orchestrator for the bent iron recognition system
    """
    # Initialize logger first
    logger = IronManLogger()
    
    print("="*60)
    print("         BENT IRON ORDER RECOGNITION SYSTEM")
    print("="*60)
    print("\n[🦾 IRONMAN] Starting system initialization...")
    
    logger.log_system_start()
    
    # Check API key
    print("\n[🦾 IRONMAN] Checking API credentials...")
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        print("[🦾 IRONMAN]   ❌ ERROR: API key not found")
        print("[🦾 IRONMAN]   → Please set OPENAI_API_KEY in .env file")
        return
    print("[🦾 IRONMAN]   ✓ API key loaded successfully")
    
    # Initialize ChatGPT Agents with their nicknames
    print("\n[🦾 IRONMAN] Creating sub-agents...")
    
    print("[🦾 IRONMAN]   → Initializing CLEANER (Drawing Cleaning Specialist)...")
    cleaner = CleanerAgent()  # CLEANER
    print("[🦾 IRONMAN]   ✓ CLEANER (Drawing Cleaner) created and ready")
    logger.log_agent_creation("CLEANER", "Drawing Cleaner")
    
    print("[🦾 IRONMAN]   → Initializing RIBFINDER (Premium Rib Counter)...")
    ribfinder = create_rib_finder_agent(api_key)  # RIBFINDER
    print("[🦾 IRONMAN]   ✓ RIBFINDER (GPT-4o Rib Counter) created and ready")
    logger.log_agent_creation("RIBFINDER", "GPT-4o Rib Counter")
    
    print("[🦾 IRONMAN]   → Initializing CHATAN (Chat Analyse Agent)...")
    chat_analyse = create_chatgpt_vision_agent(api_key)  # CHATAN
    print("[🦾 IRONMAN]   ✓ CHATAN (Analysis Agent) created and ready")
    logger.log_agent_creation("CHATAN", "Analysis Agent")
    
    print("[🦾 IRONMAN]   → Initializing CHATCO (Chat Compare Agent)...")
    chat_compare = create_chatgpt_comparison_agent(api_key)  # CHATCO
    print("[🦾 IRONMAN]   ✓ CHATCO (Comparison Agent) created and ready")
    logger.log_agent_creation("CHATCO", "Comparison Agent")
    
    print("[🦾 IRONMAN]   → Initializing PATHFINDER (Vector Path Extraction)...")
    pathfinder = create_pathfinder_agent(api_key)  # PATHFINDER
    print("[🦾 IRONMAN]   ✓ PATHFINDER (Path Vector Agent) created and ready")
    logger.log_agent_creation("PATHFINDER", "Vector Path Agent")
    
    print("[🦾 IRONMAN]   → Initializing DATAOUTPUT (Database Storage Manager)...")
    dataoutput = create_dataoutput_agent("data")  # DATAOUTPUT
    print("[🦾 IRONMAN]   ✓ DATAOUTPUT (Database Agent) created and ready")
    logger.log_agent_creation("DATAOUTPUT", "Database Agent")
    
    # Check for input files
    print("\n[🦾 IRONMAN] Scanning input directory...")
    input_dir = "io/input"
    if not os.path.exists(input_dir):
        os.makedirs(input_dir)
        print(f"[🦾 IRONMAN]   → Created input directory: {input_dir}")
        print("[🦾 IRONMAN]   ❌ No files to process")
        print("[🦾 IRONMAN]   → Please place drawing files in this directory")
        return
    
    # List available files
    print(f"[🦾 IRONMAN]   → Scanning: {input_dir}")
    files = [f for f in os.listdir(input_dir) if f.lower().endswith(('.png', '.jpg', '.jpeg', '.bmp', '.gif'))]
    
    if not files:
        print("[🦾 IRONMAN]   ❌ No image files found")
        print("[🦾 IRONMAN]   → Supported formats: .png, .jpg, .jpeg, .bmp, .gif")
        return
    
    print(f"[🦾 IRONMAN]   ✓ Found {len(files)} drawing file(s)")
    
    print("\n[🦾 IRONMAN] Files to process:")
    for i, file in enumerate(files, 1):
        try:
            print(f"[🦾 IRONMAN]   {i}. {file}")
        except UnicodeEncodeError:
            print(f"[🦾 IRONMAN]   {i}. {file.encode('ascii', 'ignore').decode('ascii')}")
    
    logger.log_input_scan(len(files), files)
    
    # Process each file
    print("\n[🦾 IRONMAN] Starting batch processing...")
    all_results = []
    for i, file in enumerate(files, 1):
        file_path = os.path.join(input_dir, file)
        print(f"\n[🦾 IRONMAN] Dispatching file {i}/{len(files)} to RIBFINDER, CHATAN & CHATCO...")
        
        logger.log_file_processing_start(file, i, len(files))
        
        # Initial analysis with RibFinder first
        result = process_drawing(file_path, cleaner, ribfinder, chat_analyse, chat_compare, pathfinder, logger)
        
        # Validate results with user
        print(f"\n[🦾 IRONMAN] Requesting user validation for file {i}/{len(files)}")
        max_retries = 3
        retry_count = 0
        
        while retry_count < max_retries:
            # Skip validation if there was an error in processing
            if "error" in result:
                break
                
            user_approved = validate_results_with_user(result, file)
            
            if user_approved:
                print(f"[🦾 IRONMAN] Results validated for {file}")
                logger.log_validation_result(True)
                
                # Store results in database using DATAOUTPUT agent
                print(f"\n[🦾 IRONMAN] [STEP 8] Storing results in database...")
                print("[🦾 IRONMAN]   → Sending to DATAOUTPUT (Database Storage)")
                
                logger.log_step_start(7, "Storing results in database", "DATAOUTPUT")
                
                # Generate order number (could be enhanced with proper order management)
                from datetime import datetime
                order_number = f"ORD-{datetime.now().strftime('%Y%m%d')}-{i:03d}"
                
                storage_result = dataoutput.process_and_store(
                    order_number=order_number,
                    file_name=file,
                    analysis_results=result
                )
                
                if storage_result['status'] == 'success':
                    print(f"[🦾 IRONMAN]   ✓ Data stored successfully")
                    print(f"[🦾 IRONMAN]   → Order Number: {order_number}")
                    print(f"[🦾 IRONMAN]   → Record ID: {storage_result['record_id']}")
                    result['order_number'] = order_number
                    result['database_id'] = storage_result['record_id']
                    
                    logger.log_agent_output("DATAOUTPUT", storage_result)
                else:
                    print(f"[🦾 IRONMAN]   ⚠ Storage failed: {storage_result.get('message', 'Unknown error')}")
                    logger.log_error(f"Storage failed: {storage_result.get('message', 'Unknown error')}", "DATAOUTPUT")
                
                break
            else:
                retry_count += 1
                logger.log_validation_result(False, retry_count)
                
                if retry_count < max_retries:
                    print(f"\n[🦾 IRONMAN] Reprocessing attempt {retry_count}/{max_retries-1}")
                    print("[🦾 IRONMAN]   → Asking CHATAN to recheck analysis...")
                    
                    # Add instruction for recheck
                    result = reprocess_drawing(file_path, ribfinder, chat_analyse, chat_compare, pathfinder, result, retry_count)
                else:
                    print(f"\n[🦾 IRONMAN] Maximum retries reached for {file}")
                    result["status"] = "Max retries reached - user rejected"
        
        all_results.append({
            "file": file,
            "result": result
        })
        logger.log_file_completion(file, "error" not in result)
        print(f"\n[🦾 IRONMAN] File {i}/{len(files)} processing complete")
    
    # Summary
    print("\n[🦾 IRONMAN] All files processed")
    print("\n" + "="*60)
    print("🦾 IRONMAN FINAL REPORT")
    print("="*60)
    print(f"[🦾 IRONMAN] Total files processed: {len(files)}")
    
    successful = sum(1 for r in all_results if "error" not in r["result"])
    print(f"[🦾 IRONMAN] Successful analyses: {successful}")
    print(f"[🦾 IRONMAN] Failed analyses: {len(files) - successful}")
    
    print("\n[🦾 IRONMAN] Summary of Results:")
    for item in all_results:
        file_name = item["file"]
        result = item["result"]
        if "error" in result:
            print(f"[🦾 IRONMAN]   • {file_name}: ERROR - {result['error']}")
        else:
            shape = result.get('shape_type', 'Unknown')
            confidence = result.get('confidence', 0)
            comp = result.get('comparison', {})
            if comp.get('best_match_file'):
                print(f"[🦾 IRONMAN]   • {file_name}: {shape} (Confidence: {confidence}%) → Catalog: {comp['best_match_file']} ({comp['similarity_score']}%)")
            else:
                print(f"[🦾 IRONMAN]   • {file_name}: {shape} (Confidence: {confidence}%) → No catalog match")
    
    # Detailed breakdown per agent
    print("\n" + "="*60)
    print("🦾 IRONMAN DETAILED AGENT BREAKDOWN")
    print("="*60)
    
    for item in all_results:
        file_name = item["file"]
        result = item["result"]
        if "error" not in result:
            print(f"\n[🦾 IRONMAN] FILE: {file_name}")
            print("-" * 50)
            
            # RibFinder results
            ribfinder_data = result.get('ribfinder', {})
            ribfinder_count = ribfinder_data.get('rib_count', 0)
            match_percentage = ribfinder_data.get('match_percentage', 0)
            vision_agreement = ribfinder_data.get('vision_agreement', 'UNKNOWN')
            print(f"RIBFINDER: number of ribs is - {ribfinder_count}")
            print(f"         match percentage - {match_percentage}% ({vision_agreement})")
            
            # CHATAN results
            chatan_count = result.get('number_of_ribs', 0)
            chatan_match_percentage = result.get('match_percentage', 0)
            chatan_vision_agreement = result.get('vision_agreement', 'UNKNOWN')
            print(f"CHATAN: number of ribs - {chatan_count}")
            print(f"        match percentage - {chatan_match_percentage}% ({chatan_vision_agreement})")
            
            # Show Google Vision data if available
            google_vision_data = result.get('google_vision_data')
            if google_vision_data and 'dimensions' in google_vision_data:
                print(f"        Google Vision dimensions: {google_vision_data.get('dimensions', [])}")
            
            sides = result.get('sides', [])
            if sides:
                for side in sides:
                    side_num = side.get('side_number', '?')
                    description = side.get('description', 'unknown')
                    length = side.get('length', 0)
                    print(f"         rib {side_num}: {description}, {length} cm")
            else:
                print("         no rib details available")
            
            # CHATCO results
            comp = result.get('comparison', {})
            if comp.get('best_match_file'):
                catalog_shape = comp.get('best_match_file', 'unknown')
                similarity = comp.get('similarity_score', 0)
                print(f"CHATCO: shape {catalog_shape} (similarity: {similarity}%)")
                
                # Show CHATCO's detailed analysis
                matching = comp.get('matching_features', [])
                differences = comp.get('differences', [])
                reasoning = comp.get('reasoning', '')
                
                if matching:
                    print(f"         matching features: {', '.join(matching)}")
                if differences:
                    print(f"         differences: {', '.join(differences)}")
                if reasoning:
                    print(f"         reasoning: {reasoning}")
            else:
                print("CHATCO: no matching shape found")
            
            # PATHFINDER results
            pathfinder_data = result.get('pathfinder', {})
            if pathfinder_data and "error" not in pathfinder_data:
                shape_type = pathfinder_data.get('shape_type', 'Unknown')
                vertex_count = pathfinder_data.get('vertex_count', 0)
                total_length = pathfinder_data.get('total_path_length', 0)
                is_closed = pathfinder_data.get('is_closed', False)
                print(f"PATHFINDER: {shape_type} with {vertex_count} vertices")
                print(f"            total path length: {total_length} units")
                print(f"            closed shape: {is_closed}")
                
                # Show vector details
                vectors = pathfinder_data.get('vectors', [])
                if vectors:
                    print(f"            vectors:")
                    for vec in vectors:
                        rib_num = vec.get('rib_number', '?')
                        length = vec.get('length', 0)
                        angle = vec.get('angle_degrees', 0)
                        print(f"              vector {rib_num}: {length:.1f} units at {angle:.1f}°")
            else:
                if pathfinder_data.get("error"):
                    print(f"PATHFINDER: error - {pathfinder_data['error']}")
                else:
                    print("PATHFINDER: no analysis available")
            
            # Database storage status
            if "order_number" in result:
                print(f"DATABASE: Order {result['order_number']} - Record ID: {result.get('database_id', 'N/A')}")
            else:
                print("DATABASE: Not stored")
    
    logger.log_system_completion()
    print("\n[🦾 IRONMAN] System workflow completed successfully")
    print("="*60)

if __name__ == "__main__":
    main()
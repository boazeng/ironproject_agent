import os
import sys
from dotenv import load_dotenv
from agents.llm_agents import create_chatgpt_vision_agent, create_chatgpt_comparison_agent, create_rib_finder_agent

# Set UTF-8 encoding for Windows
if sys.platform == "win32":
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# Load environment variables
load_dotenv()

def process_drawing(file_path, ribfinder, chat_analyse, chat_compare):
    """
    Process a bent iron drawing using RibFinder, CHATAN, and CHATCO
    
    Args:
        file_path: Path to the drawing file
        ribfinder: RibFinder agent instance (RIBFINDER)
        chat_analyse: ChatGPT vision agent instance (CHATAN) 
        chat_compare: ChatGPT comparison agent instance (CHATCO)
    
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
    
    # Step 2: Count ribs with RibFinder
    print("\n[🦾 IRONMAN] [STEP 2] Counting ribs with RIBFINDER...")
    print("[🦾 IRONMAN]   → Sending to RIBFINDER (Premium Agent)")
    print("[🦾 IRONMAN]   → Using GPT-4o for maximum rib counting accuracy...")
    
    rib_result = ribfinder.count_ribs(file_path)
    
    if "error" in rib_result:
        print(f"[🦾 IRONMAN]   ❌ RIBFINDER Error: {rib_result['error']}")
        return rib_result
    
    rib_count = rib_result.get("rib_count", 0)
    shape_pattern = rib_result.get("shape_pattern", "unknown")
    confidence = rib_result.get("confidence", 0)
    
    print(f"[🦾 IRONMAN]   ✓ RIBFINDER found: {rib_count} ribs")
    print(f"[🦾 IRONMAN]   → Pattern: {shape_pattern}")
    print(f"[🦾 IRONMAN]   → Confidence: {confidence}%")
    
    # Step 3: Prepare for detailed analysis  
    print("\n[🦾 IRONMAN] [STEP 3] Preparing detailed analysis request...")
    print(f"[🦾 IRONMAN]   ✓ File size: {os.path.getsize(file_path) / 1024:.2f} KB")
    print(f"[🦾 IRONMAN]   ✓ Rib count established: {rib_count} ribs")
    
    # Step 4: Send to CHATAN (Chat Analyse Agent) with rib count info
    print("\n[🦾 IRONMAN] [STEP 4] Sending request to CHATAN (Analysis Agent)...")
    print(f"[🦾 IRONMAN]   → Transferring image to CHATAN with established rib count: {rib_count}")
    print(f"[🦾 IRONMAN]   → CHATAN will use RIBFINDER's accurate count ({rib_count} ribs)")
    
    result = chat_analyse.analyze_with_rib_count(file_path, rib_result)
    
    print("[🦾 IRONMAN]   ✓ Response received from CHATAN")
    
    # Add RibFinder results to the main result
    result["ribfinder"] = rib_result
    result["expected_rib_count"] = rib_count
    
    # Step 5: Process and display results
    print("\n[🦾 IRONMAN] [STEP 5] Processing analysis results...")
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
                rib_info = f"[🦾 IRONMAN]   Rib {side_num}: {length} mm"
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
        print(f"\n[🦾 IRONMAN] [STEP 3.1] Requesting CHATAN to search for missing dimensions...")
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
    
    # Step 6: Compare with catalog shapes using CHATCO
    print("\n[🦾 IRONMAN] [STEP 6] Comparing with catalog shapes...")
    print("[🦾 IRONMAN]   → Sending to CHATCO (Comparison Agent)")
    print("[🦾 IRONMAN]   → CHATCO analyzing similarity with catalog...")
    
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
        print(f"[🦾 IRONMAN] [STEP 6.1] CHATCO recheck with established {ribfinder_count} ribs...")
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
    else:
        print("[🦾 IRONMAN]   ⚠️ No matching catalog shape found")
        result["comparison"] = {
            "best_match_file": None,
            "similarity_score": 0,
            "shape_match": False,
            "match_quality": "NO_MATCH"
        }
    
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

def reprocess_drawing(file_path, ribfinder, chat_analyse, chat_compare, previous_result, attempt_number):
    """
    Reprocess a drawing with additional instructions for CHATAN to recheck
    
    Args:
        file_path: Path to the drawing file
        chat_analyse: ChatGPT vision agent instance (CHATAN)
        chat_compare: ChatGPT comparison agent instance (CHATCO)
        previous_result: Previous analysis results that were rejected
        attempt_number: Current attempt number
        
    Returns:
        Dictionary with new analysis results
    """
    print(f"\n[🦾 IRONMAN] [STEP 3.{attempt_number}] Re-sending request to CHATAN...")
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
                rib_info = f"[🦾 IRONMAN]   Rib {side_num}: {length} mm"
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
    print("="*60)
    print("         BENT IRON ORDER RECOGNITION SYSTEM")
    print("="*60)
    print("\n[🦾 IRONMAN] Starting system initialization...")
    
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
    print("[🦾 IRONMAN]   → Initializing RIBFINDER (Premium Rib Counter)...")
    ribfinder = create_rib_finder_agent(api_key)  # RIBFINDER
    print("[🦾 IRONMAN]   ✓ RIBFINDER (GPT-4o Rib Counter) created and ready")
    
    print("[🦾 IRONMAN]   → Initializing CHATAN (Chat Analyse Agent)...")
    chat_analyse = create_chatgpt_vision_agent(api_key)  # CHATAN
    print("[🦾 IRONMAN]   ✓ CHATAN (Analysis Agent) created and ready")
    
    print("[🦾 IRONMAN]   → Initializing CHATCO (Chat Compare Agent)...")
    chat_compare = create_chatgpt_comparison_agent(api_key)  # CHATCO
    print("[🦾 IRONMAN]   ✓ CHATCO (Comparison Agent) created and ready")
    
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
    
    # Process each file
    print("\n[🦾 IRONMAN] Starting batch processing...")
    all_results = []
    for i, file in enumerate(files, 1):
        file_path = os.path.join(input_dir, file)
        print(f"\n[🦾 IRONMAN] Dispatching file {i}/{len(files)} to RIBFINDER, CHATAN & CHATCO...")
        
        # Initial analysis with RibFinder first
        result = process_drawing(file_path, ribfinder, chat_analyse, chat_compare)
        
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
                break
            else:
                retry_count += 1
                if retry_count < max_retries:
                    print(f"\n[🦾 IRONMAN] Reprocessing attempt {retry_count}/{max_retries-1}")
                    print("[🦾 IRONMAN]   → Asking CHATAN to recheck analysis...")
                    
                    # Add instruction for recheck
                    result = reprocess_drawing(file_path, ribfinder, chat_analyse, chat_compare, result, retry_count)
                else:
                    print(f"\n[🦾 IRONMAN] Maximum retries reached for {file}")
                    result["status"] = "Max retries reached - user rejected"
        
        all_results.append({
            "file": file,
            "result": result
        })
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
            print(f"RIBFINDER: number of ribs is - {ribfinder_count}")
            
            # CHATAN results
            chatan_count = result.get('number_of_ribs', 0)
            print(f"CHATAN: number of ribs - {chatan_count}")
            
            sides = result.get('sides', [])
            if sides:
                for side in sides:
                    side_num = side.get('side_number', '?')
                    description = side.get('description', 'unknown')
                    length = side.get('length', 0)
                    print(f"         rib {side_num}: {description}, {length} mm")
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
    
    print("\n[🦾 IRONMAN] System workflow completed successfully")
    print("="*60)

if __name__ == "__main__":
    main()
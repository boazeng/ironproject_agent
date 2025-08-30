import os
import sys
from dotenv import load_dotenv
from agents.llm_agents import create_chatgpt_vision_agent

# Set UTF-8 encoding for Windows
if sys.platform == "win32":
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# Load environment variables
load_dotenv()

def process_drawing(file_path, chatgpt_agent):
    """
    Process a bent iron drawing using ChatGPT Vision
    
    Args:
        file_path: Path to the drawing file
        chatgpt_agent: ChatGPT vision agent instance
    
    Returns:
        Dictionary with analysis results
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
    
    # Step 2: Prepare for analysis
    print("\n[🦾 IRONMAN] [STEP 2] Preparing analysis request...")
    print(f"[🦾 IRONMAN]   ✓ File size: {os.path.getsize(file_path) / 1024:.2f} KB")
    print("[🦾 IRONMAN]   ✓ Request prepared")
    
    # Step 3: Send to ChatGPT Vision Agent
    print("\n[🦾 IRONMAN] [STEP 3] Sending request to ChatGPT Vision Agent...")
    print("[🦾 IRONMAN]   → Transferring image to sub-agent")
    print("[🦾 IRONMAN]   → Waiting for vision analysis...")
    
    result = chatgpt_agent.analyze_drawing(file_path)
    
    print("[🦾 IRONMAN]   ✓ Response received from ChatGPT Vision Agent")
    
    # Step 4: Process and display results
    print("\n[🦾 IRONMAN] [STEP 4] Processing analysis results...")
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

def reprocess_drawing(file_path, chatgpt_agent, previous_result, attempt_number):
    """
    Reprocess a drawing with additional instructions for ChatGPT to recheck
    
    Args:
        file_path: Path to the drawing file
        chatgpt_agent: ChatGPT vision agent instance
        previous_result: Previous analysis results that were rejected
        attempt_number: Current attempt number
        
    Returns:
        Dictionary with new analysis results
    """
    print(f"\n[🦾 IRONMAN] [STEP 3.{attempt_number}] Re-sending request to ChatGPT Vision Agent...")
    print("[🦾 IRONMAN]   → Asking agent to double-check previous analysis")
    print("[🦾 IRONMAN]   → Requesting more careful examination of the drawing")
    
    # Create a special recheck method
    result = chatgpt_agent.recheck_analysis(file_path, previous_result)
    
    print("[🦾 IRONMAN]   ✓ Recheck analysis received from ChatGPT Vision Agent")
    
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
    
    # Initialize ChatGPT Vision Agent
    print("\n[🦾 IRONMAN] Creating sub-agents...")
    print("[🦾 IRONMAN]   → Initializing ChatGPT Vision Agent...")
    chatgpt_agent = create_chatgpt_vision_agent(api_key)
    print("[🦾 IRONMAN]   ✓ ChatGPT Vision Agent created and ready")
    
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
        print(f"\n[🦾 IRONMAN] Dispatching file {i}/{len(files)} to sub-agent...")
        
        # Initial analysis
        result = process_drawing(file_path, chatgpt_agent)
        
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
                    print("[🦾 IRONMAN]   → Asking ChatGPT agent to recheck analysis...")
                    
                    # Add instruction for recheck
                    result = reprocess_drawing(file_path, chatgpt_agent, result, retry_count)
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
            print(f"[🦾 IRONMAN]   • {file_name}: {shape} (Confidence: {confidence}%)")
    
    print("\n[🦾 IRONMAN] System workflow completed successfully")
    print("="*60)

if __name__ == "__main__":
    main()
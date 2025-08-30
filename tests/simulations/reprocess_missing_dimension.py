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

def simulate_missing_dimension_reprocess():
    """
    Simulate reprocessing when user rejects results due to missing dimension
    """
    print("="*60)
    print("🔍 REPROCESSING: MISSING DIMENSION DETECTED")
    print("="*60)
    
    # The rejected results with missing dimension
    rejected_result = {
        "shape_type": "L",
        "number_of_ribs": 2,
        "sides": [
            {"side_number": 1, "length": 415, "angle_to_next": 90, "description": "horizontal leg"},
            {"side_number": 2, "length": 0, "angle_to_next": 0, "description": "vertical leg"}
        ],
        "angles_between_ribs": [90],
        "confidence": 95
    }
    
    print("\n[USER INPUT] 'n' - Results REJECTED!")
    print("  ❌ User identified issue: Missing vertical dimension (0 mm)")
    print("  📁 File: Screenshot 2025-08-28 at 10.06.23 AM.png")
    print("  🎯 Problem: Incomplete dimension analysis")
    
    print("\n[MAIN ORCHESTRATOR] User rejected results!")
    print("  ❌ Results rejected - missing dimension detected")
    print("  🔍 Issue: Vertical leg shows 0 mm")
    
    print("\n[MAIN ORCHESTRATOR] Reprocessing attempt 1/2")
    print("  → Asking ChatGPT agent to search more carefully for dimensions")
    print("  → Focus on finding ALL numerical values on the drawing")
    
    # Initialize ChatGPT Vision Agent
    api_key = os.getenv("OPENAI_API_KEY")
    chatgpt_agent = create_chatgpt_vision_agent(api_key)
    
    # Get the file
    files = os.listdir("io/input")
    file_path = os.path.join("io", "input", files[0])
    
    print(f"\n[STEP 3.1] Enhanced dimension search request...")
    print("  🔍 Model: GPT-4o-mini")
    print("  📏 Focus: Find ALL dimension numbers")
    print("  🎯 Special instruction: Look for small/faint numbers")
    print("  ⚠️  Previous issue: Missing vertical leg dimension")
    
    # Recheck with enhanced dimension detection
    recheck_result = chatgpt_agent.recheck_analysis(file_path, rejected_result)
    
    print("  ✅ Enhanced dimension search complete")
    
    # Show recheck results
    print("\n" + "-"*60)
    print("ENHANCED DIMENSION ANALYSIS RESULTS:")
    print("-"*60)
    
    if "error" in recheck_result:
        print(f"ERROR: {recheck_result['error']}")
    else:
        print(f"Shape Type:        {recheck_result.get('shape_type', 'Unknown')}")
        print(f"Number of Ribs:    {recheck_result.get('number_of_ribs', 0)}")
        print(f"Confidence Score:  {recheck_result.get('confidence', 0)}%")
        
        # Display angles between ribs
        angles = recheck_result.get('angles_between_ribs', [])
        if angles:
            print(f"Angles between Ribs: {angles}°")
        
        # Display each rib with enhanced detail
        sides = recheck_result.get('sides', [])
        if sides:
            print("\nEnhanced Ribs Analysis:")
            for side in sides:
                side_num = side.get('side_number', '?')
                length = side.get('length', 0)
                angle = side.get('angle_to_next', 0)
                description = side.get('description', '')
                
                # Highlight if dimension was found
                status = "✅ FOUND" if length > 0 else "❌ MISSING"
                rib_info = f"  Rib {side_num}: {length} mm ({description}) {status}"
                print(rib_info)
                
                if angle > 0:
                    print(f"    → Angle to next rib: {angle}°")
        else:
            print("\nNo rib details detected")
    
    print("-"*60)
    
    # Compare results
    print("\n📊 DIMENSION COMPARISON:")
    print("Original Analysis:")
    for side in rejected_result['sides']:
        status = "❌ MISSING" if side['length'] == 0 else "✅"
        print(f"  {side['description']}: {side['length']} mm {status}")
    
    print("Enhanced Analysis:")
    for side in recheck_result.get('sides', []):
        status = "✅ FOUND" if side.get('length', 0) > 0 else "❌ STILL MISSING"
        print(f"  {side.get('description', 'unknown')}: {side.get('length', 0)} mm {status}")
    
    # Next validation step
    print("\n[MAIN ORCHESTRATOR] Requesting user validation...")
    print("?"*60)
    print("USER VALIDATION - ENHANCED DIMENSION ANALYSIS")
    print("?"*60)
    print(f"File: Screenshot 2025-08-28 at 10.06.23 AM.png")
    print(f"Shape: {recheck_result.get('shape_type', 'Unknown')}")
    print(f"Ribs: {recheck_result.get('number_of_ribs', 0)}")
    print(f"Confidence: {recheck_result.get('confidence', 0)}%")
    print("\nAre these ENHANCED results correct? (y/n):")
    print("(Focus: Did we find the missing vertical dimension?)")

if __name__ == "__main__":
    simulate_missing_dimension_reprocess()
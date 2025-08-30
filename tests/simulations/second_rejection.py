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

def simulate_second_rejection():
    """
    Simulate the second rejection (attempt 2/2)
    """
    print("="*60)
    print("SECOND REJECTION - FINAL RECHECK ATTEMPT")
    print("="*60)
    
    # The recheck results that were just rejected again
    rejected_recheck = {
        "shape_type": "L",
        "number_of_ribs": 2,
        "sides": [
            {"side_number": 1, "length": 405, "angle_to_next": 90},
            {"side_number": 2, "length": 405, "angle_to_next": 90}
        ],
        "angles_between_ribs": [90],
        "confidence": 95
    }
    
    print("\n[MAIN ORCHESTRATOR] User rejected recheck results!")
    print("  ❌ Results rejected by user (2nd time)")
    print("\n[MAIN ORCHESTRATOR] Reprocessing attempt 2/2 (FINAL ATTEMPT)")
    print("  → Asking ChatGPT agent to recheck analysis one more time...")
    
    # Initialize ChatGPT Vision Agent
    api_key = os.getenv("OPENAI_API_KEY")
    chatgpt_agent = create_chatgpt_vision_agent(api_key)
    
    # Get the file
    files = os.listdir("io/input")
    file_path = os.path.join("io", "input", files[0])
    
    print(f"\n[STEP 3.2] Final re-analysis request to ChatGPT Vision Agent...")
    print("  → This is the FINAL attempt (3/3)")
    print("  → Requesting VERY careful examination")
    print("  → Using highest detail analysis")
    
    # Final recheck attempt
    final_result = chatgpt_agent.recheck_analysis(file_path, rejected_recheck)
    
    print("  ✓ Final recheck analysis received")
    
    # Show final results
    print("\n" + "-"*60)
    print("FINAL RECHECK RESULTS (Attempt 2 - LAST CHANCE):")
    print("-"*60)
    
    if "error" in final_result:
        print(f"ERROR: {final_result['error']}")
    else:
        print(f"Shape Type:        {final_result.get('shape_type', 'Unknown')}")
        print(f"Number of Ribs:    {final_result.get('number_of_ribs', 0)}")
        print(f"Confidence Score:  {final_result.get('confidence', 0)}%")
        
        # Display angles between ribs
        angles = final_result.get('angles_between_ribs', [])
        if angles:
            print(f"Angles between Ribs: {angles}°")
        
        # Display each side with its details
        sides = final_result.get('sides', [])
        if sides:
            print("\nSides Details:")
            for side in sides:
                side_num = side.get('side_number', '?')
                length = side.get('length', 0)
                angle = side.get('angle_to_next', 0)
                print(f"  Side {side_num}: {length} mm")
                if angle > 0:
                    print(f"    → Angle to next side: {angle}°")
        else:
            print("\nNo side details detected")
    
    print("-"*60)
    
    # Final validation
    print("\n[MAIN ORCHESTRATOR] Final validation request...")
    print("?"*60)
    print("FINAL USER VALIDATION (ATTEMPT 3/3)")
    print("?"*60)
    print(f"File: Screenshot 2025-08-28 at 10.05.54 AM.png")
    print(f"Shape: {final_result.get('shape_type', 'Unknown')}")
    print(f"Ribs: {final_result.get('number_of_ribs', 0)}")
    print(f"Confidence: {final_result.get('confidence', 0)}%")
    print("\nAre these FINAL results correct? (y/n):")
    print("\n[WARNING] This is the last attempt!")
    print("If you say 'n' again, system will give up and mark as 'Max retries reached'")

if __name__ == "__main__":
    simulate_second_rejection()
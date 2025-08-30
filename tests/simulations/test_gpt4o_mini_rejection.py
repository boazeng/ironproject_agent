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

def test_gpt4o_mini_rejection():
    """
    Test GPT-4o-mini model rejection and reprocessing
    """
    print("="*60)
    print("GPT-4o-mini MODEL - USER REJECTION TEST")
    print("="*60)
    
    # The GPT-4o-mini results that were just rejected
    rejected_result = {
        "shape_type": "L",
        "number_of_ribs": 2,
        "sides": [
            {"side_number": 1, "length": 405, "angle_to_next": 90},
            {"side_number": 2, "length": 405, "angle_to_next": 90}
        ],
        "angles_between_ribs": [90],
        "confidence": 95
    }
    
    print("\n[MAIN ORCHESTRATOR] User rejected GPT-4o-mini results!")
    print("  ❌ Results rejected by user")
    print("  📱 Model: GPT-4o-mini")
    
    print("\n[MAIN ORCHESTRATOR] Reprocessing attempt 1/2")
    print("  → Asking GPT-4o-mini to recheck analysis...")
    print("  → Using enhanced prompt for more careful analysis")
    
    # Initialize ChatGPT Vision Agent (now with GPT-4o-mini)
    api_key = os.getenv("OPENAI_API_KEY")
    chatgpt_agent = create_chatgpt_vision_agent(api_key)
    
    # Get the file
    files = os.listdir("io/input")
    file_path = os.path.join("io", "input", files[0])
    
    print(f"\n[STEP 3.1] Re-sending request to GPT-4o-mini Vision Agent...")
    print("  → Model: GPT-4o-mini")
    print("  → Detail level: HIGH")
    print("  → Temperature: 0.1 (very consistent)")
    print("  → Asking to double-check previous analysis")
    
    # Recheck with GPT-4o-mini
    recheck_result = chatgpt_agent.recheck_analysis(file_path, rejected_result)
    
    print("  ✅ GPT-4o-mini recheck analysis received")
    
    # Show recheck results
    print("\n" + "-"*60)
    print("GPT-4o-mini RECHECK RESULTS:")
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
        
        # Display each side with its details
        sides = recheck_result.get('sides', [])
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
    
    # Compare original vs recheck
    print("\n📊 COMPARISON (GPT-4o-mini):")
    print(f"Original:  Shape={rejected_result['shape_type']}, Ribs={rejected_result['number_of_ribs']}, Conf={rejected_result['confidence']}%")
    print(f"Recheck:   Shape={recheck_result.get('shape_type')}, Ribs={recheck_result.get('number_of_ribs')}, Conf={recheck_result.get('confidence')}%")
    
    # Next validation step
    print("\n[MAIN ORCHESTRATOR] Requesting user validation again...")
    print("?"*60)
    print("USER VALIDATION REQUIRED (GPT-4o-mini RECHECK)")
    print("?"*60)
    print(f"Model: GPT-4o-mini")
    print(f"File: Screenshot 2025-08-28 at 10.05.54 AM.png")
    print(f"Shape: {recheck_result.get('shape_type', 'Unknown')}")
    print(f"Ribs: {recheck_result.get('number_of_ribs', 0)}")
    print(f"Confidence: {recheck_result.get('confidence', 0)}%")
    print("\nAre these GPT-4o-mini RECHECK results correct? (y/n):")

if __name__ == "__main__":
    test_gpt4o_mini_rejection()
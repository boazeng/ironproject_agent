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

def final_gpt4o_mini_attempt():
    """
    Final attempt with GPT-4o-mini before system gives up
    """
    print("="*60)
    print("🚨 FINAL GPT-4o-mini ATTEMPT (3/3)")
    print("="*60)
    
    # The recheck results that were rejected again
    second_rejection = {
        "shape_type": "L",
        "number_of_ribs": 2,
        "sides": [
            {"side_number": 1, "length": 405, "angle_to_next": 90},
            {"side_number": 2, "length": 405, "angle_to_next": 90}
        ],
        "angles_between_ribs": [90],
        "confidence": 95
    }
    
    print("\n[MAIN ORCHESTRATOR] User rejected GPT-4o-mini recheck!")
    print("  ❌❌ Results rejected TWICE by user")
    print("  📱 Model: GPT-4o-mini")
    print("  ⚠️  This is the FINAL attempt!")
    
    print("\n[MAIN ORCHESTRATOR] Final reprocessing attempt 2/2")
    print("  → Last chance for GPT-4o-mini")
    print("  → Maximum detail analysis")
    print("  → Lowest temperature for consistency")
    
    # Initialize ChatGPT Vision Agent
    api_key = os.getenv("OPENAI_API_KEY")
    chatgpt_agent = create_chatgpt_vision_agent(api_key)
    
    # Get the file
    files = os.listdir("io/input")
    file_path = os.path.join("io", "input", files[0])
    
    print(f"\n[STEP 3.2] FINAL request to GPT-4o-mini Vision Agent...")
    print("  🎯 Model: GPT-4o-mini")
    print("  🔍 Detail level: MAXIMUM")
    print("  🎛️  Temperature: 0.1 (ultra-consistent)")
    print("  💪 Enhanced 'final attempt' instructions")
    print("  📊 Previous rejections: 2")
    
    # Final attempt with GPT-4o-mini
    final_result = chatgpt_agent.recheck_analysis(file_path, second_rejection)
    
    print("  ✅ GPT-4o-mini FINAL analysis received")
    
    # Show final results
    print("\n" + "🔥"*60)
    print("GPT-4o-mini FINAL RESULTS (LAST CHANCE):")
    print("🔥"*60)
    
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
    
    print("🔥"*60)
    
    # Show all attempts comparison
    print("\n📈 ALL GPT-4o-mini ATTEMPTS COMPARISON:")
    print("-" * 50)
    print("Attempt 1: Shape=L, Ribs=2, Conf=95%")
    print("Attempt 2: Shape=L, Ribs=2, Conf=95%")
    print(f"Attempt 3: Shape={final_result.get('shape_type')}, Ribs={final_result.get('number_of_ribs')}, Conf={final_result.get('confidence')}%")
    print("-" * 50)
    
    # Final validation
    print("\n[MAIN ORCHESTRATOR] ABSOLUTE FINAL validation...")
    print("🚨"*60)
    print("FINAL USER VALIDATION (GPT-4o-mini - ATTEMPT 3/3)")
    print("🚨"*60)
    print(f"🤖 Model: GPT-4o-mini")
    print(f"📁 File: Screenshot 2025-08-28 at 10.05.54 AM.png")
    print(f"🔷 Shape: {final_result.get('shape_type', 'Unknown')}")
    print(f"🔢 Ribs: {final_result.get('number_of_ribs', 0)}")
    print(f"📊 Confidence: {final_result.get('confidence', 0)}%")
    print("\n❓ Are these FINAL GPT-4o-mini results correct? (y/n):")
    print("\n⚠️  WARNING: If you say 'n', system will give up!")
    print("💀 Status will be: 'Max retries reached - user rejected'")

if __name__ == "__main__":
    final_gpt4o_mini_attempt()
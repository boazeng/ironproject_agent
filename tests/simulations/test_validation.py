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

def simulate_user_validation():
    """
    Simulate the validation workflow
    """
    print("="*60)
    print("         BENT IRON ORDER RECOGNITION SYSTEM")
    print("         (VALIDATION TEST MODE)")
    print("="*60)
    
    # Initialize ChatGPT Vision Agent
    api_key = os.getenv("OPENAI_API_KEY")
    chatgpt_agent = create_chatgpt_vision_agent(api_key)
    
    # Test file
    file_path = os.path.join("io", "input", "Screenshot 2025-08-28 at 10.05.54 AM.png")
    
    # Check if file exists
    if not os.path.exists(file_path):
        print(f"File not found: {file_path}")
        print(f"Current directory: {os.getcwd()}")
        return
    
    print("\n[TEST] Initial Analysis...")
    result1 = chatgpt_agent.analyze_drawing(file_path)
    print(f"First result: {result1}")
    
    print("\n[TEST] Simulating user rejection...")
    print("User says: 'No, these results are wrong'")
    
    print("\n[TEST] Recheck Analysis...")
    result2 = chatgpt_agent.recheck_analysis(file_path, result1)
    print(f"Recheck result: {result2}")
    
    print("\n[TEST] Comparison:")
    print(f"Original: Shape={result1.get('shape_type')}, Ribs={result1.get('number_of_ribs')}")
    print(f"Recheck:  Shape={result2.get('shape_type')}, Ribs={result2.get('number_of_ribs')}")

if __name__ == "__main__":
    simulate_user_validation()
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

def simulate_rejection():
    """
    Simulate what happens when user rejects the results
    """
    print("="*60)
    print("         SIMULATING USER REJECTION")
    print("="*60)
    
    # Initialize ChatGPT Vision Agent
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        print("ERROR: Please set OPENAI_API_KEY in .env file")
        return
        
    chatgpt_agent = create_chatgpt_vision_agent(api_key)
    
    # Test file - use exact filename
    files = os.listdir("io/input")
    if not files:
        print("No files in io/input")
        return
    
    file_path = os.path.join("io", "input", files[0])
    print(f"Using file: {file_path}")
    
    print(f"\n[SIMULATION] Analyzing: {os.path.basename(file_path)}")
    
    # Step 1: Initial analysis (like we just saw)
    print("\n[STEP 1] Initial ChatGPT Analysis...")
    result1 = chatgpt_agent.analyze_drawing(file_path)
    
    if "error" in result1:
        print(f"Error: {result1['error']}")
        return
    
    print("Initial Results:")
    print(f"  Shape: {result1.get('shape_type')}")
    print(f"  Ribs: {result1.get('number_of_ribs')}")
    print(f"  Confidence: {result1.get('confidence')}%")
    
    # Step 2: User says "NO"
    print("\n[USER] Says: 'n' - Results are WRONG!")
    
    # Step 3: System reprocesses
    print("\n[STEP 2] Main Agent asks ChatGPT to recheck...")
    result2 = chatgpt_agent.recheck_analysis(file_path, result1)
    
    if "error" in result2:
        print(f"Recheck Error: {result2['error']}")
        return
    
    print("Recheck Results:")
    print(f"  Shape: {result2.get('shape_type')}")
    print(f"  Ribs: {result2.get('number_of_ribs')}")
    print(f"  Confidence: {result2.get('confidence')}%")
    
    # Display sides for both
    print("\n[COMPARISON]")
    print("Original Analysis:")
    for side in result1.get('sides', []):
        print(f"  Side {side.get('side_number')}: {side.get('length')} mm")
    
    print("Recheck Analysis:")
    for side in result2.get('sides', []):
        print(f"  Side {side.get('side_number')}: {side.get('length')} mm")
    
    print("\n[SIMULATION] Now the system would ask you again:")
    print("'Are these RECHECK results correct? (y/n)'")

if __name__ == "__main__":
    simulate_rejection()
import os
from dotenv import load_dotenv
import autogen

# Load environment variables
load_dotenv()

# Configuration for the main orchestrator agent
config_list = [
    {
        "model": "gpt-3.5-turbo",  # Using lower cost model
        "api_key": os.getenv("OPENAI_API_KEY"),
    }
]

# LLM configuration with cost-saving settings
llm_config = {
    "config_list": config_list,
    "temperature": 0.5,  # Lower temperature for more consistent outputs
    "max_tokens": 500,   # Limit tokens to control costs
    "timeout": 120,
    "cache_seed": 42,    # Enable caching to reduce API calls
}

# Create the main orchestrator agent
orchestrator = autogen.AssistantAgent(
    name="Orchestrator",
    llm_config=llm_config,
    system_message="""You are the main orchestrator for a bent iron order recognition system.
    
    Your responsibilities:
    1. Receive bent iron drawing files from the input folder
    2. Coordinate different specialized agents to analyze the drawings
    3. Combine results from multiple analysis methods
    4. Output final shape recognition and dimension extraction results
    
    Analysis workflow:
    - First, send the drawing to computer vision agents (OpenCV, YOLO)
    - Then, send it to LLM-based analysis agents
    - Compare and validate results from different methods
    - Produce a final consensus on shape type and dimensions
    
    Expected drawing types:
    - L-shaped bends
    - U-shaped bends
    - Z-shaped bends
    - Custom polygon shapes
    - Stirrups and hooks
    
    Output format should include:
    - Shape type identification
    - All dimension measurements
    - Bend angles
    - Confidence score
    """
)

# Create user proxy agent for interaction
user_proxy = autogen.UserProxyAgent(
    name="UserProxy",
    human_input_mode="TERMINATE",
    max_consecutive_auto_reply=10,
    is_termination_msg=lambda x: x.get("content", "").rstrip().endswith("TERMINATE"),
    code_execution_config={
        "work_dir": "io/output",
        "use_docker": False,
    },
)

def process_drawing(file_path):
    """
    Main function to process a bent iron drawing
    
    Args:
        file_path: Path to the drawing file
    
    Returns:
        Dictionary with shape analysis results
    """
    
    # Check if file exists
    if not os.path.exists(file_path):
        return {"error": f"File not found: {file_path}"}
    
    # Start the conversation with the orchestrator
    message = f"""
    Please analyze the bent iron drawing at: {file_path}
    
    Steps to follow:
    1. Load and preprocess the image
    2. Apply multiple detection methods
    3. Extract dimensions and angles
    4. Validate and combine results
    5. Return final analysis
    
    Begin the analysis now.
    """
    
    # Initiate the analysis
    user_proxy.initiate_chat(
        orchestrator,
        message=message
    )
    
    return {"status": "Analysis complete"}

def main():
    """
    Main entry point for the bent iron recognition system
    """
    print("=" * 50)
    print("BENT IRON ORDER RECOGNITION SYSTEM")
    print("=" * 50)
    print("\nOrchestrator Agent Initialized")
    print("Using GPT-3.5-turbo for cost efficiency")
    print("\nReady to process bent iron drawings...")
    
    # Check for input files
    input_dir = "io/input"
    if not os.path.exists(input_dir):
        os.makedirs(input_dir)
        print(f"\nCreated input directory: {input_dir}")
        print("Please place drawing files in this directory")
        return
    
    # List available files
    files = os.listdir(input_dir)
    if not files:
        print(f"\nNo files found in {input_dir}")
        print("Please add drawing files to process")
        return
    
    print(f"\nFound {len(files)} file(s) to process:")
    for i, file in enumerate(files, 1):
        print(f"  {i}. {file}")
    
    # Process each file
    for file in files:
        file_path = os.path.join(input_dir, file)
        print(f"\nProcessing: {file}")
        result = process_drawing(file_path)
        print(f"Result: {result}")

if __name__ == "__main__":
    # Check API key
    if not os.getenv("OPENAI_API_KEY"):
        print("ERROR: Please set OPENAI_API_KEY in .env file")
        exit(1)
    
    main()
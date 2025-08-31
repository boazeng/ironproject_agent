import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from dotenv import load_dotenv
from agents.llm_agents import create_rib_finder_agent

# Set UTF-8 encoding for Windows
if sys.platform == "win32":
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# Load environment variables
load_dotenv()

def test_rib_finder():
    """
    Test the RibFinder agent accuracy
    """
    print("="*60)
    print("🔢 TESTING RIBFINDER AGENT")
    print("="*60)
    
    # Check API key
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        print("❌ ERROR: API key not found")
        print("→ Please set OPENAI_API_KEY in .env file")
        return
    print("✓ API key loaded successfully")
    
    # Initialize RibFinder agent
    print("\n🤖 Initializing RibFinder agent...")
    ribfinder = create_rib_finder_agent(api_key)
    print("✓ RibFinder Agent created (using GPT-4o)")
    
    # Check for input files
    input_dir = "io/input"
    input_files = [f for f in os.listdir(input_dir) 
                   if f.lower().endswith(('.png', '.jpg', '.jpeg', '.bmp', '.gif'))]
    
    if not input_files:
        print(f"\n❌ No input files found in {input_dir}")
        return
    
    # Use first input file for testing
    test_file = input_files[0]
    test_path = os.path.join(input_dir, test_file)
    
    print(f"\n🎯 Testing RibFinder with: {test_file}")
    print("="*60)
    print("RIB COUNTING ANALYSIS")
    print("="*60)
    
    # Count ribs using RibFinder
    rib_result = ribfinder.count_ribs(test_path)
    
    # Display results
    if "error" in rib_result:
        print(f"❌ Error: {rib_result['error']}")
    else:
        print(f"🔢 RIB COUNT: {rib_result.get('rib_count', 0)}")
        print(f"📐 SHAPE PATTERN: {rib_result.get('shape_pattern', 'Unknown')}")
        print(f"🎯 CONFIDENCE: {rib_result.get('confidence', 0)}%")
        print(f"💭 REASONING: {rib_result.get('reasoning', 'Not provided')}")
        print(f"⭐ QUALITY: {rib_result.get('quality', 'Unknown')}")
        
        # Determine expected result based on pattern
        rib_count = rib_result.get('rib_count', 0)
        pattern = rib_result.get('shape_pattern', '').lower()
        
        print(f"\n📊 ANALYSIS:")
        if rib_count == 3:
            print("✅ Found 3 ribs - This indicates a U-shape")
            print("   → Pattern: left vertical + base + right vertical")
        elif rib_count == 2:
            print("⚠️ Found 2 ribs - This indicates an L-shape")  
            print("   → Pattern: vertical + horizontal (or horizontal + vertical)")
        elif rib_count == 1:
            print("📏 Found 1 rib - This is a straight bar")
        elif rib_count >= 4:
            print(f"🔧 Found {rib_count} ribs - This is a complex multi-bend shape")
        else:
            print("❓ Unexpected rib count")
        
        print(f"\n🔍 VERIFICATION:")
        confidence = rib_result.get('confidence', 0)
        if confidence >= 90:
            print("✅ Very high confidence - Result likely accurate")
        elif confidence >= 70:
            print("✅ Good confidence - Result probably correct")
        elif confidence >= 50:
            print("⚠️ Moderate confidence - May need verification")
        else:
            print("❌ Low confidence - Result questionable")
    
    print("\n" + "="*60)
    print("✅ RIBFINDER TEST COMPLETE")
    print("="*60)
    
    return rib_result

if __name__ == "__main__":
    test_rib_finder()
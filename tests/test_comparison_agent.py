import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from dotenv import load_dotenv
from agents.llm_agents import create_chatgpt_vision_agent, create_chatgpt_comparison_agent

# Set UTF-8 encoding for Windows
if sys.platform == "win32":
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# Load environment variables
load_dotenv()

def test_comparison_agent():
    """
    Test the comparison agent functionality
    """
    print("="*60)
    print("🔍 TESTING SHAPE COMPARISON AGENT")
    print("="*60)
    
    # Check API key
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        print("❌ ERROR: API key not found")
        print("→ Please set OPENAI_API_KEY in .env file")
        return
    print("✓ API key loaded successfully")
    
    # Initialize agents
    print("\n📊 Initializing agents...")
    vision_agent = create_chatgpt_vision_agent(api_key)
    comparison_agent = create_chatgpt_comparison_agent(api_key)
    print("✓ ChatGPT Vision Agent created")
    print("✓ ChatGPT Comparison Agent created")
    
    # Check for input files
    input_dir = "io/input"
    catalog_dir = "io/catalog"
    
    # Get first file from input directory
    input_files = [f for f in os.listdir(input_dir) 
                   if f.lower().endswith(('.png', '.jpg', '.jpeg', '.bmp', '.gif'))]
    
    if not input_files:
        print(f"\n❌ No input files found in {input_dir}")
        return
    
    # Check catalog directory
    catalog_files = [f for f in os.listdir(catalog_dir) 
                     if f.lower().endswith(('.png', '.jpg', '.jpeg', '.bmp', '.gif'))]
    
    print(f"\n📁 Found {len(input_files)} input file(s)")
    print(f"📁 Found {len(catalog_files)} catalog shape(s)")
    
    # Use first input file for testing
    test_file = input_files[0]
    test_path = os.path.join(input_dir, test_file)
    
    print(f"\n🎯 Testing with: {test_file}")
    
    # Step 1: Analyze the input shape
    print("\n" + "="*60)
    print("STEP 1: ANALYZING INPUT SHAPE")
    print("="*60)
    
    analysis_result = vision_agent.analyze_drawing(test_path)
    
    if "error" not in analysis_result:
        print(f"Shape Type: {analysis_result.get('shape_type', 'Unknown')}")
        print(f"Number of Ribs: {analysis_result.get('number_of_ribs', 0)}")
        print(f"Confidence: {analysis_result.get('confidence', 0)}%")
    else:
        print(f"Analysis Error: {analysis_result['error']}")
        return
    
    # Step 2: Compare with catalog
    print("\n" + "="*60)
    print("STEP 2: COMPARING WITH CATALOG SHAPES")
    print("="*60)
    
    comparison_result = comparison_agent.compare_with_analysis(
        test_path, 
        analysis_result,
        catalog_dir
    )
    
    # Display results
    print("\n" + "="*60)
    print("COMPARISON RESULTS")
    print("="*60)
    
    if "error" in comparison_result:
        print(f"❌ Error: {comparison_result['error']}")
    elif comparison_result.get("best_match"):
        best = comparison_result["best_match"]
        print(f"\n🏆 BEST MATCH FOUND:")
        print(f"  File: {best['catalog_file']}")
        print(f"  Similarity: {best.get('similarity_score', 0)}%")
        print(f"  Shape Match: {best.get('shape_match', False)}")
        print(f"  Match Quality: {comparison_result.get('match_quality', 'UNKNOWN')}")
        
        if best.get('matching_features'):
            print(f"\n✓ Matching Features:")
            for feature in best['matching_features']:
                print(f"    • {feature}")
        
        if best.get('differences'):
            print(f"\n⚠ Differences:")
            for diff in best['differences']:
                print(f"    • {diff}")
        
        # Show top 3 matches
        print(f"\n📊 TOP MATCHES:")
        for i, comp in enumerate(comparison_result['all_comparisons'][:3], 1):
            print(f"  {i}. {comp['catalog_file']}: {comp.get('similarity_score', 0)}%")
    else:
        print("❌ No matches found in catalog")
    
    print("\n" + "="*60)
    print("✅ COMPARISON TEST COMPLETE")
    print("="*60)
    
    # Return the comparison configuration name
    if comparison_result.get("best_match"):
        config_name = comparison_result["best_match_file"]
        print(f"\n💾 COMPARISON CONFIGURATION: {config_name}")
        return config_name
    else:
        print("\n💾 COMPARISON CONFIGURATION: No match found")
        return None

if __name__ == "__main__":
    test_comparison_agent()
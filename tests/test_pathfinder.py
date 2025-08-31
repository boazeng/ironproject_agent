import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Set UTF-8 encoding for Windows
if sys.platform == "win32":
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

from dotenv import load_dotenv
from agents.llm_agents import create_pathfinder_agent
import json

# Load environment variables
load_dotenv()

def test_pathfinder():
    """
    Test the PathFinder agent for vector path extraction
    """
    print("="*60)
    print("TESTING PATHFINDER AGENT - Vector Path Extraction")
    print("="*60)
    
    # Get API key from environment
    api_key = os.getenv("OPENAI_API_KEY")
    
    if not api_key:
        print("[ERROR] OPENAI_API_KEY not found in environment variables")
        return
    
    # Initialize PathFinder agent
    pathfinder = create_pathfinder_agent(api_key)
    print("[SUCCESS] PathFinder agent initialized\n")
    
    # Test with available image
    test_image = "io/input/Screenshot 2025-08-28 at 10.05.54 AM.png"
    
    if not os.path.exists(test_image):
        print(f"[ERROR] Test image not found: {test_image}")
        # Try to find any available image
        import glob
        images = glob.glob("io/input/*.png")
        if images:
            test_image = images[0]
            print(f"[SUCCESS] Using alternative image: {test_image}")
        else:
            print("[ERROR] No images found in io/input/")
            return
    
    # Test Case 1: U-shape with 3 ribs
    print("\n" + "="*40)
    print("TEST CASE: U-shape with 3 ribs")
    print("="*40)
    
    result = pathfinder.find_path(
        image_path=test_image,
        rib_count=3,
        all_straight=True
    )
    
    if "error" in result:
        print(f"[ERROR] {result['error']}")
    else:
        print(f"[SUCCESS] Path analysis successful!")
        print(f"\nRESULTS:")
        print(f"  - Shape Type: {result.get('shape_type', 'Unknown')}")
        print(f"  - Vertex Count: {result.get('vertex_count', 0)}")
        print(f"  - Total Path Length: {result.get('total_path_length', 0)} units")
        print(f"  - Is Closed: {result.get('is_closed', False)}")
        
        # Display vertices
        vertices = result.get('vertices', [])
        if vertices:
            print(f"\nVERTICES ({len(vertices)} points):")
            for v in vertices[:5]:  # Show first 5 vertices
                print(f"    V{v['index']}: ({v['x']}, {v['y']})")
            if len(vertices) > 5:
                print(f"    ... and {len(vertices) - 5} more")
        
        # Display vectors
        vectors = result.get('vectors', [])
        if vectors:
            print(f"\nVECTORS ({len(vectors)} segments):")
            for vec in vectors:
                print(f"    Rib {vec['rib_number']}:")
                print(f"      - Vector: ({vec['vector']['dx']:.1f}, {vec['vector']['dy']:.1f})")
                print(f"      - Length: {vec['length']:.1f} units")
                print(f"      - Angle: {vec['angle_degrees']:.1f} degrees")
                if 'bend_angle_to_next' in vec:
                    print(f"      - Bend to next: {vec['bend_angle_to_next']:.1f} degrees")
        
        # Display bounding box
        bbox = result.get('path_summary', {}).get('bounding_box', {})
        if bbox:
            print(f"\nBOUNDING BOX:")
            print(f"    - Width: {bbox.get('width', 0):.1f} units")
            print(f"    - Height: {bbox.get('height', 0):.1f} units")
            print(f"    - Min: ({bbox.get('min_x', 0):.1f}, {bbox.get('min_y', 0):.1f})")
            print(f"    - Max: ({bbox.get('max_x', 0):.1f}, {bbox.get('max_y', 0):.1f})")
    
    # Example of expected output for U-shape
    print("\n" + "="*40)
    print("EXPECTED U-SHAPE VECTOR REPRESENTATION:")
    print("="*40)
    print("For a U-shape (|___|) we expect:")
    print("  - 4 vertices: bottom-left, top-left, top-right, bottom-right")
    print("  - 3 vectors:")
    print("    1. Vertical up (left leg)")
    print("    2. Horizontal right (top/base)")
    print("    3. Vertical down (right leg)")
    print("  - 2 bend angles: both ~90 or ~-90 degrees")
    
    print("\n[SUCCESS] PathFinder test complete!")


if __name__ == "__main__":
    test_pathfinder()
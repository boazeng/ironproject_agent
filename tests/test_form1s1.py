import logging
import sys
from agents.llm_agents.format1_agent.order_format1_step1 import OrderFormat1Step1Agent

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)

def main():
    print("=" * 60)
    print("    TESTING ORDER FORMAT 1 STEP 1 AGENT (form1s1)")
    print("=" * 60)
    print()

    # Create agent instance
    agent = OrderFormat1Step1Agent()
    print(f"Agent created: {agent.name} (short: {agent.short_name})")
    print(f"Output directory: {agent.output_dir}")
    print()

    # Process all PDFs in input directory
    print("Starting batch processing...")
    print("-" * 60)

    results = agent.process_batch("io/input")

    print()
    print("=" * 60)
    print("PROCESSING SUMMARY")
    print("=" * 60)

    success_count = 0
    error_count = 0

    for result in results:
        if result["status"] == "success":
            success_count += 1
            print(f"[SUCCESS] {result['order_name']}")
            print(f"  -> Output: {result['output_filename']}")
            print(f"  -> Dimensions: {result['image_width']}x{result['image_height']} @ {result['dpi']} DPI")
        else:
            error_count += 1
            print(f"[ERROR] {result.get('order_name', 'Unknown')}")
            print(f"  -> Error: {result.get('error', 'Unknown error')}")

    print()
    print(f"Total processed: {len(results)}")
    print(f"Successful: {success_count}")
    print(f"Failed: {error_count}")
    print()
    print("Testing complete!")

if __name__ == "__main__":
    main()
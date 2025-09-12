"""
Test script for GLOBAL Agent - Full Order Page Analysis
"""

import os
import sys
import io
from dotenv import load_dotenv
from agents.llm_agents.global_agent import create_global_agent
import json

# Set UTF-8 encoding for Windows
if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# Load environment variables
load_dotenv()

def test_global_agent():
    """Test the GLOBAL agent with full order documents"""
    
    print("="*60)
    print("       GLOBAL AGENT TEST - FULL ORDER ANALYSIS")
    print("="*60)
    
    # Get API key
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        print("❌ ERROR: OPENAI_API_KEY not found in .env file")
        return
    
    # Create GLOBAL agent
    print("\n[TEST] Creating GLOBAL agent...")
    global_agent = create_global_agent(api_key)
    print("[TEST] ✓ GLOBAL agent created")
    
    # Check for input files in fullorder directory
    input_dir = "io/fullorder"
    if not os.path.exists(input_dir):
        print(f"[TEST] ❌ Directory not found: {input_dir}")
        return
    
    # List files in fullorder directory
    files = [f for f in os.listdir(input_dir) if f.lower().endswith(('.pdf', '.png', '.jpg', '.jpeg'))]
    
    if not files:
        print(f"[TEST] ❌ No files found in {input_dir}")
        return
    
    print(f"\n[TEST] Found {len(files)} file(s) to analyze:")
    for i, file in enumerate(files, 1):
        print(f"  {i}. {file}")
    
    # Process each file
    for file in files:
        file_path = os.path.join(input_dir, file)
        print(f"\n[TEST] {'='*50}")
        print(f"[TEST] Analyzing: {file}")
        print(f"[TEST] {'='*50}")
        
        # Analyze the order page
        results = global_agent.analyze_order_page(file_path)
        
        # Display results
        if "error" in results:
            print(f"[TEST] ❌ Error: {results['error']}")
        else:
            print("\n[TEST] ✓ Analysis Complete!")
            
            # Show OCR results
            if "ocr_data" in results and results["ocr_data"].get("text"):
                ocr_text = results["ocr_data"]["text"]
                print(f"\n[TEST] OCR Extracted Text (first 500 chars):")
                print("-" * 40)
                print(ocr_text[:500])
                print("-" * 40)
                print(f"[TEST] Total text length: {len(ocr_text)} characters")
                print(f"[TEST] Text blocks found: {len(results['ocr_data'].get('blocks', []))}")
            
            # Show document analysis
            if "analysis" in results and "sections" in results["analysis"]:
                sections = results["analysis"]["sections"]
                
                print("\n[TEST] Document Structure Analysis:")
                print("-" * 40)
                
                # Header section
                if "header" in sections:
                    header = sections["header"]
                    print(f"\n📄 HEADER SECTION:")
                    print(f"   Found: {header.get('found', False)}")
                    if header.get('found'):
                        print(f"   Company: {header.get('company_name', 'N/A')}")
                        print(f"   Order #: {header.get('order_number', 'N/A')}")
                        print(f"   Date: {header.get('date', 'N/A')}")
                        print(f"   Customer: {header.get('customer', 'N/A')}")
                        if header.get('header_table', {}).get('found'):
                            print(f"   Header Table: {header['header_table']['rows']} rows")
                
                # Main table section
                if "main_table" in sections:
                    main_table = sections["main_table"]
                    print(f"\n📊 MAIN TABLE SECTION:")
                    print(f"   Found: {main_table.get('found', False)}")
                    if main_table.get('found'):
                        print(f"   Row Count: {main_table.get('row_count', 0)}")
                        print(f"   Columns: {', '.join(main_table.get('columns', []))}")
                        print(f"   Contains Iron Orders: {main_table.get('contains_iron_orders', False)}")
                        if main_table.get('sample_items'):
                            print(f"   Sample Items: {len(main_table['sample_items'])} items")
                
                # Footer section
                if "footer" in sections:
                    footer = sections["footer"]
                    print(f"\n📝 FOOTER SECTION:")
                    print(f"   Found: {footer.get('found', False)}")
                    if footer.get('found'):
                        print(f"   Total Amount: {footer.get('total_amount', 'N/A')}")
                        print(f"   Has Signatures: {footer.get('signatures', False)}")
                        print(f"   Contact Info: {footer.get('contact_info', 'N/A')}")
            
            # Show summary
            if "analysis" in results and "summary" in results["analysis"]:
                print(f"\n[TEST] Summary:")
                print("-" * 40)
                print(results["analysis"]["summary"])
            
            # Save results to output file
            output_dir = "io/fullorder_output"
            if not os.path.exists(output_dir):
                os.makedirs(output_dir)
            
            output_file = os.path.join(output_dir, f"{os.path.splitext(file)[0]}_analysis.json")
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(results, f, ensure_ascii=False, indent=2)
            print(f"\n[TEST] Results saved to: {output_file}")
    
    print("\n" + "="*60)
    print("[TEST] All files processed successfully!")
    print("="*60)

if __name__ == "__main__":
    test_global_agent()
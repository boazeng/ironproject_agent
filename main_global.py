"""
IRONMAN System - GLOBAL Agent Only
Processes full order pages with the GLOBAL agent
"""

import os
import sys
from dotenv import load_dotenv
from agents.llm_agents.global_agent import create_global_agent
from utils.logger import IronManLogger
import json

# Set UTF-8 encoding for Windows
if sys.platform == "win32":
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# Load environment variables
load_dotenv()

def process_order_document(file_path, global_agent, logger):
    """
    Process a full order document using GLOBAL agent
    
    Args:
        file_path: Path to the order document
        global_agent: GLOBAL agent instance
        logger: Logger instance for workflow tracking
    
    Returns:
        Dictionary with analysis results
    """
    
    print("\n" + "="*60)
    print(f"[🦾 IRONMAN] NEW ORDER DOCUMENT ANALYSIS: {os.path.basename(file_path)}")
    print("="*60)
    
    # Step 1: Validate file
    print("\n[🦾 IRONMAN] [STEP 1] Validating file existence...")
    if not os.path.exists(file_path):
        print("[🦾 IRONMAN]   ❌ File not found!")
        logger.log_error(f"File not found: {file_path}", "GLOBAL")
        return {"error": f"File not found: {file_path}"}
    print(f"[🦾 IRONMAN]   ✓ File found at: {file_path}")
    
    # Step 2: Analyze with GLOBAL agent
    print("\n[🦾 IRONMAN] [STEP 2] Sending to GLOBAL agent for analysis...")
    print("[🦾 IRONMAN]   → GLOBAL will analyze document structure")
    print("[🦾 IRONMAN]   → Extracting header, table, and footer sections")
    
    logger.log_step_start(2, "Analyzing order document with GLOBAL", "GLOBAL")
    
    # Call GLOBAL agent
    result = global_agent.analyze_order_page(file_path)
    
    # Log the results
    logger.log_agent_output("GLOBAL", result)
    
    # Step 3: Process and display results
    print("\n[🦾 IRONMAN] [STEP 3] Processing analysis results...")
    print("-"*60)
    
    if "error" in result:
        print(f"[🦾 IRONMAN] ❌ ERROR: {result['error']}")
        logger.log_error(result['error'], "GLOBAL")
    else:
        print("[🦾 IRONMAN] DOCUMENT ANALYSIS RESULTS:")
        print("-"*60)
        
        # Display file info
        print(f"[🦾 IRONMAN] File: {result.get('file', 'Unknown')}")
        print(f"[🦾 IRONMAN] Type: {result.get('file_type', 'Unknown')}")
        if result.get('pdf_pages'):
            print(f"[🦾 IRONMAN] PDF Pages: {result['pdf_pages']}")
            print(f"[🦾 IRONMAN] Analyzed Page: {result.get('analyzing_page', 1)}")
        
        # Display sections analysis
        if "analysis" in result and "sections" in result["analysis"]:
            sections = result["analysis"]["sections"]
            
            # Header section
            print("\n[🦾 IRONMAN] 📄 HEADER SECTION:")
            if "header" in sections:
                header = sections["header"]
                if header.get('found'):
                    print(f"[🦾 IRONMAN]   ✓ Header found at: {header.get('location', 'unknown')}")
                    if header.get('order_number'):
                        print(f"[🦾 IRONMAN]   → Order Number: {header['order_number']}")
                    if header.get('customer'):
                        print(f"[🦾 IRONMAN]   → Customer: {header['customer']}")
                    if header.get('date'):
                        print(f"[🦾 IRONMAN]   → Date: {header['date']}")
                    if header.get('header_table', {}).get('found'):
                        print(f"[🦾 IRONMAN]   → Header Table: {header['header_table'].get('rows', 0)} rows")
                        key_values = header['header_table'].get('key_values', [])
                        if key_values:
                            print("[🦾 IRONMAN]   → Key Values:")
                            for kv in key_values[:3]:  # Show first 3 key-value pairs
                                for k, v in kv.items():
                                    print(f"[🦾 IRONMAN]     • {k}: {v}")
                else:
                    print("[🦾 IRONMAN]   ⚠ Header not found")
            
            # Main table section
            print("\n[🦾 IRONMAN] 📊 MAIN TABLE SECTION:")
            if "main_table" in sections:
                main_table = sections["main_table"]
                if main_table.get('found'):
                    print(f"[🦾 IRONMAN]   ✓ Main table found at: {main_table.get('location', 'unknown')}")
                    print(f"[🦾 IRONMAN]   → Row Count: {main_table.get('row_count', 0)}")
                    columns = main_table.get('columns', [])
                    if columns:
                        print(f"[🦾 IRONMAN]   → Columns: {', '.join(columns)}")
                    print(f"[🦾 IRONMAN]   → Contains Iron Orders: {main_table.get('contains_iron_orders', False)}")
                    sample_items = main_table.get('sample_items', [])
                    if sample_items:
                        print(f"[🦾 IRONMAN]   → Sample Items ({len(sample_items)} shown):")
                        for item in sample_items[:2]:  # Show first 2 items
                            item_str = ', '.join([f"{k}={v}" for k, v in item.items()])
                            print(f"[🦾 IRONMAN]     • {item_str}")
                else:
                    print("[🦾 IRONMAN]   ⚠ Main table not found")
            
            # Footer section
            print("\n[🦾 IRONMAN] 📝 FOOTER SECTION:")
            if "footer" in sections:
                footer = sections["footer"]
                if footer.get('found'):
                    print(f"[🦾 IRONMAN]   ✓ Footer found at: {footer.get('location', 'unknown')}")
                    if footer.get('total_amount'):
                        print(f"[🦾 IRONMAN]   → Total Amount: {footer['total_amount']}")
                    if footer.get('signatures'):
                        print("[🦾 IRONMAN]   → Has Signatures: Yes")
                    if footer.get('contact_info'):
                        print(f"[🦾 IRONMAN]   → Contact Info: {footer['contact_info']}")
                else:
                    print("[🦾 IRONMAN]   ⚠ Footer not found")
        
        # Display document language
        if "analysis" in result:
            language = result["analysis"].get("language", "unknown")
            print(f"\n[🦾 IRONMAN] Document Language: {language}")
        
        # Display summary
        if "analysis" in result and "summary" in result["analysis"]:
            print(f"\n[🦾 IRONMAN] Summary:")
            print(f"[🦾 IRONMAN]   {result['analysis']['summary']}")
    
    print("-"*60)
    return result

def main():
    """
    Main orchestrator for IRONMAN with GLOBAL agent only
    """
    # Initialize logger first
    logger = IronManLogger()
    
    print("="*60)
    print("    🦾 IRONMAN - FULL ORDER DOCUMENT ANALYSIS SYSTEM")
    print("="*60)
    print("\n[🦾 IRONMAN] Starting system initialization...")
    
    logger.log_system_start()
    
    # Check API key
    print("\n[🦾 IRONMAN] Checking API credentials...")
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        print("[🦾 IRONMAN]   ❌ ERROR: API key not found")
        print("[🦾 IRONMAN]   → Please set OPENAI_API_KEY in .env file")
        logger.log_error("API key not found", "SYSTEM")
        return
    print("[🦾 IRONMAN]   ✓ API key loaded successfully")
    
    # Initialize GLOBAL Agent
    print("\n[🦾 IRONMAN] Creating GLOBAL agent...")
    print("[🦾 IRONMAN]   → Initializing GLOBAL (Full Order Document Analyzer)...")
    global_agent = create_global_agent(api_key)
    print("[🦾 IRONMAN]   ✓ GLOBAL (Document Analyzer) created and ready")
    logger.log_agent_creation("GLOBAL", "Full Order Document Analyzer")
    
    # Check for input files in input directory
    print("\n[🦾 IRONMAN] Scanning input directory...")
    input_dir = "io/input"
    if not os.path.exists(input_dir):
        os.makedirs(input_dir)
        print(f"[🦾 IRONMAN]   → Created input directory: {input_dir}")
        print("[🦾 IRONMAN]   ❌ No files to process")
        print("[🦾 IRONMAN]   → Please place order documents in this directory")
        logger.log_error("No input files found", "SYSTEM")
        return
    
    # Check if specific filename was provided as command line argument
    if len(sys.argv) > 1:
        specific_filename = sys.argv[1]
        file_path = os.path.join(input_dir, specific_filename)
        if os.path.exists(file_path):
            print(f"[🦾 IRONMAN]   → Processing specific file: {specific_filename}")
            files = [specific_filename]
        else:
            print(f"[🦾 IRONMAN]   ❌ Specific file not found: {specific_filename}")
            logger.log_error(f"Specific file not found: {specific_filename}", "SYSTEM")
            return
    else:
        # List available files (original behavior)
        print(f"[🦾 IRONMAN]   → Scanning: {input_dir}")
        files = [f for f in os.listdir(input_dir) if f.lower().endswith(('.pdf', '.png', '.jpg', '.jpeg', '.bmp'))]
    
    if not files:
        print("[🦾 IRONMAN]   ❌ No document files found")
        print("[🦾 IRONMAN]   → Supported formats: .pdf, .png, .jpg, .jpeg, .bmp")
        logger.log_error("No valid files found", "SYSTEM")
        return
    
    print(f"[🦾 IRONMAN]   ✓ Found {len(files)} document file(s)")
    
    print("\n[🦾 IRONMAN] Files to process:")
    for i, file in enumerate(files, 1):
        try:
            print(f"[🦾 IRONMAN]   {i}. {file}")
        except UnicodeEncodeError:
            print(f"[🦾 IRONMAN]   {i}. {file.encode('ascii', 'ignore').decode('ascii')}")
    
    logger.log_input_scan(len(files), files)
    
    # Process each file
    print("\n[🦾 IRONMAN] Starting batch processing...")
    all_results = []
    
    for i, file in enumerate(files, 1):
        file_path = os.path.join(input_dir, file)
        print(f"\n[🦾 IRONMAN] Processing file {i}/{len(files)}...")
        
        logger.log_file_processing_start(file, i, len(files))
        
        # Process with GLOBAL agent
        result = process_order_document(file_path, global_agent, logger)
        
        # Save results
        if "error" not in result:
            output_dir = "io/fullorder_output"
            if not os.path.exists(output_dir):
                os.makedirs(output_dir)
            
            output_file = os.path.join(output_dir, f"{os.path.splitext(file)[0]}_ironman_analysis.json")
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(result, f, ensure_ascii=False, indent=2)
            print(f"\n[🦾 IRONMAN]   ✓ Results saved to: {output_file}")
            logger.log_file_completion(file, True)
        else:
            logger.log_file_completion(file, False)
        
        all_results.append({
            "file": file,
            "result": result
        })
        
        print(f"\n[🦾 IRONMAN] File {i}/{len(files)} processing complete")
    
    # Summary
    print("\n[🦾 IRONMAN] All files processed")
    print("\n" + "="*60)
    print("🦾 IRONMAN FINAL REPORT - DOCUMENT ANALYSIS")
    print("="*60)
    print(f"[🦾 IRONMAN] Total files processed: {len(files)}")
    
    successful = sum(1 for r in all_results if "error" not in r["result"])
    print(f"[🦾 IRONMAN] Successful analyses: {successful}")
    print(f"[🦾 IRONMAN] Failed analyses: {len(files) - successful}")
    
    print("\n[🦾 IRONMAN] Summary of Results:")
    for item in all_results:
        file_name = item["file"]
        result = item["result"]
        if "error" in result:
            print(f"[🦾 IRONMAN]   • {file_name}: ERROR - {result['error']}")
        else:
            if "analysis" in result and "sections" in result["analysis"]:
                sections = result["analysis"]["sections"]
                header_found = sections.get("header", {}).get("found", False)
                table_found = sections.get("main_table", {}).get("found", False)
                footer_found = sections.get("footer", {}).get("found", False)
                
                status_parts = []
                if header_found:
                    status_parts.append("Header ✓")
                if table_found:
                    rows = sections["main_table"].get("row_count", 0)
                    status_parts.append(f"Table ✓ ({rows} rows)")
                if footer_found:
                    status_parts.append("Footer ✓")
                
                status = ", ".join(status_parts) if status_parts else "No sections detected"
                print(f"[🦾 IRONMAN]   • {file_name}: {status}")
    
    # Detailed breakdown
    print("\n" + "="*60)
    print("🦾 IRONMAN DETAILED AGENT BREAKDOWN")
    print("="*60)
    
    for item in all_results:
        file_name = item["file"]
        result = item["result"]
        if "error" not in result:
            print(f"\n[🦾 IRONMAN] FILE: {file_name}")
            print("-" * 50)
            
            # GLOBAL agent results
            if "analysis" in result and "sections" in result["analysis"]:
                sections = result["analysis"]["sections"]
                
                # Header details
                if sections.get("header", {}).get("found"):
                    header = sections["header"]
                    print(f"GLOBAL: Header detected")
                    if header.get("order_number"):
                        print(f"        Order #: {header['order_number']}")
                    if header.get("customer"):
                        print(f"        Customer: {header['customer']}")
                
                # Table details
                if sections.get("main_table", {}).get("found"):
                    table = sections["main_table"]
                    print(f"GLOBAL: Main table detected")
                    print(f"        Rows: {table.get('row_count', 0)}")
                    print(f"        Iron orders: {table.get('contains_iron_orders', False)}")
                
                # Language detection
                language = result.get("analysis", {}).get("language", "unknown")
                print(f"GLOBAL: Language: {language}")
    
    logger.log_system_completion()
    print("\n[🦾 IRONMAN] System workflow completed successfully")
    print("="*60)

if __name__ == "__main__":
    main()
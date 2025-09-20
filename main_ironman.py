import os
import sys
from dotenv import load_dotenv
from agents.llm_agents.global_agent import create_global_agent
from utils.logger import IronManLogger

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
        file_path: Path to the order document file
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
        return {"error": f"File not found: {file_path}"}
    print(f"[🦾 IRONMAN]   ✓ File found at: {file_path}")
    
    # Step 2: Send to GLOBAL agent for analysis
    print("\n[🦾 IRONMAN] [STEP 2] Sending to GLOBAL agent for analysis...")
    print("[🦾 IRONMAN]   → GLOBAL will analyze document structure")
    print("[🦾 IRONMAN]   → Extracting header, table, and footer sections")
    
    logger.log_step_start(2, "Sending to GLOBAL agent for analysis", "GLOBAL")
    
    # Analyze document with GLOBAL agent
    result = global_agent.analyze_order_page(file_path)
    
    if "error" in result:
        print(f"[🦾 IRONMAN]   ❌ GLOBAL Error: {result['error']}")
        logger.log_error(f"GLOBAL analysis failed: {result['error']}", "GLOBAL")
        return result
    
    print("[🦾 IRONMAN]   ✓ GLOBAL analysis complete")
    logger.log_agent_output("GLOBAL", result)
    
    # Step 3: Process and display results
    print("\n[🦾 IRONMAN] [STEP 3] Processing analysis results...")
    print("-"*60)
    print("[🦾 IRONMAN] DOCUMENT ANALYSIS RESULTS:")
    print("-"*60)
    print(f"[🦾 IRONMAN] File: {os.path.basename(file_path)}")
    print(f"[🦾 IRONMAN] Type: {result.get('file_type', 'unknown')}")
    
    if result.get('pdf_pages'):
        print(f"[🦾 IRONMAN] PDF Pages: {result['pdf_pages']}")
        print(f"[🦾 IRONMAN] Analyzed Page: {result.get('analyzing_page', 1)}")
    
    # Display header section info
    sections = result.get('sections', {})
    header = sections.get('header', {})
    if header.get('found'):
        print(f"\n[🦾 IRONMAN] 📄 HEADER SECTION:")
        print(f"[🦾 IRONMAN]   ✓ Header found at: {header.get('location', 'unknown')}")
        if header.get('order_number'):
            print(f"[🦾 IRONMAN]   → Order Number: {header['order_number']}")
        if header.get('company_name'):
            print(f"[🦾 IRONMAN]   → Company: {header['company_name']}")
        if header.get('header_table', {}).get('found'):
            header_table = header['header_table']
            print(f"[🦾 IRONMAN]   → Header Table: {header_table.get('rows', 0)} rows")
            if header_table.get('key_values'):
                print(f"[🦾 IRONMAN]   → Key Values:")
                for kv in header_table['key_values']:
                    for key, value in kv.items():
                        print(f"[🦾 IRONMAN]     • {key}: {value}")
    else:
        print(f"\n[🦾 IRONMAN] 📄 HEADER SECTION:")
        print(f"[🦾 IRONMAN]   ⚠ Header not found")
    
    # Display main table info
    main_table = sections.get('main_table', {})
    if main_table.get('found'):
        print(f"\n[🦾 IRONMAN] 📊 MAIN TABLE SECTION:")
        print(f"[🦾 IRONMAN]   ✓ Main table found at: {main_table.get('location', 'unknown')}")
        print(f"[🦾 IRONMAN]   → Row Count: {main_table.get('row_count', 0)}")
        columns = main_table.get('columns', [])
        if columns:
            print(f"[🦾 IRONMAN]   → Columns: {', '.join(columns)}")
        if main_table.get('contains_iron_orders'):
            print(f"[🦾 IRONMAN]   → Contains Iron Orders: True")
    else:
        print(f"\n[🦾 IRONMAN] 📊 MAIN TABLE SECTION:")
        print(f"[🦾 IRONMAN]   ⚠ Main table not found")
    
    # Display footer info
    footer = sections.get('footer', {})
    if footer.get('found'):
        print(f"\n[🦾 IRONMAN] 📝 FOOTER SECTION:")
        print(f"[🦾 IRONMAN]   ✓ Footer found at: {footer.get('location', 'unknown')}")
        if footer.get('total_amount'):
            print(f"[🦾 IRONMAN]   → Total Amount: {footer['total_amount']}")
    else:
        print(f"\n[🦾 IRONMAN] 📝 FOOTER SECTION:")
        print(f"[🦾 IRONMAN]   ⚠ Footer not found")
    
    # Display language and summary
    analysis = result.get('analysis', {})
    if analysis.get('language'):
        print(f"\n[🦾 IRONMAN] Document Language: {analysis['language']}")
    
    if analysis.get('summary'):
        print(f"\n[🦾 IRONMAN] Summary:")
        print(f"[🦾 IRONMAN]   {analysis['summary']}")
    
    print("-"*60)
    
    return result

def main():
    """
    Main orchestrator for the IRONMAN Full Order Document Analysis System
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
        return
    print("[🦾 IRONMAN]   ✓ API key loaded successfully")
    
    # Initialize GLOBAL Agent
    print("\n[🦾 IRONMAN] Creating GLOBAL agent...")
    print("[🦾 IRONMAN]   → Initializing GLOBAL (Full Order Document Analyzer)...")
    global_agent = create_global_agent(api_key)
    print("[🦾 IRONMAN]   ✓ GLOBAL (Document Analyzer) created and ready")
    logger.log_agent_creation("GLOBAL", "Full Order Document Analyzer")
    
    # Check for input files
    print("\n[🦾 IRONMAN] Scanning input directory...")
    input_dir = "io/input"
    if not os.path.exists(input_dir):
        os.makedirs(input_dir)
        print(f"[🦾 IRONMAN]   → Created input directory: {input_dir}")
        print("[🦾 IRONMAN]   ❌ No files to process")
        print("[🦾 IRONMAN]   → Please place order document files in this directory")
        return
    
    # List available files (support both images and PDFs)
    print(f"[🦾 IRONMAN]   → Scanning: {input_dir}")
    files = [f for f in os.listdir(input_dir) if f.lower().endswith(('.png', '.jpg', '.jpeg', '.bmp', '.gif', '.pdf'))]
    
    if not files:
        print("[🦾 IRONMAN]   ❌ No document files found")
        print("[🦾 IRONMAN]   → Supported formats: .png, .jpg, .jpeg, .bmp, .gif, .pdf")
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
        
        # Save results to output directory
        if "error" not in result:
            output_dir = "io/fullorder_output"
            os.makedirs(output_dir, exist_ok=True)
            
            # Generate output filename
            base_name = os.path.splitext(file)[0]
            output_file = os.path.join(output_dir, f"{base_name}_ironman_analysis.json")
            
            # Save results as JSON
            import json
            try:
                with open(output_file, 'w', encoding='utf-8') as f:
                    json.dump(result, f, indent=2, ensure_ascii=False)
                print(f"\n[🦾 IRONMAN]   ✓ Results saved to: {output_file}")
            except Exception as e:
                print(f"[🦾 IRONMAN]   ⚠ Failed to save results: {e}")
        
        all_results.append({
            "file": file,
            "result": result
        })
        
        logger.log_file_completion(file, "error" not in result)
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
            sections = result.get('sections', {})
            header_found = "✓" if sections.get('header', {}).get('found') else "❌"
            table_found = "✓" if sections.get('main_table', {}).get('found') else "❌"
            table_rows = sections.get('main_table', {}).get('row_count', 0)
            if table_found == "✓":
                print(f"[🦾 IRONMAN]   • {file_name}: Header {header_found}, Table {table_found} ({table_rows} rows)")
            else:
                print(f"[🦾 IRONMAN]   • {file_name}: Header {header_found}, Table {table_found}")
    
    # Detailed breakdown per file
    print("\n" + "="*60)
    print("🦾 IRONMAN DETAILED AGENT BREAKDOWN")
    print("="*60)
    
    for item in all_results:
        file_name = item["file"]
        result = item["result"]
        if "error" not in result:
            print(f"\n[🦾 IRONMAN] FILE: {file_name}")
            print("-" * 50)
            
            # GLOBAL results
            sections = result.get('sections', {})
            analysis = result.get('analysis', {})
            
            # Header analysis
            header = sections.get('header', {})
            if header.get('found'):
                order_num = header.get('order_number', 'N/A')
                print(f"GLOBAL: Header detected")
                print(f"        Order #: {order_num}")
            else:
                print(f"GLOBAL: No header detected")
            
            # Table analysis
            main_table = sections.get('main_table', {})
            if main_table.get('found'):
                rows = main_table.get('row_count', 0)
                iron_orders = main_table.get('contains_iron_orders', False)
                print(f"GLOBAL: Main table detected")
                print(f"        Rows: {rows}")
                print(f"        Iron orders: {iron_orders}")
            else:
                print(f"GLOBAL: No main table detected")
            
            # Language detection
            language = analysis.get('language', 'unknown')
            print(f"GLOBAL: Language: {language}")
    
    logger.log_system_completion()
    print("\n[🦾 IRONMAN] System workflow completed successfully")
    print("="*60)

if __name__ == "__main__":
    main()
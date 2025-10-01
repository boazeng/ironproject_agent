#!/usr/bin/env python3
"""
Main Table Detection Pipeline
Orchestrates the table detection workflow for bent iron order documents

Workflow:
1. Clean output directory
2. Process PDFs with form1s1 agent to extract first page images
3. Future: Additional table detection steps
"""

import os
import sys
import glob
import logging
from datetime import datetime
from pathlib import Path

# Import agents
from output_cleaner import OutputCleanerAgent
from agents.llm_agents.format1_agent import OrderFormat1MainAgent
from agents.llm_agents.format1_agent.form1s2 import Form1S2Agent
from agents.llm_agents.format1_agent.form1s3 import Form1S3Agent
from agents.llm_agents.format1_agent.form1s3_1 import Form1S31Agent
from agents.llm_agents.format1_agent.form1s3_2 import Form1S32Agent
from agents.llm_agents.format1_agent.form1s3_3 import Form1S3_3Agent
from agents.llm_agents.format1_agent.form1s4 import Form1S4Agent
from agents.llm_agents.format1_agent.form1s4_1 import Form1S4_1Agent
from agents.llm_agents.format1_agent.form1s5 import Form1S5Agent
from agents.llm_agents.format1_agent.form1ocr1 import Form1OCR1Agent
from agents.llm_agents.format1_agent.form1ocr2 import Form1OCR2Agent
from agents.llm_agents.format1_agent.form1dat1 import Form1Dat1Agent

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('io/log/table_detection_log.txt', encoding='utf-8')
    ]
)

logger = logging.getLogger(__name__)

class TableDetectionPipeline:
    """Main pipeline for table detection workflow"""

    def __init__(self):
        self.input_dir = "io/input"
        self.output_dir = "io/fullorder_output"
        self.start_time = None
        self.results = {
            "cleaning": None,
            "form1s1": None,
            "form1s2": None,
            "form1s3": None,
            "form1s3_1": None,
            "form1s3_2": None,
            "form1s4": None,
            "form1s5": None,
            "form1ocr1": None,
            "form1ocr2": None,
            "form1dat1": None,
            "errors": []
        }

    def print_header(self):
        """Print the application header"""
        print("=" * 70)
        print(" " * 15 + "TABLE DETECTION PIPELINE")
        print(" " * 10 + "Bent Iron Order Document Processing System")
        print("=" * 70)
        print()

    def print_section(self, title):
        """Print a section header"""
        print()
        print("-" * 70)
        print(f"[{datetime.now().strftime('%H:%M:%S')}] {title}")
        print("-" * 70)

    def clean_output_directory(self, skip_cleaning=False):
        """Step 1: Clean the output directory"""
        self.print_section("STEP 1: CLEANING OUTPUT DIRECTORY")

        if skip_cleaning:
            print("[INFO] Skipping output cleaning (--skip-clean flag)")
            self.results["cleaning"] = {"status": "skipped"}
            return True

        try:
            cleaner = OutputCleanerAgent()

            # First get statistics
            print("[CLEANER] Analyzing output directory...")
            stats = cleaner.get_output_statistics()

            if stats["total_files"] == 0:
                print("[CLEANER] Output directory is already clean")
                self.results["cleaning"] = {"status": "already_clean"}
                return True

            print(f"[CLEANER] Found {stats['total_files']} files to clean ({stats['total_size_mb']:.2f} MB)")

            # Perform cleaning
            print("[CLEANER] Cleaning output files...")
            result = cleaner.clean_output_directory(dry_run=False)

            if result["status"] == "success":
                print(f"[CLEANER] Successfully cleaned {result['statistics']['files_deleted']} files")
                print(f"[CLEANER] Freed {result['statistics']['total_size_deleted_mb']:.2f} MB")
                print(f"[CLEANER] Preserved {result['statistics']['folders_preserved']} folders")
                self.results["cleaning"] = result
                return True
            else:
                error_msg = result.get("error", "Unknown error during cleaning")
                print(f"[CLEANER] [ERROR] {error_msg}")
                self.results["errors"].append(f"Cleaning error: {error_msg}")
                return False

        except Exception as e:
            error_msg = f"Failed to initialize cleaner: {str(e)}"
            print(f"[CLEANER] [ERROR] {error_msg}")
            self.results["errors"].append(error_msg)
            return False

    def process_with_format1(self):
        """Step 2: Process PDFs with Format 1 Main agent"""
        self.print_section("STEP 2: FORMAT 1 ORDER PROCESSING")

        try:
            # Initialize Format 1 Main agent
            format1_agent = OrderFormat1MainAgent()
            print(f"[FORMAT1] Agent initialized: {format1_agent.short_name}")
            print(f"[FORMAT1] Input directory: {self.input_dir}")

            # Process with Format 1 Main agent
            print(f"[FORMAT1] Starting Format 1 processing pipeline...")
            result = format1_agent.process_format1_orders(input_dir=self.input_dir)

            # Handle results based on status
            if result["status"] == "no_files":
                print(f"[FORMAT1] No PDF files found in {self.input_dir}")
                self.results["form1s1"] = {"status": "no_files"}
                return True

            elif result["status"] == "error":
                error_msg = f"Format 1 processing failed: {', '.join(result['errors'])}"
                print(f"[FORMAT1] [ERROR] {error_msg}")
                self.results["errors"].extend(result["errors"])
                self.results["form1s1"] = result
                return False

            else:  # completed or completed_with_errors
                # Get summary information
                summary = result.get("summary", {})

                # Display step results
                for step_name, step_data in result.get("steps", {}).items():
                    if step_data:
                        print()
                        print(f"[FORMAT1] {step_name}:")
                        print(f"  Status: {step_data.get('status', 'unknown')}")
                        print(f"  Files processed: {step_data.get('total_count', 0)}")
                        print(f"  Successful: {step_data.get('success_count', 0)}")
                        if step_data.get('error_count', 0) > 0:
                            print(f"  Failed: {step_data.get('error_count', 0)}")

                        # Show individual file results
                        for file_result in step_data.get("files_processed", []):
                            file_name = file_result.get('file', file_result.get('order', 'Unknown'))
                            if file_result["status"] == "success":
                                print(f"[FORMAT1] [SUCCESS] {file_name}")
                            else:
                                print(f"[FORMAT1] [ERROR] {file_name}: {file_result.get('error', 'Unknown error')}")

                # Store results
                self.results["form1s1"] = result

                # Add any errors to our error list
                if result.get("errors"):
                    self.results["errors"].extend(result["errors"])

                print()
                print(f"[FORMAT1] Processing completed in {result.get('processing_time_seconds', 0):.2f} seconds")

                return result["status"] == "completed"  # Return true only if no errors

        except Exception as e:
            error_msg = f"Failed during Format 1 processing: {str(e)}"
            print(f"[FORMAT1] [ERROR] {error_msg}")
            self.results["errors"].append(error_msg)
            return False

    def process_with_form1s2(self):
        """Step 3: Process images with Form1S2 agent for table detection"""
        self.print_section("STEP 3: TABLE BOUNDARY DETECTION (FORM1S2)")

        try:
            # Initialize Form1S2 agent
            form1s2_agent = Form1S2Agent()
            print(f"[FORM1S2] Agent initialized: {form1s2_agent.name}")

            # Find page1.png files from form1s1 output
            import glob
            page1_files = glob.glob(f"{self.output_dir}/*_page1.png")

            if not page1_files:
                print(f"[FORM1S2] No page1.png files found in {self.output_dir}")
                self.results["form1s2"] = {"status": "no_files"}
                return True

            print(f"[FORM1S2] Found {len(page1_files)} page1.png files to process")

            # Process each page1.png file
            processed_files = []
            successful_files = 0
            failed_files = 0

            for page1_file in page1_files:
                file_name = os.path.basename(page1_file)
                print(f"[FORM1S2] Processing: {file_name}")

                try:
                    result = form1s2_agent.process_image(page1_file)

                    if result["status"] == "success":
                        print(f"[FORM1S2] [SUCCESS] {file_name}")
                        print(f"[FORM1S2]   Coordinates: x={result['coordinates']['x']}, y={result['coordinates']['y']}, w={result['coordinates']['width']}, h={result['coordinates']['height']}")
                        print(f"[FORM1S2]   Output: {result['output_image_path']}")
                        successful_files += 1
                    else:
                        print(f"[FORM1S2] [ERROR] {file_name}: {result.get('error', 'Unknown error')}")
                        failed_files += 1

                    processed_files.append({
                        "file": file_name,
                        "status": result["status"],
                        "coordinates": result.get("coordinates"),
                        "output_image_path": result.get("output_image_path"),
                        "error": result.get("error")
                    })

                except Exception as e:
                    error_msg = f"Failed to process {file_name}: {str(e)}"
                    print(f"[FORM1S2] [ERROR] {error_msg}")
                    processed_files.append({
                        "file": file_name,
                        "status": "error",
                        "error": error_msg
                    })
                    failed_files += 1
                    self.results["errors"].append(error_msg)

            # Store results
            self.results["form1s2"] = {
                "status": "completed" if failed_files == 0 else "completed_with_errors",
                "total_files": len(page1_files),
                "successful_files": successful_files,
                "failed_files": failed_files,
                "processed_files": processed_files
            }

            print()
            print(f"[FORM1S2] Processing summary:")
            print(f"[FORM1S2]   Total files: {len(page1_files)}")
            print(f"[FORM1S2]   Successful: {successful_files}")
            print(f"[FORM1S2]   Failed: {failed_files}")

            return failed_files == 0

        except Exception as e:
            error_msg = f"Failed during Form1S2 processing: {str(e)}"
            print(f"[FORM1S2] [ERROR] {error_msg}")
            self.results["errors"].append(error_msg)
            return False

    def process_with_form1s3(self):
        """Step 4: Process ordertable.png with Form1S3 agent for grid line detection"""
        self.print_section("STEP 4: GRID LINE DETECTION (FORM1S3)")

        try:
            # Initialize Form1S3 agent
            form1s3_agent = Form1S3Agent()
            print(f"[FORM1S3] Agent initialized: {form1s3_agent.name}")

            # Look for ordertable.png from form1s2 output in grid folder with page number
            ordertable_files = glob.glob(f"{self.output_dir}/table_detection/grid/*_ordertable_page1.png")

            if not ordertable_files:
                print(f"[FORM1S3] ordertable.png not found at {self.output_dir}/table_detection/grid/*_ordertable_page1.png")
                self.results["form1s3"] = {"status": "no_files"}
                return True

            ordertable_path = ordertable_files[0]  # Use first matching file

            print(f"[FORM1S3] Found ordertable.png, processing grid line detection")

            try:
                result = form1s3_agent.process_image(ordertable_path)

                if result["status"] == "success":
                    print(f"[FORM1S3] [SUCCESS] Grid line detection completed")
                    print(f"[FORM1S3]   Red bounding box: x={result['red_bounding_box']['x']}, y={result['red_bounding_box']['y']}, w={result['red_bounding_box']['width']}, h={result['red_bounding_box']['height']}")
                    print(f"[FORM1S3]   Grid lines detected: {result['grid_lines']['horizontal_count']} horizontal, {result['grid_lines']['vertical_count']} vertical")
                    print(f"[FORM1S3]   Output: {result['output_image_path']}")

                    # Store results
                    self.results["form1s3"] = {
                        "status": "completed",
                        "total_files": 1,
                        "successful_files": 1,
                        "failed_files": 0,
                        "result": result
                    }
                    return True
                else:
                    error_msg = result.get("error", "Unknown error")
                    print(f"[FORM1S3] [ERROR] {error_msg}")

                    self.results["form1s3"] = {
                        "status": "completed_with_errors",
                        "total_files": 1,
                        "successful_files": 0,
                        "failed_files": 1,
                        "error": error_msg
                    }
                    self.results["errors"].append(f"Form1S3 error: {error_msg}")
                    return False

            except Exception as e:
                error_msg = f"Failed to process ordertable.png: {str(e)}"
                print(f"[FORM1S3] [ERROR] {error_msg}")

                self.results["form1s3"] = {
                    "status": "error",
                    "total_files": 1,
                    "successful_files": 0,
                    "failed_files": 1,
                    "error": error_msg
                }
                self.results["errors"].append(error_msg)
                return False

        except Exception as e:
            error_msg = f"Failed during Form1S3 processing: {str(e)}"
            print(f"[FORM1S3] [ERROR] {error_msg}")
            self.results["errors"].append(error_msg)
            return False

    def process_with_form1s3_1(self):
        """Step 4.1: Process ordertable_gridlines.png with Form1S3.1 agent for table body extraction"""
        self.print_section("STEP 4.1: TABLE BODY EXTRACTION (FORM1S3.1)")

        try:
            # Initialize Form1S3.1 agent
            form1s3_1_agent = Form1S31Agent()
            print(f"[FORM1S3.1] Agent initialized: {form1s3_1_agent.name}")

            # Look for ordertable_gridlines.png from form1s3 output in grid folder with page number
            gridlines_files = glob.glob(f"{self.output_dir}/table_detection/grid/*_ordertable_page1_gridlines.png")

            if not gridlines_files:
                print(f"[FORM1S3.1] ordertable_gridlines.png not found at {self.output_dir}/table_detection/grid/*_ordertable_page1_gridlines.png")
                self.results["form1s3_1"] = {"status": "no_files"}
                return True

            gridlines_path = gridlines_files[0]  # Use first matching file

            print(f"[FORM1S3.1] Found ordertable_gridlines.png, processing table body extraction")

            # Set output directory
            output_dir = f"{self.output_dir}/table_detection/table"

            # Process with Form1S3.1 agent
            result = form1s3_1_agent.process_file(gridlines_path, output_dir)

            if result["status"] == "success":
                print(f"[FORM1S3.1] [SUCCESS] Table body extraction completed")
                print(f"[FORM1S3.1]   Table dimensions: {result['table_dimensions']['width']}x{result['table_dimensions']['height']} px")
                print(f"[FORM1S3.1]   Output: {result['output_file']}")

                self.results["form1s3_1"] = {
                    "status": "success",
                    "files_processed": 1,
                    "successful": 1,
                    "failed": 0,
                    "table_dimensions": result["table_dimensions"],
                    "output_file": result["output_file"]
                }
                return True
            else:
                error_msg = f"Form1S3.1 processing failed: {result.get('error', 'Unknown error')}"
                print(f"[FORM1S3.1] [ERROR] {error_msg}")
                self.results["form1s3_1"] = {
                    "status": "error",
                    "files_processed": 1,
                    "successful": 0,
                    "failed": 1,
                    "error": result.get('error', 'Unknown error')
                }
                return False

        except Exception as e:
            error_msg = f"Failed during Form1S3.1 processing: {str(e)}"
            print(f"[FORM1S3.1] [ERROR] {error_msg}")
            self.results["errors"].append(error_msg)
            return False

    def process_with_form1s3_2(self):
        """Step 4.2: Process table_body.png with Form1S3.2 agent for order line counting"""
        self.print_section("STEP 4.2: ORDER LINE COUNTING (FORM1S3.2)")

        try:
            # Initialize Form1S3.2 agent
            form1s3_2_agent = Form1S32Agent()
            print(f"[FORM1S3.2] Agent initialized: {form1s3_2_agent.name}")

            # Look for table_bodyonly.png from form1s3.1 output with page number
            table_body_files = glob.glob(f"{self.output_dir}/table_detection/table/*_table_bodyonly_page1.png")

            if not table_body_files:
                print(f"[FORM1S3.2] table_bodyonly.png not found at {self.output_dir}/table_detection/table/*_table_bodyonly_page1.png")
                self.results["form1s3_2"] = {"status": "no_files"}
                return True

            table_body_path = table_body_files[0]  # Use first matching file

            print(f"[FORM1S3.2] Found table_bodyonly.png, processing order line counting")

            # Set output directory (same as table_body.png)
            output_dir = f"{self.output_dir}/table_detection/table"

            # Process with Form1S3.2 agent
            result = form1s3_2_agent.process_file(table_body_path, output_dir)

            if result["status"] == "success":
                print(f"[FORM1S3.2] [SUCCESS] Order line counting completed")
                print(f"[FORM1S3.2]   Row count: {result['row_count']}")
                print(f"[FORM1S3.2]   Analysis: {result.get('analysis', 'N/A')}")
                if result.get("row_coordinates"):
                    print(f"[FORM1S3.2]   Y coordinates extracted for {len(result['row_coordinates'])} rows")
                print(f"[FORM1S3.2]   Output: {result['output_file']}")

                self.results["form1s3_2"] = {
                    "status": "success",
                    "files_processed": 1,
                    "successful": 1,
                    "failed": 0,
                    "row_count": result["row_count"],
                    "analysis": result.get("analysis", ""),
                    "row_coordinates": result.get("row_coordinates", []),
                    "output_file": result["output_file"]
                }
                return True
            else:
                error_msg = f"Form1S3.2 processing failed: {result.get('error', 'Unknown error')}"
                print(f"[FORM1S3.2] [ERROR] {error_msg}")
                self.results["form1s3_2"] = {
                    "status": "error",
                    "files_processed": 1,
                    "successful": 0,
                    "failed": 1,
                    "error": result.get("error", "Unknown error")
                }
                return False

        except Exception as e:
            error_msg = f"Failed during Form1S3.2 processing: {str(e)}"
            print(f"[FORM1S3.2] [ERROR] {error_msg}")
            self.results["errors"].append(error_msg)
            return False

    def process_with_form1s3_3(self):
        """Step 4.3: Extract table header using Form1S3_3 agent"""
        self.print_section("STEP 4.3: TABLE HEADER EXTRACTION (FORM1S3.3)")

        try:
            # Initialize Form1S3_3 agent
            form1s3_3_agent = Form1S3_3Agent()
            print(f"[FORM1S3.3] Agent initialized: {form1s3_3_agent.name}")

            # Process to extract table headers (auto-detects gridlines files)
            results = form1s3_3_agent.process_batch()

            if results and len(results) > 0:
                success_count = sum(1 for r in results if r.get('status') == 'success')

                if success_count > 0:
                    print(f"[FORM1S3.3] [SUCCESS] Table header extraction completed")

                    for result in results:
                        if result['status'] == 'success':
                            print(f"[FORM1S3.3]   Order: {result['order_name']}")
                            print(f"[FORM1S3.3]   Header dimensions: {result['header_width']}x{result['header_height']} px")
                            print(f"[FORM1S3.3]   Output: {result['output_file']}")

                    self.results["form1s3_3"] = {
                        "status": "success",
                        "files_processed": len(results),
                        "successful": success_count,
                        "results": results
                    }
                    return True
                else:
                    print(f"[FORM1S3.3] No files successfully processed")
                    self.results["form1s3_3"] = {"status": "no_success"}
                    return True
            else:
                print(f"[FORM1S3.3] No gridlines files found to process")
                self.results["form1s3_3"] = {"status": "no_files"}
                return True

        except Exception as e:
            error_msg = f"Failed during Form1S3.3 processing: {str(e)}"
            print(f"[FORM1S3.3] [ERROR] {error_msg}")
            self.results["errors"].append(error_msg)
            return False

    def process_with_form1s4(self):
        """Step 5: Process shape_column files with Form1S4 agent for drawing cell extraction"""
        self.print_section("STEP 5: DRAWING CELL EXTRACTION (FORM1S4)")

        try:
            # Initialize Form1S4 agent
            form1s4_agent = Form1S4Agent()
            print(f"[FORM1S4] Agent initialized: {form1s4_agent.name}")

            # Look for shape_column files from form1s4_1 output in shape_column folder
            shape_column_files = glob.glob(f"{self.output_dir}/table_detection/shape_column/*_shape_column_page*.png")

            if not shape_column_files:
                print(f"[FORM1S4] shape_column files not found at {self.output_dir}/table_detection/shape_column/*_shape_column_page*.png")
                self.results["form1s4"] = {"status": "no_files"}
                return True

            print(f"[FORM1S4] Found {len(shape_column_files)} shape_column files, processing drawing cell extraction")

            total_successful = 0
            all_saved_files = []

            # Process all shape_column files
            for shape_column_path in shape_column_files:
                print(f"[FORM1S4] Processing: {os.path.basename(shape_column_path)}")

                try:
                    result = form1s4_agent.process_image(shape_column_path)

                    if result["status"] == "success":
                        extraction_results = result.get("extraction_results", {})
                        total_cells = extraction_results.get("total_cells_extracted", 0)

                        if total_cells > 0:
                            total_successful += 1
                            if extraction_results.get("saved_files"):
                                all_saved_files.extend(extraction_results["saved_files"])

                        print(f"[FORM1S4] [SUCCESS] {os.path.basename(shape_column_path)} - {total_cells} cells extracted")
                    else:
                        error_msg = result.get("error", "Unknown error")
                        print(f"[FORM1S4] [ERROR] Failed to process {os.path.basename(shape_column_path)}: {error_msg}")

                except Exception as e:
                    print(f"[FORM1S4] [ERROR] Exception processing {os.path.basename(shape_column_path)}: {str(e)}")

            # Final summary
            if total_successful > 0:
                print(f"[FORM1S4] [SUCCESS] Drawing cell extraction completed")
                print(f"[FORM1S4]   Files processed: {total_successful}/{len(shape_column_files)}")
                print(f"[FORM1S4]   Total cells extracted: {len(all_saved_files)}")

                if all_saved_files:
                    print(f"[FORM1S4]   Sample files saved:")
                    for file_path in all_saved_files[:5]:  # Show first 5 files
                        file_name = os.path.basename(file_path)
                        print(f"[FORM1S4]     - {file_name}")
                    if len(all_saved_files) > 5:
                        print(f"[FORM1S4]     ... and {len(all_saved_files) - 5} more files")

                # Store results
                self.results["form1s4"] = {
                    "status": "completed",
                    "total_files": len(shape_column_files),
                    "successful_files": total_successful,
                    "failed_files": len(shape_column_files) - total_successful,
                    "total_cells_extracted": len(all_saved_files)
                }
                return True
            else:
                error_msg = "No files processed successfully"
                print(f"[FORM1S4] [ERROR] {error_msg}")

                self.results["form1s4"] = {
                    "status": "completed_with_errors",
                    "total_files": len(shape_column_files),
                    "successful_files": 0,
                    "failed_files": len(shape_column_files),
                    "error": error_msg
                }
                self.results["errors"].append(f"Form1S4 error: {error_msg}")
                return False

        except Exception as e:
            error_msg = f"Failed to process shape_column files: {str(e)}"
            print(f"[FORM1S4] [ERROR] {error_msg}")

            self.results["form1s4"] = {
                "status": "error",
                "total_files": 1,
                "successful_files": 0,
                "failed_files": 1,
                "error": error_msg
            }
            self.results["errors"].append(error_msg)
            return False

    def process_with_form1s4_1(self):
        """Step 5.1: Process table_bodyonly files with Form1S4.1 agent for full drawing column extraction"""
        self.print_section("STEP 5.1: FULL DRAWING COLUMN EXTRACTION (FORM1S4.1)")

        try:
            # Initialize Form1S4.1 agent
            form1s4_1_agent = Form1S4_1Agent()
            print(f"[FORM1S4.1] Agent initialized: {form1s4_1_agent.name}")

            # Use batch processing to handle all table_bodyonly files
            results = form1s4_1_agent.process_batch()

            if results:
                successful_results = [r for r in results if r.get("status") == "success"]

                if successful_results:
                    result = successful_results[0]  # Take first successful result
                    print(f"[FORM1S4.1] [SUCCESS] Full drawing column extraction completed")
                    print(f"[FORM1S4.1]   Order: {result.get('order_name', 'Unknown')}")
                    print(f"[FORM1S4.1]   Column dimensions: {result.get('column_width', 0)}x{result.get('column_height', 0)} px")
                    print(f"[FORM1S4.1]   Output: {result.get('output_file', 'Unknown')}")

                    self.results["form1s4_1"] = {
                        "status": "success",
                        "total_files": len(results),
                        "successful_files": len(successful_results),
                        "failed_files": len(results) - len(successful_results),
                        "output_files": [r.get("output_file") for r in successful_results],
                        "column_dimensions": [(r.get("column_width", 0), r.get("column_height", 0)) for r in successful_results]
                    }
                    return True
                else:
                    error_msg = "No successful column extractions"
                    print(f"[FORM1S4.1] [ERROR] {error_msg}")

                    self.results["form1s4_1"] = {
                        "status": "no_success",
                        "total_files": len(results),
                        "successful_files": 0,
                        "failed_files": len(results),
                        "error": error_msg
                    }
                    self.results["errors"].append(f"Form1S4.1 error: {error_msg}")
                    return False
            else:
                print(f"[FORM1S4.1] No table_bodyonly files found for processing")
                self.results["form1s4_1"] = {"status": "no_files"}
                return True

        except Exception as e:
            error_msg = f"Failed during Form1S4.1 processing: {str(e)}"
            print(f"[FORM1S4.1] [ERROR] {error_msg}")
            self.results["errors"].append(error_msg)
            return False

    def process_with_form1s5(self):
        """Step 6: Process ordertable_gridlines.png with Form1S5 agent for order title extraction"""
        self.print_section("STEP 6: ORDER TITLE EXTRACTION (FORM1S5)")

        try:
            # Initialize Form1S5 agent
            form1s5_agent = Form1S5Agent()
            print(f"[FORM1S5] Agent initialized: {form1s5_agent.name}")

            # Look for ordertable_gridlines.png from form1s3 output in grid folder with page number
            gridlines_files = glob.glob(f"{self.output_dir}/table_detection/grid/*_ordertable_page1_gridlines.png")

            if not gridlines_files:
                print(f"[FORM1S5] ordertable_gridlines.png not found at {self.output_dir}/table_detection/grid/*_ordertable_page1_gridlines.png")
                self.results["form1s5"] = {"status": "no_files"}
                return True

            gridlines_path = gridlines_files[0]  # Use first matching file

            print(f"[FORM1S5] Found ordertable_gridlines.png, processing order title extraction")

            try:
                result = form1s5_agent.process_image(gridlines_path, self.output_dir)

                if result["status"] == "success":
                    title_extraction = result.get("title_extraction", {})
                    title_dimensions = title_extraction.get("title_dimensions", {})

                    print(f"[FORM1S5] [SUCCESS] Order title extraction completed")
                    print(f"[FORM1S5]   Title dimensions: {title_dimensions.get('width', 0)}x{title_dimensions.get('height', 0)} px")
                    print(f"[FORM1S5]   Saved to: {title_extraction.get('saved_file', 'N/A')}")

                    # Store results
                    self.results["form1s5"] = {
                        "status": "completed",
                        "total_files": 1,
                        "successful_files": 1,
                        "failed_files": 0,
                        "result": result
                    }
                    return True
                else:
                    error_msg = result.get("error", "Unknown error")
                    print(f"[FORM1S5] [ERROR] {error_msg}")

                    self.results["form1s5"] = {
                        "status": "completed_with_errors",
                        "total_files": 1,
                        "successful_files": 0,
                        "failed_files": 1,
                        "error": error_msg
                    }
                    self.results["errors"].append(f"Form1S5 error: {error_msg}")
                    return False

            except Exception as e:
                error_msg = f"Failed to process ordertable_gridlines.png with Form1S5: {str(e)}"
                print(f"[FORM1S5] [ERROR] {error_msg}")

                self.results["form1s5"] = {
                    "status": "error",
                    "total_files": 1,
                    "successful_files": 0,
                    "failed_files": 1,
                    "error": error_msg
                }
                self.results["errors"].append(error_msg)
                return False

        except Exception as e:
            error_msg = f"Failed during Form1S5 processing: {str(e)}"
            print(f"[FORM1S5] [ERROR] {error_msg}")
            self.results["errors"].append(error_msg)
            return False

    def process_all_pages(self):
        """Process all pages found in order_to_image folder through form1s2-5 pipeline"""
        # Find all page files in order_to_image directory
        order_to_image_dir = os.path.join(self.output_dir, "order_to_image")

        if not os.path.exists(order_to_image_dir):
            print()
            print(f"[ERROR] order_to_image directory not found: {order_to_image_dir}")
            self.results["errors"].append("order_to_image directory not found")
            return False

        # Find all page files
        page_files = glob.glob(os.path.join(order_to_image_dir, "*_page*.png"))

        if not page_files:
            print()
            print(f"[ERROR] No page files found in {order_to_image_dir}")
            self.results["errors"].append("No page files found in order_to_image directory")
            return False

        # Sort files by page number
        page_files.sort()

        print()
        print(f"[INFO] Found {len(page_files)} page(s) to process")

        # Initialize results tracking for multiple pages
        self.results["pages"] = {}

        # Process each page through the complete pipeline
        for page_file in page_files:
            page_name = os.path.basename(page_file)
            print()
            print(f"[INFO] Processing page: {page_name}")

            # Extract page number from filename
            page_number = "1"
            if "_page" in page_name:
                try:
                    page_number = page_name.split("_page")[1].split(".")[0]
                except:
                    page_number = "1"

            # Process this page through all steps
            page_success = self.process_single_page(page_file, page_number)

            # Store page results
            self.results["pages"][page_number] = {
                "file": page_file,
                "success": page_success
            }

            if page_success:
                print(f"[SUCCESS] Page {page_number} processed successfully")
            else:
                print(f"[ERROR] Page {page_number} processing failed")

    def process_single_page(self, page_file, page_number):
        """Process a single page through form1s2-5 pipeline"""
        try:
            page_name = os.path.basename(page_file)

            # Step 1: Form1S2 - Table boundary detection
            print(f"  -> Running Form1S2 for page {page_number}")
            form1s2_success = self.process_page_with_form1s2(page_file, page_number)

            if not form1s2_success:
                print(f"  -> Form1S2 failed for page {page_number}")
                return False

            # Step 2: Form1S3 - Grid line detection
            print(f"  -> Running Form1S3 for page {page_number}")
            form1s3_success = self.process_page_with_form1s3(page_number)

            if not form1s3_success:
                print(f"  -> Form1S3 failed for page {page_number}")
                return False

            # Step 3: Form1S3.1 - Table body extraction
            print(f"  -> Running Form1S3.1 for page {page_number}")
            form1s3_1_success = self.process_page_with_form1s3_1(page_number)

            # Step 4: Form1S3.2 - Order line counting
            print(f"  -> Running Form1S3.2 for page {page_number}")
            form1s3_2_success = self.process_page_with_form1s3_2(page_number)

            # Step 5: Form1S3.3 - Table header extraction
            print(f"  -> Running Form1S3.3 for page {page_number}")
            form1s3_3_success = self.process_page_with_form1s3_3(page_number)

            # Step 6: Form1S4.1 - Full drawing column extraction (must run first)
            print(f"  -> Running Form1S4.1 for page {page_number}")
            form1s4_1_success = self.process_page_with_form1s4_1(page_number)

            # Step 7: Form1S4 - Drawing cell extraction from shape columns
            print(f"  -> Running Form1S4 for page {page_number}")
            form1s4_success = self.process_page_with_form1s4(page_number)

            # Step 8: Form1S5 - Order title extraction
            print(f"  -> Running Form1S5 for page {page_number}")
            form1s5_success = self.process_page_with_form1s5(page_number)

            return True

        except Exception as e:
            error_msg = f"Error processing page {page_number}: {str(e)}"
            print(f"  -> {error_msg}")
            self.results["errors"].append(error_msg)
            return False

    def process_page_with_form1s2(self, page_file, page_number):
        """Process single page with Form1S2 agent"""
        try:
            form1s2_agent = Form1S2Agent()
            result = form1s2_agent.process_image(page_file)
            return result.get("status") == "success"
        except Exception as e:
            self.results["errors"].append(f"Form1S2 page {page_number} error: {str(e)}")
            return False

    def process_page_with_form1s3(self, page_number):
        """Process single page with Form1S3 agent"""
        try:
            form1s3_agent = Form1S3Agent()
            # Look for ordertable file for this page
            ordertable_pattern = f"{self.output_dir}/table_detection/grid/*_ordertable_page{page_number}.png"
            ordertable_files = glob.glob(ordertable_pattern)

            if not ordertable_files:
                return False

            result = form1s3_agent.process_image(ordertable_files[0])
            return result.get("status") == "success"
        except Exception as e:
            self.results["errors"].append(f"Form1S3 page {page_number} error: {str(e)}")
            return False

    def process_page_with_form1s3_1(self, page_number):
        """Process single page with Form1S3.1 agent"""
        try:
            form1s3_1_agent = Form1S31Agent()
            # Look for gridlines file for this page
            gridlines_pattern = f"{self.output_dir}/table_detection/grid/*_ordertable_page{page_number}_gridlines.png"
            gridlines_files = glob.glob(gridlines_pattern)

            if not gridlines_files:
                return False

            output_dir = f"{self.output_dir}/table_detection/table"
            result = form1s3_1_agent.process_file(gridlines_files[0], output_dir)
            return result.get("status") == "success"
        except Exception as e:
            self.results["errors"].append(f"Form1S3.1 page {page_number} error: {str(e)}")
            return False

    def process_page_with_form1s3_2(self, page_number):
        """Process single page with Form1S3.2 agent"""
        try:
            form1s3_2_agent = Form1S32Agent()
            # Look for table_bodyonly file for this page
            table_body_pattern = f"{self.output_dir}/table_detection/table/*_table_bodyonly_page{page_number}.png"
            table_body_files = glob.glob(table_body_pattern)

            if not table_body_files:
                return False

            output_dir = f"{self.output_dir}/table_detection/table"
            result = form1s3_2_agent.process_file(table_body_files[0], output_dir)
            return result.get("status") == "success"
        except Exception as e:
            self.results["errors"].append(f"Form1S3.2 page {page_number} error: {str(e)}")
            return False

    def process_page_with_form1s3_3(self, page_number):
        """Process single page with Form1S3.3 agent"""
        try:
            form1s3_3_agent = Form1S3_3Agent()
            results = form1s3_3_agent.process_batch()
            return len([r for r in results if r.get("status") == "success"]) > 0
        except Exception as e:
            self.results["errors"].append(f"Form1S3.3 page {page_number} error: {str(e)}")
            return False

    def process_page_with_form1s4(self, page_number):
        """Process single page with Form1S4 agent using shape column files"""
        try:
            form1s4_agent = Form1S4Agent()
            # Look for shape_column file for this page (created by Form1S4_1)
            shape_column_pattern = f"{self.output_dir}/table_detection/shape_column/*_shape_column_page{page_number}.png"
            shape_column_files = glob.glob(shape_column_pattern)

            if not shape_column_files:
                print(f"[FORM1S4] No shape column file found for page {page_number}")
                return False

            result = form1s4_agent.process_image(shape_column_files[0])
            return result.get("status") == "success"
        except Exception as e:
            self.results["errors"].append(f"Form1S4 page {page_number} error: {str(e)}")
            return False

    def process_page_with_form1s4_1(self, page_number):
        """Process single page with Form1S4.1 agent"""
        try:
            form1s4_1_agent = Form1S4_1Agent()
            results = form1s4_1_agent.process_batch()
            return len([r for r in results if r.get("status") == "success"]) > 0
        except Exception as e:
            self.results["errors"].append(f"Form1S4.1 page {page_number} error: {str(e)}")
            return False

    def process_page_with_form1s5(self, page_number):
        """Process single page with Form1S5 agent"""
        try:
            form1s5_agent = Form1S5Agent()
            # Look for gridlines file for this page
            gridlines_pattern = f"{self.output_dir}/table_detection/grid/*_page{page_number}_gridlines.png"
            gridlines_files = glob.glob(gridlines_pattern)

            if not gridlines_files:
                return False

            result = form1s5_agent.process_image(gridlines_files[0], self.output_dir)
            return result.get("status") == "success"
        except Exception as e:
            self.results["errors"].append(f"Form1S5 page {page_number} error: {str(e)}")
            return False

    def print_summary(self):
        """Print final summary of the pipeline execution"""
        self.print_section("PIPELINE SUMMARY")

        # Calculate execution time
        if self.start_time:
            execution_time = datetime.now() - self.start_time
            print(f"Total execution time: {execution_time.total_seconds():.2f} seconds")
            print()

        # Cleaning summary
        if self.results["cleaning"]:
            if self.results["cleaning"].get("status") == "skipped":
                print("[CLEAN] Output Cleaning: SKIPPED")
            elif self.results["cleaning"].get("status") == "already_clean":
                print("[CLEAN] Output Cleaning: Already Clean")
            elif self.results["cleaning"].get("status") == "success":
                stats = self.results["cleaning"].get("statistics", {})
                print(f"[CLEAN] Output Cleaning: {stats.get('files_deleted', 0)} files deleted")

        # Format 1 processing summary
        if self.results["form1s1"]:
            form1_result = self.results["form1s1"]
            if form1_result.get("status") == "no_files":
                print("[FORMAT1] Processing: No PDF files found")
            elif form1_result.get("status") in ["completed", "completed_with_errors"]:
                summary = form1_result.get("summary", {})
                for step_name, step_info in summary.get("steps_summary", {}).items():
                    print(f"[FORMAT1] {step_name}: {step_info.get('success_count', 0)}/{step_info.get('files_processed', 0)} files processed")

        # Form1S2 processing summary
        if self.results["form1s2"]:
            form1s2_result = self.results["form1s2"]
            if form1s2_result.get("status") == "no_files":
                print("[FORM1S2] Table Detection: No page1.png files found")
            elif form1s2_result.get("status") in ["completed", "completed_with_errors"]:
                print(f"[FORM1S2] Table Detection: {form1s2_result.get('successful_files', 0)}/{form1s2_result.get('total_files', 0)} files processed")

        # Form1S3 processing summary
        if self.results["form1s3"]:
            form1s3_result = self.results["form1s3"]
            if form1s3_result.get("status") == "no_files":
                print("[FORM1S3] Grid Line Detection: No ordertable.png found")
            elif form1s3_result.get("status") in ["completed", "completed_with_errors"]:
                result_data = form1s3_result.get("result", {})
                grid_lines = result_data.get("grid_lines", {})
                horizontal_count = grid_lines.get("horizontal_count", 0)
                vertical_count = grid_lines.get("vertical_count", 0)
                print(f"[FORM1S3] Grid Line Detection: {horizontal_count} horizontal, {vertical_count} vertical lines detected")

        # Form1S3.1 processing summary
        if self.results["form1s3_1"]:
            form1s3_1_result = self.results["form1s3_1"]
            if form1s3_1_result.get("status") == "no_files":
                print("[FORM1S3.1] Table Body Extraction: No ordertable_gridlines.png found")
            elif form1s3_1_result.get("status") == "success":
                table_dims = form1s3_1_result.get("table_dimensions", {})
                width = table_dims.get("width", 0)
                height = table_dims.get("height", 0)
                print(f"[FORM1S3.1] Table Body Extraction: {width}x{height} px table body extracted")

        # Form1S3.2 processing summary
        if self.results["form1s3_2"]:
            form1s3_2_result = self.results["form1s3_2"]
            if form1s3_2_result.get("status") == "no_files":
                print("[FORM1S3.2] Order Line Counting: No table_body.png found")
            elif form1s3_2_result.get("status") == "success":
                row_count = form1s3_2_result.get("row_count", 0)
                coords_count = len(form1s3_2_result.get("row_coordinates", []))
                if coords_count > 0:
                    print(f"[FORM1S3.2] Order Line Counting: {row_count} order lines detected by ChatGPT, {coords_count} Y coordinates extracted")
                else:
                    print(f"[FORM1S3.2] Order Line Counting: {row_count} order lines detected by ChatGPT")

        # Form1S3.3 processing summary
        if self.results.get("form1s3_3"):
            form1s3_3_result = self.results["form1s3_3"]
            if form1s3_3_result.get("status") == "no_files":
                print("[FORM1S3.3] Table Header Extraction: No gridlines files found")
            elif form1s3_3_result.get("status") == "success":
                successful = form1s3_3_result.get("successful", 0)
                # Get first successful result for dimensions
                results = form1s3_3_result.get("results", [])
                if results:
                    first_success = next((r for r in results if r.get('status') == 'success'), None)
                    if first_success:
                        width = first_success.get("header_width", 0)
                        height = first_success.get("header_height", 0)
                        print(f"[FORM1S3.3] Table Header Extraction: {width}x{height} px header extracted")
                    else:
                        print(f"[FORM1S3.3] Table Header Extraction: {successful} header(s) extracted")
                else:
                    print(f"[FORM1S3.3] Table Header Extraction: {successful} header(s) extracted")
            elif form1s3_3_result.get("status") == "no_success":
                print("[FORM1S3.3] Table Header Extraction: No files successfully processed")

        # Form1S4 processing summary
        if self.results["form1s4"]:
            form1s4_result = self.results["form1s4"]
            if form1s4_result.get("status") == "no_files":
                print("[FORM1S4] Drawing Cell Extraction: No ordertable_gridlines.png found")
            elif form1s4_result.get("status") in ["completed", "completed_with_errors"]:
                result_data = form1s4_result.get("result", {})
                extraction_results = result_data.get("extraction_results", {})
                total_cells = extraction_results.get("total_cells_extracted", 0)
                print(f"[FORM1S4] Drawing Cell Extraction: {total_cells} drawing cells extracted")

        # Form1S4.1 processing summary
        if self.results.get("form1s4_1"):
            form1s4_1_result = self.results["form1s4_1"]
            if form1s4_1_result.get("status") == "no_files":
                print("[FORM1S4.1] Full Drawing Column Extraction: No gridlines files found")
            elif form1s4_1_result.get("status") == "success":
                successful_files = form1s4_1_result.get("successful_files", 0)
                column_dimensions = form1s4_1_result.get("column_dimensions", [])
                if column_dimensions:
                    width, height = column_dimensions[0]
                    print(f"[FORM1S4.1] Full Drawing Column Extraction: {width}x{height} px column extracted")
                else:
                    print(f"[FORM1S4.1] Full Drawing Column Extraction: {successful_files} column(s) extracted")
            elif form1s4_1_result.get("status") == "no_success":
                print("[FORM1S4.1] Full Drawing Column Extraction: No files successfully processed")

        # Form1S5 processing summary
        if self.results["form1s5"]:
            form1s5_result = self.results["form1s5"]
            if form1s5_result.get("status") == "no_files":
                print("[FORM1S5] Order Title Extraction: No ordertable_gridlines.png found")
            elif form1s5_result.get("status") in ["completed", "completed_with_errors"]:
                result_data = form1s5_result.get("result", {})
                title_extraction = result_data.get("title_extraction", {})
                title_dimensions = title_extraction.get("title_dimensions", {})
                width = title_dimensions.get("width", 0)
                height = title_dimensions.get("height", 0)
                print(f"[FORM1S5] Order Title Extraction: {width}x{height} px title extracted")

        # Error summary
        if self.results["errors"]:
            print()
            print("[WARNING] Errors encountered:")
            for error in self.results["errors"]:
                print(f"  - {error}")

        # Success status
        print()
        if not self.results["errors"]:
            print("[SUCCESS] PIPELINE COMPLETED SUCCESSFULLY")
        else:
            print("[WARNING] PIPELINE COMPLETED WITH ERRORS")

    def process_with_form1ocr1(self):
        """Process order header with Form1OCR1 agent (page 1 only)"""
        self.print_section("STEP 4: ORDER HEADER OCR PROCESSING")

        try:
            # Check if order header image from page 1 exists
            order_header_dir = os.path.join(self.output_dir, "table_detection", "order_header")

            if not os.path.exists(order_header_dir):
                print("[FORM1OCR1] [ERROR] Order header directory not found")
                self.results["form1ocr1"] = {"status": "failed", "error": "order_header directory not found"}
                return False

            # Look for page 1 order header image
            page1_header_files = glob.glob(os.path.join(order_header_dir, "*_page1_order_header.png"))
            if not page1_header_files:
                # Try alternative naming patterns
                page1_header_files = glob.glob(os.path.join(order_header_dir, "*_order_title_page1_order_header.png"))

            if not page1_header_files:
                print("[FORM1OCR1] [ERROR] No page 1 order header image found")
                self.results["form1ocr1"] = {"status": "failed", "error": "no page 1 order header image found"}
                return False

            page1_header_file = page1_header_files[0]
            print(f"[FORM1OCR1] Found page 1 order header: {os.path.basename(page1_header_file)}")

            # Initialize and run Form1OCR1 agent
            print("[FORM1OCR1] Starting OCR processing with ChatGPT...")
            form1ocr1_agent = Form1OCR1Agent()

            # Process the order header
            result = form1ocr1_agent.process()

            if result['success']:
                field_count = result['agent_result']['field_count']
                print(f"[FORM1OCR1] [SUCCESS] Extracted {field_count} fields from order header")
                print(f"[FORM1OCR1] OCR output: {result['agent_result']['output_file']}")
                print(f"[FORM1OCR1] Website analysis file: {result['agent_result']['analysis_file']}")

                self.results["form1ocr1"] = {
                    "status": "success",
                    "fields_extracted": field_count,
                    "output_file": result['agent_result']['output_file'],
                    "analysis_file": result['agent_result']['analysis_file']
                }
                return True
            else:
                error_msg = result.get('error', 'Unknown OCR error')
                print(f"[FORM1OCR1] [ERROR] {error_msg}")
                self.results["form1ocr1"] = {"status": "failed", "error": error_msg}
                return False

        except Exception as e:
            error_msg = f"Failed during Form1OCR1 processing: {str(e)}"
            print(f"[FORM1OCR1] [ERROR] {error_msg}")
            self.results["form1ocr1"] = {"status": "failed", "error": error_msg}
            self.results["errors"].append(error_msg)
            return False

    def process_with_form1ocr2(self):
        """Process table bodies with Form1OCR2 agent for table OCR extraction"""
        self.print_section("STEP 7: TABLE OCR PROCESSING (FORM1OCR2)")

        try:
            # Initialize Form1OCR2 agent
            form1ocr2_agent = Form1OCR2Agent()
            print(f"[FORM1OCR2] Agent initialized: {form1ocr2_agent.short_name}")

            # Look for table_bodyonly files from form1s3.1 output
            table_bodyonly_files = glob.glob(f"{self.output_dir}/table_detection/table/*_table_bodyonly_page*.png")

            if not table_bodyonly_files:
                print(f"[FORM1OCR2] No table_bodyonly files found at {self.output_dir}/table_detection/table/")
                self.results["form1ocr2"] = {"status": "no_files"}
                return True

            print(f"[FORM1OCR2] Found {len(table_bodyonly_files)} table_bodyonly files to process")

            # Process each table_bodyonly file
            processed_files = []
            successful_files = 0
            failed_files = 0

            for table_file in table_bodyonly_files:
                file_name = os.path.basename(table_file)
                print(f"[FORM1OCR2] Processing: {file_name}")

                try:
                    # Extract order number and page number from filename
                    import re
                    match = re.search(r'(.+)_table_bodyonly_page(\d+)\.png$', file_name)
                    if not match:
                        print(f"[FORM1OCR2] [ERROR] {file_name}: Could not extract order/page info")
                        failed_files += 1
                        continue

                    order_number = match.group(1)
                    page_number = match.group(2)

                    # Process with Form1OCR2 agent
                    result = form1ocr2_agent.process_page(order_number, page_number)

                    if result and result.get("status") == "success":
                        print(f"[FORM1OCR2] [SUCCESS] {file_name}")
                        print(f"[FORM1OCR2]   OCR output: {result.get('output_file', 'N/A')}")
                        successful_files += 1
                    else:
                        error_msg = result.get("error", "Unknown error") if result else "No result returned"
                        print(f"[FORM1OCR2] [ERROR] {file_name}: {error_msg}")
                        failed_files += 1

                    processed_files.append({
                        "file": file_name,
                        "order_number": order_number,
                        "page_number": page_number,
                        "status": result.get("status", "error") if result else "error",
                        "output_file": result.get("output_file") if result else None,
                        "error": result.get("error") if result else "No result returned"
                    })

                except Exception as e:
                    error_msg = f"Failed to process {file_name}: {str(e)}"
                    print(f"[FORM1OCR2] [ERROR] {error_msg}")
                    processed_files.append({
                        "file": file_name,
                        "status": "error",
                        "error": error_msg
                    })
                    failed_files += 1
                    self.results["errors"].append(error_msg)

            # Store results
            self.results["form1ocr2"] = {
                "status": "completed" if failed_files == 0 else "completed_with_errors",
                "total_files": len(table_bodyonly_files),
                "successful_files": successful_files,
                "failed_files": failed_files,
                "processed_files": processed_files
            }

            print()
            print(f"[FORM1OCR2] Processing summary:")
            print(f"[FORM1OCR2]   Total files: {len(table_bodyonly_files)}")
            print(f"[FORM1OCR2]   Successful: {successful_files}")
            print(f"[FORM1OCR2]   Failed: {failed_files}")

            return failed_files == 0

        except Exception as e:
            error_msg = f"Failed during Form1OCR2 processing: {str(e)}"
            print(f"[FORM1OCR2] [ERROR] {error_msg}")
            self.results["errors"].append(error_msg)
            return False

    def process_with_form1dat1(self):
        """Process with Form1Dat1 agent for comprehensive data analysis"""
        self.print_section("STEP 8: COMPREHENSIVE DATA ANALYSIS (FORM1DAT1)")

        try:
            # Initialize Form1Dat1 agent
            form1dat1_agent = Form1Dat1Agent()
            print(f"[FORM1DAT1] Agent initialized: {form1dat1_agent.name}")

            # Look for order output files from previous processing
            json_output_files = glob.glob(f"{self.output_dir}/json_output/*_out.json")

            if not json_output_files:
                print(f"[FORM1DAT1] No JSON output files found at {self.output_dir}/json_output/")
                self.results["form1dat1"] = {"status": "no_files"}
                return True

            print(f"[FORM1DAT1] Found {len(json_output_files)} JSON output files to process")

            # Process each JSON file (representing an order)
            processed_orders = []
            successful_orders = 0
            failed_orders = 0

            for json_file in json_output_files:
                file_name = os.path.basename(json_file)
                print(f"[FORM1DAT1] Processing: {file_name}")

                try:
                    # Extract order number from filename
                    order_number = file_name.replace("_out.json", "")

                    # Process with Form1Dat1 agent
                    result = form1dat1_agent.process_order(order_number)

                    if result and result.get("status") == "success":
                        print(f"[FORM1DAT1] [SUCCESS] {file_name}")
                        print(f"[FORM1DAT1]   Analysis output: {result.get('output_file', 'N/A')}")
                        successful_orders += 1
                    else:
                        error_msg = result.get("error", "Unknown error") if result else "No result returned"
                        print(f"[FORM1DAT1] [ERROR] {file_name}: {error_msg}")
                        failed_orders += 1

                    processed_orders.append({
                        "file": file_name,
                        "order_number": order_number,
                        "status": result.get("status", "error") if result else "error",
                        "output_file": result.get("output_file") if result else None,
                        "error": result.get("error") if result else "No result returned"
                    })

                except Exception as e:
                    error_msg = f"Failed to process {file_name}: {str(e)}"
                    print(f"[FORM1DAT1] [ERROR] {error_msg}")
                    processed_orders.append({
                        "file": file_name,
                        "status": "error",
                        "error": error_msg
                    })
                    failed_orders += 1
                    self.results["errors"].append(error_msg)

            # Store results
            self.results["form1dat1"] = {
                "status": "completed" if failed_orders == 0 else "completed_with_errors",
                "total_orders": len(json_output_files),
                "successful_orders": successful_orders,
                "failed_orders": failed_orders,
                "processed_orders": processed_orders
            }

            print()
            print(f"[FORM1DAT1] Processing summary:")
            print(f"[FORM1DAT1]   Total orders: {len(json_output_files)}")
            print(f"[FORM1DAT1]   Successful: {successful_orders}")
            print(f"[FORM1DAT1]   Failed: {failed_orders}")

            return failed_orders == 0

        except Exception as e:
            error_msg = f"Failed during Form1Dat1 processing: {str(e)}"
            print(f"[FORM1DAT1] [ERROR] {error_msg}")
            self.results["errors"].append(error_msg)
            return False

    def run(self, skip_cleaning=False):
        """Run the complete table detection pipeline"""
        self.start_time = datetime.now()
        self.print_header()

        print(f"Starting at: {self.start_time.strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"Input directory: {self.input_dir}")
        print(f"Output directory: {self.output_dir}")

        # Create necessary directories
        os.makedirs(self.input_dir, exist_ok=True)
        os.makedirs(self.output_dir, exist_ok=True)
        os.makedirs("io/log", exist_ok=True)

        # Step 1: Clean output directory (disabled - skip cleaning to preserve existing files)
        cleaning_success = self.clean_output_directory(skip_cleaning=True)

        if not cleaning_success and not skip_cleaning:
            print()
            print("[WARNING] Cleaning failed, but continuing with processing...")

        # Step 2: Process with Format 1 Main agent (form1s1 - extracts all pages)
        format1_success = self.process_with_format1()

        if not format1_success:
            print()
            print("[ERROR] Failed to extract pages from PDF - stopping pipeline")
            self.print_summary()
            return False

        # Step 3: Process all pages from order_to_image folder
        self.process_all_pages()

        # Step 4: Run OCR on order header (page 1 only) after all table processing is complete
        ocr_success = self.process_with_form1ocr1()

        if ocr_success:
            print()
            print("[SUCCESS] Form1OCR1 order header OCR completed successfully")
        else:
            print()
            print("[WARNING] Form1OCR1 order header OCR failed, but continuing...")

        # Step 5: Run Form1OCR2 for table OCR processing on all table_bodyonly files
        ocr2_success = self.process_with_form1ocr2()

        if ocr2_success:
            print()
            print("[SUCCESS] Form1OCR2 table OCR processing completed successfully")
        else:
            print()
            print("[WARNING] Form1OCR2 table OCR processing failed, but continuing...")

        # Step 6: Run Form1Dat1 for comprehensive data analysis
        dat1_success = self.process_with_form1dat1()

        if dat1_success:
            print()
            print("[SUCCESS] Form1Dat1 comprehensive data analysis completed successfully")
        else:
            print()
            print("[WARNING] Form1Dat1 comprehensive data analysis failed, but continuing...")

        # Print summary
        self.print_summary()

        return len(self.results["errors"]) == 0

def main():
    """Main entry point"""
    import argparse

    parser = argparse.ArgumentParser(
        description="Table Detection Pipeline for Bent Iron Orders"
    )
    parser.add_argument(
        "--skip-clean",
        action="store_true",
        help="Skip the output cleaning step"
    )
    parser.add_argument(
        "--input-dir",
        type=str,
        help="Override the default input directory"
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        help="Override the default output directory"
    )

    args = parser.parse_args()

    # Create pipeline
    pipeline = TableDetectionPipeline()

    # Override directories if specified
    if args.input_dir:
        pipeline.input_dir = args.input_dir
    if args.output_dir:
        pipeline.output_dir = args.output_dir

    # Run pipeline
    try:
        success = pipeline.run(skip_cleaning=args.skip_clean)
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\n[INTERRUPTED] Pipeline interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n[FATAL ERROR] {str(e)}")
        logger.exception("Fatal error in pipeline")
        sys.exit(1)

if __name__ == "__main__":
    main()
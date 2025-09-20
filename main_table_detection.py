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
from agents.llm_agents.output_cleaner import OutputCleanerAgent
from agents.llm_agents.format1_agent import OrderFormat1MainAgent
from agents.llm_agents.format1_agent.form1s2 import Form1S2Agent
from agents.llm_agents.format1_agent.form1s3 import Form1S3Agent
from agents.llm_agents.format1_agent.form1s3_1 import Form1S31Agent
from agents.llm_agents.format1_agent.form1s3_2 import Form1S32Agent
from agents.llm_agents.format1_agent.form1s4 import Form1S4Agent
from agents.llm_agents.format1_agent.form1s5 import Form1S5Agent

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

            # Look for table_body.png from form1s3.1 output with page number
            table_body_files = glob.glob(f"{self.output_dir}/table_detection/table/*_table_body_page1.png")

            if not table_body_files:
                print(f"[FORM1S3.2] table_body.png not found at {self.output_dir}/table_detection/table/*_table_body_page1.png")
                self.results["form1s3_2"] = {"status": "no_files"}
                return True

            table_body_path = table_body_files[0]  # Use first matching file

            print(f"[FORM1S3.2] Found table_body.png, processing order line counting")

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

    def process_with_form1s4(self):
        """Step 5: Process ordertable_gridlines.png with Form1S4 agent for drawing cell extraction"""
        self.print_section("STEP 5: DRAWING CELL EXTRACTION (FORM1S4)")

        try:
            # Initialize Form1S4 agent
            form1s4_agent = Form1S4Agent()
            print(f"[FORM1S4] Agent initialized: {form1s4_agent.name}")

            # Look for ordertable_gridlines.png from form1s3 output in grid folder with page number
            gridlines_files = glob.glob(f"{self.output_dir}/table_detection/grid/*_ordertable_page1_gridlines.png")

            if not gridlines_files:
                print(f"[FORM1S4] ordertable_gridlines.png not found at {self.output_dir}/table_detection/grid/*_ordertable_page1_gridlines.png")
                self.results["form1s4"] = {"status": "no_files"}
                return True

            gridlines_path = gridlines_files[0]  # Use first matching file

            print(f"[FORM1S4] Found ordertable_gridlines.png, processing drawing cell extraction")

            try:
                result = form1s4_agent.process_image(gridlines_path)

                if result["status"] == "success":
                    extraction_results = result.get("extraction_results", {})
                    total_cells = extraction_results.get("total_cells_extracted", 0)

                    print(f"[FORM1S4] [SUCCESS] Drawing cell extraction completed")
                    print(f"[FORM1S4]   Cells extracted: {total_cells}")
                    print(f"[FORM1S4]   Output directory: {extraction_results.get('output_directory', 'N/A')}")

                    if extraction_results.get("saved_files"):
                        print(f"[FORM1S4]   Files saved:")
                        for file_path in extraction_results["saved_files"]:
                            file_name = os.path.basename(file_path)
                            print(f"[FORM1S4]     - {file_name}")

                    # Store results
                    self.results["form1s4"] = {
                        "status": "completed",
                        "total_files": 1,
                        "successful_files": 1,
                        "failed_files": 0,
                        "result": result
                    }
                    return True
                else:
                    error_msg = result.get("error", "Unknown error")
                    print(f"[FORM1S4] [ERROR] {error_msg}")

                    self.results["form1s4"] = {
                        "status": "completed_with_errors",
                        "total_files": 1,
                        "successful_files": 0,
                        "failed_files": 1,
                        "error": error_msg
                    }
                    self.results["errors"].append(f"Form1S4 error: {error_msg}")
                    return False

            except Exception as e:
                error_msg = f"Failed to process ordertable_gridlines.png: {str(e)}"
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

        except Exception as e:
            error_msg = f"Failed during Form1S4 processing: {str(e)}"
            print(f"[FORM1S4] [ERROR] {error_msg}")
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

        # Step 1: Clean output directory
        cleaning_success = self.clean_output_directory(skip_cleaning)

        if not cleaning_success and not skip_cleaning:
            print()
            print("[WARNING] Cleaning failed, but continuing with processing...")

        # Step 2: Process with Format 1 Main agent
        format1_success = self.process_with_format1()

        # Step 3: Process with Form1S2 agent for table detection
        form1s2_success = True
        if format1_success:
            form1s2_success = self.process_with_form1s2()
        else:
            print()
            print("[WARNING] Skipping Form1S2 processing due to Format1 failures")

        # Step 4: Process with Form1S3 agent for grid line detection
        form1s3_success = True
        if form1s2_success:
            form1s3_success = self.process_with_form1s3()
        else:
            print()
            print("[WARNING] Skipping Form1S3 processing due to Form1S2 failures")

        # Step 4.1: Process with Form1S3.1 agent for table body extraction
        form1s3_1_success = True
        if form1s3_success:
            form1s3_1_success = self.process_with_form1s3_1()
        else:
            print()
            print("[WARNING] Skipping Form1S3.1 processing due to Form1S3 failures")

        # Step 4.2: Process with Form1S3.2 agent for order line counting
        form1s3_2_success = True
        if form1s3_1_success:
            form1s3_2_success = self.process_with_form1s3_2()
        else:
            print()
            print("[WARNING] Skipping Form1S3.2 processing due to Form1S3.1 failures")

        # Step 5: Process with Form1S4 agent for drawing cell extraction
        form1s4_success = True
        if form1s3_success:
            form1s4_success = self.process_with_form1s4()
        else:
            print()
            print("[WARNING] Skipping Form1S4 processing due to Form1S3 failures")

        # Step 6: Process with Form1S5 agent for order title extraction
        form1s5_success = True
        if form1s3_success:
            form1s5_success = self.process_with_form1s5()
        else:
            print()
            print("[WARNING] Skipping Form1S5 processing due to Form1S3 failures")

        # Future steps can be added here:
        # Step 7: Shape analysis
        # Step 8: Text recognition
        # etc.

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
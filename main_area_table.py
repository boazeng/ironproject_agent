#!/usr/bin/env python3
"""
Main Area Table Detection Pipeline
Processes a single specific page through the table detection workflow for bent iron order documents

Workflow:
1. Takes page number as input parameter
2. Processes only the specified page through form1s2-5 agents
3. Skips cleaning and PDF extraction (assumes pages already exist)
"""

import os
import sys
import glob
import logging
from datetime import datetime
from pathlib import Path

# Import agents
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
        logging.FileHandler('io/log/area_table_log.txt', encoding='utf-8')
    ]
)

logger = logging.getLogger(__name__)

class AreaTableDetectionPipeline:
    """Pipeline for processing a single page through table detection workflow"""

    def __init__(self, page_number, process_mode="full"):
        self.page_number = page_number
        self.process_mode = process_mode
        self.input_dir = "io/input"
        self.output_dir = "io/fullorder_output"
        self.start_time = None
        self.order_name = None
        self.results = {
            "copy_operation": None,
            "form1s2": None,
            "form1s3": None,
            "form1s3_1": None,
            "form1s3_2": None,
            "form1s3_3": None,
            "form1s4_1": None,
            "form1s4": None,
            "form1s5": None,
            "form1ocr2": None,
            "form1dat1": None,
            "errors": []
        }

        # Define available process modes
        self.process_modes = {
            "full": "Complete pipeline: Form1S2->S3->S3.1->S3.2->S3.3->S4.1->S4->S5->OCR2->Dat1",
            "copy_replace": "Copy user area to replace table_bodyonly and run dependent processes",
            "update_table": "Update table area: S3.2->S4.1->S4->OCR2->Dat1",
            "shapes_only": "Extract shapes only: S4.1->S4",
            "ocr_only": "OCR processing only: OCR2->Dat1"
        }

    def print_header(self):
        """Print the application header"""
        print("=" * 70)
        print(" " * 10 + f"AREA TABLE DETECTION PIPELINE - PAGE {self.page_number}")
        print(" " * 10 + f"Process Mode: {self.process_mode.upper()}")
        print("=" * 70)
        print()

    def print_section(self, title):
        """Print a section header"""
        print()
        print("-" * 70)
        print(f"[{datetime.now().strftime('%H:%M:%S')}] {title}")
        print("-" * 70)

    def _detect_order_name(self):
        """Detect order name from existing files"""
        # Try user_saved_area first
        pattern = f"{self.output_dir}/user_saved_area/*_table_area_page{self.page_number}.png"
        files = glob.glob(pattern)

        if files:
            filename = os.path.basename(files[0])
            import re
            match = re.search(r'([A-Z0-9]+)_table_area_page\d+\.png', filename)
            if match:
                return match.group(1)

        # Try order_to_image directory
        pattern = f"{self.output_dir}/order_to_image/*_page{self.page_number}.png"
        files = glob.glob(pattern)

        if files:
            filename = os.path.basename(files[0])
            import re
            match = re.search(r'([A-Z0-9]+)_page\d+\.png', filename)
            if match:
                return match.group(1)

        return None

    def _copy_user_area_to_table_bodyonly(self):
        """Copy user-selected table area to replace table_bodyonly file"""
        self.print_section(f"STEP 1: COPY USER-SELECTED AREA - PAGE {self.page_number}")

        try:
            import shutil

            # Source: user-selected area
            source_file = f"{self.output_dir}/user_saved_area/{self.order_name}_table_area_page{self.page_number}.png"

            # Target: table_bodyonly file
            target_file = f"{self.output_dir}/table_detection/table/{self.order_name}_table_bodyonly_page{self.page_number}.png"

            if not os.path.exists(source_file):
                print(f"[ERROR] Source file not found: {source_file}")
                return False

            # Create target directory if needed
            os.makedirs(os.path.dirname(target_file), exist_ok=True)

            # Backup existing file
            if os.path.exists(target_file):
                backup_file = f"{target_file}.backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
                shutil.copy2(target_file, backup_file)
                print(f"[INFO] Backed up existing file: {os.path.basename(backup_file)}")

            # Copy user-selected area to replace table_bodyonly
            shutil.copy2(source_file, target_file)
            print(f"[SUCCESS] Copied user area to table_bodyonly")
            print(f"         Source: {os.path.basename(source_file)}")
            print(f"         Target: {os.path.basename(target_file)}")

            self.results["copy_operation"] = {"status": "success"}
            return True

        except Exception as e:
            error_msg = f"Error copying user area: {str(e)}"
            print(f"[ERROR] {error_msg}")
            self.results["errors"].append(error_msg)
            self.results["copy_operation"] = {"status": "error", "error": str(e)}
            return False

    def process_page_with_form1s2(self, page_file):
        """Process page with Form1S2 agent for table detection"""
        try:
            form1s2_agent = Form1S2Agent()

            # Set output directory
            output_dir = f"{self.output_dir}/table_detection/grid"
            os.makedirs(output_dir, exist_ok=True)

            # Process the page
            result = form1s2_agent.process_image(page_file)

            if result["status"] == "success":
                print(f"[FORM1S2] [SUCCESS] Table detection completed for page {self.page_number}")
                return True
            else:
                error_msg = f"Failed to process page {self.page_number} with Form1S2: {result.get('error', 'Unknown error')}"
                print(f"[FORM1S2] [ERROR] {error_msg}")
                self.results["errors"].append(error_msg)
                return False

        except Exception as e:
            error_msg = f"Exception in Form1S2 for page {self.page_number}: {str(e)}"
            print(f"[FORM1S2] [ERROR] {error_msg}")
            self.results["errors"].append(error_msg)
            return False

    def process_page_with_form1s3(self, page_number):
        """Process page with Form1S3 agent for grid line detection"""
        try:
            form1s3_agent = Form1S3Agent()

            # Look for ordertable file for this page from form1s2 output
            ordertable_pattern = f"{self.output_dir}/table_detection/grid/*_ordertable_page{page_number}.png"
            ordertable_files = glob.glob(ordertable_pattern)

            if not ordertable_files:
                print(f"[FORM1S3] ordertable file not found for page {page_number}")
                return False

            ordertable_path = ordertable_files[0]
            output_dir = f"{self.output_dir}/table_detection/grid"

            # Process with Form1S3
            result = form1s3_agent.process_image(ordertable_path)

            if result["status"] == "success":
                print(f"[FORM1S3] [SUCCESS] Grid line detection completed for page {page_number}")
                return True
            else:
                error_msg = f"Failed to process page {page_number} with Form1S3: {result.get('error', 'Unknown error')}"
                print(f"[FORM1S3] [ERROR] {error_msg}")
                self.results["errors"].append(error_msg)
                return False

        except Exception as e:
            error_msg = f"Exception in Form1S3 for page {page_number}: {str(e)}"
            print(f"[FORM1S3] [ERROR] {error_msg}")
            self.results["errors"].append(error_msg)
            return False

    def process_page_with_form1s3_1(self, page_number):
        """Process page with Form1S3.1 agent for table body extraction"""
        try:
            form1s3_1_agent = Form1S31Agent()

            # Look for gridlines file for this page
            gridlines_pattern = f"{self.output_dir}/table_detection/grid/*_ordertable_page{page_number}_gridlines.png"
            gridlines_files = glob.glob(gridlines_pattern)

            if not gridlines_files:
                print(f"[FORM1S3.1] gridlines file not found for page {page_number}")
                return False

            output_dir = f"{self.output_dir}/table_detection/table"
            result = form1s3_1_agent.process_file(gridlines_files[0], output_dir)

            if result["status"] == "success":
                print(f"[FORM1S3.1] [SUCCESS] Table body extraction completed for page {page_number}")
                return True
            else:
                error_msg = f"Failed to process page {page_number} with Form1S3.1: {result.get('error', 'Unknown error')}"
                print(f"[FORM1S3.1] [ERROR] {error_msg}")
                self.results["errors"].append(error_msg)
                return False

        except Exception as e:
            error_msg = f"Exception in Form1S3.1 for page {page_number}: {str(e)}"
            print(f"[FORM1S3.1] [ERROR] {error_msg}")
            self.results["errors"].append(error_msg)
            return False

    def process_page_with_form1s3_2(self, page_number):
        """Process page with Form1S3.2 agent for table row analysis"""
        try:
            form1s3_2_agent = Form1S32Agent("form1s3_2")

            # Look for table_bodyonly file for this page
            bodyonly_pattern = f"{self.output_dir}/table_detection/table/*_table_bodyonly_page{page_number}.png"
            bodyonly_files = glob.glob(bodyonly_pattern)

            if not bodyonly_files:
                print(f"[FORM1S3.2] table_bodyonly file not found for page {page_number}")
                return False

            output_dir = f"{self.output_dir}/table_detection/table"
            result = form1s3_2_agent.process_file(bodyonly_files[0], output_dir)

            if result["status"] == "success":
                print(f"[FORM1S3.2] [SUCCESS] Table row analysis completed for page {page_number}")
                return True
            else:
                error_msg = f"Failed to process page {page_number} with Form1S3.2: {result.get('error', 'Unknown error')}"
                print(f"[FORM1S3.2] [ERROR] {error_msg}")
                self.results["errors"].append(error_msg)
                return False

        except Exception as e:
            error_msg = f"Exception in Form1S3.2 for page {page_number}: {str(e)}"
            print(f"[FORM1S3.2] [ERROR] {error_msg}")
            self.results["errors"].append(error_msg)
            return False

    def process_page_with_form1s3_3(self, page_number):
        """Process page with Form1S3.3 agent for table header extraction"""
        try:
            form1s3_3_agent = Form1S3_3Agent()

            # Look for gridlines file for this page
            gridlines_pattern = f"{self.output_dir}/table_detection/grid/*_ordertable_page{page_number}_gridlines.png"
            gridlines_files = glob.glob(gridlines_pattern)

            if not gridlines_files:
                print(f"[FORM1S3.3] gridlines file not found for page {page_number}")
                return False

            output_dir = f"{self.output_dir}/table_detection/table_header"
            result = form1s3_3_agent.process_order(gridlines_files[0])

            if result["status"] == "success":
                print(f"[FORM1S3.3] [SUCCESS] Table header extraction completed for page {page_number}")
                return True
            else:
                error_msg = f"Failed to process page {page_number} with Form1S3.3: {result.get('error', 'Unknown error')}"
                print(f"[FORM1S3.3] [ERROR] {error_msg}")
                self.results["errors"].append(error_msg)
                return False

        except Exception as e:
            error_msg = f"Exception in Form1S3.3 for page {page_number}: {str(e)}"
            print(f"[FORM1S3.3] [ERROR] {error_msg}")
            self.results["errors"].append(error_msg)
            return False

    def process_page_with_form1s4_1(self, page_number):
        """Process page with Form1S4.1 agent for full drawing column extraction"""
        try:
            form1s4_1_agent = Form1S4_1Agent()

            # Look for table_bodyonly file for this page
            bodyonly_pattern = f"{self.output_dir}/table_detection/table/*_table_bodyonly_page{page_number}.png"
            bodyonly_files = glob.glob(bodyonly_pattern)

            if not bodyonly_files:
                print(f"[FORM1S4.1] table_bodyonly file not found for page {page_number}")
                return False

            output_dir = f"{self.output_dir}/table_detection/shape_column"
            result = form1s4_1_agent.process_order(bodyonly_files[0])

            if result["status"] == "success":
                print(f"[FORM1S4.1] [SUCCESS] Full drawing column extraction completed for page {page_number}")
                return True
            else:
                error_msg = f"Failed to process page {page_number} with Form1S4.1: {result.get('error', 'Unknown error')}"
                print(f"[FORM1S4.1] [ERROR] {error_msg}")
                self.results["errors"].append(error_msg)
                return False

        except Exception as e:
            error_msg = f"Exception in Form1S4.1 for page {page_number}: {str(e)}"
            print(f"[FORM1S4.1] [ERROR] {error_msg}")
            self.results["errors"].append(error_msg)
            return False

    def process_page_with_form1s4(self, page_number):
        """Process page with Form1S4 agent for individual shape extraction"""
        try:
            form1s4_agent = Form1S4Agent()

            # Look for shape_column file for this page (created by Form1S4_1)
            shape_column_pattern = f"{self.output_dir}/table_detection/shape_column/*_shape_column_page{page_number}.png"
            shape_column_files = glob.glob(shape_column_pattern)

            if not shape_column_files:
                print(f"[FORM1S4] shape_column file not found for page {page_number}")
                return False

            output_dir = f"{self.output_dir}/table_detection/shapes"
            result = form1s4_agent.process_image(shape_column_files[0])

            if result["status"] == "success":
                print(f"[FORM1S4] [SUCCESS] Individual shape extraction completed for page {page_number}")
                return True
            else:
                error_msg = f"Failed to process page {page_number} with Form1S4: {result.get('error', 'Unknown error')}"
                print(f"[FORM1S4] [ERROR] {error_msg}")
                self.results["errors"].append(error_msg)
                return False

        except Exception as e:
            error_msg = f"Exception in Form1S4 for page {page_number}: {str(e)}"
            print(f"[FORM1S4] [ERROR] {error_msg}")
            self.results["errors"].append(error_msg)
            return False

    def process_page_with_form1s5(self, page_number):
        """Process page with Form1S5 agent for order title extraction"""
        try:
            form1s5_agent = Form1S5Agent()

            # Look for gridlines file for this page
            gridlines_pattern = f"{self.output_dir}/table_detection/grid/*_page{page_number}_gridlines.png"
            gridlines_files = glob.glob(gridlines_pattern)

            if not gridlines_files:
                print(f"[FORM1S5] gridlines file not found for page {page_number}")
                return False

            result = form1s5_agent.process_image(gridlines_files[0], self.output_dir)

            if result["status"] == "success":
                print(f"[FORM1S5] [SUCCESS] Order title extraction completed for page {page_number}")
                return True
            else:
                error_msg = f"Failed to process page {page_number} with Form1S5: {result.get('error', 'Unknown error')}"
                print(f"[FORM1S5] [ERROR] {error_msg}")
                self.results["errors"].append(error_msg)
                return False

        except Exception as e:
            error_msg = f"Exception in Form1S5 for page {page_number}: {str(e)}"
            print(f"[FORM1S5] [ERROR] {error_msg}")
            self.results["errors"].append(error_msg)
            return False

    def process_page_with_form1ocr2(self, page_number):
        """Process page with Form1OCR2 agent for table OCR"""
        try:
            form1ocr2_agent = Form1OCR2Agent()

            # Look for table_bodyonly file for this page
            bodyonly_pattern = f"{self.output_dir}/table_detection/table/*_table_bodyonly_page{page_number}.png"
            bodyonly_files = glob.glob(bodyonly_pattern)

            if not bodyonly_files:
                print(f"[FORM1OCR2] table_bodyonly file not found for page {page_number}")
                return False

            # Extract order name from bodyonly file path
            import re
            match = re.search(r'([A-Z0-9]+)_table_bodyonly_page\d+\.png', bodyonly_files[0])
            order_name = match.group(1) if match else 'Unknown'
            result = form1ocr2_agent.process_page(order_name, self.page_number)

            if result["status"] == "success":
                print(f"[FORM1OCR2] [SUCCESS] Table OCR completed for page {page_number}")
                return True
            else:
                error_msg = f"Failed to process page {page_number} with Form1OCR2: {result.get('error', 'Unknown error')}"
                print(f"[FORM1OCR2] [ERROR] {error_msg}")
                self.results["errors"].append(error_msg)
                return False

        except Exception as e:
            error_msg = f"Exception in Form1OCR2 for page {page_number}: {str(e)}"
            print(f"[FORM1OCR2] [ERROR] {error_msg}")
            self.results["errors"].append(error_msg)
            return False

    def process_with_form1dat1(self):
        """Process with Form1Dat1 agent for database integration"""
        try:
            form1dat1_agent = Form1Dat1Agent()

            # Get order number from existing files
            order_files = glob.glob(f"{self.output_dir}/order_to_image/*_page{self.page_number}.png")
            if not order_files:
                print(f"[FORM1DAT1] No order files found for page {self.page_number}")
                return False

            # Extract order number from filename
            filename = os.path.basename(order_files[0])
            order_number = filename.split('_page')[0]

            # Process with Form1Dat1
            result = form1dat1_agent.process_order(order_number)

            if result and result.get("status") == "success":
                print(f"[FORM1DAT1] [SUCCESS] Database integration completed for order {order_number}")
                return True
            else:
                error_msg = f"Failed to process order {order_number} with Form1Dat1"
                print(f"[FORM1DAT1] [ERROR] {error_msg}")
                self.results["errors"].append(error_msg)
                return False

        except Exception as e:
            error_msg = f"Exception in Form1Dat1: {str(e)}"
            print(f"[FORM1DAT1] [ERROR] {error_msg}")
            self.results["errors"].append(error_msg)
            return False

    def run(self):
        """Run the area table detection pipeline for the specified page"""
        self.start_time = datetime.now()
        self.print_header()

        print(f"Starting at: {self.start_time.strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"Processing page: {self.page_number}")
        print(f"Process mode: {self.process_mode}")
        print(f"Description: {self.process_modes.get(self.process_mode, 'Unknown process mode')}")
        print(f"Output directory: {self.output_dir}")

        # Create necessary directories
        os.makedirs("io/log", exist_ok=True)

        # Detect order name
        self.order_name = self._detect_order_name()
        if not self.order_name:
            print(f"[ERROR] Could not detect order name for page {self.page_number}")
            return False

        print(f"Order: {self.order_name}")
        print()

        # Run selected process mode
        if self.process_mode == "full":
            return self._run_full_pipeline()
        elif self.process_mode == "copy_replace":
            return self._run_copy_replace_pipeline()
        elif self.process_mode == "update_table":
            return self._run_update_table_pipeline()
        elif self.process_mode == "shapes_only":
            return self._run_shapes_only_pipeline()
        elif self.process_mode == "ocr_only":
            return self._run_ocr_only_pipeline()
        else:
            print(f"[ERROR] Unknown process mode: {self.process_mode}")
            return False

    def _run_full_pipeline(self):
        """Run the complete pipeline"""
        # Find the page file to process
        order_to_image_dir = os.path.join(self.output_dir, "order_to_image")
        page_files = glob.glob(os.path.join(order_to_image_dir, f"*_page{self.page_number}.png"))

        if not page_files:
            print(f"[ERROR] No page file found for page {self.page_number} in {order_to_image_dir}")
            return False

        page_file = page_files[0]
        print(f"[INFO] Processing file: {os.path.basename(page_file)}")

        # Step 1: Form1S2 - Table Detection
        self.print_section(f"STEP 1: TABLE DETECTION (FORM1S2) - PAGE {self.page_number}")
        if not self.process_page_with_form1s2(page_file):
            print(f"[ERROR] Failed to process page {self.page_number} with Form1S2")
            return False

        # Step 2: Form1S3 - Grid Line Detection
        self.print_section(f"STEP 2: GRID LINE DETECTION (FORM1S3) - PAGE {self.page_number}")
        if not self.process_page_with_form1s3(self.page_number):
            print(f"[ERROR] Failed to process page {self.page_number} with Form1S3")
            return False

        # Step 3: Form1S3.1 - Table Body Extraction
        self.print_section(f"STEP 3: TABLE BODY EXTRACTION (FORM1S3.1) - PAGE {self.page_number}")
        if not self.process_page_with_form1s3_1(self.page_number):
            print(f"[ERROR] Failed to process page {self.page_number} with Form1S3.1")
            return False

        # Step 4: Form1S3.2 - Table Row Analysis
        self.print_section(f"STEP 4: TABLE ROW ANALYSIS (FORM1S3.2) - PAGE {self.page_number}")
        if not self.process_page_with_form1s3_2(self.page_number):
            print(f"[WARNING] Failed to process page {self.page_number} with Form1S3.2, continuing...")

        # Step 5: Form1S3.3 - Table Header Extraction
        self.print_section(f"STEP 5: TABLE HEADER EXTRACTION (FORM1S3.3) - PAGE {self.page_number}")
        if not self.process_page_with_form1s3_3(self.page_number):
            print(f"[WARNING] Failed to process page {self.page_number} with Form1S3.3, continuing...")

        # Step 6: Form1S4.1 - Full Drawing Column Extraction
        self.print_section(f"STEP 6: FULL DRAWING COLUMN EXTRACTION (FORM1S4.1) - PAGE {self.page_number}")
        if not self.process_page_with_form1s4_1(self.page_number):
            print(f"[WARNING] Failed to process page {self.page_number} with Form1S4.1, continuing...")

        # Step 7: Form1S4 - Individual Shape Extraction
        self.print_section(f"STEP 7: INDIVIDUAL SHAPE EXTRACTION (FORM1S4) - PAGE {self.page_number}")
        if not self.process_page_with_form1s4(self.page_number):
            print(f"[WARNING] Failed to process page {self.page_number} with Form1S4, continuing...")

        # Step 8: Form1S5 - Order Title Extraction
        self.print_section(f"STEP 8: ORDER TITLE EXTRACTION (FORM1S5) - PAGE {self.page_number}")
        if not self.process_page_with_form1s5(self.page_number):
            print(f"[WARNING] Failed to process page {self.page_number} with Form1S5, continuing...")

        # Step 9: Form1OCR2 - Table OCR
        self.print_section(f"STEP 9: TABLE OCR (FORM1OCR2) - PAGE {self.page_number}")
        if not self.process_page_with_form1ocr2(self.page_number):
            print(f"[WARNING] Failed to process page {self.page_number} with Form1OCR2, continuing...")

        # Step 10: Form1Dat1 - Database Integration
        self.print_section(f"STEP 10: DATABASE INTEGRATION (FORM1DAT1)")
        if not self.process_with_form1dat1():
            print(f"[WARNING] Failed to process with Form1Dat1, continuing...")

        # Print summary
        self.print_summary()

        return len(self.results["errors"]) == 0

    def _run_copy_replace_pipeline(self):
        """Run copy_replace pipeline: Copy user area to table_bodyonly and run dependent processes"""

        # Step 1: Copy user area to replace table_bodyonly
        if not self._copy_user_area_to_table_bodyonly():
            print(f"[ERROR] Failed to copy user area for page {self.page_number}")
            return False

        # Step 2: Form1S3.2 - Table Row Count Analysis
        self.print_section(f"STEP 2: TABLE ROW COUNT ANALYSIS (FORM1S3.2) - PAGE {self.page_number}")
        if not self.process_page_with_form1s3_2(self.page_number):
            print(f"[ERROR] Failed to process page {self.page_number} with Form1S3.2")
            return False

        # Step 3: Form1S4.1 - Full Drawing Column Extraction
        self.print_section(f"STEP 3: FULL DRAWING COLUMN EXTRACTION (FORM1S4.1) - PAGE {self.page_number}")
        if not self.process_page_with_form1s4_1(self.page_number):
            print(f"[ERROR] Failed to process page {self.page_number} with Form1S4.1")
            return False

        # Step 4: Form1S4 - Individual Shape Extraction
        self.print_section(f"STEP 4: INDIVIDUAL SHAPE EXTRACTION (FORM1S4) - PAGE {self.page_number}")
        if not self.process_page_with_form1s4(self.page_number):
            print(f"[ERROR] Failed to process page {self.page_number} with Form1S4")
            return False

        # Step 5: Form1OCR2 - Table OCR Processing
        self.print_section(f"STEP 5: TABLE OCR PROCESSING (FORM1OCR2) - PAGE {self.page_number}")
        if not self.process_page_with_form1ocr2(self.page_number):
            print(f"[WARNING] Failed to process page {self.page_number} with Form1OCR2, continuing...")

        # Step 6: Form1Dat1 - Database Integration
        self.print_section(f"STEP 6: DATABASE INTEGRATION (FORM1DAT1)")
        if not self.process_with_form1dat1():
            print(f"[WARNING] Failed to process with Form1Dat1, continuing...")

        # Print summary
        self.print_summary()

        return len(self.results["errors"]) == 0

    def _run_update_table_pipeline(self):
        """Run update_table pipeline: S3.2->S4.1->S4->OCR2->Dat1 (assumes table_bodyonly already exists)"""

        # Step 1: Form1S3.2 - Table Row Count Analysis
        self.print_section(f"STEP 1: TABLE ROW COUNT ANALYSIS (FORM1S3.2) - PAGE {self.page_number}")
        if not self.process_page_with_form1s3_2(self.page_number):
            print(f"[ERROR] Failed to process page {self.page_number} with Form1S3.2")
            return False

        # Step 2: Form1S4.1 - Full Drawing Column Extraction
        self.print_section(f"STEP 2: FULL DRAWING COLUMN EXTRACTION (FORM1S4.1) - PAGE {self.page_number}")
        if not self.process_page_with_form1s4_1(self.page_number):
            print(f"[ERROR] Failed to process page {self.page_number} with Form1S4.1")
            return False

        # Step 3: Form1S4 - Individual Shape Extraction
        self.print_section(f"STEP 3: INDIVIDUAL SHAPE EXTRACTION (FORM1S4) - PAGE {self.page_number}")
        if not self.process_page_with_form1s4(self.page_number):
            print(f"[ERROR] Failed to process page {self.page_number} with Form1S4")
            return False

        # Step 4: Form1OCR2 - Table OCR Processing
        self.print_section(f"STEP 4: TABLE OCR PROCESSING (FORM1OCR2) - PAGE {self.page_number}")
        if not self.process_page_with_form1ocr2(self.page_number):
            print(f"[WARNING] Failed to process page {self.page_number} with Form1OCR2, continuing...")

        # Step 5: Form1Dat1 - Database Integration
        self.print_section(f"STEP 5: DATABASE INTEGRATION (FORM1DAT1)")
        if not self.process_with_form1dat1():
            print(f"[WARNING] Failed to process with Form1Dat1, continuing...")

        # Print summary
        self.print_summary()

        return len(self.results["errors"]) == 0

    def print_summary(self):
        """Print processing summary"""
        end_time = datetime.now()
        duration = end_time - self.start_time

        print()
        print("=" * 70)
        print(" " * 20 + f"PROCESSING SUMMARY - PAGE {self.page_number}")
        print("=" * 70)
        print()
        print(f"Started:  {self.start_time.strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"Finished: {end_time.strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"Duration: {duration.total_seconds():.2f} seconds")
        print()

        if self.results["errors"]:
            print("ERRORS ENCOUNTERED:")
            for error in self.results["errors"]:
                print(f"  - {error}")
            print()
            print(f"RESULT: COMPLETED WITH {len(self.results['errors'])} ERROR(S)")
        else:
            print("RESULT: ALL STEPS COMPLETED SUCCESSFULLY")

        print("=" * 70)

def main():
    """Main entry point"""
    import argparse

    parser = argparse.ArgumentParser(
        description="Area Table Detection Pipeline for Single Page Processing"
    )
    parser.add_argument(
        "page_number",
        type=int,
        help="Page number to process"
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        help="Override the default output directory"
    )
    parser.add_argument(
        "--process",
        type=str,
        default="full",
        choices=["full", "copy_replace", "update_table", "shapes_only", "ocr_only"],
        help="Processing mode: full (default), copy_replace, update_table, shapes_only, ocr_only"
    )

    args = parser.parse_args()

    if args.page_number < 1:
        print("Error: Page number must be 1 or greater")
        sys.exit(1)

    # Create pipeline
    pipeline = AreaTableDetectionPipeline(args.page_number, args.process)

    # Override directories if specified
    if args.output_dir:
        pipeline.output_dir = args.output_dir

    # Run pipeline
    try:
        success = pipeline.run()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print(f"\n\n[INTERRUPTED] Pipeline interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n[FATAL ERROR] {str(e)}")
        logger.exception("Fatal error in pipeline")
        sys.exit(1)

if __name__ == "__main__":
    main()
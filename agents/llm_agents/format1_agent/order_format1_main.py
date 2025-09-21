import os
import logging
import json
from datetime import datetime
from pathlib import Path
from .form1s1 import Form1S1Agent

logger = logging.getLogger(__name__)

class OrderFormat1MainAgent:
    """
    Main coordinator agent for Format 1 order processing
    Orchestrates all Format 1 processing steps
    """

    def __init__(self):
        self.name = "order_format1_main"
        self.short_name = "form1main"
        self.input_dir = "io/input"
        self.output_dir = "io/fullorder_output"
        self.steps_completed = []
        self.steps_pending = []

        # Initialize sub-agents
        self.agents = {
            "form1s1": None   # Will be initialized when needed
        }

        logger.info(f"[{self.short_name.upper()}] Agent initialized - Format 1 Main Coordinator")

    def initialize_agents(self):
        """Initialize all sub-agents"""
        try:
            if not self.agents["form1s1"]:
                self.agents["form1s1"] = Form1S1Agent()
                logger.info(f"[{self.short_name.upper()}] Initialized form1s1 agent")
            return True
        except Exception as e:
            logger.error(f"[{self.short_name.upper()}] Failed to initialize agents: {str(e)}")
            return False

    def process_format1_orders(self, input_dir=None, specific_order=None):
        """
        Main processing function for Format 1 orders

        Args:
            input_dir (str): Optional input directory override
            specific_order (str): Optional specific order to process

        Returns:
            dict: Complete processing results
        """
        start_time = datetime.now()

        # Use provided input_dir or default
        if input_dir:
            self.input_dir = input_dir

        result = {
            "status": "processing",
            "agent": self.name,
            "short_name": self.short_name,
            "start_time": start_time.isoformat(),
            "input_dir": self.input_dir,
            "output_dir": self.output_dir,
            "specific_order": specific_order,
            "steps": {},
            "errors": [],
            "summary": {}
        }

        logger.info(f"[{self.short_name.upper()}] Starting Format 1 processing pipeline")
        logger.info(f"[{self.short_name.upper()}] Input directory: {self.input_dir}")
        logger.info(f"[{self.short_name.upper()}] Output directory: {self.output_dir}")

        # Initialize agents
        if not self.initialize_agents():
            result["status"] = "error"
            result["errors"].append("Failed to initialize sub-agents")
            return result

        # Get list of files to process
        files_to_process = self.get_files_to_process(specific_order)

        if not files_to_process:
            logger.warning(f"[{self.short_name.upper()}] No PDF files found to process")
            result["status"] = "no_files"
            result["message"] = "No PDF files found in input directory"
            return result

        logger.info(f"[{self.short_name.upper()}] Found {len(files_to_process)} file(s) to process")

        # Step 1: Extract first page images (form1s1)
        step1_result = self.execute_step1(files_to_process)
        result["steps"]["step1_page_extraction"] = step1_result

        if step1_result["status"] == "success":
            self.steps_completed.append("step1_page_extraction")
            logger.info(f"[{self.short_name.upper()}] Step 1 completed: {step1_result['success_count']}/{step1_result['total_count']} files")
        else:
            result["errors"].append(f"Step 1 failed: {step1_result.get('error', 'Unknown error')}")

        # Step 2: Table detection (form1s2) - now handled in main_table_detection.py
        logger.info(f"[{self.short_name.upper()}] Step 2 will be handled by main_table_detection.py")

        # Future steps can be added here:
        # Step 3: Header extraction
        # Step 4: Shape recognition
        # Step 5: Dimension extraction
        # etc.

        # Calculate summary
        end_time = datetime.now()
        processing_time = (end_time - start_time).total_seconds()

        result["end_time"] = end_time.isoformat()
        result["processing_time_seconds"] = processing_time
        result["status"] = "completed" if not result["errors"] else "completed_with_errors"

        # Generate summary
        result["summary"] = self.generate_summary(result)

        # Save results to JSON
        self.save_results(result)

        logger.info(f"[{self.short_name.upper()}] Processing complete in {processing_time:.2f} seconds")

        return result

    def get_files_to_process(self, specific_order=None):
        """Get list of PDF files to process"""
        files = []

        if not os.path.exists(self.input_dir):
            logger.error(f"[{self.short_name.upper()}] Input directory does not exist: {self.input_dir}")
            return files

        for file in os.listdir(self.input_dir):
            if file.lower().endswith('.pdf'):
                # If specific order is provided, only process that order
                if specific_order:
                    if specific_order in file:
                        files.append(os.path.join(self.input_dir, file))
                else:
                    files.append(os.path.join(self.input_dir, file))

        return files

    def execute_step1(self, files_to_process):
        """Execute Step 1: Page extraction using form1s1 agent"""
        logger.info(f"[{self.short_name.upper()}] Executing Step 1: Page Extraction")

        step_result = {
            "step": "page_extraction",
            "agent": "form1s1",
            "status": "processing",
            "files_processed": [],
            "success_count": 0,
            "error_count": 0,
            "total_count": len(files_to_process)
        }

        try:
            form1s1 = self.agents["form1s1"]

            for file_path in files_to_process:
                file_name = os.path.basename(file_path)
                logger.info(f"[{self.short_name.upper()}] Processing with form1s1: {file_name}")

                # Process individual file
                file_result = form1s1.process_order(file_path)

                step_result["files_processed"].append({
                    "file": file_name,
                    "status": file_result["status"],
                    "output": file_result.get("output_file", None),
                    "error": file_result.get("error", None)
                })

                if file_result["status"] == "success":
                    step_result["success_count"] += 1
                    logger.info(f"[{self.short_name.upper()}] Successfully processed: {file_name}")
                else:
                    step_result["error_count"] += 1
                    logger.error(f"[{self.short_name.upper()}] Failed to process: {file_name} - {file_result.get('error', 'Unknown error')}")

            step_result["status"] = "success" if step_result["error_count"] == 0 else "partial_success"

        except Exception as e:
            logger.error(f"[{self.short_name.upper()}] Step 1 failed: {str(e)}")
            step_result["status"] = "error"
            step_result["error"] = str(e)

        return step_result

    # execute_step2 removed - now handled in main_table_detection.py

    def generate_summary(self, result):
        """Generate processing summary"""
        summary = {
            "total_files": 0,
            "successful_steps": len(self.steps_completed),
            "total_errors": len(result["errors"]),
            "steps_summary": {}
        }

        # Summarize each step
        for step_name, step_data in result["steps"].items():
            if isinstance(step_data, dict):
                summary["steps_summary"][step_name] = {
                    "status": step_data.get("status", "unknown"),
                    "files_processed": step_data.get("total_count", 0),
                    "success_count": step_data.get("success_count", 0),
                    "error_count": step_data.get("error_count", 0)
                }

                if step_data.get("total_count", 0) > 0:
                    summary["total_files"] = max(summary["total_files"], step_data["total_count"])

        return summary

    def save_results(self, result):
        """Save processing results to JSON file - DISABLED"""
        # JSON file creation disabled - no longer saving format1_processing_results file
        logger.info(f"[{self.short_name.upper()}] JSON result file creation skipped (disabled)")
        return

    def get_processing_status(self):
        """Get current processing status"""
        return {
            "agent": self.name,
            "steps_completed": self.steps_completed,
            "steps_pending": self.steps_pending,
            "agents_initialized": list(self.agents.keys())
        }
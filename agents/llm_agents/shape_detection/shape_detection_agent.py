import os
import json
import subprocess
import sys
from pathlib import Path
from typing import Dict, List, Optional
from datetime import datetime

# Add parent directories to path for imports
sys.path.append(str(Path(__file__).parent.parent.parent))
from llm_agents.format1_agent.form1dat2 import Form1Dat2Agent


class ShapeDetectionAgent:
    """
    Shape Detection Agent
    Orchestrates the complete shape detection pipeline:
    1. Run skeleton analyzer
    2. Run shape to YOLO table
    3. Run YOLO detection
    4. Update central database with results
    """

    def __init__(self):
        """Initialize the Shape Detection Agent"""
        self.project_root = Path(__file__).parent.parent.parent.parent
        self.skeleton_script = self.project_root / "agents/llm_agents/shape_detection/skeleton/skeleton_analyzer.py"
        self.table_script = self.project_root / "agents/llm_agents/shape_detection/skeleton/shape_to_yolo_table.py"
        self.yolo_script = self.project_root / "agents/llm_agents/shape_detection/yolo/yolos1shape.py"
        self.yolo_output_dir = self.project_root / "io/fullorder_output/table_detection/shape_detection/yolo_output"
        self.central_db_path = self.project_root / "io/fullorder_output/json_output"

        # Initialize Form1Dat2Agent for catalog updates
        self.form1dat2_agent = Form1Dat2Agent()

    def run_pipeline(self, order_number: str = "CO25S006375") -> Dict:
        """
        Run the complete shape detection pipeline

        Args:
            order_number: Order number to process

        Returns:
            Dictionary with pipeline results
        """
        print("=" * 80)
        print("SHAPE DETECTION AGENT - STARTING PIPELINE")
        print("=" * 80)
        print(f"Order: {order_number}")
        print(f"Timestamp: {datetime.now().isoformat()}")
        print()

        results = {
            "order_number": order_number,
            "timestamp": datetime.now().isoformat(),
            "steps": {},
            "database_updates": []
        }

        # Step 1: Run skeleton analyzer
        print("[1/4] Running skeleton analyzer...")
        skeleton_result = self._run_script(self.skeleton_script)
        results["steps"]["skeleton_analyzer"] = skeleton_result
        if not skeleton_result["success"]:
            print(f"[FAILED] Skeleton analyzer failed: {skeleton_result.get('error')}")
            return results
        print("[SUCCESS] Skeleton analyzer completed")
        print()

        # Step 2: Run shape to YOLO table
        print("[2/4] Running shape to YOLO table...")
        table_result = self._run_script(self.table_script)
        results["steps"]["shape_to_yolo_table"] = table_result
        if not table_result["success"]:
            print(f"[FAILED] Shape to YOLO table failed: {table_result.get('error')}")
            return results
        print("[SUCCESS] Shape to YOLO table completed")
        print()

        # Step 3: Run YOLO detection
        print("[3/4] Running YOLO shape detection...")
        yolo_result = self._run_script(self.yolo_script)
        results["steps"]["yolo_detection"] = yolo_result
        if not yolo_result["success"]:
            print(f"[FAILED] YOLO detection failed: {yolo_result.get('error')}")
            return results
        print("[SUCCESS] YOLO detection completed")
        print()

        # Step 4: Update central database
        print("[4/4] Updating central database...")
        db_updates = self._update_central_database(order_number)
        results["database_updates"] = db_updates
        print(f"[SUCCESS] Updated {len(db_updates)} entries in central database")
        print()

        # Step 5: Update rib configurations using Form1Dat2Agent
        print("[5/5] Updating rib configurations for detected shapes...")
        rib_updates = self._update_rib_configurations(order_number, db_updates)
        results["rib_configuration_updates"] = rib_updates
        print(f"[SUCCESS] Updated rib configurations for {len(rib_updates['successful'])} shapes")
        if rib_updates['failed']:
            print(f"[WARNING] Failed to update {len(rib_updates['failed'])} shapes")
        print()

        print("=" * 80)
        print("SHAPE DETECTION PIPELINE COMPLETED SUCCESSFULLY")
        print("=" * 80)

        return results

    def _run_script(self, script_path: Path) -> Dict:
        """
        Run a Python script and capture results

        Args:
            script_path: Path to the script to run

        Returns:
            Dictionary with execution results
        """
        try:
            result = subprocess.run(
                ["python", str(script_path)],
                capture_output=True,
                text=True,
                timeout=600  # 10 minutes timeout
            )

            return {
                "success": result.returncode == 0,
                "stdout": result.stdout,
                "stderr": result.stderr,
                "returncode": result.returncode
            }
        except subprocess.TimeoutExpired:
            return {
                "success": False,
                "error": "Script execution timeout (10 minutes)"
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }

    def _update_central_database(self, order_number: str) -> List[Dict]:
        """
        Update central database with YOLO detection results

        Args:
            order_number: Order number being processed

        Returns:
            List of database updates performed
        """
        # Read YOLO summary file
        summary_file = self.yolo_output_dir / "yolo_summary_all_shapes.json"

        if not summary_file.exists():
            print(f"Warning: YOLO summary file not found at {summary_file}")
            return []

        with open(summary_file, 'r', encoding='utf-8') as f:
            yolo_summary = json.load(f)

        # Find central database file for this order
        central_db_file = self.central_db_path / f"{order_number}_out.json"

        if not central_db_file.exists():
            print(f"Warning: Central database file not found at {central_db_file}")
            return []

        # Load central database
        with open(central_db_file, 'r', encoding='utf-8') as f:
            central_db = json.load(f)

        updates = []

        # Process each shape determination from YOLO summary
        for determination in yolo_summary.get("shape_determinations", []):
            page = determination.get("page")
            row = determination.get("row")
            shape_number = determination.get("shape_number")

            # Convert shape_number: 200 -> 218, unknown -> empty
            if shape_number == "200":
                final_shape = "218"
            elif shape_number == "unknown":
                final_shape = ""
            else:
                final_shape = shape_number

            # Update central database
            update_result = self._update_db_entry(
                central_db,
                page,
                row,
                final_shape,
                determination.get("shape_type_counts", {}),
                determination.get("total_detections", 0)
            )

            if update_result:
                updates.append({
                    "page": page,
                    "row": row,
                    "original_shape": shape_number,
                    "final_shape": final_shape,
                    "updated": update_result
                })

        # Save updated central database
        with open(central_db_file, 'w', encoding='utf-8') as f:
            json.dump(central_db, f, indent=2, ensure_ascii=False)

        print(f"Central database updated: {central_db_file}")

        return updates

    def _update_db_entry(
        self,
        db: Dict,
        page: str,
        row: str,
        shape_number: str,
        shape_counts: Dict,
        total_detections: int
    ) -> bool:
        """
        Update a specific entry in the central database

        Args:
            db: Central database dictionary
            page: Page number
            row: Row number
            shape_number: Shape number to set (empty string if unknown)
            shape_counts: Shape type counts (not used, kept for compatibility)
            total_detections: Total detections (not used, kept for compatibility)

        Returns:
            True if update was successful
        """
        try:
            # The database structure is:
            # section_3_shape_analysis -> page_X -> order_lines -> line_X -> shape_catalog_number

            if "section_3_shape_analysis" not in db:
                return False

            shape_analysis = db["section_3_shape_analysis"]
            page_key = f"page_{page}"

            if page_key not in shape_analysis:
                return False

            page_data = shape_analysis[page_key]

            if "order_lines" not in page_data:
                return False

            order_lines = page_data["order_lines"]
            line_key = f"line_{row}"

            if line_key not in order_lines:
                return False

            line_data = order_lines[line_key]

            # Update the shape catalog number
            # If shape_number is empty (unknown), set to empty string
            # Otherwise, set to the detected shape number
            line_data["shape_catalog_number"] = shape_number

            return True

        except Exception as e:
            print(f"Error updating DB entry for page {page}, row {row}: {e}")
            return False

    def _update_rib_configurations(self, order_number: str, db_updates: List[Dict]) -> Dict:
        """
        Update rib configurations for all detected shapes using Form1Dat2Agent

        Args:
            order_number: Order number being processed
            db_updates: List of database updates with page, row, and shape info

        Returns:
            Dictionary with successful and failed updates
        """
        results = {
            "successful": [],
            "failed": [],
            "skipped": []
        }

        for update in db_updates:
            page = update.get("page")
            row = update.get("row")
            final_shape = update.get("final_shape")

            # Skip if shape is empty (unknown)
            if not final_shape or final_shape == "":
                results["skipped"].append({
                    "page": page,
                    "row": row,
                    "reason": "Unknown shape - no catalog number"
                })
                print(f"  Skipped page {page}, row {row}: Unknown shape")
                continue

            try:
                # Call Form1Dat2Agent to update rib configuration
                print(f"  Updating ribs for page {page}, row {row}, shape {final_shape}...")

                result = self.form1dat2_agent.update_shape_in_order(
                    order_number=order_number,
                    page_number=int(page),
                    line_number=int(row),
                    new_shape_number=final_shape
                )

                if result.get("status") == "success":
                    results["successful"].append({
                        "page": page,
                        "row": row,
                        "shape": final_shape,
                        "updated_fields": result.get("updated_fields", [])
                    })
                    print(f"  [OK] Updated ribs for page {page}, row {row}, shape {final_shape}")
                else:
                    results["failed"].append({
                        "page": page,
                        "row": row,
                        "shape": final_shape,
                        "error": result.get("error", "Unknown error")
                    })
                    print(f"  [FAILED] Failed to update page {page}, row {row}: {result.get('error')}")

            except Exception as e:
                results["failed"].append({
                    "page": page,
                    "row": row,
                    "shape": final_shape,
                    "error": str(e)
                })
                print(f"  [ERROR] Exception updating page {page}, row {row}: {e}")

        return results

    def get_pipeline_status(self) -> Dict:
        """
        Get the current status of the pipeline

        Returns:
            Dictionary with status information
        """
        status = {
            "skeleton_analyzer": os.path.exists(self.skeleton_script),
            "shape_to_yolo_table": os.path.exists(self.table_script),
            "yolo_detection": os.path.exists(self.yolo_script),
            "yolo_output_dir": os.path.exists(self.yolo_output_dir),
            "central_db_dir": os.path.exists(self.central_db_path)
        }
        return status


def main():
    """Main function to run the shape detection pipeline"""
    agent = ShapeDetectionAgent()

    # Check pipeline status
    status = agent.get_pipeline_status()
    print("Pipeline Status:")
    for component, exists in status.items():
        print(f"  {component}: {'OK' if exists else 'MISSING'}")
    print()

    # Run the pipeline
    results = agent.run_pipeline()

    # Print summary
    print("\nPipeline Results Summary:")
    print(f"Order: {results['order_number']}")
    print(f"Timestamp: {results['timestamp']}")
    print(f"\nSteps Completed:")
    for step, result in results["steps"].items():
        print(f"  {step}: {'SUCCESS' if result.get('success') else 'FAILED'}")

    print(f"\nDatabase Updates: {len(results['database_updates'])} entries")

    return results


if __name__ == "__main__":
    main()

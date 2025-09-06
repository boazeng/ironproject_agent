import os
from datetime import datetime
from typing import Optional

class IronManLogger:
    """
    Logging utility for IronMan agent workflow tracking.
    Creates and manages last_run_log.txt file in io/log/ directory.
    """
    
    def __init__(self, log_dir: str = "io/log"):
        self.log_dir = log_dir
        self.log_file = os.path.join(log_dir, "last_run_log.txt")
        self.current_step = 0
        
        # Ensure log directory exists
        os.makedirs(log_dir, exist_ok=True)
        
        # Clear previous log and start new session
        self._clear_log()
        self._log_session_start()
    
    def _clear_log(self):
        """Clear the contents of the log file for new run."""
        with open(self.log_file, 'w', encoding='utf-8') as f:
            f.write("")
    
    def _write_to_log(self, message: str):
        """Write message to log file with timestamp."""
        timestamp = datetime.now().strftime("%H:%M:%S")
        with open(self.log_file, 'a', encoding='utf-8') as f:
            f.write(f"[{timestamp}] {message}\n")
    
    def _log_session_start(self):
        """Log the start of a new session."""
        session_start = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self._write_to_log("="*80)
        self._write_to_log(f"🦾 IRONMAN SYSTEM LOG - SESSION START: {session_start}")
        self._write_to_log("="*80)
    
    def log_system_start(self):
        """Log system initialization."""
        self._write_to_log("\n[🦾 IRONMAN] System initializing...")
        self._write_to_log("[🦾 IRONMAN] Loading environment variables and API keys")
    
    def log_agent_creation(self, agent_name: str, description: str):
        """Log agent creation."""
        self._write_to_log(f"[🦾 IRONMAN]   ✓ {agent_name} ({description}) created and ready")
    
    def log_input_scan(self, file_count: int, files: list):
        """Log input file scanning."""
        self._write_to_log(f"\n[🦾 IRONMAN] Scanning input directory...")
        self._write_to_log(f"[🦾 IRONMAN] Found {file_count} files to process:")
        for file in files:
            self._write_to_log(f"[🦾 IRONMAN]   • {file}")
    
    def log_file_processing_start(self, file_name: str, file_number: int, total_files: int):
        """Log start of file processing."""
        self._write_to_log(f"\n{'='*60}")
        self._write_to_log(f"[🦾 IRONMAN] Processing file {file_number}/{total_files}: {file_name}")
        self._write_to_log(f"{'='*60}")
        self.current_step = 0
    
    def log_step_start(self, step_number: int, step_name: str, agent_name: str):
        """Log start of processing step."""
        self.current_step = step_number
        self._write_to_log(f"\n[🦾 IRONMAN] [STEP {step_number}] {step_name}")
        self._write_to_log(f"[🦾 IRONMAN]   → Sending to {agent_name}")
    
    def log_agent_output(self, agent_name: str, output_data: dict):
        """Log detailed agent output."""
        self._write_to_log(f"\n[{agent_name.upper()}] AGENT OUTPUT:")
        self._write_to_log("-" * 40)
        
        # Log different types of agent outputs
        if agent_name.upper() == "RIBFINDER":
            self._log_ribfinder_output(output_data)
        elif agent_name.upper() == "RIBFINDER_CLEANED":
            self._write_to_log("="*50)
            self._write_to_log("[RIBFINDER] CLEANED IMAGE ANALYSIS:")
            self._log_ribfinder_output(output_data)
        elif agent_name.upper() == "RIBFINDER_ORIGINAL":
            self._write_to_log("="*50)  
            self._write_to_log("[RIBFINDER] ORIGINAL IMAGE ANALYSIS:")
            self._log_ribfinder_output(output_data)
        elif agent_name.upper() == "RIBFINDER_FINAL_CHOICE":
            self._write_to_log("="*50)
            self._write_to_log("[RIBFINDER] FINAL SELECTED RESULT:")
            self._log_ribfinder_output(output_data)
            self._write_to_log("="*50)
        elif agent_name.upper() == "CHATAN":
            self._log_chatan_output(output_data)
        elif agent_name.upper() == "PATHFINDER":
            self._log_pathfinder_output(output_data)
        elif agent_name.upper() == "CHATCO":
            self._log_chatco_output(output_data)
        elif agent_name.upper() == "DATAOUTPUT":
            self._log_dataoutput_output(output_data)
        else:
            # Generic output logging
            for key, value in output_data.items():
                self._write_to_log(f"[{agent_name.upper()}] {key}: {value}")
        
        self._write_to_log("-" * 40)
    
    def _log_ribfinder_output(self, data: dict):
        """Log RibFinder specific output."""
        if 'rib_count' in data:
            self._write_to_log(f"[RIBFINDER] Rib Count: {data['rib_count']}")
        if 'match_percentage' in data:
            self._write_to_log(f"[RIBFINDER] Match Percentage: {data['match_percentage']}%")
        if 'vision_agreement' in data:
            self._write_to_log(f"[RIBFINDER] Vision Agreement: {data['vision_agreement']}")
        if 'chatgpt_count' in data:
            self._write_to_log(f"[RIBFINDER] ChatGPT Count: {data['chatgpt_count']}")
        if 'google_vision_count' in data:
            self._write_to_log(f"[RIBFINDER] Google Vision Count: {data['google_vision_count']}")
        if 'opencv_count' in data:
            self._write_to_log(f"[RIBFINDER] OpenCV Count: {data['opencv_count']}")
        if 'scikit_count' in data:
            self._write_to_log(f"[RIBFINDER] Scikit-image Count: {data['scikit_count']}")
        if 'claude_count' in data:
            self._write_to_log(f"[RIBFINDER] Claude Count: {data['claude_count']}")
    
    def _log_chatan_output(self, data: dict):
        """Log CHATAN specific output."""
        if 'shape_type' in data:
            self._write_to_log(f"[CHATAN] Shape Type: {data['shape_type']}")
        if 'number_of_ribs' in data:
            self._write_to_log(f"[CHATAN] Number of Ribs: {data['number_of_ribs']}")
        if 'confidence' in data:
            self._write_to_log(f"[CHATAN] Confidence: {data['confidence']}%")
        if 'match_percentage' in data:
            self._write_to_log(f"[CHATAN] Vision Match: {data['match_percentage']}%")
        if 'vision_agreement' in data:
            self._write_to_log(f"[CHATAN] Vision Agreement: {data['vision_agreement']}")
        if 'sides' in data:
            self._write_to_log(f"[CHATAN] Sides Analysis:")
            for side in data['sides']:
                side_num = side.get('side_number', '?')
                length = side.get('length', 0)
                description = side.get('description', 'unknown')
                self._write_to_log(f"[CHATAN]   Rib {side_num}: {length} cm ({description})")
        if 'angles_between_ribs' in data:
            self._write_to_log(f"[CHATAN] Angles Between Ribs: {data['angles_between_ribs']}°")
        if 'google_vision_data' in data and data['google_vision_data']:
            gv_data = data['google_vision_data']
            if 'dimensions' in gv_data:
                self._write_to_log(f"[CHATAN] Google Vision Dimensions: {gv_data['dimensions']}")
        if 'status' in data:
            self._write_to_log(f"[CHATAN] Status: {data['status']}")
    
    def _log_pathfinder_output(self, data: dict):
        """Log PathFinder specific output."""
        if 'shape_type' in data:
            self._write_to_log(f"[PATHFINDER] Shape Type: {data['shape_type']}")
        if 'vertex_count' in data:
            self._write_to_log(f"[PATHFINDER] Vertex Count: {data['vertex_count']}")
        if 'total_path_length' in data:
            self._write_to_log(f"[PATHFINDER] Total Path Length: {data['total_path_length']} units")
        if 'is_closed' in data:
            self._write_to_log(f"[PATHFINDER] Closed Shape: {data['is_closed']}")
        if 'vectors' in data:
            self._write_to_log("[PATHFINDER] Vector Analysis:")
            for vector in data['vectors']:
                rib_num = vector.get('rib_number', '?')
                length = vector.get('length', 0)
                angle = vector.get('angle_degrees', 0)
                self._write_to_log(f"[PATHFINDER]   Vector {rib_num}: {length:.1f} units at {angle:.1f}°")
        if 'path_summary' in data and 'bounding_box' in data['path_summary']:
            bbox = data['path_summary']['bounding_box']
            width = bbox.get('width', 0)
            height = bbox.get('height', 0)
            self._write_to_log(f"[PATHFINDER] Bounding Box: {width:.1f} × {height:.1f} units")
        if 'error' in data:
            self._write_to_log(f"[PATHFINDER] Error: {data['error']}")
    
    def _log_chatco_output(self, data: dict):
        """Log CHATCO specific output."""
        if 'best_match_file' in data:
            self._write_to_log(f"[CHATCO] Best Match File: {data['best_match_file']}")
        if 'similarity_score' in data:
            self._write_to_log(f"[CHATCO] Similarity Score: {data['similarity_score']}%")
        if 'shape_match' in data:
            self._write_to_log(f"[CHATCO] Shape Match: {'YES' if data['shape_match'] else 'NO'}")
        if 'match_quality' in data:
            self._write_to_log(f"[CHATCO] Match Quality: {data['match_quality']}")
        if 'matching_features' in data and data['matching_features']:
            self._write_to_log(f"[CHATCO] Matching Features: {', '.join(data['matching_features'])}")
        if 'differences' in data and data['differences']:
            self._write_to_log(f"[CHATCO] Differences: {', '.join(data['differences'])}")
        if 'reasoning' in data and data['reasoning']:
            self._write_to_log(f"[CHATCO] Reasoning: {data['reasoning']}")
    
    def _log_cleaner_output(self, data: dict):
        """Log CLEANER specific output."""
        if 'status' in data:
            self._write_to_log(f"[CLEANER] Status: {data['status'].upper()}")
        if 'cleaned_path' in data:
            self._write_to_log(f"[CLEANER] Cleaned Image: {data['cleaned_path']}")
        if 'cleaning_method' in data:
            self._write_to_log(f"[CLEANER] Cleaning Method: {data['cleaning_method']}")
        if 'text_regions_detected' in data:
            self._write_to_log(f"[CLEANER] Text Regions Detected: {data['text_regions_detected']}")
        if 'dimension_lines_detected' in data:
            self._write_to_log(f"[CLEANER] Dimension Lines Detected: {data['dimension_lines_detected']}")
        if 'google_vision_used' in data:
            vision_status = "Yes" if data['google_vision_used'] else "No (fallback used)"
            self._write_to_log(f"[CLEANER] Google Vision Used: {vision_status}")
        if 'pixels_removed' in data:
            self._write_to_log(f"[CLEANER] Pixels Removed: {data['pixels_removed']:,}")
        if 'cleaning_percentage' in data:
            self._write_to_log(f"[CLEANER] Cleaning Percentage: {data['cleaning_percentage']}%")
    
    def _log_dataoutput_output(self, data: dict):
        """Log DataOutput specific output."""
        if 'status' in data:
            self._write_to_log(f"[DATAOUTPUT] Status: {data['status'].upper()}")
        if 'record_id' in data:
            self._write_to_log(f"[DATAOUTPUT] Record ID: {data['record_id']}")
        if 'order_number' in data:
            self._write_to_log(f"[DATAOUTPUT] Order Number: {data['order_number']}")
    
    def log_validation_result(self, is_valid: bool, retry_count: int = 0):
        """Log validation results."""
        if is_valid:
            self._write_to_log(f"[🦾 IRONMAN] ✓ Results validated successfully")
        else:
            self._write_to_log(f"[🦾 IRONMAN] ⚠ Validation failed (Retry {retry_count}/3)")
    
    def log_file_completion(self, file_name: str, success: bool):
        """Log file processing completion."""
        status = "✓ COMPLETED" if success else "✗ FAILED"
        self._write_to_log(f"\n[🦾 IRONMAN] File {file_name}: {status}")
    
    def log_system_completion(self):
        """Log system completion."""
        session_end = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self._write_to_log(f"\n[🦾 IRONMAN] System workflow completed successfully")
        self._write_to_log("="*80)
        self._write_to_log(f"🦾 IRONMAN SYSTEM LOG - SESSION END: {session_end}")
        self._write_to_log("="*80)
    
    def log_error(self, error_message: str, agent_name: Optional[str] = None):
        """Log error messages."""
        if agent_name:
            self._write_to_log(f"[{agent_name.upper()}] ERROR: {error_message}")
        else:
            self._write_to_log(f"[🦾 IRONMAN] ERROR: {error_message}")
    
    def get_log_file_path(self) -> str:
        """Return the path to the log file."""
        return self.log_file
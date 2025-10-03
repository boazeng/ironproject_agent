"""
Analysis Routes - IRONMAN System
Main analysis functionality for running the global analysis pipeline
"""

from flask import Blueprint, request, jsonify
import os
import sys
import subprocess
import threading
from datetime import datetime
import glob

# Create the blueprint
analysis_bp = Blueprint('analysis', __name__)

# Global analysis status tracking
analysis_status = {
    'running': False,
    'error': None,
    'current_stage': 'לא פעיל',
    'progress_messages': [],
    'last_run': None,
    'last_result': None
}

@analysis_bp.route('/api/run-analysis', methods=['POST'])
def run_analysis():
    """Run the main_table_detection.py analysis script"""
    global analysis_status

    print(f"[DEBUG] /api/run-analysis endpoint called")

    if analysis_status['running']:
        print(f"[DEBUG] Analysis already running, returning error")
        return jsonify({
            'success': False,
            'error': 'Analysis already running'
        })

    # Get the selected filename from request
    data = request.get_json() or {}
    selected_file = data.get('filename', '')
    print(f"[DEBUG] Request data: {data}")
    print(f"[DEBUG] Selected file: {selected_file}")

    def run_script():
        global analysis_status

        # Create log file for this run
        log_filename = f"io/log/analysis_run_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
        os.makedirs("io/log", exist_ok=True)

        try:
            print(f"[DEBUG] Starting run_script function")
            print(f"[DEBUG] Selected file: {selected_file}")
            print(f"[DEBUG] Logging to: {log_filename}")

            # Open log file for writing
            with open(log_filename, 'w', encoding='utf-8') as log_file:
                log_file.write(f"Analysis started at {datetime.now().isoformat()}\n")
                log_file.write(f"Selected file: {selected_file}\n")
                log_file.write("="*60 + "\n\n")

            analysis_status['running'] = True
            analysis_status['error'] = None
            analysis_status['current_stage'] = 'מתחיל עיבוד...'
            analysis_status['progress_messages'] = []

            # Run the main_table_detection.py script (doesn't accept filename arguments)
            cmd = ['python', 'main_table_detection.py', '--skip-clean']

            print(f"[DEBUG] Running command: {' '.join(cmd)}")
            print(f"[DEBUG] Current working directory: {os.getcwd()}")
            print(f"[DEBUG] Python executable: {sys.executable}")

            # Run the script with real-time output capture
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                encoding='utf-8',
                bufsize=1,
                cwd=os.getcwd()
            )

            # Process output in real-time
            output_lines = []

            # Append to log file
            with open(log_filename, 'a', encoding='utf-8') as log_file:
                for line in process.stdout:
                    line = line.strip()
                    if line:
                        output_lines.append(line)
                        print(f"[PROCESS] {line}")

                        # Write to log file with timestamp
                        log_file.write(f"[{datetime.now().strftime('%H:%M:%S')}] {line}\n")
                        log_file.flush()  # Ensure immediate write

                        # Parse and update progress based on output patterns
                        if 'STEP' in line:
                            # Extract stage from STEP messages
                            if ':' in line:
                                parts = line.split(':')
                                if len(parts) > 1:
                                    stage_msg = parts[1].strip()
                                    analysis_status['current_stage'] = stage_msg
                                    analysis_status['progress_messages'].append(f"שלב: {stage_msg}")
                                    log_file.write(f"[STAGE] {stage_msg}\n")
                        elif '[FORMAT1]' in line:
                            analysis_status['current_stage'] = 'מעבד פורמט 1...'
                            analysis_status['progress_messages'].append('מעבד הזמנה בפורמט 1')
                            log_file.write(f"[STAGE] Processing Format 1\n")
                        elif '[FORM1S1]' in line:
                            analysis_status['current_stage'] = 'ממיר PDF לתמונות...'
                            analysis_status['progress_messages'].append('ממיר PDF לתמונות')
                            log_file.write(f"[STAGE] Converting PDF to images\n")
                        elif '[FORM1S2]' in line:
                            analysis_status['current_stage'] = 'מזהה טבלאות...'
                            analysis_status['progress_messages'].append('מזהה טבלאות בדפים')
                            log_file.write(f"[STAGE] Detecting tables\n")
                        elif '[FORM1S3]' in line:
                            analysis_status['current_stage'] = 'מוצא קווי רשת...'
                            analysis_status['progress_messages'].append('מוצא קווי רשת בטבלאות')
                            log_file.write(f"[STAGE] Finding grid lines\n")
                        elif '[FORM1S3_1]' in line:
                            analysis_status['current_stage'] = 'מחלץ גוף טבלה...'
                            analysis_status['progress_messages'].append('מחלץ גוף טבלה')
                            log_file.write(f"[STAGE] Extracting table body\n")
                        elif '[FORM1S3_2]' in line:
                            analysis_status['current_stage'] = 'סופר שורות...'
                            analysis_status['progress_messages'].append('סופר שורות בטבלה')
                            log_file.write(f"[STAGE] Counting rows\n")
                        elif '[FORM1S4]' in line:
                            analysis_status['current_stage'] = 'מחלץ צורות...'
                            analysis_status['progress_messages'].append('מחלץ צורות מטבלה')
                            log_file.write(f"[STAGE] Extracting shapes\n")
                        elif '[FORM1OCR2]' in line:
                            analysis_status['current_stage'] = 'מבצע OCR על טבלה...'
                            analysis_status['progress_messages'].append('מבצע OCR על תוכן הטבלה')
                            log_file.write(f"[STAGE] Performing OCR\n")
                        elif '[FORM1DAT1]' in line:
                            analysis_status['current_stage'] = 'שומר במאגר נתונים...'
                            analysis_status['progress_messages'].append('שומר נתונים במאגר')
                            log_file.write(f"[STAGE] Saving to database\n")
                        elif 'SUCCESS' in line or 'completed successfully' in line:
                            analysis_status['progress_messages'].append('✓ ' + line[:100])
                            log_file.write(f"[SUCCESS] {line}\n")
                        elif 'ERROR' in line or 'failed' in line:
                            analysis_status['progress_messages'].append('✗ ' + line[:100])
                            log_file.write(f"[ERROR] {line}\n")

                # Wait for process to complete
                process.wait()
                return_code = process.returncode

                # Log final status
                log_file.write(f"\n{'='*60}\n")
                log_file.write(f"[{datetime.now().strftime('%H:%M:%S')}] PROCESS COMPLETED\n")
                log_file.write(f"Return code: {return_code}\n")
                log_file.write(f"Total output lines: {len(output_lines)}\n")

            print(f"[DEBUG] Command return code: {return_code}")
            print(f"[DEBUG] Total output lines: {len(output_lines)}")

            analysis_status['last_run'] = datetime.now().isoformat()

            # Append final status to log file
            with open(log_filename, 'a', encoding='utf-8') as log_file:
                if return_code == 0:
                    analysis_status['last_result'] = 'success'
                    analysis_status['current_stage'] = 'הושלם בהצלחה!'
                    analysis_status['progress_messages'].append('✓ העיבוד הושלם בהצלחה')
                    log_file.write(f"[FINAL] SUCCESS - Analysis completed successfully\n")
                    print("[DEBUG] Analysis completed successfully")
                else:
                    analysis_status['last_result'] = 'error'
                    analysis_status['error'] = 'Analysis process failed'
                    analysis_status['current_stage'] = 'שגיאה בעיבוד'
                    analysis_status['progress_messages'].append('✗ העיבוד נכשל')
                    log_file.write(f"[FINAL] ERROR - Analysis failed with return code: {return_code}\n")
                    print(f"[DEBUG] Analysis failed with return code: {return_code}")

        except Exception as e:
            analysis_status['last_result'] = 'error'
            analysis_status['error'] = str(e)
            print(f"[DEBUG] Error running analysis: {e}")
            import traceback
            print(f"[DEBUG] Traceback: {traceback.format_exc()}")
        finally:
            analysis_status['running'] = False
            if not analysis_status['current_stage']:
                analysis_status['current_stage'] = 'לא פעיל'
            print(f"[DEBUG] run_script function completed")

    # Run in background thread
    print(f"[DEBUG] Creating background thread")
    thread = threading.Thread(target=run_script)
    print(f"[DEBUG] Starting background thread")
    thread.start()
    print(f"[DEBUG] Background thread started, returning response")

    return jsonify({
        'success': True,
        'message': 'Analysis started'
    })

@analysis_bp.route('/api/analysis-progress')
def get_analysis_progress():
    """Get current analysis progress with detailed stage information"""
    return jsonify({
        'running': analysis_status['running'],
        'current_stage': analysis_status['current_stage'],
        'progress_messages': analysis_status['progress_messages'][-10:],  # Return last 10 messages
        'error': analysis_status['error']
    })

@analysis_bp.route('/api/analysis-status')
def get_analysis_status():
    """Get the current analysis status"""
    return jsonify(analysis_status)
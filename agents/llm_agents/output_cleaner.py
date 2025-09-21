import os
import logging
import json
from datetime import datetime
from pathlib import Path
import shutil

logger = logging.getLogger(__name__)

class OutputCleanerAgent:
    """
    Agent for cleaning output files from fullorder_output directory
    Safely removes only files, preserves folder structure
    """

    def __init__(self):
        self.name = "output_cleaner"
        self.short_name = "cleaner"
        self.output_dir = "io/fullorder_output"
        self.log_dir = "io/log"  # Add log directory for cleaning
        self.protected_extensions = ['.gitkeep', '.gitignore']  # Files to never delete
        self.protected_folders = ['table_detection', 'order_header', 'shapes', 'table', 'table_header']
        logger.info(f"[{self.short_name.upper()}] Agent initialized - Output file cleaner")

    def clean_output_directory(self, dry_run=False, specific_order=None):
        """
        Clean output files from the fullorder_output directory

        Args:
            dry_run (bool): If True, only report what would be deleted without actually deleting
            specific_order (str): If provided, only delete files for this specific order

        Returns:
            dict: Cleaning results including deleted files and statistics
        """
        result = {
            "status": "processing",
            "agent": self.name,
            "short_name": self.short_name,
            "dry_run": dry_run,
            "specific_order": specific_order,
            "timestamp": datetime.now().isoformat(),
            "deleted_files": [],
            "skipped_files": [],
            "preserved_folders": [],
            "errors": []
        }

        try:
            logger.info(f"[{self.short_name.upper()}] Starting output cleaning...")
            if dry_run:
                logger.info(f"[{self.short_name.upper()}] DRY RUN MODE - No files will be deleted")

            if specific_order:
                logger.info(f"[{self.short_name.upper()}] Cleaning files for specific order: {specific_order}")

            # Check if output directory exists
            if not os.path.exists(self.output_dir):
                logger.warning(f"[{self.short_name.upper()}] Output directory does not exist: {self.output_dir}")
                result["status"] = "warning"
                result["message"] = f"Output directory does not exist: {self.output_dir}"
                return result

            # Walk through the directory
            total_size_deleted = 0
            files_deleted = 0
            files_skipped = 0

            for root, dirs, files in os.walk(self.output_dir):
                # Get relative path for logging
                rel_path = os.path.relpath(root, self.output_dir)

                # Process files in current directory (no folder protection)
                for file in files:
                    file_path = os.path.join(root, file)
                    rel_file_path = os.path.relpath(file_path, self.output_dir)

                    try:
                        # Check if file should be skipped
                        should_skip = False
                        skip_reason = ""

                        # Check if it's a protected file type
                        for protected_ext in self.protected_extensions:
                            if file.endswith(protected_ext):
                                should_skip = True
                                skip_reason = f"Protected file type: {protected_ext}"
                                break

                        # If specific order is provided, only delete files for that order
                        if specific_order and not should_skip:
                            if specific_order not in file:
                                should_skip = True
                                skip_reason = f"Not matching order: {specific_order}"

                        # Check if it's a directory (extra safety check)
                        if os.path.isdir(file_path):
                            should_skip = True
                            skip_reason = "Is a directory"

                        if should_skip:
                            files_skipped += 1
                            result["skipped_files"].append({
                                "file": rel_file_path,
                                "reason": skip_reason
                            })
                            logger.debug(f"[{self.short_name.upper()}] Skipping: {rel_file_path} - {skip_reason}")
                            continue

                        # Get file size before deletion
                        file_size = os.path.getsize(file_path)
                        file_size_mb = file_size / (1024 * 1024)

                        if dry_run:
                            # Clean filename for logging to avoid encoding issues
                            safe_filename = rel_file_path.encode('ascii', 'replace').decode('ascii')
                            logger.info(f"[{self.short_name.upper()}] [DRY RUN] Would delete: {safe_filename} ({file_size_mb:.2f} MB)")
                        else:
                            # Actually delete the file
                            os.remove(file_path)
                            # Clean filename for logging to avoid encoding issues
                            safe_filename = rel_file_path.encode('ascii', 'replace').decode('ascii')
                            logger.info(f"[{self.short_name.upper()}] Deleted: {safe_filename} ({file_size_mb:.2f} MB)")

                        files_deleted += 1
                        total_size_deleted += file_size
                        result["deleted_files"].append({
                            "file": rel_file_path,
                            "size_bytes": file_size,
                            "size_mb": file_size_mb
                        })

                    except Exception as e:
                        error_msg = f"Error processing {rel_file_path}: {str(e)}"
                        logger.error(f"[{self.short_name.upper()}] {error_msg}")
                        result["errors"].append(error_msg)

                # Note preserved folders
                for dir_name in dirs:
                    dir_path = os.path.join(root, dir_name)
                    rel_dir_path = os.path.relpath(dir_path, self.output_dir)
                    result["preserved_folders"].append(rel_dir_path)

            # Calculate statistics
            total_size_mb = total_size_deleted / (1024 * 1024)

            result["status"] = "success"
            result["statistics"] = {
                "files_deleted": files_deleted,
                "files_skipped": files_skipped,
                "total_size_deleted_bytes": total_size_deleted,
                "total_size_deleted_mb": total_size_mb,
                "folders_preserved": len(result["preserved_folders"])
            }

            # Create summary message
            if dry_run:
                result["message"] = f"[DRY RUN] Would delete {files_deleted} file(s) ({total_size_mb:.2f} MB)"
            else:
                result["message"] = f"Successfully deleted {files_deleted} file(s) ({total_size_mb:.2f} MB)"

            logger.info(f"[{self.short_name.upper()}] {result['message']}")
            logger.info(f"[{self.short_name.upper()}] Skipped {files_skipped} file(s)")
            logger.info(f"[{self.short_name.upper()}] Preserved {len(result['preserved_folders'])} folder(s)")

            # Clean log directory files
            log_files_deleted, log_size_deleted = self._clean_log_directory(dry_run)
            if log_files_deleted > 0:
                files_deleted += log_files_deleted
                total_size_deleted += log_size_deleted
                # Update statistics
                result["statistics"]["files_deleted"] = files_deleted
                result["statistics"]["total_size_deleted_bytes"] = total_size_deleted
                result["statistics"]["total_size_deleted_mb"] = total_size_deleted / (1024 * 1024)

            # Save cleaning log
            if not dry_run and files_deleted > 0:
                log_file = os.path.join("io/log", f"cleaning_log_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json")
                os.makedirs(os.path.dirname(log_file), exist_ok=True)
                with open(log_file, 'w', encoding='utf-8') as f:
                    json.dump(result, f, indent=2, ensure_ascii=False)
                logger.info(f"[{self.short_name.upper()}] Cleaning log saved to: {log_file}")

        except Exception as e:
            logger.error(f"[{self.short_name.upper()}] Unexpected error during cleaning: {str(e)}")
            result["status"] = "error"
            result["error"] = f"Unexpected error: {str(e)}"

        return result

    def clean_specific_file_types(self, file_extensions, dry_run=False):
        """
        Clean only specific file types from the output directory

        Args:
            file_extensions (list): List of file extensions to delete (e.g., ['.png', '.json'])
            dry_run (bool): If True, only report what would be deleted

        Returns:
            dict: Cleaning results
        """
        logger.info(f"[{self.short_name.upper()}] Cleaning specific file types: {file_extensions}")

        result = {
            "status": "processing",
            "agent": self.name,
            "file_types_targeted": file_extensions,
            "dry_run": dry_run,
            "deleted_files": [],
            "errors": []
        }

        try:
            if not os.path.exists(self.output_dir):
                result["status"] = "error"
                result["error"] = f"Output directory does not exist: {self.output_dir}"
                return result

            files_deleted = 0
            total_size = 0

            for root, dirs, files in os.walk(self.output_dir):
                for file in files:
                    # Check if file matches target extensions
                    if any(file.endswith(ext) for ext in file_extensions):
                        file_path = os.path.join(root, file)
                        rel_path = os.path.relpath(file_path, self.output_dir)

                        try:
                            file_size = os.path.getsize(file_path)

                            if dry_run:
                                logger.info(f"[{self.short_name.upper()}] [DRY RUN] Would delete: {rel_path}")
                            else:
                                os.remove(file_path)
                                logger.info(f"[{self.short_name.upper()}] Deleted: {rel_path}")

                            files_deleted += 1
                            total_size += file_size
                            result["deleted_files"].append(rel_path)

                        except Exception as e:
                            error_msg = f"Error deleting {rel_path}: {str(e)}"
                            logger.error(f"[{self.short_name.upper()}] {error_msg}")
                            result["errors"].append(error_msg)

            result["status"] = "success"
            result["files_deleted"] = files_deleted
            result["total_size_mb"] = total_size / (1024 * 1024)

            if dry_run:
                result["message"] = f"[DRY RUN] Would delete {files_deleted} file(s)"
            else:
                result["message"] = f"Deleted {files_deleted} file(s)"

        except Exception as e:
            logger.error(f"[{self.short_name.upper()}] Error: {str(e)}")
            result["status"] = "error"
            result["error"] = str(e)

        return result

    def _clean_log_directory(self, dry_run=False):
        """
        Clean log files from the io/log directory

        Args:
            dry_run (bool): If True, only report what would be deleted

        Returns:
            tuple: (files_deleted_count, total_size_deleted)
        """
        files_deleted = 0
        total_size_deleted = 0

        try:
            if not os.path.exists(self.log_dir):
                logger.debug(f"[{self.short_name.upper()}] Log directory does not exist: {self.log_dir}")
                return files_deleted, total_size_deleted

            logger.info(f"[{self.short_name.upper()}] Cleaning log directory: {self.log_dir}")

            # Process all files in log directory
            for file in os.listdir(self.log_dir):
                file_path = os.path.join(self.log_dir, file)

                # Skip if it's a directory
                if os.path.isdir(file_path):
                    continue

                # Skip protected files
                should_skip = False
                for protected_ext in self.protected_extensions:
                    if file.endswith(protected_ext):
                        should_skip = True
                        break

                if should_skip:
                    continue

                try:
                    # Get file size before deletion
                    file_size = os.path.getsize(file_path)
                    file_size_mb = file_size / (1024 * 1024)

                    if dry_run:
                        logger.info(f"[{self.short_name.upper()}] [DRY RUN] Would delete log: {file} ({file_size_mb:.2f} MB)")
                    else:
                        os.remove(file_path)
                        logger.info(f"[{self.short_name.upper()}] Deleted log: {file} ({file_size_mb:.2f} MB)")

                    files_deleted += 1
                    total_size_deleted += file_size

                except Exception as e:
                    logger.error(f"[{self.short_name.upper()}] Error deleting log file {file}: {str(e)}")

        except Exception as e:
            logger.error(f"[{self.short_name.upper()}] Error cleaning log directory: {str(e)}")

        return files_deleted, total_size_deleted

    def get_output_statistics(self):
        """
        Get statistics about files in the output directory without deleting

        Returns:
            dict: Statistics about the output directory
        """
        logger.info(f"[{self.short_name.upper()}] Gathering output directory statistics...")

        stats = {
            "total_files": 0,
            "total_size_bytes": 0,
            "total_size_mb": 0,
            "file_types": {},
            "orders": set(),
            "folders": []
        }

        try:
            if not os.path.exists(self.output_dir):
                logger.warning(f"[{self.short_name.upper()}] Output directory does not exist")
                return stats

            for root, dirs, files in os.walk(self.output_dir):
                # Track folders
                for dir_name in dirs:
                    rel_path = os.path.relpath(os.path.join(root, dir_name), self.output_dir)
                    stats["folders"].append(rel_path)

                # Track files
                for file in files:
                    file_path = os.path.join(root, file)

                    # Skip if it's actually a directory
                    if os.path.isdir(file_path):
                        continue

                    stats["total_files"] += 1

                    # Get file size
                    try:
                        file_size = os.path.getsize(file_path)
                        stats["total_size_bytes"] += file_size
                    except:
                        pass

                    # Track file types
                    ext = os.path.splitext(file)[1].lower()
                    if ext:
                        stats["file_types"][ext] = stats["file_types"].get(ext, 0) + 1

                    # Extract order name if present
                    if '_' in file:
                        order_name = file.split('_')[0]
                        if order_name.startswith('CO'):
                            stats["orders"].add(order_name)

            # Include log directory statistics
            if os.path.exists(self.log_dir):
                for file in os.listdir(self.log_dir):
                    file_path = os.path.join(self.log_dir, file)
                    if os.path.isfile(file_path):
                        stats["total_files"] += 1
                        file_size = os.path.getsize(file_path)
                        stats["total_size_bytes"] += file_size

                        # Track file extension
                        _, ext = os.path.splitext(file)
                        if ext:
                            stats["file_types"][ext] = stats["file_types"].get(ext, 0) + 1

            stats["total_size_mb"] = stats["total_size_bytes"] / (1024 * 1024)
            stats["orders"] = list(stats["orders"])

            logger.info(f"[{self.short_name.upper()}] Found {stats['total_files']} files ({stats['total_size_mb']:.2f} MB)")
            logger.info(f"[{self.short_name.upper()}] Orders: {len(stats['orders'])}")
            logger.info(f"[{self.short_name.upper()}] File types: {stats['file_types']}")

        except Exception as e:
            logger.error(f"[{self.short_name.upper()}] Error gathering statistics: {str(e)}")

        return stats
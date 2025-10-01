import logging
import sys
from agents.llm_agents.output_cleaner import OutputCleanerAgent

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)

def main():
    print("=" * 60)
    print("    TESTING OUTPUT CLEANER AGENT")
    print("=" * 60)
    print()

    # Create agent instance
    agent = OutputCleanerAgent()
    print(f"Agent created: {agent.name} (short: {agent.short_name})")
    print(f"Target directory: {agent.output_dir}")
    print()

    # First, get statistics about current output directory
    print("CURRENT OUTPUT DIRECTORY STATISTICS")
    print("-" * 60)
    stats = agent.get_output_statistics()
    print(f"Total files: {stats['total_files']}")
    print(f"Total size: {stats['total_size_mb']:.2f} MB")
    print(f"File types: {stats['file_types']}")
    print(f"Orders found: {stats['orders']}")
    print(f"Folders: {len(stats['folders'])}")
    print()

    # Perform dry run first
    print("PERFORMING DRY RUN (no files will be deleted)")
    print("-" * 60)
    dry_run_result = agent.clean_output_directory(dry_run=True)

    if dry_run_result["status"] == "success":
        print(f"Files that would be deleted: {dry_run_result['statistics']['files_deleted']}")
        print(f"Files that would be skipped: {dry_run_result['statistics']['files_skipped']}")
        print(f"Size that would be freed: {dry_run_result['statistics']['total_size_deleted_mb']:.2f} MB")
        print(f"Folders that would be preserved: {dry_run_result['statistics']['folders_preserved']}")

        if dry_run_result['deleted_files']:
            print("\nFiles to be deleted:")
            for file_info in dry_run_result['deleted_files'][:10]:  # Show first 10
                # Clean filename for display to avoid encoding issues
                safe_filename = file_info['file'].encode('ascii', 'replace').decode('ascii')
                print(f"  - {safe_filename} ({file_info['size_mb']:.2f} MB)")
            if len(dry_run_result['deleted_files']) > 10:
                print(f"  ... and {len(dry_run_result['deleted_files']) - 10} more files")
    print()

    # Ask user for confirmation
    print("=" * 60)
    response = input("Do you want to proceed with actual deletion? (yes/no): ").strip().lower()

    if response == 'yes':
        print("\nPROCEEDING WITH ACTUAL DELETION")
        print("-" * 60)

        # Perform actual cleaning
        result = agent.clean_output_directory(dry_run=False)

        if result["status"] == "success":
            print(f"[SUCCESS] {result['message']}")
            print(f"Files deleted: {result['statistics']['files_deleted']}")
            print(f"Files skipped: {result['statistics']['files_skipped']}")
            print(f"Space freed: {result['statistics']['total_size_deleted_mb']:.2f} MB")
            print(f"Folders preserved: {result['statistics']['folders_preserved']}")
        else:
            print(f"[ERROR] {result.get('error', 'Unknown error')}")

        if result.get('errors'):
            print("\nErrors encountered:")
            for error in result['errors']:
                print(f"  - {error}")
    else:
        print("\nCleaning cancelled by user")

    print()
    print("=" * 60)
    print("TESTING COMPLETE")
    print("=" * 60)

def test_specific_order_cleaning():
    """Test cleaning files for a specific order only"""
    print("\n" + "=" * 60)
    print("    TESTING SPECIFIC ORDER CLEANING")
    print("=" * 60)

    agent = OutputCleanerAgent()

    order_name = input("Enter order name to clean (e.g., CO25S006348): ").strip()

    if order_name:
        print(f"\nCleaning files for order: {order_name}")
        print("-" * 60)

        # Dry run first
        result = agent.clean_output_directory(dry_run=True, specific_order=order_name)

        if result["status"] == "success":
            print(f"Files found for {order_name}: {result['statistics']['files_deleted']}")

            if result['deleted_files']:
                print("\nFiles to be deleted:")
                for file_info in result['deleted_files']:
                    print(f"  - {file_info['file']}")

                response = input("\nProceed with deletion? (yes/no): ").strip().lower()

                if response == 'yes':
                    result = agent.clean_output_directory(dry_run=False, specific_order=order_name)
                    print(f"\n[SUCCESS] Deleted {result['statistics']['files_deleted']} files for order {order_name}")
                else:
                    print("\nCleaning cancelled")
            else:
                print(f"No files found for order {order_name}")

def test_file_type_cleaning():
    """Test cleaning specific file types only"""
    print("\n" + "=" * 60)
    print("    TESTING FILE TYPE SPECIFIC CLEANING")
    print("=" * 60)

    agent = OutputCleanerAgent()

    print("\nAvailable file types in output directory:")
    stats = agent.get_output_statistics()
    for ext, count in stats['file_types'].items():
        print(f"  {ext}: {count} file(s)")

    file_types = input("\nEnter file extensions to delete (comma-separated, e.g., .png,.json): ").strip()

    if file_types:
        extensions = [ext.strip() for ext in file_types.split(',')]
        print(f"\nCleaning file types: {extensions}")
        print("-" * 60)

        # Dry run first
        result = agent.clean_specific_file_types(extensions, dry_run=True)

        if result["status"] == "success":
            print(f"Files found: {result['files_deleted']}")
            print(f"Total size: {result['total_size_mb']:.2f} MB")

            if result['deleted_files']:
                print("\nFiles to be deleted:")
                for file_path in result['deleted_files'][:10]:
                    print(f"  - {file_path}")
                if len(result['deleted_files']) > 10:
                    print(f"  ... and {len(result['deleted_files']) - 10} more files")

                response = input("\nProceed with deletion? (yes/no): ").strip().lower()

                if response == 'yes':
                    result = agent.clean_specific_file_types(extensions, dry_run=False)
                    print(f"\n[SUCCESS] Deleted {result['files_deleted']} files")
                else:
                    print("\nCleaning cancelled")
            else:
                print("No files found with specified extensions")

if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1:
        if sys.argv[1] == '--specific':
            test_specific_order_cleaning()
        elif sys.argv[1] == '--types':
            test_file_type_cleaning()
        else:
            print("Usage: python test_output_cleaner.py [--specific|--types]")
    else:
        main()
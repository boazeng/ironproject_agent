"""
Initialize checkbox fields in all OCR JSON files
"""
import json
import os
import glob

# Path to OCR files
ocr_path = "io/fullorder_output/table_detection/table_ocr/"
pattern = os.path.join(ocr_path, "*.json")

print(f"Looking for OCR files in: {pattern}")
files = glob.glob(pattern)

for file_path in files:
    print(f"\nProcessing: {file_path}")

    try:
        # Load the JSON file
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)

        # Check if table_data and rows exist
        if 'table_data' in data and 'rows' in data['table_data']:
            rows = data['table_data']['rows']
            updated = False

            # Add checked field to each row if it doesn't exist
            for i, row in enumerate(rows):
                if 'checked' not in row:
                    row['checked'] = False
                    updated = True
                    print(f"  - Added 'checked' field to row {i+1}")

            if updated:
                # Save the file back
                with open(file_path, 'w', encoding='utf-8') as f:
                    json.dump(data, f, ensure_ascii=False, indent=2)
                print(f"  ✓ File updated successfully")
            else:
                print(f"  - All rows already have 'checked' field")
        else:
            print(f"  - No table_data or rows found in file")

    except Exception as e:
        print(f"  ✗ Error processing file: {e}")

print("\nDone! All OCR files have been initialized with checkbox fields.")
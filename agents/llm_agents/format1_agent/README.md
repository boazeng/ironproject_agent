# Format 1 Agent Pipeline

## Agents
- **order_format1_main.py** (`form1main`) - Main coordinator
- **order_format1_step1.py** (`form1s1`) - Step 1 processor
- **order_format1_step2.py** (`form1s2`) - Step 2 processor
- **form1s3.py** (`form1s3`) - Step 3 processor

## Step 1: First Page Extraction

**What it does:**
- Extracts the first page from PDF files
- Converts to PNG image at 300 DPI
- Saves to `io/fullorder_output/`

**Output files:**
- `{order_name}_page1.png` - Extracted page image
- `{order_name}_form1s1_result.json` - Metadata

## Step 2: Table Detection

**What it does:**
- Reads output from Step 1 (`_page1.png` files)
- Uses OpenCV to detect table boundaries
- Draws red rectangle around the detected table
- Saves result as `ordertable.png`

**Output files:**
- `ordertable.png` - Image with red table boundary
- `{order_name}_form1s2_result.json` - Table coordinates and metadata

## Step 3: Grid Line Detection

**What it does:**
- Reads output from Step 2 (`ordertable.png` with red bounding box)
- Detects the red bounding box using HSV color space
- Extracts the table region (ROI) inside the red box
- Uses Hough Line Transform to detect horizontal and vertical grid lines
- Filters lines to include only those spanning ≥95% of table dimensions
- Draws detected grid lines in thick green over the table

**Processing Steps:**
1. Load image and detect red bounding box (HSV thresholding)
2. Extract ROI (Region of Interest) inside the red box
3. Convert ROI to grayscale and apply Canny edge detection
4. Use cv2.HoughLinesP to detect straight lines
5. Filter lines:
   - Horizontal lines: must span ≥95% of table width
   - Vertical lines: must span ≥95% of table height
6. Draw accepted lines in green (color: (0,255,0), thickness: 2)
7. Save result with grid lines overlaid

**Output files:**
- `{input_name}_gridlines.png` - Image with green grid lines drawn over the table
- Processing results in JSON format with line coordinates and counts
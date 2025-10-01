# Format 1 Agent Pipeline

## Processing Flow

The Format 1 pipeline processes bent iron order PDFs through a series of specialized agents that extract, analyze, and digitize table data and shape information.

### Main Flow (Sequential Order):
```
PDF Input → Form1S1 → Form1S2 → Form1S3 → Form1S3.1 → Form1S3.2 → Form1S3.3 → Form1S4.1 → Form1S4 → Form1S5 → Form1Dat1
```

### Data Flow:
```
order.pdf → page images → table detection → gridlines → table body → OCR analysis → header extraction → shape columns → individual shapes → order title → central database
```

## Agent List & Descriptions

### **Form1S1Agent** (`form1s1`)
- **File:** `form1s1.py`
- **Purpose:** PDF to Image Conversion & Page Extraction
- Converts PDF pages to high-resolution PNG images (300 DPI)
- Extracts individual pages and saves them to order_to_image folder
- Copies original PDF to original_order folder for reference
- Creates initial metadata and stores general data in Form1Dat1 database
- **Output:** `{order}_page{N}.png` files

### **Form1S2Agent** (`form1s2`)
- **File:** `form1s2.py`
- **Purpose:** Table Boundary Detection
- Uses OpenCV to detect table boundaries in page images
- Applies morphological operations to find horizontal and vertical lines
- Draws red bounding box around detected table area
- Provides precise coordinates for table location on each page
- **Output:** `{order}_ordertable_page{N}.png` with red boundary

### **Form1S3Agent** (`form1s3`)
- **File:** `form1s3.py`
- **Purpose:** Grid Line Detection & Visualization
- Detects red bounding box from Form1S2 output using HSV color space
- Extracts table region of interest (ROI) inside the red box
- Uses Hough Line Transform to detect horizontal and vertical grid lines
- Filters lines that span ≥95% of table dimensions for accuracy
- **Output:** `{order}_ordertable_page{N}_gridlines.png` with green grid overlay

### **Form1S31Agent** (`form1s3_1.py`)
- **File:** `form1s3_1.py`
- **Purpose:** Table Body Extraction
- Processes gridlines images to extract clean table body content
- Detects and removes table headers using green line analysis
- Creates table_body (with headers) and table_bodyonly (clean data) versions
- Provides precise table dimensions and content boundaries
- **Output:** `{order}_table_body_page{N}.png`, `{order}_table_bodyonly_page{N}.png`

### **Form1S32Agent** (`form1s3_2.py`)
- **File:** `form1s3_2.py`
- **Purpose:** Table Row Count Analysis via ChatGPT
- Analyzes table_bodyonly images using ChatGPT Vision API
- Counts number of data rows and provides coordinates
- Distinguishes between header rows and actual order data
- Creates detailed analysis of table structure and content
- **Output:** `{order}_order_line_count_page{N}.json` with row analysis

### **Form1S3_3Agent** (`form1s3_3`)
- **File:** `form1s3_3.py`
- **Purpose:** Table Header Extraction
- Processes gridlines files to extract table header sections
- Uses green line detection to identify header boundaries
- Extracts header region above the second horizontal green line
- Provides clean header images for OCR processing
- **Output:** `{order}_table_header_page{N}.png`

### **Form1S4_1Agent** (`form1s4_1`)
- **File:** `form1s4_1.py`
- **Purpose:** Full Drawing Column Extraction
- Extracts complete drawing/shape columns from table_bodyonly images
- Detects vertical lines to identify column boundaries
- Finds widest gap between vertical lines (drawing column location)
- Uses full image height to ensure no rows are missed
- **Output:** `{order}_shape_column_page{N}.png`

### **Form1S4Agent** (`form1s4`)
- **File:** `form1s4.py`
- **Purpose:** Individual Shape Cell Extraction
- Processes shape_column images to extract individual drawing cells
- Uses green line detection to identify row boundaries (including first/last rows)
- Applies intensity and variance thresholds to skip empty cells
- Creates sequential numbering for actual shape-containing cells
- **Output:** `{order}_drawing_row_{N}_page{P}.png` for each shape

### **Form1S5Agent** (`form1s5`)
- **File:** `form1s5.py`
- **Purpose:** Order Title Extraction
- Extracts order title/header information from above the table area
- Detects red bounding box and extracts region above it
- Provides order title images for OCR and header analysis
- Creates metadata about title location and dimensions
- **Output:** `{order}_order_title_page{N}_order_header.png`

### **Form1OCR1Agent** (`form1ocr1`)
- **File:** `form1ocr1.py`
- **Purpose:** Table Content OCR Processing
- Performs OCR on table_bodyonly images to extract text data
- Uses OCR engines to read table cell contents
- Processes row and column data with text recognition
- Creates structured data from table text content
- **Output:** OCR text data in JSON format

### **Form1OCR2Agent** (`form1ocr2`)
- **File:** `form1ocr2.py`
- **Purpose:** Enhanced Table OCR with Format Detection
- Advanced OCR processing with table format recognition
- Handles complex table structures and formatting
- Provides improved accuracy for structured table data
- Includes error correction and validation for OCR results
- **Output:** Enhanced OCR data with format validation

### **Form1Dat1Agent** (`form1dat1_agent`)
- **File:** `form1dat1.py`
- **Purpose:** Central Database Management
- Consolidates all processing results into centralized JSON database
- Manages three main sections: general info, OCR data, shape analysis
- Integrates table OCR files and maintains data consistency
- Provides unified access to all order processing results
- **Output:** `{order}_analysis.json` (central database file)

### **UseAreaTableAgent** (`areatable`)
- **File:** `use_area_table.py`
- **Purpose:** User Area Table Processing (Manual Selection Support)
- Processes user-manually-selected table areas from PDF viewer
- Adds precise green grid lines showing row and column separators
- Uses Hough Line Transform for pixel-perfect line positioning
- Creates enhanced visualization of table structure for user verification
- **Output:** `{order}_table_area_page{N}_testout.png` with precise grid overlay

### **OrderFormat1MainAgent** (`form1main`)
- **File:** `order_format1_main.py`
- **Purpose:** Main Pipeline Coordinator
- Orchestrates the execution of Form1S1 step in the pipeline
- Manages file processing workflow and error handling
- Coordinates between different processing stages
- Provides overall pipeline status and result management
- **Output:** Workflow coordination and pipeline results

## Processing Directories

### Input/Output Structure:
```
io/input/                          # Source PDF files
io/fullorder_output/
├── order_to_image/               # Form1S1: Page images
├── original_order/               # Form1S1: Original PDFs
├── table_detection/
│   ├── grid/                     # Form1S2, Form1S3: Table detection & gridlines
│   ├── table/                    # Form1S3.1, Form1S3.2: Table body & analysis
│   ├── table_header/             # Form1S3.3: Header extraction
│   ├── shapes/                   # Form1S4: Individual shape cells
│   ├── shape_column/             # Form1S4.1: Full drawing columns
│   └── table_ocr/                # Form1OCR1, Form1OCR2: OCR results
├── user_saved_area/              # UseAreaTable: User manual selections
└── {order}_analysis.json         # Form1Dat1: Central database
```

## Key Technologies

- **OpenCV**: Image processing, line detection, morphological operations
- **Hough Line Transform**: Precise grid line detection
- **HSV Color Space**: Color-based detection (red boxes, green lines)
- **ChatGPT Vision API**: Intelligent table analysis and row counting
- **OCR Engines**: Text extraction from table cells
- **JSON Database**: Structured data storage and retrieval

## Integration Notes

- All agents are coordinated through `main_table_detection.py`
- Sequential processing ensures data dependency requirements
- Each agent validates input from previous stage
- Error handling maintains pipeline integrity
- Results are consolidated in Form1Dat1 central database
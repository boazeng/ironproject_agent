# Database Structure Documentation
# Form1Dat1 Agent - JSON Database Format
# File: {ordernumber}_out.json
# Location: io/fullorder_output/json_output/

===============================================
DATABASE STRUCTURE OVERVIEW
===============================================

The database consists of a single JSON file per order with two main sections:
- Section 1: General Data (populated by form1s1)
- Section 2: OCR Data (populated by form1ocr1)

===============================================
SECTION 1: GENERAL DATA
===============================================
Source Agent: form1s1
Purpose: Basic order information and metadata

Structure:
{
  "section_1_general": {
    "order_number": "string",      // Order identifier
    "date_created": "ISO datetime", // When the order was first created
    "date_modified": "ISO datetime", // Last modification timestamp
    "order_name": "string",        // Order name (same as order_number)
    "order_create_date": "ISO datetime", // When order processing started
    "number_of_pages": integer     // Total pages in the PDF document
  }
}

===============================================
SECTION 2: OCR DATA
===============================================
Source Agent: form1ocr1
Purpose: Extracted text fields from order header image

Structure:
{
  "section_2_ocr": {
    "לקוח/פרויקט": "string",       // Customer/Project name (Hebrew)
    "איש קשר באתר": "string",      // Site contact person (Hebrew)
    "טלפון": "string",             // Phone number (Hebrew)
    "כתובת האתר": "string",        // Site address (Hebrew)
    "תאריך הזמנה": "string",       // Order date (Hebrew)
    "מס הזמנה": "string",          // Order number (Hebrew)
    "תאריך אספקה": "string",       // Delivery date (Hebrew)
    "שם התוכנית": "string",        // Program name (Hebrew)
    "סה\"כ משקל": "string"         // Total weight (Hebrew)
  }
}

===============================================
SECTION 3: SHAPE ANALYSIS DATA
===============================================
Source Agent: TBD (future implementation)
Purpose: Detailed shape analysis data from order pages

Structure:
{
  "section_3_shape_analysis": {
    "page_1": {
      "page_number": integer,           // Page number
      "number_of_order_lines": integer, // Total order lines on this page
      "order_lines": {
        "line_1": {
          "line_number": integer,       // Line number on page
          "order_line_no": "string",    // Order line identifier
          "shape_description": "string", // Shape description/identifier
          "shape_catalog_number": "string", // Catalog number for the shape
          "number_of_ribs": integer,    // Total number of ribs in shape
          "diameter": "string",         // Shape diameter
          "number_of_units": integer,   // Number of units for this shape
          "ribs": {
            "rib_1": {
              "letter": "string",       // Rib identifier (A, B, C, etc.)
              "length": "string",       // Rib length measurement
              "angle_to_next": "string" // Angle to next rib
            },
            "rib_2": {
              "letter": "string",
              "length": "string",
              "angle_to_next": "string"
            }
            // Additional ribs as needed...
          }
        }
        // Additional lines as needed...
      }
    }
    // Additional pages as needed...
  }
}


===============================================
AGENT WORKFLOW
===============================================

1. form1s1 Agent:
   - Processes PDF file
   - Calls form1dat1.initialize_order(order_number)
   - Calls form1dat1.update_section("section_1_general", general_data)
   - Populates Section 1 with order metadata

2. form1ocr1 Agent:
   - Processes order header image with OCR
   - Calls form1dat1.store_ocr_data(order_number, ocr_data)
   - Populates Section 2 with extracted Hebrew fields

3. form1dat1 Agent:
   - Manages centralized database storage
   - Creates and maintains {ordernumber}_out.json files
   - Handles both sections in unified structure

===============================================
NOTES
===============================================

- All Hebrew text is stored in UTF-8 encoding
- Empty fields are marked as "empty" string
- Date fields use ISO 8601 format
- Order numbers follow pattern: CO25S######
- Database files are stored in: io/fullorder_output/json_output/

===============================================
FUTURE SECTIONS (PLANNED)
===============================================

Section 4: Measurements (future implementation)
Section 5: Processing Status (future implementation)

Currently Section 1, Section 2, and Section 3 structure are defined.
Section 3 implementation is pending.
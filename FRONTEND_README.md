# IRONMAN Frontend - Order Analysis Web Interface

## Overview
A web-based interface for the IRONMAN GLOBAL agent system that analyzes iron order documents.

## Features
- **Two-column layout**:
  - Left column: PDF viewer with zoom and navigation controls
  - Right column: Extracted data display with tabs
- **Run Analysis Button**: Execute main_global.py directly from the web interface
- **Real-time Updates**: Auto-refresh every 30 seconds
- **Hebrew/English Support**: RTL layout for Hebrew content

## Installation & Running

1. **Install dependencies** (if not already installed):
```bash
pip install flask flask-cors
```

2. **Start the web server**:
```bash
python app.py
```

3. **Open in browser**:
Navigate to: http://localhost:5000

## Usage

### Running Analysis
1. Click the **"הרץ ניתוח" (Run Analysis)** button in the header
2. The system will run `main_global.py` in the background
3. Results will automatically load when complete

### Viewing Results
- **Header Tab**: Shows order details (customer, order number, contact info)
- **Table Tab**: Displays iron order items in a table format
- **Raw Data Tab**: Shows the complete JSON analysis

### PDF Viewer Controls
- **Navigation**: Use ◀/▶ buttons to navigate pages
- **Zoom**: Use 🔍+/🔍- buttons to zoom in/out
- **Page Info**: Shows current page and total pages

## File Structure
```
├── app.py                 # Flask backend server
├── templates/
│   └── index.html        # Main HTML page
├── static/
│   ├── css/
│   │   └── style.css     # Styling
│   └── js/
│       └── app.js        # Frontend JavaScript
├── io/
│   ├── fullorder/        # Input PDF/image files
│   └── fullorder_output/ # Analysis results (JSON)
```

## API Endpoints

- `GET /` - Main web interface
- `POST /api/run-analysis` - Run main_global.py
- `GET /api/latest-analysis` - Get most recent analysis results
- `GET /api/status` - Check analysis status
- `GET /pdf/<filename>` - Serve PDF files
- `GET /api/files` - List available files
- `GET /api/analysis-history` - Get analysis history

## Notes
- Place PDF/image files in `io/fullorder/` directory
- Analysis results are saved to `io/fullorder_output/`
- The interface auto-refreshes every 30 seconds
- PDF.js library is used for PDF rendering
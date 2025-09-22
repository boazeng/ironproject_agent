// Global variables - CACHE BUST: 2025-09-21-23:20 - MANUAL TEST ADDED
let pdfDoc = null;
let pageNum = 1;
let pageRendering = false;
let pageNumPending = null;
let scale = 1.0;
let currentData = null;
let currentSelectedFile = null;

// Area selection variables
let isSelectingArea = false;
let selectionCanvas = null;
let selectionCtx = null;
let isDrawing = false;
let startX = 0;
let startY = 0;
let selectedAreas = [];

// Section selection variables
let currentSectionType = null;
let showDetectedAreas = false;
let sectionSelections = {
    order_header: null,
    table_header: null,
    table_area: null,
    shape_column: null
};

// Section colors for visual distinction
const sectionColors = {
    order_header: { stroke: '#dc3545', fill: 'rgba(220, 53, 69, 0.15)' },
    table_header: { stroke: '#fd7e14', fill: 'rgba(253, 126, 20, 0.15)' },
    table_area: { stroke: '#198754', fill: 'rgba(25, 135, 84, 0.15)' },
    shape_column: { stroke: '#6610f2', fill: 'rgba(102, 16, 242, 0.15)' }
};

// Initialize when page loads
document.addEventListener('DOMContentLoaded', function() {
    // Setup event listeners
    setupEventListeners();

    // Load initial data if available
    loadLatestAnalysis();

    // Update timestamp
    updateLastUpdateTime();

    // Initialize button visibility
    updateClearButtonVisibility();

    // Removed: Order header section display - not needed anymore

    // Initialize page displays
    setTimeout(() => {
        updatePageDisplays(1);
    }, 500);


});

// Setup all event listeners
function setupEventListeners() {
    // Run Analysis button
    document.getElementById('run-analysis').addEventListener('click', runAnalysis);
    
    // Refresh button
    document.getElementById('refresh-data').addEventListener('click', loadLatestAnalysis);
    
    // Tab buttons
    document.querySelectorAll('.tab-btn').forEach(btn => {
        btn.addEventListener('click', (e) => switchTab(e.target.dataset.tab));
    });
    
    // PDF controls
    document.getElementById('pdf-prev').addEventListener('click', onPrevPage);
    document.getElementById('pdf-next').addEventListener('click', onNextPage);
    document.getElementById('pdf-zoom-in').addEventListener('click', () => changeScale(0.2));
    document.getElementById('pdf-zoom-out').addEventListener('click', () => changeScale(-0.2));
    document.getElementById('area-select-btn').addEventListener('click', toggleAreaSelection);
    document.getElementById('clear-selections-btn').addEventListener('click', clearSelections);
    
    // Section selection buttons
    document.querySelectorAll('.btn-section').forEach(btn => {
        btn.addEventListener('click', (e) => selectSectionType(e.target.closest('.btn-section').dataset.section));
    });
    
    // Save sections button
    document.getElementById('save-sections-btn').addEventListener('click', saveSectionSelections);
    
    // Setup inline editing for header fields
    setupInlineEditing();
    
    // Header action buttons (removed)

    // Table save button removed

    // OCR button removed

    // Shapes re-detect button
    document.getElementById('redetect-shapes-btn').addEventListener('click', redetectShapes);

    // File selection
    document.getElementById('select-file-btn').addEventListener('click', showFileSelection);
    document.getElementById('close-file-modal').addEventListener('click', hideFileSelection);
    document.getElementById('cancel-file-selection').addEventListener('click', hideFileSelection);
    document.getElementById('confirm-file-selection').addEventListener('click', confirmFileSelection);
}

// Run the main_global analysis
async function runAnalysis() {
    const runBtn = document.getElementById('run-analysis');
    const status = document.getElementById('status');
    const processingStatus = document.getElementById('processing-status');
    
    // Update UI to show processing
    runBtn.disabled = true;
    runBtn.innerHTML = '<span class="loading"></span> מעבד...';
    status.textContent = 'מעבד';
    status.className = 'value status-processing';
    processingStatus.textContent = 'מריץ זיהוי טבלה...';
    
    try {
        // Prepare request body with selected filename
        const requestBody = {};
        if (currentSelectedFile) {
            requestBody.filename = currentSelectedFile;
        }
        
        // Call Flask endpoint to run analysis
        const response = await fetch('/api/run-analysis', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(requestBody)
        });
        
        const result = await response.json();

        if (result.success) {
            // Analysis started, now poll for completion
            processingStatus.textContent = 'מריץ זיהוי טבלה... אנא המתן';
            pollForCompletion();
        } else {
            // Error occurred
            throw new Error(result.error || 'שגיאה בהרצת הניתוח');
        }
    } catch (error) {
        console.error('Error running analysis:', error);
        status.textContent = 'שגיאה';
        status.className = 'value status-error';
        processingStatus.textContent = `שגיאה: ${error.message}`;

        // Reset button on error
        resetAnalysisButton();
    }
}

function pollForCompletion() {
    const checkStatus = async () => {
        try {
            const response = await fetch('/api/analysis-status');
            const statusData = await response.json();

            if (!statusData.running) {
                // Analysis completed
                if (statusData.last_result === 'success') {
                    // Success
                    const status = document.getElementById('status');
                    const processingStatus = document.getElementById('processing-status');

                    status.textContent = 'הושלם';
                    status.className = 'value status-ready';
                    processingStatus.textContent = 'זיהוי הטבלה הושלם בהצלחה!';

                    // Load the new data
                    setTimeout(() => {
                        loadLatestAnalysis();
                    }, 1000);
                } else if (statusData.last_result === 'error') {
                    // Error
                    const status = document.getElementById('status');
                    const processingStatus = document.getElementById('processing-status');

                    status.textContent = 'שגיאה';
                    status.className = 'value status-error';
                    processingStatus.textContent = `שגיאה: ${statusData.error || 'שגיאה לא ידועה'}`;
                }

                // Reset button
                resetAnalysisButton();

                // Clear status after 5 seconds
                setTimeout(() => {
                    document.getElementById('processing-status').textContent = '';
                }, 5000);
            } else {
                // Still running, check again in 1 second
                setTimeout(checkStatus, 1000);
            }
        } catch (error) {
            console.error('Error checking status:', error);
            resetAnalysisButton();
        }
    };

    checkStatus();
}

function resetAnalysisButton() {
    const runBtn = document.getElementById('run-analysis');
    runBtn.disabled = false;
    runBtn.innerHTML = '<span class="btn-icon">▶</span> הרץ ניתוח';
}

// Load latest analysis results
async function loadLatestAnalysis() {
    try {
        const response = await fetch('/api/latest-analysis');
        const data = await response.json();
        
        if (data && data.file) {
            currentData = data;
            displayAnalysisData(data);
            
            // Load PDF if available
            if (data.pdf_path) {
                loadPDF(data.pdf_path);
            }
            
            // Note: detected areas are only drawn when user explicitly toggles the בחירת איזור button
            
            // Update status
            document.getElementById('current-file').textContent = data.file;
            document.getElementById('files-processed').textContent = `קבצים שעובדו: 1`;
            updateLastUpdateTime();
        } else {
            // No data available
            document.getElementById('current-file').textContent = 'לא נמצאו נתונים';
            document.getElementById('processing-status').textContent = 'אין נתונים זמינים - הרץ ניתוח חדש';
        }
    } catch (error) {
        console.error('Error loading analysis:', error);
        document.getElementById('processing-status').textContent = 'שגיאה בטעינת נתונים';
    }
}

// Display analysis data in the UI
function displayAnalysisData(data) {
    // Update header info - prioritize data.analysis.sections as it contains complete key_values
    const sections = (data.analysis && data.analysis.sections) || data.sections;
    
    if (sections) {
        
        // Header section
        if (sections.header && sections.header.found) {
            const header = sections.header;
            document.getElementById('order-number').textContent = header.order_number || '-';
            document.getElementById('customer-name').textContent = header.customer || '-';
            document.getElementById('detail-order-number').value = header.order_number || '';
            document.getElementById('detail-customer').value = header.customer || '';
            
            // Extract more header details if available
            if (header.header_table && header.header_table.key_values) {
                console.log('Processing key_values:', header.header_table.key_values);
                header.header_table.key_values.forEach(kv => {
                    Object.entries(kv).forEach(([key, value]) => {
                        console.log(`Processing key: "${key}", value: "${value}"`);
                        if (key.includes('איש') && key.includes('קשר')) {
                            console.log('Setting contact:', value);
                            document.getElementById('detail-contact').value = value || '';
                        }
                        if (key.includes('טלפון')) {
                            console.log('Setting phone:', value);
                            document.getElementById('detail-phone').value = value || '';
                        }
                        if ((key.includes('כתובת') && key.includes('אתר')) || key.trim() === 'אתר') {
                            console.log('Setting address:', value);
                            document.getElementById('detail-address').value = value || '';
                        }
                        if (key === 'לקוח/פרויקט' || key.includes('לקוח')) {
                            console.log('Setting customer:', value);
                            document.getElementById('detail-customer').value = value || '';
                        }
                        if (key.includes('תוכנית') && !key.includes('לקוח') && !key.includes('פרויקט')) {
                            console.log('Setting program name:', value);
                            document.getElementById('detail-program-name').value = value || '';
                        }
                        if (key.includes('משקל')) {
                            console.log('Setting weight:', value);
                            document.getElementById('detail-weight').value = value || '';
                        }
                    });
                });
            }
        }

        // Process OCR data if available (prioritize over header data)
        if (data.ocr_data) {
            console.log('Processing OCR data:', data.ocr_data);
            const ocrData = data.ocr_data;

            // Map OCR fields to form fields with null checks
            if (ocrData['לקוח/פרויקט'] && ocrData['לקוח/פרויקט'] !== 'empty') {
                const customerEl = document.getElementById('detail-customer');
                const customerNameEl = document.getElementById('customer-name');
                if (customerEl) customerEl.value = ocrData['לקוח/פרויקט'];
                if (customerNameEl) customerNameEl.textContent = ocrData['לקוח/פרויקט'];
            }
            if (ocrData['איש קשר באתר'] && ocrData['איש קשר באתר'] !== 'empty') {
                const contactEl = document.getElementById('detail-contact');
                if (contactEl) contactEl.value = ocrData['איש קשר באתר'];
            }
            if (ocrData['טלפון'] && ocrData['טלפון'] !== 'empty') {
                const phoneEl = document.getElementById('detail-phone');
                if (phoneEl) phoneEl.value = ocrData['טלפון'];
            }
            if (ocrData['כתובת האתר'] && ocrData['כתובת האתר'] !== 'empty') {
                const addressEl = document.getElementById('detail-address');
                if (addressEl) addressEl.value = ocrData['כתובת האתר'];
            }
            if (ocrData['מס הזמנה'] && ocrData['מס הזמנה'] !== 'empty') {
                const orderNumEl = document.getElementById('detail-order-number');
                const orderDisplayEl = document.getElementById('order-number');
                if (orderNumEl) orderNumEl.value = ocrData['מס הזמנה'];
                if (orderDisplayEl) orderDisplayEl.textContent = ocrData['מס הזמנה'];
            }
            if (ocrData['שם התוכנית'] && ocrData['שם התוכנית'] !== 'empty') {
                const programEl = document.getElementById('detail-program-name');
                if (programEl) programEl.value = ocrData['שם התוכנית'];
            }
            if (ocrData['סה"כ משקל'] && ocrData['סה"כ משקל'] !== 'empty') {
                const weightEl = document.getElementById('detail-weight');
                if (weightEl) weightEl.value = ocrData['סה"כ משקל'];
            }
            if (ocrData['תאריך הזמנה'] && ocrData['תאריך הזמנה'] !== 'empty') {
                const orderDateEl = document.getElementById('detail-order-date');
                if (orderDateEl) orderDateEl.value = ocrData['תאריך הזמנה'];
            }
            if (ocrData['תאריך אספקה'] && ocrData['תאריך אספקה'] !== 'empty') {
                const deliveryDateEl = document.getElementById('detail-delivery-date');
                if (deliveryDateEl) deliveryDateEl.value = ocrData['תאריך אספקה'];
            }

            console.log('OCR data has been populated to form fields');

            // Removed: showOrderHeaderSection() call
        }
            
            // Display order header image for page 1
            const headerImage = document.getElementById('order-header-image');
            if (headerImage && data.file) {
                // Extract the order number from the filename
                const orderNumber = data.file.replace('.pdf', '');
                // Always use page 1 header image
                const headerImageUrl = `/order_header_image/${orderNumber}_order_title_page1_order_header.png`;

                headerImage.onerror = function() {
                    console.log('Header image not found, trying alternative path...');
                    // Fallback to the default image if specific one not found
                    this.src = '/order_header_image/CO25S006375_order_title_page1_order_header.png';
                };

                headerImage.src = headerImageUrl;
                console.log('🖼️ Loading header image:', headerImageUrl);
            }

        // Table section
        if (sections.main_table && sections.main_table.found) {
            const table = sections.main_table;
            document.getElementById('total-rows').textContent = table.row_count || 0;
            document.getElementById('order-type').textContent = 
                table.contains_iron_orders ? 'הזמנת ברזל' : 'אחר';
            
            // Populate table with sample items
            const tbody = document.getElementById('items-tbody');
            tbody.innerHTML = '';
            
            // Use all_items if available, otherwise fall back to sample_items
            const items = table.all_items || table.sample_items || [];
            if (items.length > 0) {
                let totalWeight = 0;
                
                items.forEach((item, index) => {
                    const row = tbody.insertRow();
                    row.setAttribute('data-row-id', index);
                    
                    // Expand button
                    const expandCell = row.insertCell(0);
                    expandCell.innerHTML = '<button class="expand-btn" onclick="toggleRow(' + index + ')">+</button>';
                    
                    // Handle both array format and object format
                    if (Array.isArray(item)) {
                        // Array format: [מס', סה"כ משקל, אורך, סה"כ יח', קוטר, הערות]
                        row.insertCell(1).textContent = item[0] || (index + 1);  // מס'
                        row.insertCell(2).textContent = '-';  // מספר קטלוגי - not available in array format
                        row.insertCell(3).textContent = item[4] || '-';  // קוטר [mm]
                        row.insertCell(4).textContent = item[3] || '1';  // סה"כ יח'
                        row.insertCell(5).textContent = item[2] || '-';  // אורך [m]

                        const weight = parseFloat(item[1] || '0');
                        row.insertCell(6).textContent = weight || '-';  // סה"כ משקל [kg]
                        totalWeight += weight;

                        row.insertCell(7).textContent = item[5] || '-';  // הערות
                    } else {
                        // Object format (fallback)
                        row.insertCell(1).textContent = item['מס\''] || item['מס'] || (index + 1);
                        row.insertCell(2).textContent = item['מספר קטלוגי'] || item['catalog'] || '-';
                        row.insertCell(3).textContent = item['קוטר'] || item['קוטר [mm]'] || '-';
                        row.insertCell(4).textContent = item['יחידות'] || item['units'] || item['כמות'] || item['סה"כ יח\''] || '1';
                        row.insertCell(5).textContent = item['אורך'] || item['אורך [m]'] || '-';

                        const weight = parseFloat(item['סה"כ משקל'] || item['סה"כ משקל [kg]'] || '0');
                        row.insertCell(6).textContent = weight || '-';
                        totalWeight += weight;

                        row.insertCell(7).textContent = item['הערות'] || '-';
                    }
                });
                
                // Update total weight
                document.getElementById('total-weight').textContent = totalWeight.toFixed(1) + ' kg';
            } else {
                tbody.innerHTML = '<tr><td colspan="8" class="no-data">אין נתונים להצגה</td></tr>';
            }
        }
    }

    // Shapes section
    displayShapes(data);
    
    // Raw JSON display
    document.getElementById('raw-json').textContent = JSON.stringify(data, null, 2);
}

// Load and display PDF
async function loadPDF(pdfPath) {
    try {
        // Show canvas, hide placeholder
        document.getElementById('pdf-canvas').style.display = 'block';
        document.getElementById('pdf-placeholder').style.display = 'none';
        
        // Load PDF document
        const loadingTask = pdfjsLib.getDocument(pdfPath);
        pdfDoc = await loadingTask.promise;
        
        // Update page count
        const pageCountElement = document.getElementById('page-count');
        if (pageCountElement) {
            pageCountElement.textContent = pdfDoc.numPages;
        }
        
        // Initial page rendering
        renderPage(pageNum);
    } catch (error) {
        console.error('Error loading PDF:', error);
        document.getElementById('pdf-canvas').style.display = 'none';
        document.getElementById('pdf-placeholder').style.display = 'block';
        document.getElementById('pdf-placeholder').innerHTML = 
            '<p>❌ שגיאה בטעינת PDF</p><p>' + error.message + '</p>';
    }
}

// Render specific page of PDF
function renderPage(num) {
    pageRendering = true;
    
    pdfDoc.getPage(num).then(function(page) {
        const canvas = document.getElementById('pdf-canvas');
        const ctx = canvas.getContext('2d');
        const viewport = page.getViewport({scale: scale});
        
        canvas.height = viewport.height;
        canvas.width = viewport.width;
        
        const renderContext = {
            canvasContext: ctx,
            viewport: viewport
        };
        
        const renderTask = page.render(renderContext);
        
        renderTask.promise.then(function() {
            pageRendering = false;
            if (pageNumPending !== null) {
                renderPage(pageNumPending);
                pageNumPending = null;
            }
            
            // Update selection canvas size after PDF rendering
            updateSelectionCanvasSize();
            
            // Redraw existing user selections
            drawExistingSelections();
            
            // Draw detected areas only if explicitly enabled by user
            if (showDetectedAreas) {
                setTimeout(() => drawDetectedAreas(), 50); // Small delay to ensure canvas is ready
            }
        });
    });
    
    // Update page info
    const pageNumElement = document.getElementById('page-num');
    if (pageNumElement) {
        pageNumElement.textContent = num;
    }

    // Update current page display in table section and title
    updatePageDisplays(num);
}

// Queue page rendering
function queueRenderPage(num) {
    if (pageRendering) {
        pageNumPending = num;
    } else {
        renderPage(num);
    }
}

// Previous page
function onPrevPage() {
    if (pageNum <= 1) {
        return;
    }
    pageNum--;
    queueRenderPage(pageNum);
}

// Next page
function onNextPage() {
    if (pageNum >= pdfDoc.numPages) {
        return;
    }
    pageNum++;
    queueRenderPage(pageNum);
}

// Change zoom scale
function changeScale(delta) {
    scale = Math.max(0.5, Math.min(3.0, scale + delta));
    if (pdfDoc) {
        queueRenderPage(pageNum);
    }
}

// Switch between tabs
function switchTab(tabName) {
    // Update tab buttons
    document.querySelectorAll('.tab-btn').forEach(btn => {
        btn.classList.toggle('active', btn.dataset.tab === tabName);
    });
    
    // Update tab content
    document.querySelectorAll('.tab-content').forEach(content => {
        content.classList.toggle('active', content.id === `${tabName}-tab`);
    });
}

// Update page displays
function updatePageDisplays(pageNumber) {
    // Update the title page display
    const titlePageDisplay = document.getElementById('title-page-display');
    if (titlePageDisplay) {
        titlePageDisplay.textContent = `עמוד ${pageNumber}`;
    }

    // Update table data for current page
    updateTableForCurrentPage(pageNumber);
}

// Filter and display table OCR data for specific page
function updateTableForCurrentPage(pageNumber) {
    // Fetch table OCR data from the new API endpoint
    fetch(`/api/table-ocr/${pageNumber}`)
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                // Transform the OCR data format to match our table structure
                const transformedItems = data.rows.map(row => ({
                    'מס': row['מס'] || row['row_number'] || '',
                    'shape': row['shape'] || '-', // Shape information for צורה column
                    'קוטר': row['קוטר'] || '-',
                    'סהכ יחידות': row['סהכ יחידות'] || '-',
                    'אורך': row['אורך'] || '-',
                    'משקל': row['משקל'] || '-',
                    'הערות': row['הערות'] || '-',
                    'checked': false  // Default to unchecked initially
                }));

                displayTableItems(transformedItems, pageNumber);
            } else {

                // Fallback to existing data structure for backward compatibility
                if (currentData && currentData.table) {
                    const table = currentData.table;
                    let pageItems = [];

                    // Check if we have page-specific data structure
                    if (table.pages && table.pages[pageNumber]) {
                        pageItems = table.pages[pageNumber].items || [];
                    } else if (table.all_items && Array.isArray(table.all_items)) {
                        pageItems = table.all_items.filter(item => {
                            if (item.page === pageNumber) return true;
                            if (Array.isArray(item) && item.length > 6 && item[6] === pageNumber) return true;
                            return false;
                        });

                        if (pageItems.length === 0 && pageNumber === 1) {
                            pageItems = table.all_items;
                        }
                    } else if (pageNumber === 1) {
                        pageItems = table.sample_items || [];
                    }

                    displayTableItems(pageItems, pageNumber);
                } else {
                    // No data available
                    displayTableItems([], pageNumber);
                }
            }
        })
        .catch(error => {
            console.error(`❌ Error fetching table OCR data for page ${pageNumber}:`, error);
            // Fallback to empty data
            displayTableItems([], pageNumber);
        });
}

// Display table items in the UI
function displayTableItems(items, pageNumber) {
    const tbody = document.getElementById('items-tbody');
    if (!tbody) {
        console.log('❌ Table body not found');
        return;
    }

    tbody.innerHTML = '';

    if (items.length > 0) {
        let totalWeight = 0;
        console.log(`📊 Displaying ${items.length} items for page ${pageNumber}`);

        items.forEach((item, index) => {
            const row = tbody.insertRow();
            row.setAttribute('data-row-id', index);
            row.setAttribute('data-page', pageNumber);

            // Expand button
            const expandCell = row.insertCell(0);
            expandCell.innerHTML = '<button class="expand-btn" onclick="toggleRow(' + index + ')">+</button>';

            // Create editable cells
            function createEditableCell(value, fieldName) {
                const cell = row.insertCell();
                const input = document.createElement('input');
                input.type = 'text';
                input.value = value || '-';
                input.className = 'table-editable';
                input.style.cssText = 'width: 100%; border: none; background: transparent; padding: 2px 4px; font-size: 13px;';
                input.setAttribute('data-field', fieldName);
                input.setAttribute('data-row-id', index);
                input.setAttribute('data-original-value', value || '-');

                // Add event listeners for editing
                input.addEventListener('focus', function() {
                    this.style.background = '#f0f8ff';
                    this.select();
                });

                input.addEventListener('blur', function() {
                    this.style.background = 'transparent';
                    if (this.value !== this.getAttribute('data-original-value')) {
                        saveTableCell(pageNumber, index, fieldName, this.value);
                        this.setAttribute('data-original-value', this.value);
                    }
                });

                input.addEventListener('keypress', function(e) {
                    if (e.key === 'Enter') {
                        this.blur();
                    }
                });

                cell.appendChild(input);
                return cell;
            }

            // Handle both array format and object format
            if (Array.isArray(item)) {
                // Array format: [מס', סה"כ משקל, אורך, סה"כ יח', קוטר, הערות]
                createEditableCell(item[0] || (index + 1), 'מס');
                createEditableCell('-', 'shape');  // צורה - not available in array format
                createEditableCell(item[4] || '-', 'קוטר');
                createEditableCell(item[3] || '1', 'סהכ יחידות');
                createEditableCell(item[2] || '-', 'אורך');

                const weight = parseFloat(item[1] || '0');
                createEditableCell(weight || '-', 'משקל');
                totalWeight += weight;

                createEditableCell(item[5] || '-', 'הערות');
            } else {
                // Object format - now handles OCR data structure properly
                createEditableCell(item['מס'] || item['מס\''] || (index + 1), 'מס');
                createEditableCell(item['shape'] || item['צורה'] || '-', 'shape');
                createEditableCell(item['קוטר'] || '-', 'קוטר');
                createEditableCell(item['סהכ יחידות'] || item['יחידות'] || item['units'] || item['כמות'] || '1', 'סהכ יחידות');
                createEditableCell(item['אורך'] || '-', 'אורך');

                const weight = parseFloat(item['משקל'] || item['סה"כ משקל'] || '0');
                createEditableCell(weight || '-', 'משקל');
                totalWeight += weight;

                createEditableCell(item['הערות'] || '-', 'הערות');
            }

            // Add check button cell
            const checkCell = row.insertCell();
            let checked = item['checked'] || false;

            const checkButton = document.createElement('button');
            checkButton.className = 'check-btn';
            checkButton.style.cssText = `
                width: 30px;
                height: 30px;
                border: 2px solid ${checked ? '#28a745' : '#ccc'};
                background: ${checked ? '#28a745' : 'transparent'};
                color: ${checked ? 'white' : '#666'};
                border-radius: 4px;
                cursor: pointer;
                font-weight: bold;
                font-size: 16px;
                display: flex;
                align-items: center;
                justify-content: center;
            `;
            checkButton.textContent = checked ? '✓' : '';
            checkButton.title = checked ? 'הסר סימון' : 'סמן כבדוק';
            checkButton.setAttribute('data-checked', checked);

            checkButton.addEventListener('click', function() {
                const currentChecked = this.getAttribute('data-checked') === 'true';
                const newChecked = !currentChecked;
                toggleCheckStatus(pageNumber, index + 1, newChecked, this);
                this.setAttribute('data-checked', newChecked);
            });

            checkCell.appendChild(checkButton);
            checkCell.style.textAlign = 'center';
        });

        // Update total weight and row count
        document.getElementById('total-weight').textContent = totalWeight.toFixed(1) + ' kg';
        document.getElementById('total-rows').textContent = items.length;

        console.log(`✅ Table updated: ${items.length} items, total weight: ${totalWeight.toFixed(1)} kg`);

        // Initialize row lock states after table is rendered
        setTimeout(() => {
            initializeRowLockStates();
        }, 100);
    } else {
        tbody.innerHTML = '<tr><td colspan="9" class="no-data">אין נתונים להצגה עבור עמוד ' + pageNumber + '</td></tr>';
        document.getElementById('total-weight').textContent = '0 kg';
        document.getElementById('total-rows').textContent = '0';
        console.log(`📄 No data to display for page ${pageNumber}`);
    }
}

// Toggle check status for a line
async function toggleCheckStatus(pageNumber, lineNumber, checked, buttonElement) {
    try {
        // Get the current order number
        const orderNumber = getCurrentOrderNumber();
        if (!orderNumber) {
            alert('לא נמצא מספר הזמנה');
            return;
        }

        // Get the current row data from screen
        const row = buttonElement.closest('tr');
        const rowData = {};

        // Extract data from all input fields in this row
        const inputs = row.querySelectorAll('input[data-field]');
        inputs.forEach(input => {
            const fieldName = input.getAttribute('data-field');
            let value = input.value;

            // Convert numeric fields to proper types
            if (fieldName === 'משקל' || fieldName === 'קוטר' || fieldName === 'סהכ יחידות') {
                const numValue = parseFloat(value);
                value = !isNaN(numValue) ? numValue : value;
            }

            rowData[fieldName] = value;
        });

        // Update button appearance immediately for better UX
        buttonElement.style.border = `2px solid ${checked ? '#28a745' : '#ccc'}`;
        buttonElement.style.background = checked ? '#28a745' : 'transparent';
        buttonElement.style.color = checked ? 'white' : '#666';
        buttonElement.textContent = checked ? '✓' : '';
        buttonElement.title = checked ? 'הסר סימון' : 'סמן כבדוק';

        // Send update to server with current screen data
        const response = await fetch('/api/update-checked-status', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                orderNumber: orderNumber,
                pageNumber: pageNumber,
                lineNumber: lineNumber,
                checked: checked,
                rowData: rowData  // Add the current screen data
            })
        });

        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }

        const result = await response.json();

        if (!result.success) {
            // Revert button appearance if update failed
            buttonElement.style.border = `2px solid ${!checked ? '#28a745' : '#ccc'}`;
            buttonElement.style.background = !checked ? '#28a745' : 'transparent';
            buttonElement.style.color = !checked ? 'white' : '#666';
            buttonElement.textContent = !checked ? '✓' : '';
            buttonElement.title = !checked ? 'הסר סימון' : 'סמן כבדוק';

            alert('שגיאה בעדכון סטטוס הבדיקה: ' + result.error);
        } else {
            // Success: Lock/unlock the row inputs based on checked status
            toggleRowLock(row, checked);
        }

    } catch (error) {
        console.error('Error updating check status:', error);

        // Revert button appearance if update failed
        buttonElement.style.border = `2px solid ${!checked ? '#28a745' : '#ccc'}`;
        buttonElement.style.background = !checked ? '#28a745' : 'transparent';
        buttonElement.style.color = !checked ? 'white' : '#666';
        buttonElement.textContent = !checked ? '✓' : '';
        buttonElement.title = !checked ? 'הסר סימון' : 'סמן כבדוק';

        alert('שגיאה בעדכון סטטוס הבדיקה');
    }
}

// Toggle row input fields lock/unlock based on checkbox status
function toggleRowLock(row, isLocked) {
    // Find all input fields in this row
    const inputs = row.querySelectorAll('input[data-field]');

    inputs.forEach(input => {
        if (isLocked) {
            // Lock the row: disable inputs and add visual styling
            input.disabled = true;
            input.style.backgroundColor = '#f8f9fa';
            input.style.borderColor = '#e9ecef';
            input.style.color = '#6c757d';
            input.style.cursor = 'not-allowed';
        } else {
            // Unlock the row: enable inputs and restore normal styling
            input.disabled = false;
            input.style.backgroundColor = '';
            input.style.borderColor = '';
            input.style.color = '';
            input.style.cursor = '';
        }
    });

    // Add/remove locked class to the entire row for additional styling
    if (isLocked) {
        row.classList.add('row-locked');
    } else {
        row.classList.remove('row-locked');
    }
}

// Get current order number from analysis file
function getCurrentOrderNumber() {
    // Get the current order number from current analysis file
    if (currentData?.file) {
        return currentData.file.replace('.pdf', '');
    }

    // Try to get from header display as fallback
    const orderElement = document.getElementById('order-number');
    if (orderElement && orderElement.textContent !== '-') {
        return orderElement.textContent;
    }

    // Try to get from detail input as fallback
    const orderDetailElement = document.getElementById('detail-order-number');
    if (orderDetailElement && orderDetailElement.value !== '-' && orderDetailElement.value !== '') {
        return orderDetailElement.value;
    }

    // Final fallback
    return 'CO25S006375';
}

// Update last update time
function updateLastUpdateTime() {
    const now = new Date();
    const timeStr = now.toLocaleTimeString('he-IL');
    const dateStr = now.toLocaleDateString('he-IL');
    document.getElementById('last-update').textContent = `עדכון אחרון: ${dateStr} ${timeStr}`;
}

// Toggle row expansion for rib details
function toggleRow(rowId) {
    const tbody = document.getElementById('items-tbody');
    const row = tbody.querySelector(`tr[data-row-id="${rowId}"]`);
    const expandBtn = row.querySelector('.expand-btn');
    const existingExpanded = tbody.querySelector(`tr[data-expanded-for="${rowId}"]`);
    
    if (existingExpanded) {
        // Collapse - remove expanded row
        existingExpanded.remove();
        expandBtn.textContent = '+';
        expandBtn.classList.remove('expanded');
    } else {
        // Expand - create new row with rib details
        const expandedRow = tbody.insertRow(row.rowIndex);
        expandedRow.classList.add('expanded-row');
        expandedRow.setAttribute('data-expanded-for', rowId);
        
        const expandedCell = expandedRow.insertCell(0);
        expandedCell.colSpan = 8;
        
        // Create rib details table
        expandedCell.innerHTML = `
            <div class="rib-header">פירוט צלעות - פריט #${rowId + 1}</div>
            <table class="rib-details">
                <thead>
                    <tr>
                        <th>צלע #</th>
                        <th>אורך צלע (cm)</th>
                        <th>זוית לצלע הבאה (°)</th>
                    </tr>
                </thead>
                <tbody>
                    ${generateRibDetails(rowId)}
                </tbody>
            </table>
        `;
        
        expandBtn.textContent = '−';
        expandBtn.classList.add('expanded');
    }
}

// Generate rib details (mock data for now - will be replaced with real data)
function generateRibDetails(rowId) {
    // For demonstration, create 8 ribs with sample data
    let ribHtml = '';
    for (let i = 1; i <= 8; i++) {
        const length = Math.floor(Math.random() * 100) + 10; // Random length 10-110 cm
        const angle = i < 8 ? (Math.floor(Math.random() * 3) + 1) * 90 : null; // 90°, 180°, or 270° (null for last rib)
        
        ribHtml += `
            <tr>
                <td>${i}</td>
                <td>${length}</td>
                <td>${angle || '-'}</td>
            </tr>
        `;
    }
    return ribHtml;
}

// Setup inline editing functionality
function setupInlineEditing() {
    // Get all editable input fields
    const editableFields = document.querySelectorAll('.data-editable');
    
    editableFields.forEach(field => {
        // Store original value when field gets focus
        field.addEventListener('focus', function() {
            this.dataset.originalValue = this.value;
            this.classList.add('editing');
        });
        
        // Save changes when field loses focus
        field.addEventListener('blur', function() {
            this.classList.remove('editing');
            if (this.value !== this.dataset.originalValue) {
                saveFieldChange(this);
            }
        });
        
        // Also save on Enter key
        field.addEventListener('keypress', function(e) {
            if (e.key === 'Enter') {
                this.blur();
            }
        });
    });
}

// Save individual field change
function saveFieldChange(field) {
    const fieldName = field.dataset.field;
    const newValue = field.value;
    
    // Show saving state
    field.classList.add('saving');
    
    // Update header info at top of page if applicable
    if (fieldName === 'orderNumber') {
        document.getElementById('order-number').textContent = newValue || '-';
    } else if (fieldName === 'customer') {
        document.getElementById('customer-name').textContent = newValue || '-';
    }
    
    // Prepare data for server
    const headerData = {};
    headerData[fieldName] = newValue;
    
    // Save to server
    saveHeaderToServer(headerData).then(() => {
        field.classList.remove('saving');
        field.classList.add('saved');
        
        // Remove saved indicator after 2 seconds
        setTimeout(() => {
            field.classList.remove('saved');
        }, 2000);
        
        // Show success message briefly
        const saveStatus = document.getElementById('save-status');
        if (saveStatus) {
            saveStatus.textContent = 'נשמר ✓';
            saveStatus.style.color = '#10b981';
            setTimeout(() => {
                saveStatus.textContent = '';
            }, 2000);
        }
    }).catch((error) => {
        field.classList.remove('saving');
        console.error('Save failed:', error);
        
        // Show error message
        const saveStatus = document.getElementById('save-status');
        if (saveStatus) {
            saveStatus.textContent = 'שגיאה בשמירה ✗';
            saveStatus.style.color = '#ef4444';
            setTimeout(() => {
                saveStatus.textContent = '';
            }, 3000);
        }
    });
}

async function saveHeaderToServer(headerData) {
    try {
        const response = await fetch('/api/update-header', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(headerData)
        });
        
        const result = await response.json();
        if (result.success) {
            console.log('Header data saved to server');
            return result;
        } else {
            throw new Error(result.error || 'Failed to save header data');
        }
    } catch (error) {
        console.error('Error saving header data:', error);
        throw error;
    }
}

// Clear header data
function clearHeaderData() {
    // Clear all input fields
    document.getElementById('detail-order-number').value = '';
    document.getElementById('detail-customer').value = '';
    document.getElementById('detail-program-name').value = '';
    document.getElementById('detail-contact').value = '';
    document.getElementById('detail-phone').value = '';
    document.getElementById('detail-address').value = '';
    document.getElementById('detail-weight').value = '';
    document.getElementById('detail-order-date').value = '';
    document.getElementById('detail-delivery-date').value = '';
    
    // Clear header info at top
    document.getElementById('order-number').textContent = '-';
    document.getElementById('customer-name').textContent = '-';
    
    // Save cleared data to server
    const clearedData = {
        orderNumber: '',
        customer: '',
        programName: '',
        contact: '',
        phone: '',
        address: '',
        weight: ''
    };
    
    saveHeaderToServer(clearedData).then(() => {
        // Show success message
        document.getElementById('processing-status').textContent = 'נתוני הכותרת נוקו בהצלחה';
        setTimeout(() => {
            document.getElementById('processing-status').textContent = '';
        }, 3000);
    }).catch(() => {
        // Show error message
        document.getElementById('processing-status').textContent = 'שגיאה בניקוי נתוני הכותרת';
        setTimeout(() => {
            document.getElementById('processing-status').textContent = '';
        }, 3000);
    });
}

// Re-detect header data by running analysis again
async function redetectHeader() {
    const redetectBtn = document.getElementById('redetect-header-btn');
    const originalContent = redetectBtn.innerHTML;
    
    // Update button to show processing
    redetectBtn.disabled = true;
    redetectBtn.innerHTML = '<span class="loading"></span> מנתח...';
    
    // Show processing status
    document.getElementById('processing-status').textContent = 'מריץ ניתוח מתמחה לכותרת הזמנה...';
    
    try {
        // Call the OrderHeader agent API
        const response = await fetch('/api/analyze-order-header', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            }
        });
        
        const result = await response.json();
        
        if (result.success) {
            console.log('OrderHeader agent result:', result.agent_result);
            
            // Process the extracted fields from the agent
            const agentResult = result.agent_result;
            
            if (agentResult.extracted_fields && agentResult.extracted_fields.length > 0) {
                // Update the UI with the newly extracted fields
                agentResult.extracted_fields.forEach(fieldObj => {
                    Object.entries(fieldObj).forEach(([key, value]) => {
                        console.log(`OrderHeader extracted: "${key}" = "${value}"`);
                        
                        // Map the exact fields that OrderHeader agent returns
                        if (key === 'מספר הזמנה' || key.includes('הזמנה')) {
                            console.log('Setting order number from OrderHeader:', value);
                            document.getElementById('detail-order-number').value = value || '';
                        }
                        else if (key === 'לקוח/פרויקט' || key.includes('לקוח')) {
                            console.log('Setting customer from OrderHeader:', value);
                            document.getElementById('detail-customer').value = value || '';
                        }
                        else if (key === 'שם התוכנית' || (key.includes('תוכנית') && !key.includes('לקוח') && !key.includes('פרויקט'))) {
                            console.log('Setting program name from OrderHeader:', value);
                            document.getElementById('detail-program-name').value = value || '';
                        }
                        else if (key === 'איש קשר' || (key.includes('איש') && key.includes('קשר'))) {
                            console.log('Setting contact from OrderHeader:', value);
                            document.getElementById('detail-contact').value = value || '';
                        }
                        else if (key === 'טלפון' || key.includes('טלפון')) {
                            console.log('Setting phone from OrderHeader:', value);
                            document.getElementById('detail-phone').value = value || '';
                        }
                        else if (key === 'כתובת האתר' || (key.includes('כתובת') && key.includes('אתר'))) {
                            console.log('Setting address from OrderHeader:', value);
                            document.getElementById('detail-address').value = value || '';
                        }
                        else if (key === 'משקל כולל' || key.includes('משקל')) {
                            console.log('Setting weight from OrderHeader:', value);
                            document.getElementById('detail-weight').value = value || '';
                        }
                    });
                });
                
                document.getElementById('processing-status').textContent = `ניתוח הכותרת הושלם בהצלחה! נמצאו ${agentResult.field_count} שדות`;
            } else {
                document.getElementById('processing-status').textContent = 'ניתוח הכותרת הושלם, אך לא נמצאו שדות חדשים';
            }
            
            // Removed: Header image reload logic - not needed anymore
            
        } else {
            throw new Error(result.error || 'ניתוח הכותרת נכשל');
        }
        
        // Clear status after delay
        setTimeout(() => {
            document.getElementById('processing-status').textContent = '';
        }, 4000);
        
    } catch (error) {
        console.error('Error in OrderHeader analysis:', error);
        document.getElementById('processing-status').textContent = `שגיאה בניתוח הכותרת: ${error.message}`;
        setTimeout(() => {
            document.getElementById('processing-status').textContent = '';
        }, 5000);
    } finally {
        // Reset button
        redetectBtn.disabled = false;
        redetectBtn.innerHTML = originalContent;
    }
}

async function runOCRAnalysis() {
    const ocrBtn = document.getElementById('run-ocr-btn');
    const originalContent = ocrBtn.innerHTML;

    try {
        // Update button to show processing
        ocrBtn.disabled = true;
        ocrBtn.innerHTML = '<span class="btn-icon">⏳</span>מפעיל OCR...';

        // Show processing status
        document.getElementById('processing-status').textContent = 'מפעיל OCR חכם על כותרת ההזמנה...';

        // Call the OCR analysis API
        const response = await fetch('/api/run-ocr-analysis', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            }
        });

        const result = await response.json();

        if (result.success) {
            const fieldCount = result.agent_result.field_count;
            document.getElementById('processing-status').textContent =
                `OCR הושלם בהצלחה! נמצאו ${fieldCount} שדות. טוען נתונים...`;

            // Reload the latest analysis data to show the OCR results
            setTimeout(() => {
                loadLatestAnalysis();
                document.getElementById('processing-status').textContent = 'נתוני OCR נטענו בהצלחה!';
            }, 1000);

        } else {
            throw new Error(result.error || 'OCR analysis failed');
        }

        // Clear status after delay
        setTimeout(() => {
            document.getElementById('processing-status').textContent = '';
        }, 4000);

    } catch (error) {
        console.error('Error in OCR analysis:', error);
        document.getElementById('processing-status').textContent = `שגיאה ב-OCR: ${error.message}`;
        setTimeout(() => {
            document.getElementById('processing-status').textContent = '';
        }, 5000);
    } finally {
        // Reset button
        ocrBtn.disabled = false;
        ocrBtn.innerHTML = originalContent;
    }
}

async function redetectShapes() {
    const redetectBtn = document.getElementById('redetect-shapes-btn');
    const originalContent = redetectBtn.innerHTML;
    const columnName = document.getElementById('shape-column-name').value || 'צורה';

    try {
        // Disable button and show loading state
        redetectBtn.disabled = true;
        redetectBtn.innerHTML = '<span class="btn-icon">⏳</span>מעבד...';

        document.getElementById('processing-status').textContent = `מפעיל את הגלובל ויוצר קבצי צורות חדשים מעמודת "${columnName}"...`;

        // Call the shapes re-detection API with column name
        const response = await fetch('/api/redetect-shapes', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                column_name: columnName
            })
        });

        const result = await response.json();

        if (result.success) {
            document.getElementById('processing-status').textContent = `זיהוי צורות הושלם בהצלחה! נמצאו ${result.shapes_count} צורות חדשות`;

            // Reload the latest analysis data to get updated shapes
            await loadLatestAnalysis();

        } else {
            throw new Error(result.error || 'זיהוי הצורות נכשל');
        }

        // Clear status after delay
        setTimeout(() => {
            document.getElementById('processing-status').textContent = '';
        }, 4000);

    } catch (error) {
        console.error('Error in shapes re-detection:', error);
        document.getElementById('processing-status').textContent = `שגיאה בזיהוי הצורות: ${error.message}`;
        setTimeout(() => {
            document.getElementById('processing-status').textContent = '';
        }, 5000);
    } finally {
        // Reset button
        redetectBtn.disabled = false;
        redetectBtn.innerHTML = originalContent;
    }
}

// Display shapes detected by GLOBAL agent
function displayShapes(data) {
    const shapesContainer = document.getElementById('shapes-container');
    const shapesCount = document.getElementById('shapes-count');
    
    // Check if detailed shape info is available (new format)
    if (data.shape_cells && data.shape_cells.length > 0) {
        const shapes = data.shape_cells;
        
        // Update count
        shapesCount.textContent = `${shapes.length} צורות נמצאו`;
        
        // Clear container
        shapesContainer.innerHTML = '';
        
        // Create shape items with column information
        shapes.forEach((shapeInfo, index) => {
            // Extract filename from path
            const filename = shapeInfo.path.split('\\').pop() || shapeInfo.path.split('/').pop();
            const shapeNumber = shapeInfo.row_number;
            const columnInfo = shapeInfo.column_position;
            
            // Create shape item element with column info
            const shapeItem = document.createElement('div');
            shapeItem.className = 'shape-item';
            shapeItem.innerHTML = `
                <div class="shape-header">
                    <h4>צורה ${shapeNumber}</h4>
                    <span class="shape-filename">${filename}</span>
                </div>
                <div class="shape-image-container">
                    <img src="/shape_image/${filename}" 
                         alt="צורה ${shapeNumber}" 
                         class="shape-image"
                         loading="lazy"
                         onerror="this.onerror=null; this.src='data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iMjAwIiBoZWlnaHQ9IjEwMCIgdmlld0JveD0iMCAwIDIwMCAxMDAiIGZpbGw9Im5vbmUiIHhtbG5zPSJodHRwOi8vd3d3LnczLm9yZy8yMDAwL3N2ZyI+CjxyZWN0IHdpZHRoPSIyMDAiIGhlaWdodD0iMTAwIiBmaWxsPSIjZjVmNWY1Ii8+Cjx0ZXh0IHg9IjEwMCIgeT0iNTAiIGZvbnQtZmFtaWx5PSJBcmlhbCIgZm9udC1zaXplPSIxNCIgZmlsbD0iIzk5OTk5OSIgdGV4dC1hbmNob3I9Im1pZGRsZSIgZG9taW5hbnQtYmFzZWxpbmU9ImNlbnRyYWwiPtepKb3wIA0wpUJU14ngsOhPDwvdGV4dD4KPC9zdmc+'; this.alt='שגיאה בטעינה';"
                    />
                </div>
                <div class="shape-info">
                    <small>שורה ${shapeNumber} בטבלה</small>
                    <div class="column-info">
                        <span class="column-label">עמודה:</span>
                        <span class="column-description">${columnInfo.description}</span>
                        <div class="column-position">
                            <span class="position-details">רוחב: ${columnInfo.width} פיקסלים</span>
                        </div>
                    </div>
                </div>
            `;
            
            shapesContainer.appendChild(shapeItem);
        });
        
    } else if (data.shape_cell_paths && data.shape_cell_paths.length > 0) {
        // Fallback to old format (backward compatibility)
        const shapes = data.shape_cell_paths;
        
        // Update count
        shapesCount.textContent = `${shapes.length} צורות נמצאו`;
        
        // Clear container
        shapesContainer.innerHTML = '';
        
        // Create shape items (without column information)
        shapes.forEach((shapePath, index) => {
            // Extract filename from path
            const filename = shapePath.split('\\').pop() || shapePath.split('/').pop();
            const shapeNumber = index + 1;
            
            // Create shape item element
            const shapeItem = document.createElement('div');
            shapeItem.className = 'shape-item';
            shapeItem.innerHTML = `
                <div class="shape-header">
                    <h4>צורה ${shapeNumber}</h4>
                    <span class="shape-filename">${filename}</span>
                </div>
                <div class="shape-image-container">
                    <img src="/shape_image/${filename}" 
                         alt="צורה ${shapeNumber}" 
                         class="shape-image"
                         loading="lazy"
                         onerror="this.onerror=null; this.src='data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iMjAwIiBoZWlnaHQ9IjEwMCIgdmlld0JveD0iMCAwIDIwMCAxMDAiIGZpbGw9Im5vbmUiIHhtbG5zPSJodHRwOi8vd3d3LnczLm9yZy8yMDAwL3N2ZyI+CjxyZWN0IHdpZHRoPSIyMDAiIGhlaWdodD0iMTAwIiBmaWxsPSIjZjVmNWY1Ii8+Cjx0ZXh0IHg9IjEwMCIgeT0iNTAiIGZvbnQtZmFtaWx5PSJBcmlhbCIgZm9udC1zaXplPSIxNCIgZmlsbD0iIzk5OTk5OSIgdGV4dC1hbmNob3I9Im1pZGRsZSIgZG9taW5hbnQtYmFzZWxpbmU9ImNlbnRyYWwiPtepKb3wIA0wpUJU14ngsOhPDwvdGV4dD4KPC9zdmc+'; this.alt='שגיאה בטעינה';"
                    />
                </div>
                <div class="shape-info">
                    <small>שורה ${shapeNumber} בטבלה</small>
                </div>
            `;
            
            shapesContainer.appendChild(shapeItem);
        });
        
    } else {
        // No shapes found
        shapesCount.textContent = '0 צורות נמצאו';
        shapesContainer.innerHTML = `
            <div class="no-shapes-placeholder">
                <p>🔍 לא נמצאו צורות</p>
                <p>הרץ ניתוח כדי לזהות צורות מהמסמך</p>
            </div>
        `;
    }
}

// File Selection Functions
let selectedFile = null;

async function showFileSelection() {
    const modal = document.getElementById('file-selection-modal');
    const container = document.getElementById('file-list-container');
    
    // Show modal
    modal.style.display = 'block';
    
    // Load files
    container.innerHTML = '<div class="loading">טוען קבצים...</div>';
    
    try {
        const response = await fetch('/api/files');
        const data = await response.json();
        
        if (data.files && data.files.length > 0) {
            // Create file list
            container.innerHTML = `
                <div class="file-list">
                    ${data.files.map(file => `
                        <div class="file-item" data-filename="${file.name}">
                            <div class="file-icon">
                                ${file.type === 'pdf' ? '📄' : '🖼️'}
                            </div>
                            <div class="file-info">
                                <div class="file-name">${file.name}</div>
                                <div class="file-details">
                                    ${formatFileSize(file.size)} • ${formatDate(file.modified)}
                                </div>
                            </div>
                            <div class="file-select">
                                <input type="radio" name="selected-file" value="${file.name}" id="file-${file.name}">
                                <label for="file-${file.name}"></label>
                            </div>
                        </div>
                    `).join('')}
                </div>
            `;
            
            // Add click handlers for file items
            container.querySelectorAll('.file-item').forEach(item => {
                item.addEventListener('click', () => {
                    const filename = item.dataset.filename;
                    const radio = container.querySelector(`input[value="${filename}"]`);
                    radio.checked = true;
                    selectedFile = filename;
                    
                    // Enable confirm button
                    document.getElementById('confirm-file-selection').disabled = false;
                    
                    // Update visual selection
                    container.querySelectorAll('.file-item').forEach(i => i.classList.remove('selected'));
                    item.classList.add('selected');
                });
            });
            
        } else {
            container.innerHTML = `
                <div class="no-files">
                    <p>📁 לא נמצאו קבצים</p>
                    <p>הוסף קבצים לתיקיית io/input</p>
                </div>
            `;
        }
        
    } catch (error) {
        container.innerHTML = `
            <div class="error">
                <p>❌ שגיאה בטעינת קבצים</p>
                <p>${error.message}</p>
            </div>
        `;
    }
}

function hideFileSelection() {
    document.getElementById('file-selection-modal').style.display = 'none';
    selectedFile = null;
    document.getElementById('confirm-file-selection').disabled = true;
}

async function confirmFileSelection() {
    if (!selectedFile) return;
    
    try {
        // Select the file
        const response = await fetch('/api/select-file', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ filename: selectedFile })
        });
        
        const result = await response.json();
        
        if (result.success) {
            // Store the selected file globally
            currentSelectedFile = selectedFile;
            
            // Update UI
            document.getElementById('current-file').textContent = selectedFile;
            document.getElementById('processing-status').textContent = `נבחר קובץ: ${selectedFile}`;
            
            // Load PDF if it's a PDF file
            if (selectedFile.toLowerCase().endsWith('.pdf')) {
                loadPDF(`/input/${selectedFile}`);
            }
            
            // Hide modal
            hideFileSelection();
        } else {
            throw new Error(result.error || 'שגיאה בבחירת קובץ');
        }
        
    } catch (error) {
        console.error('Error selecting file:', error);
        document.getElementById('processing-status').textContent = `שגיאה: ${error.message}`;
    }
}

function formatFileSize(bytes) {
    if (bytes === 0) return '0 B';
    const k = 1024;
    const sizes = ['B', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
}

function formatDate(dateString) {
    const date = new Date(dateString);
    return date.toLocaleString('he-IL', {
        year: 'numeric',
        month: '2-digit',
        day: '2-digit',
        hour: '2-digit',
        minute: '2-digit'
    });
}

// Auto-refresh every 30 seconds
setInterval(() => {
    if (document.getElementById('status').textContent !== 'מעבד') {
        loadLatestAnalysis();
    }
}, 30000);

// Area Selection Functions
function initializeSelectionCanvas() {
    selectionCanvas = document.getElementById('selection-canvas');
    if (!selectionCanvas) return;
    
    selectionCtx = selectionCanvas.getContext('2d');
    
    // Set canvas size to match PDF canvas
    const pdfCanvas = document.getElementById('pdf-canvas');
    if (pdfCanvas) {
        // Get the computed styles and positions
        const pdfRect = pdfCanvas.getBoundingClientRect();
        const containerRect = selectionCanvas.parentElement.getBoundingClientRect();
        
        // Set canvas dimensions to match PDF canvas
        selectionCanvas.width = pdfCanvas.width;
        selectionCanvas.height = pdfCanvas.height;
        
        // Position the selection canvas to exactly overlay the PDF canvas
        selectionCanvas.style.width = pdfCanvas.style.width || pdfRect.width + 'px';
        selectionCanvas.style.height = pdfCanvas.style.height || pdfRect.height + 'px';
        selectionCanvas.style.left = (pdfRect.left - containerRect.left) + 'px';
        selectionCanvas.style.top = (pdfRect.top - containerRect.top) + 'px';
        
        console.log('Canvas positioned:', {
            pdfRect: pdfRect,
            containerRect: containerRect,
            selectionStyle: {
                width: selectionCanvas.style.width,
                height: selectionCanvas.style.height,
                left: selectionCanvas.style.left,
                top: selectionCanvas.style.top
            }
        });
    }
    
    // Setup mouse events
    setupSelectionEvents();
}

function toggleAreaSelection() {
    const button = document.getElementById('area-select-btn');
    const overlay = document.getElementById('selection-canvas');
    
    isSelectingArea = !isSelectingArea;
    
    if (isSelectingArea) {
        button.classList.add('active');
        overlay.classList.add('active');
        initializeSelectionCanvas();
        updateSectionButtonStates();
        // Toggle detected areas display
        showDetectedAreas = !showDetectedAreas;
        drawDetectedAreas();
        console.log('Section selection mode enabled');
    } else {
        button.classList.remove('active');
        overlay.classList.remove('active');
        currentSectionType = null;
        // Hide detected areas
        showDetectedAreas = false;
        clearDetectedAreas();
        console.log('Section selection mode disabled');
    }
}

function selectSectionType(sectionType) {
    currentSectionType = sectionType;
    
    // Clear any existing selection for this section type
    if (sectionSelections[sectionType]) {
        sectionSelections[sectionType] = null;
        console.log(`Cleared existing selection for ${sectionType}`);
        // Redraw canvas to remove the old selection
        if (selectionCtx) {
            selectionCtx.clearRect(0, 0, selectionCanvas.width, selectionCanvas.height);
            drawExistingSelections();
            if (showDetectedAreas) {
                drawDetectedAreas();
            }
        }
    }
    
    // Update button states
    document.querySelectorAll('.btn-section').forEach(btn => {
        btn.classList.remove('active');
    });
    
    const selectedButton = document.querySelector(`[data-section="${sectionType}"]`);
    if (selectedButton) {
        selectedButton.classList.add('active');
    }
    
    // Update status text
    const sectionNames = {
        order_header: 'כותרת הזמנה',
        table_header: 'כותרת טבלה',
        table_area: 'אזור טבלה',
        shape_column: 'עמודת צורות'
    };
    
    document.getElementById('selection-status-text').textContent = 
        `נבחר: ${sectionNames[sectionType]} - צייר על הPDF לסימון האזור`;
        
    console.log('Selected section type:', sectionType);
}

function updateSectionButtonStates() {
    document.querySelectorAll('.btn-section').forEach(btn => {
        const sectionType = btn.dataset.section;
        btn.classList.remove('completed', 'active');
        
        if (sectionSelections[sectionType]) {
            btn.classList.add('completed');
        }
        
        if (currentSectionType === sectionType) {
            btn.classList.add('active');
        }
    });
}

function setupSelectionEvents() {
    if (!selectionCanvas) return;
    
    selectionCanvas.addEventListener('mousedown', startSelection);
    selectionCanvas.addEventListener('mousemove', drawSelection);
    selectionCanvas.addEventListener('mouseup', endSelection);
    selectionCanvas.addEventListener('mouseleave', endSelection);
}

function startSelection(e) {
    if (!isSelectingArea) return;
    
    isDrawing = true;
    
    // Get accurate canvas coordinates
    const rect = selectionCanvas.getBoundingClientRect();
    const scaleX = selectionCanvas.width / rect.width;
    const scaleY = selectionCanvas.height / rect.height;
    
    // Calculate relative position within the canvas
    const relativeX = e.clientX - rect.left;
    const relativeY = e.clientY - rect.top;
    
    // Scale to canvas coordinates
    startX = Math.max(0, Math.min(relativeX * scaleX, selectionCanvas.width));
    startY = Math.max(0, Math.min(relativeY * scaleY, selectionCanvas.height));
    
    console.log('Start selection:', { 
        clientX: e.clientX, 
        clientY: e.clientY, 
        rectLeft: rect.left,
        rectTop: rect.top,
        relativeX: relativeX, 
        relativeY: relativeY, 
        startX: startX, 
        startY: startY,
        scaleX: scaleX,
        scaleY: scaleY,
        canvasWidth: selectionCanvas.width,
        canvasHeight: selectionCanvas.height
    });
    
    // Clear previous drawings
    selectionCtx.clearRect(0, 0, selectionCanvas.width, selectionCanvas.height);
    drawExistingSelections();
}

function drawSelection(e) {
    if (!isDrawing || !isSelectingArea || !currentSectionType) return;
    
    const rect = selectionCanvas.getBoundingClientRect();
    const scaleX = selectionCanvas.width / rect.width;
    const scaleY = selectionCanvas.height / rect.height;
    
    // Calculate relative position within the canvas
    const relativeX = e.clientX - rect.left;
    const relativeY = e.clientY - rect.top;
    
    // Scale to canvas coordinates and clamp to canvas bounds
    const currentX = Math.max(0, Math.min(relativeX * scaleX, selectionCanvas.width));
    const currentY = Math.max(0, Math.min(relativeY * scaleY, selectionCanvas.height));
    
    // Clear canvas and redraw existing selections
    selectionCtx.clearRect(0, 0, selectionCanvas.width, selectionCanvas.height);
    drawExistingSelections();
    
    // Get section-specific colors
    const colors = sectionColors[currentSectionType];
    selectionCtx.strokeStyle = colors.stroke;
    selectionCtx.lineWidth = 2;
    selectionCtx.fillStyle = colors.fill;
    
    const width = currentX - startX;
    const height = currentY - startY;
    
    // Only draw if we have a valid selection
    if (Math.abs(width) > 1 && Math.abs(height) > 1) {
        selectionCtx.fillRect(startX, startY, width, height);
        selectionCtx.strokeRect(startX, startY, width, height);
    }
    
    // Show selection info (use screen coordinates for positioning)
    const sectionNames = {
        order_header: 'כותרת הזמנה',
        table_header: 'כותרת טבלה', 
        table_area: 'אזור טבלה',
        shape_column: 'עמודת צורות'
    };
    showSelectionInfo(e.clientX, e.clientY, width, height, sectionNames[currentSectionType]);
}

function endSelection(e) {
    if (!isDrawing || !isSelectingArea || !currentSectionType) return;
    
    isDrawing = false;
    
    const rect = selectionCanvas.getBoundingClientRect();
    const scaleX = selectionCanvas.width / rect.width;
    const scaleY = selectionCanvas.height / rect.height;
    
    // Calculate relative position within the canvas
    const relativeX = e.clientX - rect.left;
    const relativeY = e.clientY - rect.top;
    
    // Scale to canvas coordinates and clamp to canvas bounds
    const endX = Math.max(0, Math.min(relativeX * scaleX, selectionCanvas.width));
    const endY = Math.max(0, Math.min(relativeY * scaleY, selectionCanvas.height));
    
    const width = Math.abs(endX - startX);
    const height = Math.abs(endY - startY);
    
    console.log('End section selection:', { 
        sectionType: currentSectionType,
        endX: endX, 
        endY: endY, 
        width: width, 
        height: height,
        startX: startX,
        startY: startY
    });
    
    // Only save if selection is large enough
    if (width > 10 && height > 10) {
        const selection = {
            id: Date.now(),
            type: currentSectionType,
            x: Math.min(startX, endX),
            y: Math.min(startY, endY),
            width: width,
            height: height,
            page: pageNum,
            timestamp: new Date().toISOString()
        };
        
        // Store in section-specific storage
        sectionSelections[currentSectionType] = selection;
        console.log(`Section ${currentSectionType} selected:`, selection);
        
        // Update button states
        updateSectionButtonStates();
        updateClearButtonVisibility();
        
        // Auto-move to next section without confirmation dialog
        autoMoveToNextSection(currentSectionType);
    }
    
    hideSelectionInfo();
}

function drawExistingSelections() {
    // Draw section selections
    Object.entries(sectionSelections).forEach(([sectionType, selection]) => {
        if (selection && selection.page === pageNum) {
            const colors = sectionColors[sectionType];
            selectionCtx.strokeStyle = colors.stroke;
            selectionCtx.lineWidth = 2;
            selectionCtx.fillStyle = colors.fill;
            
            selectionCtx.fillRect(selection.x, selection.y, selection.width, selection.height);
            selectionCtx.strokeRect(selection.x, selection.y, selection.width, selection.height);
            
            // Add section label
            selectionCtx.fillStyle = colors.stroke;
            selectionCtx.font = 'bold 12px Arial';
            const sectionLabels = {
                order_header: 'כותרת הזמנה',
                table_header: 'כותרת טבלה',
                table_area: 'טבלה',
                shape_column: 'צורות'
            };
            selectionCtx.fillText(sectionLabels[sectionType], selection.x + 5, selection.y + 15);
        }
    });
    
    // Draw legacy area selections (if any)
    selectedAreas.forEach(area => {
        if (area.page === pageNum && !area.type) {
            selectionCtx.strokeStyle = '#28a745';
            selectionCtx.lineWidth = 2;
            selectionCtx.fillStyle = 'rgba(40, 167, 69, 0.1)';
            
            selectionCtx.fillRect(area.x, area.y, area.width, area.height);
            selectionCtx.strokeRect(area.x, area.y, area.width, area.height);
            
            // Add area number
            selectionCtx.fillStyle = '#28a745';
            selectionCtx.font = '12px Arial';
            selectionCtx.fillText(`${selectedAreas.indexOf(area) + 1}`, area.x + 5, area.y + 15);
        }
    });
}

function drawUserDefinedAreas(userSections) {
    // Define colors for user-defined areas
    const areaColors = {
        order_header: { stroke: '#ff6b6b', fill: 'rgba(255, 107, 107, 0.1)', label: 'כותרת - משתמש' },
        table_header: { stroke: '#ffa726', fill: 'rgba(255, 167, 38, 0.1)', label: 'כותרת טבלה - משתמש' },
        table_area: { stroke: '#66bb6a', fill: 'rgba(102, 187, 106, 0.1)', label: 'טבלה - משתמש' },
        shape_column: { stroke: '#6610f2', fill: 'rgba(102, 16, 242, 0.1)', label: 'עמודת צורות - משתמש' }
    };
    
    console.log('Drawing user-defined areas:', userSections);
    
    // Draw each user-defined area
    Object.entries(userSections).forEach(([areaType, areaData]) => {
        if (areaData?.selection && areaColors[areaType]) {
            const selection = areaData.selection;
            const colors = areaColors[areaType];
            
            // User selections are already in canvas coordinates - use them directly!
            const x = selection.x;
            const y = selection.y;
            const width = selection.width;
            const height = selection.height;
            
            console.log(`Drawing user area ${areaType}:`, { x, y, width, height });
            
            // Draw filled rectangle
            selectionCtx.fillStyle = colors.fill;
            selectionCtx.fillRect(x, y, width, height);
            
            // Draw border with thick dashed line
            selectionCtx.strokeStyle = colors.stroke;
            selectionCtx.lineWidth = 3;
            selectionCtx.setLineDash([8, 8]);
            selectionCtx.strokeRect(x, y, width, height);
            selectionCtx.setLineDash([]);
            
            // Add label
            selectionCtx.fillStyle = colors.stroke;
            selectionCtx.font = 'bold 12px Arial';
            selectionCtx.fillText(colors.label, x + 5, y - 5);
        }
    });
    
    console.log('Finished drawing user-defined areas');
}

function updateAreaPositionsFromUserSelections(sections, userSections) {
    // Map user selection types to section names
    const sectionMapping = {
        'order_header': 'header',
        'table_header': 'table_header',
        'table_area': 'main_table'
    };
    
    // Update each section's area_position based on user selections
    Object.entries(sectionMapping).forEach(([userKey, sectionKey]) => {
        if (userSections[userKey]?.selection && sections[sectionKey]) {
            const userSelection = userSections[userKey].selection;
            
            // The user selections are in canvas coordinates
            // We'll use them directly as "fake" image coordinates
            // The scaling will happen later in drawDetectedAreas
            
            // Update or create area_position for this section
            if (!sections[sectionKey]) {
                sections[sectionKey] = { found: true };
            }
            
            // Store user selection as if it were image coordinates
            // The drawDetectedAreas function will scale them properly
            sections[sectionKey].area_position = {
                x: userSelection.x,
                y: userSelection.y,
                width: userSelection.width,
                height: userSelection.height,
                original_image_width: 600,  // Assume canvas width
                original_image_height: 800,  // Assume canvas height
                description: `${sectionKey} - User defined`,
                source: 'user_selection'
            };
            
            console.log(`Updated ${sectionKey} area from user selection:`, sections[sectionKey].area_position);
        }
    });
}

function drawDetectedAreas() {
    if (!showDetectedAreas || !currentData || !selectionCtx) return;
    
    // If we have user_sections, use those directly instead of the estimated areas
    if (currentData.user_sections) {
        drawUserDefinedAreas(currentData.user_sections);
        return;
    }
    
    // Otherwise, use the detected areas from analysis (fallback to old behavior)
    const sections = currentData.sections || currentData.analysis?.sections;
    if (!sections) return;
    
    // Get the PDF canvas to understand the current viewport
    const pdfCanvas = document.getElementById('pdf-canvas');
    if (!pdfCanvas) return;
    
    // The area_position coordinates are in original image pixels
    // We need to scale them to match the current PDF canvas size
    const canvasWidth = pdfCanvas.width;
    const canvasHeight = pdfCanvas.height;
    
    // Get original image dimensions from the first area_position we find
    let originalImageWidth = 1224;  // Default fallback
    let originalImageHeight = 1580; // Default fallback
    
    // Try to get actual dimensions from area_position data
    const firstAreaWithDimensions = Object.values(sections).find(section => 
        section?.area_position?.original_image_width && section?.area_position?.original_image_height
    );
    
    if (firstAreaWithDimensions) {
        originalImageWidth = firstAreaWithDimensions.area_position.original_image_width;
        originalImageHeight = firstAreaWithDimensions.area_position.original_image_height;
    }
    
    // Calculate scaling factors
    const scaleX = canvasWidth / originalImageWidth;
    const scaleY = canvasHeight / originalImageHeight;
    
    // Define colors for detected areas (slightly different from user selection colors)
    const detectedAreaColors = {
        header: { stroke: '#ff6b6b', fill: 'rgba(255, 107, 107, 0.1)' },
        table_header: { stroke: '#ffa726', fill: 'rgba(255, 167, 38, 0.1)' },  
        main_table: { stroke: '#66bb6a', fill: 'rgba(102, 187, 106, 0.1)' }
    };
    
    console.log('Drawing detected areas:', {
        canvasSize: { width: canvasWidth, height: canvasHeight },
        originalImageSize: { width: originalImageWidth, height: originalImageHeight },
        scale: { scaleX, scaleY }
    });
    
    // Draw detected areas
    Object.entries(sections).forEach(([sectionType, sectionData]) => {
        if (sectionData?.found && sectionData?.area_position) {
            const area = sectionData.area_position;
            const colors = detectedAreaColors[sectionType];
            
            if (colors) {
                // Scale coordinates to match current canvas size
                const scaledX = area.x * scaleX;
                const scaledY = area.y * scaleY;
                const scaledWidth = area.width * scaleX;
                const scaledHeight = area.height * scaleY;
                
                console.log(`Drawing ${sectionType}:`, { 
                    original: area, 
                    scaled: { x: scaledX, y: scaledY, width: scaledWidth, height: scaledHeight },
                    canvasSize: { width: canvasWidth, height: canvasHeight }
                });
                
                // Add a prominent border and label for debugging
                selectionCtx.strokeStyle = colors.stroke;
                selectionCtx.lineWidth = 4; // Thicker border for debugging
                selectionCtx.setLineDash([10, 10]); // More prominent dashed line
                
                // Draw filled rectangle
                selectionCtx.fillStyle = colors.fill;
                selectionCtx.fillRect(scaledX, scaledY, scaledWidth, scaledHeight);
                
                // Draw border (already set above for debugging)
                selectionCtx.strokeRect(scaledX, scaledY, scaledWidth, scaledHeight);
                selectionCtx.setLineDash([]); // Reset to solid line
                
                // Add label
                selectionCtx.fillStyle = colors.stroke;
                selectionCtx.font = 'bold 11px Arial';
                const labels = {
                    header: 'אזור זוהה - כותרת',
                    table_header: 'אזור זוהה - כותרת טבלה',
                    main_table: 'אזור זוהה - טבלה'
                };
                const label = labels[sectionType] || area.description;
                selectionCtx.fillText(label, scaledX + 5, scaledY - 5);
            }
        }
    });
    
    console.log('Drew detected areas from analysis');
}

function clearDetectedAreas() {
    if (!selectionCtx) return;
    
    // Clear the entire canvas and redraw only user selections
    selectionCtx.clearRect(0, 0, selectionCanvas.width, selectionCanvas.height);
    drawExistingSelections(); // Redraw user selections only
    
    console.log('Cleared detected areas');
}

function showSelectionInfo(x, y, width, height, sectionName = '') {
    let infoDiv = document.querySelector('.selection-info');
    if (!infoDiv) {
        infoDiv = document.createElement('div');
        infoDiv.className = 'selection-info';
        document.body.appendChild(infoDiv);
    }
    
    const sizeText = `${Math.round(width)} × ${Math.round(height)} px`;
    infoDiv.textContent = sectionName ? `${sectionName}: ${sizeText}` : sizeText;
    infoDiv.style.left = `${x + 10}px`;
    infoDiv.style.top = `${y - 25}px`;
    infoDiv.style.display = 'block';
}

function hideSelectionInfo() {
    const infoDiv = document.querySelector('.selection-info');
    if (infoDiv) {
        infoDiv.style.display = 'none';
    }
}

function showSelectionOptions(selection) {
    const choice = prompt(`אזור נבחר (${Math.round(selection.width)}×${Math.round(selection.height)})\\nמה ברצונך לעשות עם האזור?\\n\\n1. שמור ככותרת חדשה\\n2. זהה כטבלה\\n3. זהה כצורה\\n4. מחק אזור\\n\\nהקש 1-4:`);
    
    if (choice) {
        const option = parseInt(choice);
        switch(option) {
            case 1:
                saveAsNewHeader(selection);
                break;
            case 2:
                console.log('Identify as table:', selection);
                alert('זיהוי כטבלה יתווסף בגרסה הבאה');
                break;
            case 3:
                console.log('Identify as shape:', selection);
                alert('זיהוי כצורה יתווסף בגרסה הבאה');
                break;
            case 4:
                removeSelection(selection);
                break;
            default:
                console.log('Invalid option selected');
        }
    }
}

function autoMoveToNextSection(sectionType) {
    // Move to next section automatically without confirmation
    const sectionOrder = ['order_header', 'table_header', 'table_area', 'shape_column'];
    const currentIndex = sectionOrder.indexOf(sectionType);
    
    if (currentIndex < sectionOrder.length - 1) {
        const nextSection = sectionOrder[currentIndex + 1];
        if (!sectionSelections[nextSection]) {
            selectSectionType(nextSection);
            return;
        }
    }
    
    // Check if all sections are completed
    const completedSections = Object.values(sectionSelections).filter(s => s !== null).length;
    if (completedSections === 4) {
        document.getElementById('selection-status-text').textContent = 
            'כל הקטעים הושלמו! לחץ על "שמור הגדרות" כדי לחל את השינויים';
        currentSectionType = null; // Clear active selection
        updateSectionButtonStates();
    }
}

function clearSelections() {
    selectedAreas = [];
    sectionSelections = {
        order_header: null,
        table_header: null,
        table_area: null,
        shape_column: null
    };
    
    if (selectionCanvas && selectionCtx) {
        selectionCtx.clearRect(0, 0, selectionCanvas.width, selectionCanvas.height);
    }
    
    updateSectionButtonStates();
    updateClearButtonVisibility();
    
    document.getElementById('selection-status-text').textContent = 
        'בחר סוג אזור ולאחר מכן צייר על הPDF';
        
    console.log('All selections cleared');
}

function removeSelection(selection) {
    const index = selectedAreas.findIndex(area => area.id === selection.id);
    if (index > -1) {
        selectedAreas.splice(index, 1);
        selectionCtx.clearRect(0, 0, selectionCanvas.width, selectionCanvas.height);
        drawExistingSelections();
        updateClearButtonVisibility();
        console.log('Selection removed:', selection);
    }
}

function updateClearButtonVisibility() {
    const clearBtn = document.getElementById('clear-selections-btn');
    const saveBtn = document.getElementById('save-sections-btn');
    const hasSelections = selectedAreas.length > 0 || 
                         Object.values(sectionSelections).some(selection => selection !== null);
    const hasSections = Object.values(sectionSelections).some(selection => selection !== null);
    
    if (hasSelections) {
        clearBtn.style.display = 'inline-block';
    } else {
        clearBtn.style.display = 'none';
    }
    
    // Always show the save button
    saveBtn.style.display = 'inline-block';
}

async function saveSectionSelections() {
    try {
        if (!currentSelectedFile) {
            alert('לא נמצא קובץ PDF פעיל');
            return;
        }
        
        // Check if we have any section selections
        const activeSections = Object.entries(sectionSelections)
            .filter(([_, selection]) => selection !== null)
            .reduce((acc, [key, value]) => {
                acc[key] = value;
                return acc;
            }, {});
        
        if (Object.keys(activeSections).length === 0) {
            alert('לא נבחרו אזורים לשמירה');
            return;
        }
        
        const response = await fetch('/api/save-section-selections', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                filename: currentSelectedFile,
                sections: activeSections
            })
        });
        
        const result = await response.json();
        
        if (result.success) {
            console.log(`הגדרות נשמרו בהצלחה! נשמרו ${Object.keys(activeSections).length} אזורים`);
            
            // Clear selections after successful save
            clearSelections();
            
            // Refresh analysis to show updated data
            loadLatestAnalysis();
        } else {
            alert('שגיאה בשמירת ההגדרות: ' + result.error);
        }
    } catch (error) {
        console.error('Error saving section selections:', error);
        alert('שגיאה בשמירת ההגדרות');
    }
}

async function saveAsNewHeader(selection) {
    try {
        if (!currentSelectedFile) {
            alert('לא נמצא קובץ PDF פעיל');
            return;
        }

        const response = await fetch('/api/save-header-selection', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                filename: currentSelectedFile,
                selection: {
                    x: selection.x,
                    y: selection.y,
                    width: selection.width,
                    height: selection.height,
                    page: selection.page
                }
            })
        });

        const result = await response.json();
        
        if (result.success) {
            alert('הכותרת החדשה נשמרה בהצלחה!');
            // Remove the selection after saving
            removeSelection(selection);
            // Refresh data to show new header
            loadLatestAnalysis();
        } else {
            alert('שגיאה בשמירת הכותרת: ' + result.error);
        }
    } catch (error) {
        console.error('Error saving header selection:', error);
        alert('שגיאה בשמירת הכותרת');
    }
}

// Update canvas size when PDF is rendered
function updateSelectionCanvasSize() {
    if (selectionCanvas) {
        const pdfCanvas = document.getElementById('pdf-canvas');
        if (pdfCanvas) {
            // Get the computed styles and positions
            const pdfRect = pdfCanvas.getBoundingClientRect();
            const containerRect = selectionCanvas.parentElement.getBoundingClientRect();
            
            // Set canvas dimensions to match PDF canvas
            selectionCanvas.width = pdfCanvas.width;
            selectionCanvas.height = pdfCanvas.height;
            
            // Position the selection canvas to exactly overlay the PDF canvas
            selectionCanvas.style.width = pdfCanvas.style.width || pdfRect.width + 'px';
            selectionCanvas.style.height = pdfCanvas.style.height || pdfRect.height + 'px';
            selectionCanvas.style.left = (pdfRect.left - containerRect.left) + 'px';
            selectionCanvas.style.top = (pdfRect.top - containerRect.top) + 'px';
            
            // Redraw existing selections
            if (selectionCtx) {
                selectionCtx.clearRect(0, 0, selectionCanvas.width, selectionCanvas.height);
                drawExistingSelections();
            }
            
            console.log('Selection canvas updated:', {
                canvasSize: { width: selectionCanvas.width, height: selectionCanvas.height },
                styleSize: { width: selectionCanvas.style.width, height: selectionCanvas.style.height },
                position: { left: selectionCanvas.style.left, top: selectionCanvas.style.top }
            });
        }
    }
}

// Removed: showOrderHeaderSection and createOrderHeaderSection functions - not needed anymore

// Save table cell data
async function saveTableCell(pageNumber, rowIndex, fieldName, newValue) {
    try {
        // Get the current order number
        const orderNumber = currentData?.file?.replace('.pdf', '') || 'CO25S006375';

        // Show saving indicator
        const statusEl = document.getElementById('processing-status');
        if (statusEl) {
            statusEl.textContent = 'שומר...';
            statusEl.style.color = '#ffa500';
        }

        const response = await fetch('/api/update-table-cell', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                orderNumber: orderNumber,
                pageNumber: pageNumber,
                rowIndex: rowIndex,
                fieldName: fieldName,
                value: newValue
            })
        });

        const result = await response.json();

        if (result.success) {
            // Show success message briefly
            if (statusEl) {
                statusEl.textContent = 'נשמר ✓';
                statusEl.style.color = '#10b981';
                setTimeout(() => {
                    statusEl.textContent = '';
                }, 2000);
            }

            // Update total weight if weight field was changed
            if (fieldName === 'משקל') {
                updateTotalWeight();
            }

            console.log('✅ Table cell saved successfully');
        } else {
            throw new Error(result.error || 'Failed to save');
        }
    } catch (error) {
        console.error('Error saving table cell:', error);
        const statusEl = document.getElementById('processing-status');
        if (statusEl) {
            statusEl.textContent = 'שגיאה בשמירה ✗';
            statusEl.style.color = '#ef4444';
            setTimeout(() => {
                statusEl.textContent = '';
            }, 3000);
        }
    }
}

// Update total weight calculation
function updateTotalWeight() {
    let totalWeight = 0;
    const weightInputs = document.querySelectorAll('.table-editable[data-field="משקל"]');
    weightInputs.forEach(input => {
        const weight = parseFloat(input.value) || 0;
        totalWeight += weight;
    });
    document.getElementById('total-weight').textContent = totalWeight.toFixed(1) + ' kg';
}

// Save all table data
async function saveAllTableData() {
    const statusEl = document.getElementById('processing-status');
    const saveBtn = document.getElementById('save-all-table');

    try {
        // Disable button during save
        if (saveBtn) {
            saveBtn.disabled = true;
            saveBtn.innerHTML = '<span class="btn-icon">⏳</span> שומר...';
        }

        // Show saving status
        if (statusEl) {
            statusEl.textContent = 'שומר את כל הנתונים...';
            statusEl.style.color = '#ffa500';
        }

        // Get all editable cells
        const editableCells = document.querySelectorAll('.table-editable');
        let saveCount = 0;
        let errorCount = 0;

        // Get current page number from the first row
        const firstRow = document.querySelector('tr[data-page]');
        const pageNumber = firstRow ? firstRow.getAttribute('data-page') : 1;

        // Save each cell that has been modified
        for (const cell of editableCells) {
            const currentValue = cell.value;
            const originalValue = cell.getAttribute('data-original-value');

            if (currentValue !== originalValue) {
                const rowId = cell.getAttribute('data-row-id');
                const fieldName = cell.getAttribute('data-field');

                try {
                    await saveTableCell(pageNumber, parseInt(rowId), fieldName, currentValue);
                    cell.setAttribute('data-original-value', currentValue);
                    saveCount++;
                } catch (error) {
                    errorCount++;
                    console.error('Failed to save cell:', error);
                }
            }
        }

        // Show result
        if (statusEl) {
            if (errorCount === 0) {
                statusEl.textContent = `✅ נשמרו ${saveCount} שינויים בהצלחה`;
                statusEl.style.color = '#10b981';
            } else {
                statusEl.textContent = `⚠️ נשמרו ${saveCount} שינויים, ${errorCount} שגיאות`;
                statusEl.style.color = '#ffa500';
            }

            setTimeout(() => {
                statusEl.textContent = '';
            }, 3000);
        }

    } catch (error) {
        console.error('Error saving all table data:', error);
        if (statusEl) {
            statusEl.textContent = 'שגיאה בשמירת הנתונים';
            statusEl.style.color = '#ef4444';
            setTimeout(() => {
                statusEl.textContent = '';
            }, 3000);
        }
    } finally {
        // Re-enable button
        if (saveBtn) {
            saveBtn.disabled = false;
            saveBtn.innerHTML = '<span class="btn-icon">💾</span> שמור הכל';
        }
    }
}

// Initialize row lock states based on button checked attributes
function initializeRowLockStates() {
    // Find all check buttons that have data-checked="true"
    const checkButtons = document.querySelectorAll('.check-btn[data-checked="true"]');

    checkButtons.forEach(button => {
        const row = button.closest('tr');
        if (row) {
            // Lock the row if the button is marked as checked
            toggleRowLock(row, true);
        }
    });
}

// Initialize when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    // Small delay to ensure all content is loaded
    setTimeout(initializeRowLockStates, 100);
});
// Global variables
let pdfDoc = null;
let pageNum = 1;
let pageRendering = false;
let pageNumPending = null;
let scale = 1.0;
let currentData = null;

// Initialize when page loads
document.addEventListener('DOMContentLoaded', function() {
    // Setup event listeners
    setupEventListeners();
    
    // Load initial data if available
    loadLatestAnalysis();
    
    // Update timestamp
    updateLastUpdateTime();
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
    
    // Setup inline editing for header fields
    setupInlineEditing();
    
    // Header action buttons
    document.getElementById('clear-header-btn').addEventListener('click', clearHeaderData);
    document.getElementById('redetect-header-btn').addEventListener('click', redetectHeader);
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
    processingStatus.textContent = 'מריץ ניתוח GLOBAL...';
    
    try {
        // Call Flask endpoint to run analysis
        const response = await fetch('/api/run-analysis', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            }
        });
        
        const result = await response.json();
        
        if (result.success) {
            // Analysis completed successfully
            status.textContent = 'הושלם';
            status.className = 'value status-ready';
            processingStatus.textContent = 'הניתוח הושלם בהצלחה';
            
            // Load the new data
            setTimeout(() => {
                loadLatestAnalysis();
            }, 1000);
        } else {
            // Error occurred
            throw new Error(result.error || 'שגיאה בהרצת הניתוח');
        }
    } catch (error) {
        console.error('Error running analysis:', error);
        status.textContent = 'שגיאה';
        status.className = 'value status-error';
        processingStatus.textContent = `שגיאה: ${error.message}`;
    } finally {
        // Reset button
        runBtn.disabled = false;
        runBtn.innerHTML = '<span class="btn-icon">▶</span> הרץ ניתוח';
        
        // Clear status after 5 seconds
        setTimeout(() => {
            processingStatus.textContent = '';
        }, 5000);
    }
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
    // Update header info
    if (data.analysis && data.analysis.sections) {
        const sections = data.analysis.sections;
        
        // Header section
        if (sections.header && sections.header.found) {
            const header = sections.header;
            document.getElementById('order-number').textContent = header.order_number || '-';
            document.getElementById('customer-name').textContent = header.customer || '-';
            document.getElementById('detail-order-number').value = header.order_number || '';
            document.getElementById('detail-customer').value = header.customer || '';
            
            // Extract more header details if available
            if (header.header_table && header.header_table.key_values) {
                header.header_table.key_values.forEach(kv => {
                    Object.entries(kv).forEach(([key, value]) => {
                        if (key.includes('איש') && key.includes('קשר')) {
                            document.getElementById('detail-contact').value = value || '';
                        }
                        if (key.includes('טלפון')) {
                            document.getElementById('detail-phone').value = value || '';
                        }
                        if (key.includes('כתובת') && key.includes('אתר')) {
                            document.getElementById('detail-address').value = value || '';
                        }
                        if (key.includes('משקל')) {
                            document.getElementById('detail-weight').value = value || '';
                        }
                    });
                });
            }
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
                    
                    // Fixed column order
                    row.insertCell(1).textContent = item['מס\''] || item['מס'] || (index + 1);
                    row.insertCell(2).textContent = item['מספר קטלוגי'] || item['catalog'] || '-';
                    row.insertCell(3).textContent = item['קוטר'] || item['קוטר [mm]'] || '-';
                    row.insertCell(4).textContent = item['יחידות'] || item['units'] || item['כמות'] || item['סה"כ יח\''] || '1';
                    row.insertCell(5).textContent = item['אורך'] || item['אורך [m]'] || '-';
                    
                    const weight = parseFloat(item['סה"כ משקל'] || item['סה"כ משקל [kg]'] || '0');
                    row.insertCell(6).textContent = weight || '-';
                    totalWeight += weight;
                    
                    row.insertCell(7).textContent = item['הערות'] || '-';
                });
                
                // Update total weight
                document.getElementById('total-weight').textContent = totalWeight.toFixed(1) + ' kg';
            } else {
                tbody.innerHTML = '<tr><td colspan="8" class="no-data">אין נתונים להצגה</td></tr>';
            }
        }
    }
    
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
        document.getElementById('page-count').textContent = pdfDoc.numPages;
        
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
        });
    });
    
    // Update page info
    document.getElementById('page-num').textContent = num;
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
    document.getElementById('detail-contact').value = '';
    document.getElementById('detail-phone').value = '';
    document.getElementById('detail-address').value = '';
    document.getElementById('detail-weight').value = '';
    
    // Clear header info at top
    document.getElementById('order-number').textContent = '-';
    document.getElementById('customer-name').textContent = '-';
    
    // Save cleared data to server
    const clearedData = {
        orderNumber: '',
        customer: '',
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
    redetectBtn.innerHTML = '<span class="loading"></span> מזהה...';
    
    // Show processing status
    document.getElementById('processing-status').textContent = 'מבצע זיהוי מחדש של הכותרת...';
    
    try {
        // Run analysis
        const response = await fetch('/api/run-analysis', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            }
        });
        
        const result = await response.json();
        
        if (result.success) {
            // Wait a moment for analysis to complete, then reload data
            setTimeout(() => {
                loadLatestAnalysis();
                document.getElementById('processing-status').textContent = 'זיהוי מחדש הושלם בהצלחה';
                setTimeout(() => {
                    document.getElementById('processing-status').textContent = '';
                }, 3000);
            }, 2000);
        } else {
            throw new Error(result.error || 'שגיאה בזיהוי מחדש');
        }
    } catch (error) {
        console.error('Error in re-detection:', error);
        document.getElementById('processing-status').textContent = `שגיאה בזיהוי מחדש: ${error.message}`;
        setTimeout(() => {
            document.getElementById('processing-status').textContent = '';
        }, 5000);
    } finally {
        // Reset button
        redetectBtn.disabled = false;
        redetectBtn.innerHTML = originalContent;
    }
}

// Auto-refresh every 30 seconds
setInterval(() => {
    if (document.getElementById('status').textContent !== 'מעבד') {
        loadLatestAnalysis();
    }
}, 30000);
// Global variables - CACHE BUST: 2025-10-01-20:50 - TEMPLATE BORDER FIX 110px HEIGHT 55% TOP

// Function to open template in a modal
function openTemplateModal(catalogNumber, rowIndex) {
    console.log(`[TEMPLATE MODAL] Opening template ${catalogNumber} for row ${rowIndex}`);

    // Create modal overlay
    const modal = document.createElement('div');
    modal.id = 'template-modal';
    modal.style.cssText = `
        position: fixed; top: 0; left: 0; width: 100%; height: 100%;
        background: rgba(0,0,0,0.7); z-index: 10000; display: flex;
        align-items: center; justify-content: center;
    `;

    // Create modal content
    const modalContent = document.createElement('div');
    modalContent.style.cssText = `
        background: white; border-radius: 10px; padding: 20px;
        max-width: 90%; max-height: 90%; overflow: auto; position: relative;
        box-shadow: 0 10px 30px rgba(0,0,0,0.3);
    `;

    modalContent.innerHTML = `
        <div style="display: flex; justify-content: between; align-items: center; margin-bottom: 15px; border-bottom: 2px solid #eee; padding-bottom: 10px;">
            <h3 style="margin: 0; color: #333;">Template ${catalogNumber} - Row ${parseInt(rowIndex) + 1}</h3>
            <button onclick="closeTemplateModal()" style="background: #ff4757; color: white; border: none; border-radius: 5px; padding: 8px 12px; cursor: pointer; font-size: 14px; float: right;">✕ Close</button>
        </div>
        <div id="modal-template-content" style="min-height: 200px;">
            <div style="text-align: center; padding: 50px; color: #666;">Loading template...</div>
        </div>
    `;

    modal.appendChild(modalContent);
    document.body.appendChild(modal);

    // Load template content
    fetch('/shape_template/' + catalogNumber)
        .then(response => response.text())
        .then(html => {
            document.getElementById('modal-template-content').innerHTML = html;
        })
        .catch(error => {
            document.getElementById('modal-template-content').innerHTML =
                '<div style="color: red; text-align: center; padding: 20px;">Error loading template: ' + error.message + '</div>';
        });
}

// Function to close template modal
function closeTemplateModal() {
    const modal = document.getElementById('template-modal');
    if (modal) {
        modal.remove();
    }
}
let pdfDoc = null;
let pageNum = 1;
let pageRendering = false;
let pageNumPending = null;
let scale = 1.0;
let currentData = null;
let currentSelectedFile = null;
let currentShapeRow = null;  // Store current shape row data for modal

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
    loadLatestAnalysis().then(() => {
        // Auto-upload file from input folder if no file is currently loaded
        autoUploadFromInputFolder();
    });

    // Update timestamp
    updateLastUpdateTime();

    // Initialize button visibility
    updateClearButtonVisibility();

    // Removed: Order header section display - not needed anymore

    // Initialize page displays with tab activation fix
    console.log('[INIT] 🚀 STARTING INITIALIZATION WITH TAB FIX');

    // Check if we need to initialize tab state
    setTimeout(() => {
        console.log('[INIT] 🎯 Checking tab initialization...');

        // Check which tab should be active (don't force table tab)
        const activeTabBtn = document.querySelector('.tab-btn.active');
        const activeTabContent = document.querySelector('.tab-content.active');

        if (activeTabBtn && activeTabContent) {
            const tabName = activeTabBtn.dataset.tab;
            console.log('[INIT] ✅ Tab system initialized, active tab:', tabName);
        } else {
            console.log('[INIT] ❌ Tab system not properly initialized');
        }

        // Force check table element
        const tableElement = document.getElementById('items-tbody');
        console.log('[INIT] 🔍 Table element after tab fix:', tableElement);

        if (tableElement) {
            console.log('[INIT] ✅ TABLE FOUND! Proceeding with data loading...');
            updatePageDisplays(1);
        } else {
            console.log('[INIT] ❌ TABLE STILL NOT FOUND - checking all possible elements...');

            // Debug: List all tbody elements
            const allTbodies = document.querySelectorAll('tbody');
            console.log('[INIT] 🔍 All tbody elements found:', allTbodies.length);
            allTbodies.forEach((tb, i) => {
                console.log(`[INIT] tbody ${i}: id="${tb.id}", visible="${tb.offsetParent !== null}"`);
            });

            // Try alternative approaches
            setTimeout(() => {
                console.log('[INIT] 🔄 RETRY: Checking table element again...');
                const retryTableElement = document.getElementById('items-tbody');
                if (retryTableElement) {
                    console.log('[INIT] ✅ TABLE FOUND ON RETRY! Loading data...');
                    updatePageDisplays(1);
                } else {
                    console.log('[INIT] 💥 FINAL FAILURE: Table element never found');
                }
            }, 1000);
        }
    }, 500);


});

// Setup all event listeners
function setupEventListeners() {
    // Run Analysis button
    document.getElementById('run-analysis').addEventListener('click', runAnalysis);
    
    // Refresh button - removed from UI
    
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

    // Table refresh button
    const refreshTableBtn = document.getElementById('refresh-table-btn');
    if (refreshTableBtn) {
        refreshTableBtn.addEventListener('click', refreshCurrentTableData);
    }

    // Header action buttons (removed)

    // Table save button removed

    // OCR button removed

    // Shapes re-detect button (if it exists - it was removed from the UI)
    const redetectBtn = document.getElementById('redetect-shapes-btn');
    if (redetectBtn) {
        redetectBtn.addEventListener('click', redetectShapes);
    }

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

    // Clear previous notifications
    clearProgressNotifications();

    // Update UI to show processing
    runBtn.disabled = true;
    runBtn.innerHTML = '<span class="loading"></span> מעבד...';
    status.textContent = 'מעבד';
    status.className = 'value status-processing';
    processingStatus.textContent = 'מתחיל עיבוד...';

    // Show initial notification
    showProgressNotification('🚀 מתחיל עיבוד הזמנה...', 'stage');

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

// Progress notification management
let notificationQueue = [];
let lastProgressMessages = [];

function showProgressNotification(message, type = 'info') {
    const container = document.getElementById('progress-notifications');
    if (!container) return;

    const notification = document.createElement('div');
    notification.className = `progress-notification ${type}`;

    // Choose icon based on type
    let icon = '📋';
    if (type === 'stage') icon = '⚡';
    else if (type === 'success') icon = '✅';
    else if (type === 'error') icon = '❌';
    else if (type === 'warning') icon = '⚠️';
    else if (message.includes('מעבד')) icon = '⚙️';
    else if (message.includes('מזהה')) icon = '🔍';
    else if (message.includes('ממיר')) icon = '🔄';
    else if (message.includes('מחלץ')) icon = '📤';
    else if (message.includes('סופר')) icon = '🔢';
    else if (message.includes('OCR')) icon = '📝';
    else if (message.includes('שומר')) icon = '💾';

    const time = new Date().toLocaleTimeString('he-IL');

    notification.innerHTML = `
        <div class="notification-icon">${icon}</div>
        <div class="notification-content">
            <div class="notification-message">${message}</div>
            <div class="notification-time">${time}</div>
        </div>
    `;

    container.appendChild(notification);
    notificationQueue.push(notification);

    // Keep only last 8 notifications visible
    if (notificationQueue.length > 8) {
        const oldNotification = notificationQueue.shift();
        oldNotification.classList.add('fade-out');
        setTimeout(() => oldNotification.remove(), 500);
    }

    // Auto-scroll to latest
    container.scrollTop = container.scrollHeight;
}

function clearProgressNotifications() {
    const container = document.getElementById('progress-notifications');
    if (container) {
        container.innerHTML = '';
        notificationQueue = [];
        lastProgressMessages = [];
    }
}

// Advanced notification functions for shape identification
function createProgressNotification(id, title, message, type = 'processing') {
    const container = document.getElementById('progress-notifications');
    if (!container) return;

    // Remove existing notification with same ID
    removeProgressNotification(id);

    const notification = document.createElement('div');
    notification.className = `progress-notification ${type}`;
    notification.id = `notification-${id}`;

    // Choose icon based on type
    let icon = '🔍';
    if (type === 'processing') icon = '⚙️';
    else if (type === 'success') icon = '✅';
    else if (type === 'error') icon = '❌';
    else if (type === 'warning') icon = '⚠️';

    const time = new Date().toLocaleTimeString('he-IL');

    notification.innerHTML = `
        <div class="notification-icon">${icon}</div>
        <div class="notification-content">
            <div class="notification-title">${title}</div>
            <div class="notification-message">${message}</div>
            <div class="notification-time">${time}</div>
        </div>
    `;

    container.appendChild(notification);

    // Auto-scroll to bottom
    container.scrollTop = container.scrollHeight;
}

function updateProgressNotification(id, title, message, type = 'processing') {
    const notification = document.getElementById(`notification-${id}`);
    if (!notification) {
        // If notification doesn't exist, create it
        createProgressNotification(id, title, message, type);
        return;
    }

    // Update the notification
    notification.className = `progress-notification ${type}`;

    // Choose icon based on type
    let icon = '🔍';
    if (type === 'processing') icon = '⚙️';
    else if (type === 'success') icon = '✅';
    else if (type === 'error') icon = '❌';
    else if (type === 'warning') icon = '⚠️';

    const time = new Date().toLocaleTimeString('he-IL');

    notification.innerHTML = `
        <div class="notification-icon">${icon}</div>
        <div class="notification-content">
            <div class="notification-title">${title}</div>
            <div class="notification-message">${message}</div>
            <div class="notification-time">${time}</div>
        </div>
    `;

    // Auto-scroll to bottom
    const container = document.getElementById('progress-notifications');
    if (container) {
        container.scrollTop = container.scrollHeight;
    }
}

function removeProgressNotification(id) {
    const notification = document.getElementById(`notification-${id}`);
    if (notification) {
        notification.remove();
    }
}

async function updateProgress() {
    try {
        const response = await fetch('/api/analysis-progress');
        const progress = await response.json();

        if (progress.current_stage) {
            const processingStatus = document.getElementById('processing-status');
            if (processingStatus) {
                processingStatus.textContent = progress.current_stage;
            }
        }

        // Show new progress messages
        if (progress.progress_messages && progress.progress_messages.length > 0) {
            for (const message of progress.progress_messages) {
                if (!lastProgressMessages.includes(message)) {
                    let type = 'info';
                    if (message.includes('שלב:')) type = 'stage';
                    else if (message.includes('✓')) type = 'success';
                    else if (message.includes('✗')) type = 'error';

                    showProgressNotification(message, type);
                    lastProgressMessages.push(message);
                }
            }
        }
    } catch (error) {
        console.error('Error fetching progress:', error);
    }
}

function pollForCompletion() {
    // Start progress polling
    const progressInterval = setInterval(updateProgress, 500);

    const checkStatus = async () => {
        try {
            const response = await fetch('/api/analysis-status');
            const statusData = await response.json();

            if (!statusData.running) {
                // Stop progress polling
                clearInterval(progressInterval);

                // Analysis completed
                if (statusData.last_result === 'success') {
                    // Success
                    const status = document.getElementById('status');
                    const processingStatus = document.getElementById('processing-status');

                    status.textContent = 'הושלם';
                    status.className = 'value status-ready';
                    processingStatus.textContent = 'זיהוי הטבלה הושלם בהצלחה!';

                    // Show success notification
                    showProgressNotification('✅ העיבוד הושלם בהצלחה!', 'success');

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

                    // Show error notification
                    showProgressNotification('❌ העיבוד נכשל', 'error');
                }

                // Reset button
                resetAnalysisButton();

                // Clear notifications after 8 seconds
                setTimeout(() => {
                    clearProgressNotifications();
                    document.getElementById('processing-status').textContent = '';
                }, 8000);
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

// Auto-upload file from input folder if no file is currently loaded
async function autoUploadFromInputFolder() {
    try {
        // Always try to auto-upload if no PDF is currently visible
        const pdfPlaceholder = document.getElementById('pdf-placeholder');

        // Get list of available files
        const response = await fetch('/api/files');
        const data = await response.json();

        if (data && data.files && data.files.length > 0) {
            // Find the first PDF or image file
            const file = data.files.find(f =>
                f.name.toLowerCase().endsWith('.pdf') ||
                f.name.toLowerCase().endsWith('.png') ||
                f.name.toLowerCase().endsWith('.jpg') ||
                f.name.toLowerCase().endsWith('.jpeg')
            );

            if (file) {
                // Select and upload the file
                const selectResponse = await fetch('/api/select-file', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify({ filename: file.name })
                });

                const selectData = await selectResponse.json();

                if (selectData && selectData.success) {
                    // Update current file display
                    const currentFileEl = document.getElementById('current-file');
                    if (currentFileEl) {
                        currentFileEl.textContent = file.name;
                    }

                    // Load PDF if it's a PDF file
                    if ((selectData.pdf_path || selectData.path) && file.name.toLowerCase().endsWith('.pdf')) {
                        const pdfPath = selectData.pdf_path || `/input/${file.name}`;
                        loadPDF(pdfPath);

                        // After loading PDF, also load the table data for page 1
                        setTimeout(() => {
                            updatePageDisplays(1);
                        }, 1000);
                    }
                } else {
                    console.error('Auto-upload failed:', selectData.error);
                }
            }
        }
    } catch (error) {
        console.error('Error in auto-upload:', error);
    }
}

// Display analysis data in the UI
function displayAnalysisData(data) {
    console.log('🎯 [DISPLAY ANALYSIS] Function called with data:', data);
    console.log('🎯 [DISPLAY ANALYSIS] Data type:', typeof data);
    console.log('🎯 [DISPLAY ANALYSIS] Data keys:', Object.keys(data || {}));

    // Store data for later use when switching tabs
    window.lastAnalysisData = data;

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
    }

    // Process OCR data if available (prioritize over header data) - MOVED OUTSIDE sections block
    // Support multiple data formats: analysis.section_2_ocr, data.section_2_ocr, data.ocr_data
    console.log('🔍 [OCR DEBUG] Checking for OCR data in:', data);
    console.log('🔍 [OCR DEBUG] data.analysis:', data.analysis);
    console.log('🔍 [OCR DEBUG] data.analysis?.section_2_ocr:', data.analysis?.section_2_ocr);
    console.log('🔍 [OCR DEBUG] data.section_2_ocr:', data.section_2_ocr);
    console.log('🔍 [OCR DEBUG] data.ocr_data:', data.ocr_data);

    const ocrData = (data.analysis && data.analysis.section_2_ocr) || data.section_2_ocr || data.ocr_data;
    console.log('🔍 [OCR DEBUG] Final resolved ocrData:', ocrData);

    if (ocrData) {
        console.log('✅ [OCR DEBUG] Processing OCR data:', ocrData);

        // Map OCR fields to form fields with null checks
        console.log('🔍 [OCR DEBUG] Starting field mapping...');

        if (ocrData['לקוח/פרויקט'] && ocrData['לקוח/פרויקט'] !== 'empty') {
            console.log('✅ [OCR DEBUG] Setting customer:', ocrData['לקוח/פרויקט']);
            const customerEl = document.getElementById('detail-customer');
            const customerNameEl = document.getElementById('customer-name');
            console.log('🔍 [OCR DEBUG] customerEl:', customerEl);
            console.log('🔍 [OCR DEBUG] customerNameEl:', customerNameEl);
            if (customerEl) customerEl.value = ocrData['לקוח/פרויקט'];
            if (customerNameEl) customerNameEl.textContent = ocrData['לקוח/פרויקט'];
        } else {
            console.log('❌ [OCR DEBUG] Customer field not found or empty:', ocrData['לקוח/פרויקט']);
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

    // Table section - only populate table if table-tab is active
    if (sections && sections.main_table && sections.main_table.found) {
        const table = sections.main_table;

        // Check if table tab is active before populating
        const tableTab = document.getElementById('table-tab');
        const isTableTabActive = tableTab && tableTab.classList.contains('active');

        console.log('[TABLE] Table data found, checking if table tab is active...');
        console.log('[TABLE] Table tab element:', tableTab);
        console.log('[TABLE] Is table tab active:', isTableTabActive);

        if (isTableTabActive) {
                console.log('[TABLE] ✅ Table tab is active - populating table data');
                document.getElementById('total-rows').textContent = table.row_count || 0;
                document.getElementById('order-type').textContent =
                    table.contains_iron_orders ? 'הזמנת ברזל' : 'אחר';

                // Populate table with sample items
                const tbody = document.getElementById('items-tbody');
                tbody.innerHTML = '';

                // Use all_items if available, otherwise fall back to sample_items
                const items = table.all_items || table.sample_items || [];
                if (items.length > 0) {
                    items.forEach((item, index) => {
                        const row = tbody.insertRow();
                        row.setAttribute('data-row-id', index);

                        // Get actual order line number
                        const itemOrderLineNo = Array.isArray(item) ? (item[0] || (index + 1)) : (item['מס'] || item['מס\''] || (index + 1));
                        row.setAttribute('data-order-line-no', itemOrderLineNo);

                        // Expand button and identification button
                        const expandCell = row.insertCell(0);
                        expandCell.innerHTML = `
                            <div style="display: flex; flex-direction: column; align-items: center; gap: 2px;">
                                <button class="expand-btn" onclick="toggleRow(${index})">+</button>
                                <button class="identification-btn-small" onclick="runShapeIdentification('shape-row-1-${itemOrderLineNo}')" title="הפעל זיהוי צורה">
                                    זיהוי
                                </button>
                            </div>
                        `;

                        // Handle both array format and object format
                        if (Array.isArray(item)) {
                            // Array format: [מס', סה"כ משקל, אורך, סה"כ יח', קוטר, הערות]
                            row.insertCell(1).textContent = item[0] || (index + 1);  // מס'
                            row.insertCell(2).textContent = '-';  // קטלוג - not available in array format

                            // צורה column with template iframe (default template 210 for array format)
                            const shapeCell = row.insertCell(3);
                            const templateNumber = '210'; // Default template for array format

                            if (templateNumber && templateNumber !== '-' && templateNumber !== '') {
                                const templateUrl = `/shape_template/${templateNumber}`;
                                shapeCell.innerHTML = `
                                    <iframe src="${templateUrl}"
                                            class="table-shape-image"
                                            title=""
                                            style="width: 50px; height: 40px; border: none; overflow: hidden; pointer-events: none;"
                                            scrolling="no">
                                    </iframe>
                                `;
                            } else {
                                shapeCell.innerHTML = '<span>תבנית לא זמינה</span>';
                            }

                            row.insertCell(4).textContent = item[4] || '-';  // קוטר [mm]
                            row.insertCell(5).textContent = item[3] || '1';  // סה"כ יח'
                            row.insertCell(6).textContent = item[5] || '-';  // הערות

                            // Add check button
                            const checkCell = row.insertCell(7);
                            checkCell.innerHTML = '<button class="check-btn">✓</button>';
                        } else {
                            // Object format (fallback)
                            row.insertCell(1).textContent = item['מס\''] || item['מס'] || (index + 1);
                            const catalogNumber = item['מספר קטלוגי'] || item['catalog'] || '-';
                            row.insertCell(2).textContent = catalogNumber;

                            // צורה column with template iframe
                            const shapeCell = row.insertCell(3);

                            if (catalogNumber && catalogNumber !== '-' && catalogNumber !== '') {
                                const templateUrl = `/shape_template/${catalogNumber}`;
                                shapeCell.innerHTML = `
                                    <iframe src="${templateUrl}"
                                            class="table-shape-image"
                                            title=""
                                            style="width: 50px; height: 40px; border: none; overflow: hidden; pointer-events: none;"
                                            scrolling="no">
                                    </iframe>
                                `;
                            } else {
                                shapeCell.innerHTML = '<span>תבנית לא זמינה</span>';
                            }

                            row.insertCell(4).textContent = item['קוטר'] || item['קוטר [mm]'] || '-';
                            row.insertCell(5).textContent = item['יחידות'] || item['units'] || item['כמות'] || item['סה"כ יח\''] || '1';
                            row.insertCell(6).textContent = item['הערות'] || '-';

                            // Add check button
                            const checkCell = row.insertCell(7);
                            checkCell.innerHTML = '<button class="check-btn">✓</button>';
                        }
                    });
                } else {
                    tbody.innerHTML = '<tr><td colspan="8" class="no-data">אין נתונים להצגה</td></tr>';
                }
        } else {
            console.log('[TABLE] ❌ Table tab is NOT active - clearing table and exiting');
            // Clear table if not on table tab
            const tbody = document.getElementById('items-tbody');
            if (tbody) {
                tbody.innerHTML = '<tr><td colspan="8" class="no-data">בחר כרטיסית "טבלה" לצפות בנתונים</td></tr>';
                console.log('[TABLE] Table cleared with placeholder message');
            } else {
                console.log('[TABLE] No tbody element found to clear');
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
    console.log('[TAB SWITCH] Switching to tab:', tabName);

    // Update tab buttons
    document.querySelectorAll('.tab-btn').forEach(btn => {
        btn.classList.toggle('active', btn.dataset.tab === tabName);
    });

    // Update tab content
    document.querySelectorAll('.tab-content').forEach(content => {
        const isActive = content.id === `${tabName}-tab`;
        content.classList.toggle('active', isActive);
        console.log('[TAB SWITCH] Tab content', content.id, isActive ? 'activated' : 'deactivated');
    });

    // Handle shapes tab activation - populate with stored data
    if (tabName === 'shapes' && globalShapesData && globalCurrentPage) {
        console.log('📐 Shapes tab activated - calling updateShapesDisplay with stored data');
        // Small delay to ensure DOM is ready
        setTimeout(() => {
            updateShapesDisplay(globalShapesData, globalCurrentPage);
        }, 50);
    }

    // Handle table tab activation - repopulate table data
    if (tabName === 'table') {
        console.log('📊 Table tab activated - repopulating table data');
        // Re-trigger the table population by calling displayAnalysisData if we have stored data
        if (window.lastAnalysisData) {
            setTimeout(() => {
                displayAnalysisData(window.lastAnalysisData);
            }, 50);
        }
    }

    // Handle header tab activation - repopulate header data
    if (tabName === 'header') {
        console.log('📋 [HEADER TAB] Header tab activated - repopulating header data');
        console.log('📋 [HEADER TAB] window.lastAnalysisData:', window.lastAnalysisData);
        // Re-trigger the header population by calling displayAnalysisData if we have stored data
        if (window.lastAnalysisData) {
            console.log('📋 [HEADER TAB] Re-triggering displayAnalysisData...');
            setTimeout(() => {
                console.log('📋 [HEADER TAB] Executing displayAnalysisData with stored data');
                displayAnalysisData(window.lastAnalysisData);
            }, 50);
        } else {
            console.log('❌ [HEADER TAB] No stored analysis data available');
        }
    }
}

// Shapes table is now populated by updateShapesDisplay() function (Version 15 format)

// Update page displays
function updatePageDisplays(pageNumber) {
    console.log(`[UPDATE PAGE DISPLAYS] Called with page ${pageNumber}`);
    // Update the title page display
    const titlePageDisplay = document.getElementById('title-page-display');
    if (titlePageDisplay) {
        titlePageDisplay.textContent = `עמוד ${pageNumber}`;
    }

    // Update table data for current page
    console.log(`[UPDATE PAGE DISPLAYS] About to call updateTableForCurrentPage(${pageNumber})`);
    updateTableForCurrentPage(pageNumber);
}

// Filter and display table OCR data for specific page
function updateTableForCurrentPage(pageNumber) {
    console.log(`[API FETCH] ✅ NEW FIX ACTIVE - Fetching data for page ${pageNumber}`);
    // Fetch table OCR data from the new API endpoint
    fetch(`/api/table-ocr/${pageNumber}`)
        .then(response => response.json())
        .then(data => {
            console.log(`[TABLE API] Received data for page ${pageNumber}:`, data);
            if (data.success) {
                console.log(`[TABLE API] Success! Processing ${data.rows.length} rows`);
                // Transform the OCR data format to match our table structure
                const transformedItems = data.rows.map((row, index) => {
                    const transformed = {
                        'מס': row['מס'] || row['row_number'] || '',
                        'קטלוג': row['קטלוג'] || '-', // Catalog number from database
                        'shape': row['shape'] || '-', // Shape information for צורה column
                        'קוטר': row['קוטר'] || '-',
                        'סהכ יחידות': row['סהכ יחידות'] || '-',
                        'אורך': row['אורך'] || '-',
                        'משקל': row['משקל'] || '-',
                        'הערות': row['הערות'] || '-',
                        'checked': row['checked'] || false  // Use checked status from database
                    };
                    console.log(`[TABLE API] Row ${index + 1} transformed:`, transformed);
                    return transformed;
                });

                console.log(`[TABLE API] Calling displayTableItems with ${transformedItems.length} items`);
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

// Refresh current table data without changing the page
function refreshCurrentTableData() {
    console.log('🔄 Refreshing current table data...');

    // Get current page number from the first row or page display
    const firstRow = document.querySelector('tr[data-page]');
    const currentPage = firstRow ? firstRow.getAttribute('data-page') :
                       (document.getElementById('page-num') ? document.getElementById('page-num').textContent : '1');

    console.log(`🔄 Refreshing data for page ${currentPage}`);

    // Add loading indicator to refresh button
    const refreshBtn = document.getElementById('refresh-table-btn');
    if (refreshBtn) {
        const originalText = refreshBtn.innerHTML;
        refreshBtn.innerHTML = '<span class="btn-icon">⏳</span>מרענן...';
        refreshBtn.disabled = true;

        // Reset button after refresh
        setTimeout(() => {
            refreshBtn.innerHTML = originalText;
            refreshBtn.disabled = false;
        }, 2000);
    }

    // Reload table data for current page
    updateTableForCurrentPage(parseInt(currentPage));

    // Also refresh shapes data if on shapes tab
    const shapesTab = document.querySelector('.tab-btn[data-tab="shapes"]');
    if (shapesTab && shapesTab.classList.contains('active')) {
        updateShapesDisplay(globalShapesData || [], parseInt(currentPage));
    }
}

// Refresh a specific row after shape identification
function refreshSpecificRow(rowId) {
    console.log(`🔄 Refreshing specific row: ${rowId}`);

    // Extract page number and line number from rowId (format: shape-row-{page}-{line})
    const parts = rowId.split('-');
    if (parts.length < 4) {
        console.error('Invalid rowId format:', rowId);
        return;
    }

    const pageNumber = parseInt(parts[2]);
    const lineNumber = parts[3];

    console.log(`🔄 Refreshing page ${pageNumber}, line ${lineNumber}`);

    // Reload the entire table data for the current page
    updateTableForCurrentPage(pageNumber);
}

// Display table items in the UI
function displayTableItems(items, pageNumber) {
    console.log(`[DISPLAY TABLE] FUNCTION CALLED with ${items.length} items for page ${pageNumber}`);
    console.log(`[DISPLAY TABLE] Items received:`, items);
    const tbody = document.getElementById('items-tbody');
    if (!tbody) {
        console.log('❌ Table body not found');
        return;
    }

    tbody.innerHTML = '';

    if (items.length > 0) {
        console.log(`📊 Displaying ${items.length} items for page ${pageNumber}`);

        // Template fix applied - visual test removed

        items.forEach((item, index) => {
            const row = tbody.insertRow();
            row.setAttribute('data-row-id', index);
            row.setAttribute('data-page', pageNumber);

            // Store the actual order line number as data attribute for later use
            const orderLineNo = Array.isArray(item)
                ? (item[0] || (index + 1))
                : (item['מס'] || item['מס\''] || (index + 1));
            row.setAttribute('data-order-line-no', orderLineNo);
            console.log(`[ROW CREATED] Page ${pageNumber}, Index ${index}, Order Line No: ${orderLineNo}`);

            // Expand button and identification button
            const expandCell = row.insertCell(0);
            expandCell.innerHTML = `
                <div style="display: flex; flex-direction: column; align-items: center; gap: 2px;">
                    <button class="expand-btn" onclick="toggleRow(${index})">+</button>
                    <button class="identification-btn-small" onclick="runShapeIdentification('shape-row-${pageNumber}-${orderLineNo}')" title="הפעל זיהוי צורה">
                        זיהוי
                    </button>
                </div>
            `;

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

                        // If catalog field is updated, also update it in shapes section
                        if (fieldName === 'catalog') {
                            const rowId = `shape-row-${pageNumber}-${orderLineNo}`;
                            const shapeCatalogInput = document.getElementById(`catalog-input-${rowId}`);
                            if (shapeCatalogInput) {
                                shapeCatalogInput.value = this.value;
                                updateCatalogImage(this.value, rowId);
                            }

                            // Immediately update expanded table if this row is expanded
                            updateExpandedTablesForRow(pageNumber, index, this.value);

                            // Update the shape field (צורה column) with new shape template
                            updateShapeFieldForCatalog(index, this.value);
                        }
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
                createEditableCell('-', 'catalog');  // catalog - not available in array format

                // צורה column with shape image - DIRECT TEMPLATE LOADING
                const shapeCell = row.insertCell();
                const orderNumber = getCurrentOrderNumber();

                // Get the actual order line number from the item data (not array position)
                const orderLineNo = item['מס'] || item['מס\''] || (index + 1);

                // Get catalog number from the item data and map to available templates
                const rawCatalogNumber = Array.isArray(item) ? null : (item['קטלוג'] || item['catalog'] || item['shape']);

                // Map shape numbers to available templates
                const templateMap = {
                    '210': '210',
                    '220': '210', // fallback to 210
                    '218': '218',
                    '104': '104',
                    '107': '107',
                    '000': '000'
                };

                const catalogNumber = templateMap[rawCatalogNumber] || rawCatalogNumber;
                console.log(`[DISPLAY TABLE] 🎯 TEMPLATE MAPPING - Raw: ${rawCatalogNumber} -> Mapped: ${catalogNumber} (item:`, item, ')');

                // Template mapping working - debug styling removed

                // Create iframe directly like the working extended area code
                if (catalogNumber && catalogNumber !== 'NA' && catalogNumber !== '-') {
                    console.log(`[DISPLAY TABLE] 🎯 Creating template iframe for catalog ${catalogNumber}`);

                    // Create iframe directly in the cell to show the template with proper centering
                    // Use orderLineNo (actual line number from data) instead of array position
                    const templateUrl = `/shape_template/${catalogNumber}?order=${orderNumber}&page=${pageNumber}&line=${orderLineNo}`;
                    shapeCell.innerHTML = `
                        <div style="width: 100%; height: 110px; overflow: hidden; position: relative; background: white;">
                            <iframe src="${templateUrl}"
                                    style="width: 600px; height: 350px; border: none; position: absolute; top: 55%; left: 50%; transform: translate(-50%, -50%) scale(0.7);"
                                    scrolling="no"
                                    title="Template ${catalogNumber}">
                            </iframe>
                        </div>
                    `;

                    console.log(`[DISPLAY TABLE] ✅ Template iframe created for catalog ${catalogNumber}`);
                } else {
                    console.log(`[DISPLAY TABLE] 🎯 No valid catalog for shape cell: ${catalogNumber} (condition failed)`);
                    shapeCell.innerHTML = `<div style="color: gray; font-size: 10px; text-align: center;">אין קטלוג</div>`;
                }

                createEditableCell(item[4] || '-', 'קוטר');
                createEditableCell(item[3] || '1', 'סהכ יחידות');
                createEditableCell(item[5] || '-', 'הערות');
            } else {
                // Object format - now handles OCR data structure properly
                createEditableCell(item['מס'] || item['מס\''] || (index + 1), 'מס');
                createEditableCell(item['קטלוג'] || item['catalog'] || '-', 'catalog');

                // צורה column with shape image - DIRECT TEMPLATE LOADING
                const shapeCell = row.insertCell();
                const orderNumber = getCurrentOrderNumber();

                // Get the actual order line number from the item data (not array position)
                const orderLineNo = item['מס'] || item['מס\''] || (index + 1);

                // Get catalog number from the item data and map to available templates
                const rawCatalogNumber = Array.isArray(item) ? null : (item['קטלוג'] || item['catalog'] || item['shape']);

                // Map shape numbers to available templates
                const templateMap = {
                    '210': '210',
                    '220': '210', // fallback to 210
                    '218': '218',
                    '104': '104',
                    '107': '107',
                    '000': '000'
                };

                const catalogNumber = templateMap[rawCatalogNumber] || rawCatalogNumber;
                console.log(`[DISPLAY TABLE] 🎯 TEMPLATE MAPPING - Raw: ${rawCatalogNumber} -> Mapped: ${catalogNumber} (item:`, item, ')');

                // Template mapping working - debug styling removed

                // Create iframe directly like the working extended area code
                if (catalogNumber && catalogNumber !== 'NA' && catalogNumber !== '-') {
                    console.log(`[DISPLAY TABLE] 🎯 Creating template iframe for catalog ${catalogNumber}`);

                    // Create iframe directly in the cell to show the template with proper centering
                    // Use orderLineNo (actual line number from data) instead of array position
                    const templateUrl = `/shape_template/${catalogNumber}?order=${orderNumber}&page=${pageNumber}&line=${orderLineNo}`;
                    shapeCell.innerHTML = `
                        <div style="width: 100%; height: 110px; overflow: hidden; position: relative; background: white;">
                            <iframe src="${templateUrl}"
                                    style="width: 600px; height: 350px; border: none; position: absolute; top: 55%; left: 50%; transform: translate(-50%, -50%) scale(0.7);"
                                    scrolling="no"
                                    title="Template ${catalogNumber}">
                            </iframe>
                        </div>
                    `;

                    console.log(`[DISPLAY TABLE] ✅ Template iframe created for catalog ${catalogNumber}`);
                } else {
                    console.log(`[DISPLAY TABLE] 🎯 No valid catalog for shape cell: ${catalogNumber} (condition failed)`);
                    shapeCell.innerHTML = `<div style="color: gray; font-size: 10px; text-align: center;">אין קטלוג</div>`;
                }

                createEditableCell(item['קוטר'] || '-', 'קוטר');
                createEditableCell(item['סהכ יחידות'] || item['יחידות'] || item['units'] || item['כמות'] || '1', 'סהכ יחידות');
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

        // Update row count
        document.getElementById('total-rows').textContent = items.length;

        console.log(`✅ Table updated: ${items.length} items`);

        // Initialize row lock states after table is rendered
        setTimeout(() => {
            initializeRowLockStates();
        }, 100);

        // Update shapes display for current page
        updateShapesDisplay(items, pageNumber);
    } else {
        tbody.innerHTML = '<tr><td colspan="9" class="no-data">אין נתונים להצגה עבור עמוד ' + pageNumber + '</td></tr>';

        // Update total weight if element exists
        const totalWeightEl = document.getElementById('total-weight');
        if (totalWeightEl) {
            totalWeightEl.textContent = '0 kg';
        }

        // Update total rows if element exists
        const totalRowsEl = document.getElementById('total-rows');
        if (totalRowsEl) {
            totalRowsEl.textContent = '0';
        }

        console.log(`📄 No data to display for page ${pageNumber}`);

        // Clear shapes display when no data
        updateShapesDisplay([], pageNumber);
    }
}

// Global storage for shapes data
let globalShapesData = null;
let globalCurrentPage = null;

// Update shapes display for current page
async function updateShapesDisplay(items, pageNumber) {
    // Store data globally for later use when shapes tab is activated
    globalShapesData = items;
    globalCurrentPage = pageNumber;

    const shapesTable = document.getElementById('shapes-table');
    const shapesBody = document.getElementById('shapes-tbody');

    if (!shapesTable || !shapesBody) {
        console.log('📐 Shapes data stored (shapes tab not visible)');
        return;
    }

    // Check if we already have shape images loaded for this page
    const currentPageAttr = shapesTable.getAttribute('data-current-page');
    if (currentPageAttr === String(pageNumber)) {
        // Already showing shapes for this page, don't reload
        console.log(`📐 Shape images already loaded for page ${pageNumber}`);
        return;
    }

    // Get current order number
    const orderNumber = getCurrentOrderNumber();
    if (!orderNumber) {
        console.log('❌ No order number available for shape images');
        shapesBody.innerHTML = `<tr><td colspan="4" class="no-shapes-placeholder">לא נמצאו תמונות צורות</td></tr>`;
        return;
    }

    // Clear table body and set current page
    shapesBody.innerHTML = '';
    shapesTable.setAttribute('data-current-page', pageNumber);

    // Fetch shape images for this page
    let shapeImages = [];
    try {
        const response = await fetch(`/api/shape-images/${orderNumber}/${pageNumber}`);
        const imageData = await response.json();
        if (imageData.success) {
            shapeImages = imageData.images || [];
        }
    } catch (error) {
        console.log('Could not fetch shape images:', error);
    }

    // Update summary section
    const totalShapesEl = document.getElementById('total-shapes');
    const currentPageEl = document.getElementById('current-shapes-page');
    const statusEl = document.getElementById('shapes-status');

    if (totalShapesEl) totalShapesEl.textContent = shapeImages.length;
    if (currentPageEl) currentPageEl.textContent = pageNumber;
    if (statusEl) {
        statusEl.textContent = shapeImages.length > 0 ? 'זוהו צורות' : 'לא נמצאו צורות';
    }

    console.log(`📐 Found ${shapeImages.length} shapes for page ${pageNumber}`);

    if (shapeImages.length > 0) {
        // Create table rows for each shape
        shapeImages.forEach((image, index) => {
            const rowId = `shape-row-${pageNumber}-${index + 1}`;

            // Create main data row
            const mainRow = document.createElement('tr');
            mainRow.className = 'shape-table-row';
            mainRow.innerHTML = `
                <td class="shape-page-row">
                    <div>${pageNumber}/${index + 1}</div>
                </td>
                <td class="shape-catalog-input-cell">
                    <input type="text"
                           class="catalog-input"
                           id="catalog-input-${rowId}"
                           data-row-id="${rowId}"
                           maxlength="5"
                           placeholder=""
                           pattern="[0-9]{1,5}"
                           title="הכנס מספר קטלוג (1-5 ספרות)"
                           style="width: 100%; text-align: center; font-size: 12px; padding: 2px; border: 1px solid #ccc; background: white;">
                    <div class="rib-count-container" style="margin-top: 4px; display: flex; align-items: center; gap: 4px;">
                        <button class="shape-id-btn-inline" onclick="runShapeIdentification('${rowId}')" title="הפעל זיהוי צורה">
                            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                                <path d="M9.5 3A6.5 6.5 0 0 1 16 9.5c0 1.61-.59 3.09-1.56 4.23l.27.27h.79l5 5-1.5 1.5-5-5v-.79l-.27-.27A6.516 6.516 0 0 1 9.5 16 6.5 6.5 0 0 1 3 9.5 6.5 6.5 0 0 1 9.5 3m0 2C7 5 5 7 5 9.5S7 14 9.5 14 14 12 14 9.5 12 5 9.5 5Z" fill="currentColor"/>
                                <path d="M12 10.5H14V12.5H12V10.5Z" fill="currentColor"/>
                                <path d="M10.5 6.5H12.5V8.5H10.5V6.5Z" fill="currentColor"/>
                                <path d="M8 8.5H10V10.5H8V8.5Z" fill="currentColor"/>
                            </svg>
                        </button>
                        <input type="text" class="rib-field rib-count" maxlength="2" style="width: 40px;" placeholder="מס׳ צלעות">
                    </div>
                </td>
                <td class="shape-drawing-cell" id="shape-cell-${rowId}">
                    <!-- Template iframe will be loaded here based on catalog data -->
                </td>
                <td class="shape-catalog-cell" id="catalog-image-${rowId}">
                    <div class="catalog-shape-placeholder">
                        <span>הכנס מספר קטלוג</span>
                    </div>
                </td>
            `;


            // Create rib fields HTML - First row: R1-R6, Second row: R7-R8 (under R1-R2)
            // Each rib now has 3 fields: Rib, Length, Angle grouped together with spacing
            let ribFieldsRow1Html = '';
            let ribFieldsRow2Html = '';

            // First row: R1-R6 (6 sets of 3 fields each)
            for (let i = 0; i < 6; i++) {
                ribFieldsRow1Html += `
                    <span class="rib-set">
                        <input type="text" class="rib-field rib-number" maxlength="2" style="width: 20px; margin-right: 1px;" placeholder="R${i+1}">
                        <input type="text" class="rib-field rib-length" maxlength="6" style="width: 40px; margin-right: 1px;" placeholder="L${i+1}">
                        <input type="text" class="rib-field rib-angle" maxlength="3" style="width: 30px;" placeholder="A${i+1}">
                    </span>
                    ${i < 5 ? '<span style="margin-right: 6px;"></span>' : ''}
                `;
            }

            // Second row: R7-R8 positioned exactly under R1-R2
            for (let i = 6; i < 8; i++) {
                ribFieldsRow2Html += `
                    <span class="rib-set">
                        <input type="text" class="rib-field rib-number" maxlength="2" style="width: 20px; margin-right: 1px;" placeholder="R${i+1}">
                        <input type="text" class="rib-field rib-length" maxlength="6" style="width: 40px; margin-right: 1px;" placeholder="L${i+1}">
                        <input type="text" class="rib-field rib-angle" maxlength="3" style="width: 30px;" placeholder="A${i+1}">
                    </span>
                    ${i < 7 ? '<span style="margin-right: 6px;"></span>' : ''}
                `;
            }

            // Add empty space to align R7 under R1, R8 under R2 (fill remaining space)
            ribFieldsRow2Html += `<span style="width: ${4 * (20 + 1 + 40 + 1 + 30 + 6)}px; display: inline-block;"></span>`;

            // Create first rib fields row
            const ribRow1 = document.createElement('tr');
            ribRow1.className = 'shape-rib-row';
            ribRow1.innerHTML = `
                <td colspan="4" class="rib-fields-cell" style="padding: 4px 8px;">
                    <div style="display: grid; grid-template-columns: repeat(6, 1fr); gap: 6px; font-size: 11px;">
                        ${Array.from({length: 6}, (_, i) => `
                            <div class="rib-set rib-set-${i+1}" id="rib-set-${rowId}-${i+1}" style="display: none; gap: 1px; position: relative;">
                                ${i === 0 ? '<div style="position: absolute; top: -28px; left: 0; font-size: 10px; color: #666; white-space: nowrap;">אורכי צלע וזוויות:</div>' : ''}
                                <input type="text" class="rib-field rib-number" maxlength="2" style="width: 20px;" placeholder="R${i+1}">
                                <input type="text" class="rib-field rib-length" maxlength="6" style="width: 40px;" placeholder="L${i+1}">
                                <input type="text" class="rib-field rib-angle" maxlength="3" style="width: 30px;" placeholder="A${i+1}">
                            </div>
                        `).join('')}
                    </div>
                </td>
            `;

            // Create second rib fields row
            const ribRow2 = document.createElement('tr');
            ribRow2.className = 'shape-rib-row';
            ribRow2.innerHTML = `
                <td colspan="4" class="rib-fields-cell" style="padding: 4px 8px; border-top: none; position: relative;">
                    <div style="display: grid; grid-template-columns: repeat(6, 1fr); gap: 6px; font-size: 11px;">
                        ${Array.from({length: 6}, (_, i) => {
                            if (i < 2) {
                                return `
                                    <div class="rib-set" id="rib-set-${rowId}-${i+7}" style="display: none; gap: 1px;">
                                        <input type="text" class="rib-field rib-number" maxlength="2" style="width: 20px;" placeholder="R${i+7}">
                                        <input type="text" class="rib-field rib-length" maxlength="6" style="width: 40px;" placeholder="L${i+7}">
                                        <input type="text" class="rib-field rib-angle" maxlength="3" style="width: 30px;" placeholder="A${i+7}">
                                    </div>
                                `;
                            } else {
                                return '<div></div>'; // Empty grid cell
                            }
                        }).join('')}
                    </div>
                    <div style="position: absolute; bottom: -3px; left: 0; right: 0; height: 2px; background-color: #2196F3; z-index: 10;"></div>
                </td>
            `;

            // Append all rows
            shapesBody.appendChild(mainRow);
            shapesBody.appendChild(ribRow1);
            shapesBody.appendChild(ribRow2);

            // Load template iframe based on catalog data from JSON
            loadShapeTemplateFromJSON(pageNumber, index + 1, rowId);

            // Add event listener for catalog input and set initial value
            const catalogInput = document.getElementById(`catalog-input-${rowId}`);
            // Set the catalog value from the item data if available
            if (items && items[index] && items[index]['קטלוג']) {
                catalogInput.value = items[index]['קטלוג'];
                // Also update the catalog image immediately
                updateCatalogImage(items[index]['קטלוג'], rowId);
            }

            // Store original value for change tracking
            catalogInput.setAttribute('data-original-value', catalogInput.value || '');

            catalogInput.addEventListener('input', function() {
                updateCatalogImage(this.value, rowId);
                // Also update the catalog number in the orders table
                saveTableCell(pageNumber, index, 'catalog', this.value);

                // Update the catalog field in the orders table
                const tbody = document.getElementById('items-tbody');
                if (tbody && tbody.rows[index]) {
                    const catalogCell = tbody.rows[index].cells[2]; // קטלוג is the 3rd column (index 2)
                    const catalogInput = catalogCell ? catalogCell.querySelector('input') : null;
                    if (catalogInput) {
                        catalogInput.value = this.value;
                        catalogInput.setAttribute('data-original-value', this.value);
                    }
                }

                // Fetch number of ribs from catalog when a catalog number is entered
                if (this.value.trim()) {
                    fetchCatalogRibs(this.value.trim(), rowId);
                }
            });

            // Add blur event to call Form1dat2 when field loses focus and value changed
            catalogInput.addEventListener('blur', function() {
                const originalValue = this.getAttribute('data-original-value') || '';
                const currentValue = this.value.trim();

                if (originalValue !== currentValue && currentValue !== '') {
                    console.log(`[SHAPES TABLE] Catalog number changed from "${originalValue}" to "${currentValue}" for ${rowId}`);

                    // Call Form1dat2 API to update central output file
                    updateCatalogNumber(pageNumber, index + 1, currentValue);

                    // Update stored original value
                    this.setAttribute('data-original-value', currentValue);
                }
            });

            // Add event listener for rib count input
            const ribCountInput = document.querySelector(`#catalog-input-${rowId}`).parentElement.querySelector('.rib-count');
            ribCountInput.addEventListener('input', function() {
                updateRibFieldsVisibility(this.value, rowId);
            });
        });
    } else {
        // No images found
        shapesBody.innerHTML = `
            <tr>
                <td colspan="4" class="no-shapes-placeholder">
                    <p>🔍 לא נמצאו תמונות צורות בעמוד ${pageNumber}</p>
                </td>
            </tr>
        `;
    }

    console.log(`📐 Shape images displayed: ${shapeImages.length} images found for page ${pageNumber}`);
}

// Fetch number of ribs from catalog API
async function fetchCatalogRibs(catalogNumber, rowId) {
    try {
        console.log(`🔍 Fetching ribs count for catalog number: ${catalogNumber}`);
        const response = await fetch(`/api/catalog-ribs/${catalogNumber}`);
        const data = await response.json();

        if (data.success) {
            const numberOfRibs = data.number_of_ribs;
            console.log(`📐 Found ${numberOfRibs} ribs for catalog ${catalogNumber}`);

            // Find the rib count input field for this row
            const ribCountInput = document.querySelector(`#catalog-input-${rowId}`).parentElement.querySelector('.rib-count');
            if (ribCountInput) {
                // Update the rib count field
                ribCountInput.value = numberOfRibs;
                // Trigger the visibility update for rib fields
                updateRibFieldsVisibility(numberOfRibs, rowId);
                console.log(`✅ Updated ribs count to ${numberOfRibs} for row ${rowId}`);
            }
        } else {
            console.log(`⚠️ Catalog number ${catalogNumber} not found in catalog`);
        }
    } catch (error) {
        console.error(`❌ Error fetching catalog ribs for ${catalogNumber}:`, error);
    }
}

// Update rib fields visibility based on number of ribs
function updateRibFieldsVisibility(ribCount, rowId) {
    const count = parseInt(ribCount) || 0;

    // Show/hide rib fields based on count (1-8 ribs max)
    for (let i = 1; i <= 8; i++) {
        const ribSet = document.getElementById(`rib-set-${rowId}-${i}`);
        if (ribSet) {
            if (i <= count) {
                ribSet.style.display = 'flex';
            } else {
                ribSet.style.display = 'none';
            }
        }
    }
}

// Open image modal for shape images
function openImageModal(imageUrl, shapeName, lineInfo) {
    // Remove any existing modal
    const existingModal = document.getElementById('image-modal');
    if (existingModal) {
        existingModal.remove();
    }

    // Create modal overlay
    const modal = document.createElement('div');
    modal.id = 'image-modal';
    modal.className = 'image-modal-overlay';
    modal.innerHTML = `
        <div class="image-modal-content">
            <div class="image-modal-header">
                <h3>צורה: ${shapeName}</h3>
                <p>${lineInfo}</p>
                <button class="image-modal-close" onclick="closeImageModal()">&times;</button>
            </div>
            <div class="image-modal-body">
                <img src="${imageUrl}" alt="צורה" class="image-modal-img">
            </div>
        </div>
    `;

    // Add click outside to close
    modal.addEventListener('click', function(e) {
        if (e.target === modal) {
            closeImageModal();
        }
    });

    // Add to body
    document.body.appendChild(modal);
}

// Close image modal
function closeImageModal() {
    const modal = document.getElementById('image-modal');
    if (modal) {
        modal.remove();
    }
}

// Toggle check status for a line
async function toggleCheckStatus(pageNumber, lineNumber, checked, buttonElement) {
    try {
        // Get the current order number
        const orderNumber = getCurrentOrderNumber();
        console.log('[DEBUG CHECK] Order number:', orderNumber);
        console.log('[DEBUG CHECK] Current data:', currentData);
        if (!orderNumber) {
            console.error('[DEBUG CHECK] No order number found!');
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
        const requestData = {
            order_number: orderNumber,
            page_number: pageNumber,
            line_number: lineNumber,
            checked: checked
        };
        console.log('[DEBUG CHECK] Sending request with:', requestData);
        console.log('[DEBUG CHECK] orderNumber:', orderNumber);
        console.log('[DEBUG CHECK] pageNumber:', pageNumber);
        console.log('[DEBUG CHECK] lineNumber:', lineNumber);
        console.log('[DEBUG CHECK] checked:', checked);

        const response = await fetch('/api/update-checked-status', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(requestData)
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

// Update catalog number using Form1dat2 API
async function updateCatalogNumber(pageNumber, lineNumber, catalogNumber) {
    try {
        console.log(`[DEBUG] Calling Form1dat2 API: Page ${pageNumber}, Line ${lineNumber}, Catalog ${catalogNumber}`);

        const orderNumber = getCurrentOrderNumber();
        if (!orderNumber) {
            console.warn('No order number available for catalog update');
            return;
        }

        const response = await fetch('/api/update-table-cell', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                page: pageNumber,
                row_index: lineNumber - 1,  // Convert to 0-based index
                field_name: 'catalog',
                new_value: catalogNumber
            })
        });

        const result = await response.json();

        if (result.success) {
            console.log('✅ Form1dat2 catalog update successful:', result.message);
            if (result.updated_fields) {
                console.log('Updated fields:', result.updated_fields);
            }
        } else {
            console.error('❌ Form1dat2 catalog update failed:', result.error);
        }
    } catch (error) {
        console.error('❌ Error calling Form1dat2 API:', error);
    }
}

// Update last update time
function updateLastUpdateTime() {
    const now = new Date();
    const timeStr = now.toLocaleTimeString('he-IL');
    const dateStr = now.toLocaleDateString('he-IL');
    document.getElementById('last-update').textContent = `עדכון אחרון: ${dateStr} ${timeStr}`;
}

// Toggle row expansion for rib details
async function toggleRow(rowId) {
    console.log(`%c🔄 TOGGLE: Row expansion called for rowId: ${rowId}`, 'color: purple; font-weight: bold; font-size: 14px;');

    // Get elements first (before refresh which might modify DOM)
    const tbody = document.getElementById('items-tbody');
    const row = tbody.querySelector(`tr[data-row-id="${rowId}"]`);
    const expandBtn = row.querySelector('.expand-btn');
    const existingExpanded = tbody.querySelector(`tr[data-expanded-for="${rowId}"]`);

    // If collapsing, no need to refresh
    if (existingExpanded) {
        console.log(`🔄 TOGGLE: Collapsing row ${rowId} - no refresh needed`);
        existingExpanded.remove();
        expandBtn.textContent = '+';
        expandBtn.classList.remove('expanded');
        return;
    }

    // Refresh disabled - proceeding directly with expansion
    console.log(`🔄 TOGGLE: Proceeding with expansion (refresh disabled)`);

    // Get elements directly (no refresh needed)
    const refreshedTbody = document.getElementById('items-tbody');
    const refreshedRow = refreshedTbody.querySelector(`tr[data-row-id="${rowId}"]`);
    const refreshedExpandBtn = refreshedRow.querySelector('.expand-btn');

    console.log(`🔄 TOGGLE: Proceeding with expansion`);

    // Get the catalog number from the refreshed row (assuming it's in the 3rd cell - קטלוג column)
    console.log(`🔄 TOGGLE: Getting catalog number from refreshed row, cells:`, refreshedRow.cells);

    let catalogNumber = null;
    const catalogCell = refreshedRow.cells[2]; // קטלוג column (index 2)
    console.log(`🔄 TOGGLE: Catalog cell (index 2):`, catalogCell);

    if (catalogCell) {
        const catalogInput = catalogCell.querySelector('input');
        console.log(`🔄 TOGGLE: Catalog input in cell:`, catalogInput);

        if (catalogInput) {
            catalogNumber = catalogInput.value;
            console.log(`🔄 TOGGLE: Catalog from input value: "${catalogNumber}"`);
        } else {
            catalogNumber = catalogCell.textContent.trim();
            console.log(`🔄 TOGGLE: Catalog from cell text: "${catalogNumber}"`);
        }
    }

    console.log(`🔄 TOGGLE: Initial catalog number: "${catalogNumber}"`);

    // If no catalog number, try to use a default or skip
    if (!catalogNumber || catalogNumber === '-' || catalogNumber === '') {
        catalogNumber = '210'; // Default fallback
        console.log(`🔄 TOGGLE: Using fallback catalog: "${catalogNumber}"`);
    } else {
        console.log(`🔄 TOGGLE: Using found catalog: "${catalogNumber}"`);
    }

    // Expand - create new row with rib details
    const expandedRow = refreshedTbody.insertRow(refreshedRow.rowIndex);
    expandedRow.classList.add('expanded-row');
    expandedRow.setAttribute('data-expanded-for', rowId);

    const expandedCell = expandedRow.insertCell(0);
    expandedCell.colSpan = 10;

    // Create rib details table with 1/3 width layout - load rib data async
    expandedCell.innerHTML = `
            <div class="expanded-row-container">
                <div class="rib-details-section">
                    <table class="rib-details">
                        <tbody id="rib-tbody-${rowId}">
                            <tr>
                                <td colspan="2" style="text-align: center; color: #666;">
                                    טוען נתוני צלעות...
                                </td>
                            </tr>
                        </tbody>
                    </table>
                </div>
            </div>
        `;

        // Load rib details asynchronously
        generateRibDetails(rowId, catalogNumber).then(ribHtml => {
            const ribTbody = document.getElementById(`rib-tbody-${rowId}`);
            if (ribTbody) {
                ribTbody.innerHTML = ribHtml;
            }
        }).catch(error => {
            console.error('Error loading rib details:', error);
            const ribTbody = document.getElementById(`rib-tbody-${rowId}`);
            if (ribTbody) {
                ribTbody.innerHTML = `
                    <tr>
                        <td colspan="2" style="text-align: center; color: #666;">
                            שגיאה בטעינת נתוני צלעות
                        </td>
                    </tr>
                `;
            }
        });

        refreshedExpandBtn.textContent = '−';
        refreshedExpandBtn.classList.add('expanded');

        // Load the shape template content via AJAX
        console.log(`🔄 TOGGLE: About to load template for catalog: "${catalogNumber}"`);
        if (catalogNumber && catalogNumber !== '-' && catalogNumber !== '') {
            console.log(`🔄 TOGGLE: ✅ Catalog number is valid, calling loadShapeTemplate`);
            // Use setTimeout to ensure DOM is ready
            setTimeout(() => {
                const templateContainerId = `shape-template-${rowId}`;
                console.log(`🔄 TOGGLE: Looking for container: ${templateContainerId}`);
                const testContainer = document.getElementById(templateContainerId);
                console.log(`🔄 TOGGLE: Container found:`, testContainer);
                if (testContainer) {
                    loadExpandedShapeTemplate(catalogNumber, templateContainerId)
                        .then(() => {
                            console.log(`🔄 TOGGLE: Template loaded`);
                            // Now load rib data from central output file
                            const tbody = document.getElementById('items-tbody');
                            const row = tbody ? tbody.rows[parseInt(rowId)] : null;

                            // Get page number from the row's data-page attribute (same as generateRibDetails)
                            const currentPage = row ? (row.getAttribute('data-page') || '1') : '1';

                            // Get the actual order line number from the table row
                            const orderLineCell = row ? row.querySelector('input[data-field="מס"]') : null;
                            const lineNumber = orderLineCell ? orderLineCell.value : (parseInt(rowId) + 1);

                            console.log(`🔄 TOGGLE: Loading rib data for page ${currentPage}, line ${lineNumber} (from row ${rowId})`);
                            loadTemplateRibData(currentPage, lineNumber, templateContainerId);
                        })
                        .catch(err => console.error(`🔄 TOGGLE: Template load error:`, err));
                } else {
                    console.error(`🔄 TOGGLE: Container ${templateContainerId} not found in DOM`);
                }
            }, 100);
        } else {
            console.log(`🔄 TOGGLE: ❌ Catalog number is invalid: "${catalogNumber}"`);
        }
}

// Store catalog data globally
let catalogData = null;

// Load catalog data on page load
async function loadCatalogData() {
    try {
        const response = await fetch('/api/catalog-data');
        const data = await response.json();
        if (data.success) {
            catalogData = data.data;
        }
    } catch (error) {
        console.error('Failed to load catalog data:', error);
    }
}

// Generate rib details from central output file data
async function generateRibDetails(rowId, catalogNumber) {
    console.log(`[GENERATE RIB DETAILS] Starting for rowId: ${rowId}, catalogNumber: ${catalogNumber}`);
    // Extract row information from rowId (e.g., "0" means row index 0)
    const rowIndex = parseInt(rowId);
    const tbody = document.getElementById('items-tbody');

    if (!tbody || !tbody.rows[rowIndex]) {
        return `
            <tr>
                <td colspan="2" style="text-align: center; color: #666;">
                    שורה לא נמצאה
                </td>
            </tr>
        `;
    }

    const row = tbody.rows[rowIndex];
    const pageNumber = row.getAttribute('data-page') || 1;

    // Get the actual order line number from the "מס" field in the table row
    const orderLineCell = row.querySelector('input[data-field="מס"]');
    const lineNumber = orderLineCell ? orderLineCell.value : (rowIndex + 1);

    const orderNumber = getCurrentOrderNumber();

    try {
        // Fetch real rib data from central output file
        console.log(`[GENERATE RIB DETAILS] Calling API: /api/rib-data/${orderNumber}/${pageNumber}/${lineNumber}`);
        const response = await fetch(`/api/rib-data/${orderNumber}/${pageNumber}/${lineNumber}`);

        // Handle 404 responses gracefully - this is expected when specific rib data doesn't exist
        if (response.status === 404) {
            console.log(`No specific rib data found for ${orderNumber}/${pageNumber}/${lineNumber}, showing empty ribs`);
            return `
                <tr>
                    <td colspan="2" style="text-align: center; color: #666;">
                        אין נתוני צלעות
                    </td>
                </tr>
            `;
        }

        const data = await response.json();

        if (data.success && data.rib_values && Object.keys(data.rib_values).length > 0) {
            // Use real data from central output file
            let ribHtml = '';
            Object.entries(data.rib_values).forEach(([letter, value]) => {
                ribHtml += `
                    <tr>
                        <td>${letter}</td>
                        <td>${value}</td>
                    </tr>
                `;
            });
            return ribHtml;
        } else {
            // No rib data found in central output file - show nothing as requested
            return `
                <tr>
                    <td colspan="2" style="text-align: center; color: #666;">
                        אין נתוני צלעות
                    </td>
                </tr>
            `;
        }
    } catch (error) {
        console.error('Error fetching rib data:', error);
        return `
            <tr>
                <td colspan="2" style="text-align: center; color: #666;">
                    שגיאה בטעינת נתוני צלעות
                </td>
            </tr>
        `;
    }
}

// Generate shape template display
function generateShapeTemplate(catalogNumber) {
    if (!catalogNumber || catalogNumber === '-' || catalogNumber === '') {
        return `
            <div class="template-placeholder">
                <span>בחר מספר קטלוג לתצוגת התבנית</span>
            </div>
        `;
    }

    // Return a placeholder that will be populated by loadShapeTemplate
    return `
        <div class="template-loading">טוען תבנית...</div>
    `;
}

// Load shape template content via AJAX for expanded rows
async function loadExpandedShapeTemplate(catalogNumber, containerId) {
    console.log(`[TEMPLATE] START - Loading template for catalog: ${catalogNumber}`);
    console.log(`[TEMPLATE] Container ID: ${containerId}`);

    if (!catalogNumber || catalogNumber === '-' || catalogNumber === '') {
        console.log('[TEMPLATE] Invalid catalog number, skipping template load');
        return Promise.reject('Invalid catalog number');
    }

    // Try multiple ways to find the container
    const container1 = document.getElementById(containerId);
    const container2 = document.querySelector(`#${containerId}`);
    const container3 = document.querySelector(`[id="${containerId}"]`);

    console.log(`[TEMPLATE] getElementById result:`, container1);
    console.log(`[TEMPLATE] querySelector #${containerId} result:`, container2);
    console.log(`[TEMPLATE] querySelector [id="${containerId}"] result:`, container3);

    const container = container1 || container2 || container3;

    if (!container) {
        console.error(`%c[TEMPLATE] CONTAINER NOT FOUND!`, 'color: red; font-weight: bold;');
        console.error(`[TEMPLATE] Looking for: "${containerId}"`);
        console.error(`[TEMPLATE] All template containers in DOM:`, document.querySelectorAll('.shape-template-container'));

        // Try to find ANY shape template container and use it
        const anyTemplateContainer = document.querySelector('.shape-template-container');
        if (anyTemplateContainer) {
            console.log(`[TEMPLATE] Found alternative container:`, anyTemplateContainer);
            anyTemplateContainer.innerHTML = `<div style="background: red; color: white; padding: 10px;">
                CONTAINER MISMATCH DETECTED!<br>
                Looking for: ${containerId}<br>
                Found: ${anyTemplateContainer.id || 'no-id'}
            </div>`;
        }
        return;
    }

    console.log(`%c[TEMPLATE] CONTAINER FOUND!`, 'color: green; font-weight: bold;');
    console.log(`[TEMPLATE] Container element:`, container);
    console.log(`[TEMPLATE] Container ID:`, container.id);
    console.log(`[TEMPLATE] Container classes:`, container.className);

    container.innerHTML = `<div style="text-align: center; padding: 10px;">
        <span>טוען תבנית...</span>
    </div>`;

    try {
        console.log(`[TEMPLATE] Starting fetch from /api/shape-template/${catalogNumber}`);

        const response = await fetch(`/api/shape-template/${catalogNumber}`);
        console.log(`[TEMPLATE] Response status: ${response.status}, ok: ${response.ok}`);

        if (!response.ok) {
            throw new Error(`HTTP ${response.status}`);
        }

        const templateData = await response.json();
        console.log(`[TEMPLATE] JSON received, success: ${templateData.success}`);

        if (templateData.success && templateData.template) {
            const templateContent = templateData.template;
            console.log(`[TEMPLATE] Template content length: ${templateContent.length} chars`);

            container.innerHTML = templateContent;
            console.log('[TEMPLATE] Template loaded successfully');
            return Promise.resolve('Template loaded');

        } else {
            throw new Error(templateData.error || 'Template data invalid');
        }

    } catch (error) {
        console.error('[TEMPLATE] Error:', error);
        container.innerHTML = `
            <div style="text-align: center; padding: 10px; color: #cc0000;">
                <span>שגיאה בטעינת התבנית</span>
            </div>
        `;
        return Promise.reject(error);
    }
}

// Load rib data from central output file and populate template input fields
async function loadTemplateRibData(pageNumber, lineNumber, containerId) {
    console.log(`%c[LOAD TEMPLATE RIB DATA - SIMPLIFIED] Loading rib data for page ${pageNumber}, line ${lineNumber}, container: ${containerId}`, 'background: yellow; color: red; font-weight: bold;');

    try {
        const orderNumber = getCurrentOrderNumber();
        console.log(`[LOAD TEMPLATE RIB DATA] Calling API: /api/rib-data/${orderNumber}/${pageNumber}/${lineNumber}`);
        const response = await fetch(`/api/rib-data/${orderNumber}/${pageNumber}/${lineNumber}`);

        console.log(`[LOAD TEMPLATE RIB DATA] API Response status: ${response.status}`);
        const data = await response.json();
        console.log(`[LOAD TEMPLATE RIB DATA] API Response data:`, data);

        if (data.success && data.rib_values) {
            console.log(`%c[RIB DATA SUCCESS] Received rib values for line ${lineNumber}:`, 'color: green; font-weight: bold;', data.rib_values);

            // Find the template container
            const container = document.getElementById(containerId);
            if (!container) {
                console.error(`%c[TEMPLATE ERROR] Container ${containerId} not found in DOM`, 'color: red; font-weight: bold;');
                return;
            }

            console.log(`%c[TEMPLATE FOUND] Container ${containerId} found, looking for input fields...`, 'color: blue;');

            // Find all input fields in the template and populate them using name attributes
            const inputFields = container.querySelectorAll('input[type="text"][name]');
            console.log(`%c[TEMPLATE INPUTS] Found ${inputFields.length} input fields in container`, 'color: blue;',
                Array.from(inputFields).map(input => ({ name: input.name, id: input.id, currentValue: input.value })));

            let populatedCount = 0;
            inputFields.forEach(input => {
                const ribLetter = input.name; // Get the rib letter from the name attribute
                console.log(`[TEMPLATE FIELD] Processing field: name="${ribLetter}", id="${input.id}", current value="${input.value}"`);

                if (ribLetter && data.rib_values[ribLetter]) {
                    const value = data.rib_values[ribLetter];
                    const oldValue = input.value;
                    input.value = value;
                    populatedCount++;
                    console.log(`%c[TEMPLATE POPULATE SUCCESS] Field "${ribLetter}" updated: "${oldValue}" → "${value}"`, 'color: green; font-weight: bold;');
                } else {
                    console.log(`[TEMPLATE FIELD] No data for field "${ribLetter}" - keeping existing value: "${input.value}"`);
                }
            });

            console.log(`%c[TEMPLATE COMPLETE] Successfully populated ${populatedCount} fields in container ${containerId}`, 'color: green; font-weight: bold;');
        } else {
            console.error(`%c[RIB DATA ERROR] API failed or no rib data:`, 'color: red; font-weight: bold;', data);
        }
    } catch (error) {
        console.error(`%c[RIB DATA EXCEPTION] Error loading rib data:`, 'color: red; font-weight: bold;', error);
    }
}


// Load catalog data when page loads
document.addEventListener('DOMContentLoaded', function() {
    loadCatalogData();
});

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
    if (!redetectBtn) return; // Button was removed

    const originalContent = redetectBtn.innerHTML;
    const columnName = 'צורה'; // Default value since input was removed

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

// Global storage for the complete data object
let globalAnalysisData = null;

// Display shapes detected by GLOBAL agent
function displayShapes(data) {
    // Store the complete data globally for shapes tab activation
    globalAnalysisData = data;

    const shapesTable = document.getElementById('shapes-table');
    const shapesBody = document.getElementById('shapes-tbody');
    const shapesContainer = document.getElementById('shapes-container');

    // Check if we're using the old container or new table format
    if (!shapesTable || !shapesBody) {
        // Fall back to old container if table not found
        if (!shapesContainer) return;

        // Don't clear shapes if we already have shape images displayed
        const hasShapeImages = shapesContainer.querySelector('.shape-table-row') !== null;
        if (hasShapeImages) {
            console.log('📐 Shape images already displayed, skipping displayShapes');
            return;
        }
    } else {
        // Using new table format - check if already populated
        const hasTableRows = shapesBody.querySelector('.shape-table-row') !== null;
        if (hasTableRows) {
            console.log('📐 Shape table already populated, skipping displayShapes');
            return;
        }
    }

    // Check if detailed shape info is available (new format)
    if (data.shape_cells && data.shape_cells.length > 0) {
        const shapes = data.shape_cells;
        
        // No longer updating count since element was removed
        console.log(`📐 Found ${shapes.length} shapes`);

        // Clear container
        if (shapesContainer) {
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
        }
    } else if (data.shape_cell_paths && data.shape_cell_paths.length > 0) {
        // Fallback to old format (backward compatibility)
        const shapes = data.shape_cell_paths;

        // No longer updating count since element was removed
        console.log(`📐 Found ${shapes.length} shapes`);

        if (shapesContainer) {
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
        }
 else {
        // No shapes found
        console.log('📐 No shapes found');
        if (shapesContainer) {
            shapesContainer.innerHTML = `
                <div class="no-shapes-placeholder">
                    <p>🔍 לא נמצאו צורות</p>
                    <p>הרץ ניתוח כדי לזהות צורות מהמסמך</p>
                </div>
            `;
        }
    }
}
}

// File Selection Functions
let selectedFile = null;

async function showFileSelection() {
    const modal = document.getElementById('file-selection-modal');
    const container = document.getElementById('file-list-container');
    
    // Show modal
    modal.style.display = 'flex';
    
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

// Auto-refresh every 30 seconds (but preserve shape images)
// Auto-refresh disabled
// setInterval(() => {
//     if (document.getElementById('status').textContent !== 'מעבד') {
//         // Store current shape table state before refresh
//         const shapesTable = document.getElementById('shapes-table');
//         const shapesBody = document.getElementById('shapes-tbody');
//         const currentShapeRows = shapesBody ? shapesBody.innerHTML : '';
//         const currentPageAttr = shapesTable ? shapesTable.getAttribute('data-current-page') : null;
//
//         loadLatestAnalysis().then(() => {
//             // Restore shapes if they were cleared
//             if (currentShapeRows && currentShapeRows !== '' &&
//                 !currentShapeRows.includes('no-shapes-placeholder')) {
//                 const tbody = document.getElementById('shapes-tbody');
//                 const table = document.getElementById('shapes-table');
//                 if (tbody) {
//                     // Check if shapes were cleared or changed
//                     const newContent = tbody.innerHTML;
//                     if (newContent.includes('no-shapes-placeholder') || newContent === '') {
//                         // Restore the shape rows
//                         tbody.innerHTML = currentShapeRows;
//                         if (currentPageAttr && table) {
//                             table.setAttribute('data-current-page', currentPageAttr);
//                         }
//                         console.log('📐 Restored shape table after auto-refresh');
//                     }
//                 }
//             }
//         });
//     }
// }, 30000);

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
                page: pageNumber,
                row_index: rowIndex,
                field_name: fieldName,
                new_value: newValue
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

            // Update expanded table if catalog field was changed
            if (fieldName === 'catalog') {
                // Call Form1dat2 API to update catalog data in central output file
                updateCatalogNumber(pageNumber, rowIndex + 1, newValue);

                updateExpandedTablesForRow(pageNumber, rowIndex, newValue);

                // Update the shape field (צורה column) with new shape template
                updateShapeFieldForCatalog(rowIndex, newValue);
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

// Update expanded table when catalog number changes
function updateExpandedTablesForRow(pageNumber, rowIndex, newCatalogNumber) {
    // Find the table row that corresponds to this rowIndex
    const tbody = document.getElementById('items-tbody');
    if (!tbody || !tbody.rows[rowIndex]) {
        return;
    }

    const row = tbody.rows[rowIndex];
    const rowId = `row-${row.rowIndex}`;

    // Check if this row is currently expanded
    const expandedRow = document.getElementById(`expanded-${rowId}`);
    if (expandedRow && expandedRow.style.display !== 'none') {
        // Row is expanded, find the rib details section and update it
        const ribDetailsSection = expandedRow.querySelector('.rib-details-section tbody');
        if (ribDetailsSection) {
            // Show loading message
            ribDetailsSection.innerHTML = `
                <tr>
                    <td colspan="2" style="text-align: center; color: #666;">
                        טוען נתוני צלעות...
                    </td>
                </tr>
            `;

            // Generate new rib details with the updated catalog number asynchronously
            generateRibDetails(rowId, newCatalogNumber).then(newRibDetails => {
                if (ribDetailsSection) {
                    ribDetailsSection.innerHTML = newRibDetails;
                }
            }).catch(error => {
                console.error('Error updating rib details:', error);
                if (ribDetailsSection) {
                    ribDetailsSection.innerHTML = `
                        <tr>
                            <td colspan="2" style="text-align: center; color: #666;">
                                שגיאה בטעינת נתוני צלעות
                            </td>
                        </tr>
                    `;
                }
            });
        }

        // Also update the shape template
        const templateSection = expandedRow.querySelector('.template-content');
        if (templateSection) {
            const newTemplate = generateShapeTemplate(newCatalogNumber);
            templateSection.innerHTML = newTemplate;

            // Load the actual template content via AJAX
            if (newCatalogNumber && newCatalogNumber !== '-' && newCatalogNumber !== '') {
                // Use the correct function and find the actual template container ID
                const templateContainer = templateSection.querySelector('div') || templateSection;
                const containerId = templateContainer.id || `template-${rowIndex + 1}-${new Date().getTime()}`;
                if (!templateContainer.id) {
                    templateContainer.id = containerId;
                }

                console.log(`[TEMPLATE UPDATE] Loading template for catalog ${newCatalogNumber}, container: ${containerId}`);
                loadExpandedShapeTemplate(newCatalogNumber, containerId);
            }
        }

        console.log(`Updated expanded table and shape template for row ${rowIndex + 1} with catalog number ${newCatalogNumber}`);
    }
}

// Total weight calculation removed - משקל column no longer exists

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

// Update catalog image based on catalog number input
function updateCatalogImage(catalogNumber, rowId) {
    const catalogImageCell = document.getElementById(`catalog-image-${rowId}`);

    if (!catalogImageCell) return;

    // Remove leading zeros and check if it's a valid number (1-5 digits)
    const cleanNumber = catalogNumber.replace(/^0+/, '') || '0';

    if (catalogNumber.length >= 1 && catalogNumber.length <= 5 && /^\d+$/.test(catalogNumber)) {
        // Valid number (1-5 digits) - show catalog image
        const imageUrl = `/catalog_image/${cleanNumber.padStart(3, '0')}`;

        catalogImageCell.innerHTML = `
            <img src="${imageUrl}"
                 alt="קטלוג ${catalogNumber}"
                 class="catalog-table-image"
                 title="צורת קטלוג ${catalogNumber} - לחץ להגדלה"
                 onclick="openCatalogShapeModal('${catalogNumber}', this.parentElement.parentElement)"
                 onerror="this.parentElement.innerHTML='<div class=\\'catalog-shape-placeholder\\'><span>קטלוג לא נמצא</span></div>'"
                 style="max-width: 100%; max-height: 120px; object-fit: contain; border: 1px solid #e0e0e0; border-radius: 4px; background: white;">
        `;
    } else if (catalogNumber.length === 0) {
        // Empty input - show placeholder
        catalogImageCell.innerHTML = `
            <div class="catalog-shape-placeholder">
                <span>הכנס מספר קטלוג</span>
            </div>
        `;
    } else {
        // Invalid input - show waiting message
        catalogImageCell.innerHTML = `
            <div class="catalog-shape-placeholder">
                <span>הכנס מספר תקין</span>
            </div>
        `;
    }
}

// Update shape field when catalog number changes
function updateShapeFieldForCatalog(rowIndex, catalogNumber) {
    console.log(`[SHAPE UPDATE] Called updateShapeFieldForCatalog with rowIndex: ${rowIndex}, catalogNumber: ${catalogNumber}`);

    const tbody = document.getElementById('items-tbody');
    if (!tbody) {
        console.log(`[SHAPE UPDATE] Error: tbody not found`);
        return;
    }

    if (!tbody.rows[rowIndex]) {
        console.log(`[SHAPE UPDATE] Error: row at index ${rowIndex} not found. Total rows: ${tbody.rows.length}`);
        return;
    }

    const row = tbody.rows[rowIndex];
    console.log(`[SHAPE UPDATE] Found row, total cells: ${row.cells.length}`);

    // Shape column is the 4th column (index 3) in the orders table
    const shapeCell = row.cells[3];

    if (!shapeCell) {
        console.log(`[SHAPE UPDATE] Error: shape cell at index 3 not found`);
        return;
    }

    console.log(`[SHAPE UPDATE] Found shape cell, current content: ${shapeCell.innerHTML}`);

    if (catalogNumber && catalogNumber !== '-' && catalogNumber !== '') {
        // Get order number and page number from the current context
        const orderNumber = getCurrentOrderNumber();
        const pageNumber = getCurrentPageNumber();

        // Get the order line number from the row's data attribute (stored when row was created)
        const orderLineNo = row.getAttribute('data-order-line-no') || (rowIndex + 1);
        console.log(`[SHAPE UPDATE] Row index ${rowIndex}, Order Line No from data-attr: ${orderLineNo}`);

        // Create new shape template iframe with URL parameters for auto-population
        const templateUrl = `/shape_template/${catalogNumber}?order=${orderNumber}&page=${pageNumber}&line=${orderLineNo}`;
        const newContent = `
                        <div style="width: 100%; height: 110px; overflow: hidden; position: relative; background: white;">
                            <iframe src="${templateUrl}" style="width: 600px; height: 350px; border: none; position: absolute; top: 55%; left: 50%; transform: translate(-50%, -50%) scale(0.7);" scrolling="no" title="Template ${catalogNumber}">
                            </iframe>
                        </div>
        `;
        shapeCell.innerHTML = newContent;
        console.log(`[SHAPE UPDATE] Updated shape field for row ${rowIndex + 1} with catalog ${catalogNumber} (order=${orderNumber}, page=${pageNumber}, line=${orderLineNo})`);
    } else {
        // No catalog number - show placeholder
        const placeholderContent = '<span style="color: #666; font-size: 12px;">אין קטלוג זמין</span>';
        shapeCell.innerHTML = placeholderContent;
        console.log(`[SHAPE UPDATE] Set placeholder content: ${placeholderContent}`);
    }
}

// ============================================
// Catalog Shape Modal Functions (Legacy - now handled by shape-modals.js)
// ============================================
// Note: Shape modal functionality has been moved to shape-modals.js

// ============================================
// Shape Identification Functions
// ============================================

function runShapeIdentification(rowId) {
    console.log('Shape identification started', rowId ? `for row: ${rowId}` : 'for all shapes');

    if (!rowId) {
        console.log('Global shape identification not yet implemented');
        alert('זיהוי כללי של צורות יתווסף בגרסה הבאה');
        return;
    }

    // Find the specific button for this row
    const button = document.querySelector(`button[onclick*="${rowId}"]`);
    if (!button) {
        console.error(`Button not found for row: ${rowId}`);
        return;
    }

    // Disable button during processing
    button.disabled = true;

    // Change button appearance to show processing
    const originalText = button.textContent;
    button.textContent = '...';
    button.style.backgroundColor = '#fbbf24';

    // Update shapes status
    const shapesStatus = document.getElementById('shapes-status');
    if (shapesStatus) {
        shapesStatus.textContent = 'מזהה צורה...';
    }

    // Create notification for shape identification process
    const notificationTitle = 'זיהוי צורה בודדת';
    const notificationMessage = `מזהה צורה ${rowId}...`;

    createProgressNotification(
        `shape-identification-${rowId}`,
        notificationTitle,
        notificationMessage,
        'processing'
    );

    // Call the API to run Form1OCR3 agent
    fetch('/api/run-shape-identification', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({
            row_id: rowId,
            order_number: getCurrentOrderNumber(),
            timestamp: new Date().toISOString()
        })
    })
    .then(response => response.json())
    .then(data => {
        console.log('Shape identification response:', data);

        if (data.success) {
            // Success notification
            const completedMessage = `זוהו ${data.mappings_found} מיפויים, עודכנו ${data.values_updated} ערכים`;
            updateProgressNotification(
                `shape-identification-${rowId}`,
                'זיהוי צורה הושלם',
                completedMessage,
                'success'
            );

            // Update shapes status
            if (shapesStatus) {
                shapesStatus.textContent = `הושלם - ${data.values_updated} ערכים`;
            }

            // Refresh the specific row to show updated values
            console.log('Mappings found:', data.mappings);
            refreshSpecificRow(rowId);

            // Auto-hide notification after 3 seconds
            setTimeout(() => {
                removeProgressNotification(`shape-identification-${rowId}`);
            }, 3000);

        } else {
            // Error notification
            updateProgressNotification(
                `shape-identification-${rowId}`,
                'שגיאה בזיהוי צורה',
                data.error || 'שגיאה לא ידועה',
                'error'
            );

            // Update shapes status
            if (shapesStatus) {
                shapesStatus.textContent = 'שגיאה';
            }

            console.error('Shape identification failed:', data.error);

            // Auto-hide error notification after 5 seconds
            setTimeout(() => {
                removeProgressNotification(`shape-identification-${rowId}`);
            }, 5000);
        }
    })
    .catch(error => {
        console.error('API call failed:', error);

        updateProgressNotification(
            `shape-identification-${rowId}`,
            'שגיאה בזיהוי צורה',
            'שגיאה בחיבור לשרת',
            'error'
        );

        // Update shapes status
        if (shapesStatus) {
            shapesStatus.textContent = 'שגיאת חיבור';
        }

        // Auto-hide error notification after 5 seconds
        setTimeout(() => {
            removeProgressNotification(`shape-identification-${rowId}`);
        }, 5000);
    })
    .finally(() => {
        // Restore button
        button.disabled = false;
        button.textContent = originalText;
        button.style.backgroundColor = '';
    });
}

function loadIdentifiedShapes() {
    const shapesTable = document.getElementById('shapes-tbody');
    if (!shapesTable) return;

    // Placeholder data for identified shapes
    const identifiedShapes = [
        { page: 1, line: 1, catalog: '107', drawing: 'shape_107.png' },
        { page: 1, line: 2, catalog: '104', drawing: 'shape_104.png' },
        { page: 1, line: 3, catalog: '107', drawing: 'shape_107.png' },
    ];

    // Clear existing content
    shapesTable.innerHTML = '';

    // Add identified shapes to table
    identifiedShapes.forEach(shape => {
        const row = document.createElement('tr');
        row.innerHTML = `
            <td>${shape.page}/${shape.line}</td>
            <td>${shape.catalog}</td>
            <td>
                <div class="shape-drawing-cell">
                    <img src="/shape_image/${shape.drawing}"
                         alt="ציור צורה"
                         class="shape-drawing-image"
                         onerror="this.style.display='none'; this.nextElementSibling.style.display='block';"
                         style="max-width: 100%; max-height: 80px; object-fit: contain;">
                    <div class="shape-placeholder" style="display: none;">
                        <span>ציור לא זמין</span>
                    </div>
                </div>
            </td>
            <td>
                <button class="catalog-view-btn" onclick="openCatalogShapeModal('${shape.catalog}', this.parentElement.parentElement)">
                    צפה בקטלוג
                </button>
            </td>
        `;
        shapesTable.appendChild(row);
    });

    // Update total shapes count
    const totalShapes = document.getElementById('total-shapes');
    if (totalShapes) {
        totalShapes.textContent = identifiedShapes.length;
    }
}

// Load shape template iframe from JSON data for detected shapes
async function loadShapeTemplateFromJSON(pageNumber, lineNumber, rowId) {
    try {
        const orderNumber = getCurrentOrderNumber();
        if (!orderNumber) {
            console.log(`[LOAD TEMPLATE JSON] No order number available`);
            return;
        }

        // Get the catalog number from the JSON analysis data
        const response = await fetch(`/api/latest-analysis`);
        const analysisData = await response.json();

        if (!analysisData.analysis || !analysisData.analysis.section_3_shape_analysis) {
            console.log(`[LOAD TEMPLATE JSON] No shape analysis data found`);
            return;
        }

        const pageKey = `page_${pageNumber}`;
        const shapeAnalysis = analysisData.analysis.section_3_shape_analysis[pageKey];

        if (!shapeAnalysis || !shapeAnalysis.order_lines) {
            console.log(`[LOAD TEMPLATE JSON] No data for page ${pageNumber}`);
            return;
        }

        // Find the line by line_number (not order_line_no)
        let catalogNumber = null;
        for (const lineKey in shapeAnalysis.order_lines) {
            const lineData = shapeAnalysis.order_lines[lineKey];
            if (lineData.line_number === lineNumber) {
                catalogNumber = lineData.shape_catalog_number;
                break;
            }
        }

        if (!catalogNumber || catalogNumber === 'NA' || catalogNumber === '-') {
            console.log(`[LOAD TEMPLATE JSON] No valid catalog number for page ${pageNumber}, line ${lineNumber}`);
            // Show placeholder
            const shapeCell = document.getElementById(`shape-cell-${rowId}`);
            if (shapeCell) {
                shapeCell.innerHTML = '<span style="color: #666; font-size: 12px;">אין קטלוג זמין</span>';
            }
            return;
        }

        console.log(`[LOAD TEMPLATE JSON] Found catalog number ${catalogNumber} for page ${pageNumber}, line ${lineNumber}`);

        // Load the template iframe
        const shapeCell = document.getElementById(`shape-cell-${rowId}`);
        if (shapeCell) {
            const templateUrl = `/shape_template/${catalogNumber}`;
            shapeCell.innerHTML = `
                <iframe src="${templateUrl}"
                        class="table-shape-image"
                        title=""
                        style="width: 50px; height: 40px; border: none; overflow: hidden; pointer-events: none;"
                        scrolling="no">
                </iframe>
            `;
            console.log(`[LOAD TEMPLATE JSON] Template iframe loaded for catalog ${catalogNumber}`);
        }

    } catch (error) {
        console.error(`[LOAD TEMPLATE JSON] Error loading template:`, error);
        const shapeCell = document.getElementById(`shape-cell-${rowId}`);
        if (shapeCell) {
            shapeCell.innerHTML = '<span style="color: #999; font-size: 12px;">שגיאה בטעינה</span>';
        }
    }
}

// Load shape template iframe for main order table - SIMPLIFIED VERSION
function loadOrderTableTemplate(shapeCell, lineNumber, pageNumber, catalogNumber = null) {
    console.log(`[TEMPLATE] Called with line ${lineNumber}, page ${pageNumber}, catalog ${catalogNumber}`);

    // If catalog number is provided directly, use it
    if (catalogNumber && catalogNumber !== 'NA' && catalogNumber !== '-' && catalogNumber !== '000') {
        console.log(`[TEMPLATE] Loading template for catalog ${catalogNumber}`);
        const templateUrl = `/shape_template/${catalogNumber}`;
        shapeCell.innerHTML = `
            <iframe src="${templateUrl}"
                    class="table-shape-image"
                    title=""
                    style="width: 50px; height: 40px; border: none; overflow: hidden; pointer-events: none;"
                    scrolling="no">
            </iframe>
        `;
        console.log(`[TEMPLATE] Template iframe created for catalog ${catalogNumber}`);
        return;
    }

    // Fallback: Hard-coded mapping for testing if no catalog provided
    const catalogMappings = {
        '1': '210',  // Line 1 -> Shape 210
        '3': '218'   // Line 3 -> Shape 218
    };

    const fallbackCatalog = catalogMappings[String(lineNumber)];

    if (fallbackCatalog) {
        console.log(`[TEMPLATE] Loading fallback template for catalog ${fallbackCatalog}`);
        const templateUrl = `/shape_template/${fallbackCatalog}`;
        shapeCell.innerHTML = `
            <iframe src="${templateUrl}"
                    class="table-shape-image"
                    title=""
                    style="width: 50px; height: 40px; border: none; overflow: hidden; pointer-events: none;"
                    scrolling="no">
            </iframe>
        `;
        console.log(`[TEMPLATE] Fallback template iframe created for catalog ${fallbackCatalog}`);
    } else {
        console.log(`[TEMPLATE] No catalog available for line ${lineNumber}`);
        shapeCell.innerHTML = '<span style="color: #666; font-size: 12px;">אין קטלוג</span>';
    }
}

// DEBUG: Test function for the button in main page
function testTemplateLoading() {
    console.log('[DEBUG] Test template loading button clicked');
    const testDiv = document.getElementById('debug-template-test');
    if (testDiv) {
        console.log('[DEBUG] Test div found, calling loadOrderTableTemplate');
        loadOrderTableTemplate(testDiv, 1, 1);  // Test with line 1 (should load shape 210)
    } else {
        console.log('[DEBUG] Test div not found');
    }
}

// DEBUG: Function to add templates to existing table
function addTemplatesToExistingTable() {
    console.log('[DEBUG] Adding templates to existing table - FUNCTION CALLED');
    alert('[DEBUG] Button clicked! Check console for details.');

    const tbody = document.getElementById('items-tbody');
    if (!tbody) {
        console.log('[DEBUG] Table body not found');
        alert('[DEBUG] Table body not found!');
        return;
    }

    console.log('[DEBUG] Table body found:', tbody);

    const rows = tbody.querySelectorAll('tr');
    console.log(`[DEBUG] Found ${rows.length} rows`);
    alert(`[DEBUG] Found ${rows.length} rows in table`);

    if (rows.length === 0) {
        console.log('[DEBUG] No rows found in table');
        alert('[DEBUG] No rows found in table');
        return;
    }

    rows.forEach((row, index) => {
        const cells = row.querySelectorAll('td');
        console.log(`[DEBUG] Row ${index} has ${cells.length} cells`);

        if (cells.length >= 3) {  // Make sure there are enough cells
            // Log all cell contents to find the right columns
            console.log(`[DEBUG] Row ${index} all cells:`,
                Array.from(cells).map((cell, i) => `Cell ${i}: "${cell?.textContent?.trim()}"`));

            // Try to find line number in different columns
            let lineNumber = null;
            let lineCell = null;
            let shapeCell = null;

            // Check columns 0, 1, 2 for line numbers (should be numeric)
            for (let i = 0; i < Math.min(cells.length, 4); i++) {
                const cellText = cells[i]?.textContent?.trim();
                if (cellText && /^\d+$/.test(cellText)) {  // Check if it's a number
                    lineNumber = cellText;
                    lineCell = cells[i];
                    // Shape cell should be nearby (try next column)
                    shapeCell = cells[i + 1] || cells[i + 2];
                    console.log(`[DEBUG] Found line number "${lineNumber}" in column ${i}`);
                    break;
                }
            }

            if (lineNumber && shapeCell) {
                console.log(`[DEBUG] Adding template for line ${lineNumber}`);
                loadOrderTableTemplate(shapeCell, lineNumber, 1);
            } else {
                console.log(`[DEBUG] Skipping row ${index} - no valid line number found`);
            }
        } else {
            console.log(`[DEBUG] Row ${index} has insufficient cells (${cells.length})`);
        }
    });

    console.log('[DEBUG] Template addition process completed');
}
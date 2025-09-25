// Simple Shape Modal Management System (Embedded Templates)
// ==========================================================

// Embedded shape templates
const shapeTemplates = {
    '000': `
        <div id="shape-000" class="shape-content">
            <div class="shape-diagram-with-input" style="position: relative; text-align: center; padding: 40px 0;">
                <div style="position: absolute; top: 35px; left: 50%; transform: translateX(-50%); display: flex; align-items: center;">
                    <input type="text"
                           id="length-A-000"
                           class="inline-shape-input shape-000-input"
                           maxlength="8"
                           placeholder="0"
                           style="width: 100px; height: 32px; font-size: 18px; border: 2px solid #333; border-radius: 4px; margin-right: 4px;">
                    <span style="font-size: 20px; font-weight: bold; margin-left: 4px;">= A</span>
                </div>
                <svg width="400" height="100" viewBox="0 0 400 100" style="margin-top: 20px;">
                    <line x1="50" y1="50" x2="350" y2="50" stroke="black" stroke-width="4"/>
                </svg>
            </div>
            <div class="modal-buttons" style="margin-top: 30px;">
                <button id="save-shape-000" class="btn btn-success" onclick="saveShape('000')">שמור</button>
            </div>
        </div>
    `,
    '104': `
        <div id="shape-104" class="shape-content">
            <div class="shape-diagram-with-input" style="position: relative; text-align: center; padding: 40px 0;">
                <div style="position: absolute; top: 100px; left: 40px; display: flex; align-items: center;">
                    <input type="text"
                           id="length-A-104"
                           class="inline-shape-input shape-104-input"
                           maxlength="8"
                           placeholder="0"
                           style="width: 80px; height: 28px; font-size: 18px; border: 2px solid #333; border-radius: 4px; margin-right: 4px;">
                    <span style="font-size: 20px; font-weight: bold; margin-left: 4px;">= A</span>
                </div>
                <div style="position: absolute; bottom: 10px; left: 50%; transform: translateX(-50%); display: flex; align-items: center;">
                    <input type="text"
                           id="length-C-104"
                           class="inline-shape-input shape-104-input"
                           maxlength="8"
                           placeholder="0"
                           style="width: 80px; height: 28px; font-size: 18px; border: 2px solid #333; border-radius: 4px; margin-right: 4px;">
                    <span style="font-size: 20px; font-weight: bold; margin-left: 4px;">= C</span>
                </div>
                <svg width="400" height="200" viewBox="0 0 400 200" style="margin-top: 20px;">
                    <path d="M 100 50 L 100 140 Q 100 150 110 150 L 300 150"
                          stroke="black"
                          stroke-width="4"
                          fill="none"
                          stroke-linecap="round"/>
                </svg>
            </div>
            <div class="modal-buttons" style="margin-top: 30px;">
                <button id="save-shape-104" class="btn btn-success" onclick="saveShape('104')">שמור</button>
            </div>
        </div>
    `,
    '107': `
        <div id="shape-107" class="shape-content">
            <div class="shape-diagram-with-input" style="position: relative; text-align: center; padding: 40px 0;">
                <!-- Standalone input field -->
                <div style="position: absolute; top: 58.8%; left: 47.2%; transform: translate(-50%, -50%);">
                    <input type="text"
                           id="length-field_1-107"
                           class="inline-shape-input shape-107-input"
                           maxlength="8"
                           placeholder="0"
                           style="width: 80px; height: 28px; font-size: 18px; border: 2px solid #4a90e2; border-radius: 4px; background: #e6f2ff;">
                </div>
                <!-- Standalone input field -->
                <div style="position: absolute; top: 70.0%; left: 51.4%; transform: translate(-50%, -50%);">
                    <input type="text"
                           id="length-field_2-107"
                           class="inline-shape-input shape-107-input"
                           maxlength="8"
                           placeholder="0"
                           style="width: 80px; height: 28px; font-size: 18px; border: 2px solid #4a90e2; border-radius: 4px; background: #e6f2ff;">
                </div>
                <!-- Standalone input field -->
                <div style="position: absolute; top: 57.3%; left: 80.0%; transform: translate(-50%, -50%);">
                    <input type="text"
                           id="length-field_3-107"
                           class="inline-shape-input shape-107-input"
                           maxlength="8"
                           placeholder="0"
                           style="width: 80px; height: 28px; font-size: 18px; border: 2px solid #4a90e2; border-radius: 4px; background: #e6f2ff;">
                </div>
                <!-- Standalone input field -->
                <div style="position: absolute; top: 51.0%; left: 52.1%; transform: translate(-50%, -50%);">
                    <input type="text"
                           id="length-field_4-107"
                           class="inline-shape-input shape-107-input"
                           maxlength="8"
                           placeholder="0"
                           style="width: 80px; height: 28px; font-size: 18px; border: 2px solid #4a90e2; border-radius: 4px; background: #e6f2ff;">
                </div>
                <!-- Standalone input field -->
                <div style="position: absolute; top: 42.2%; left: 55.1%; transform: translate(-50%, -50%);">
                    <input type="text"
                           id="length-field_5-107"
                           class="inline-shape-input shape-107-input"
                           maxlength="8"
                           placeholder="0"
                           style="width: 80px; height: 28px; font-size: 18px; border: 2px solid #4a90e2; border-radius: 4px; background: #e6f2ff;">
                </div>

                <!-- Original catalog shape 107 image -->
                <div style="text-align: center; margin-top: 20px;">
                    <img src="/static/images/shape_107.png?v=2024092403"
                         alt="Shape 107"
                         style="max-width: 300px; height: auto; border: 2px solid #ddd; border-radius: 8px; padding: 20px; background-color: white;">
                </div>
            </div>
            <div class="modal-buttons" style="margin-top: 30px;">
                <button id="save-shape-107" class="btn btn-success" onclick="saveShape('107')">שמור</button>
            </div>
        </div>
    `
};

// Shape configurations
const shapeConfigs = {
    '000': {
        name: 'קו ישר',
        fields: ['A']
    },
    '104': {
        name: 'צורת L',
        fields: ['A', 'C']
    },
    '107': {
        name: 'צורת U',
        fields: ['A', 'E']
    },
    '210': {
        name: 'צורת U',
        fields: ['field_1', 'field_2', 'field_3']
    },
    '218': {
        name: 'צורת U',
        fields: ['A', 'C', 'E']
    }
};

// Load shape template into modal (dynamic loading from API)
async function loadShapeTemplate(shapeNumber) {
    const container = document.getElementById('shape-container');
    const config = shapeConfigs[shapeNumber];

    try {
        // First try to load from API (positioning tool generated templates)
        const response = await fetch(`/api/shape-template/${shapeNumber}`);
        const data = await response.json();

        if (data.success) {
            // Use the template from the file
            container.innerHTML = data.template;

            // Initialize input validation for this shape
            initializeShapeInputs(shapeNumber);

            return true;
        } else {
            console.log(`Template file for shape ${shapeNumber} not found, using embedded template`);
        }

    } catch (error) {
        console.error(`Error loading template for shape ${shapeNumber}:`, error);
    }

    // Fall back to embedded template
    const template = shapeTemplates[shapeNumber];
    if (config && template) {
        container.innerHTML = template;

        // Initialize input validation for this shape
        initializeShapeInputs(shapeNumber);

        return true;
    }

    // If all fails, show error
    container.innerHTML = '<div style="padding: 20px; text-align: center;"><p>צורה זו אינה זמינה עדיין</p></div>';
    return false;
}

// Initialize input validation and event handlers
function initializeShapeInputs(shapeNumber) {
    const config = shapeConfigs[shapeNumber];

    config.fields.forEach(field => {
        const input = document.getElementById(`length-${field}-${shapeNumber}`);
        if (input) {
            // Allow only numbers and dots
            input.addEventListener('input', function(event) {
                let value = this.value;
                value = value.replace(/[^0-9.]/g, '');

                // Ensure only one dot
                const parts = value.split('.');
                if (parts.length > 2) {
                    value = parts[0] + '.' + parts.slice(1).join('');
                }

                this.value = value;
            });

            // Allow Enter to save
            input.addEventListener('keypress', function(event) {
                if (event.key === 'Enter') {
                    saveShape(shapeNumber);
                }
            });
        }
    });

    // Focus on first input
    const firstInput = document.getElementById(`length-${config.fields[0]}-${shapeNumber}`);
    if (firstInput) {
        setTimeout(function() {
            firstInput.focus();
        }, 100);
    }
}

// Open catalog shape modal with embedded content
async function openCatalogShapeModal(catalogNumber, rowElement) {
    console.log('Opening catalog shape modal for:', catalogNumber);

    // Store the current row for reference
    window.currentShapeRow = rowElement;
    window.currentShapeNumber = catalogNumber;

    // Get the modal
    const modal = document.getElementById('catalogShapeModal');
    const modalTitle = document.getElementById('modal-title');

    // Update modal title
    const config = shapeConfigs[catalogNumber];
    modalTitle.textContent = `צורת קטלוג ${catalogNumber}${config ? ' - ' + config.name : ''}`;

    // Load the shape template (now async)
    const loaded = await loadShapeTemplate(catalogNumber);

    if (loaded) {
        // Show the modal
        modal.style.display = 'flex';
    } else {
        alert(`צורת קטלוג ${catalogNumber} עדיין לא זמינה`);
    }
}

// Save shape data
function saveShape(shapeNumber) {
    console.log('saveShape called with:', shapeNumber);
    const config = shapeConfigs[shapeNumber];
    if (!config) {
        console.log('No config found for shape:', shapeNumber);
        return;
    }

    // Collect all field values
    const values = {};
    let allValid = true;

    config.fields.forEach(field => {
        const input = document.getElementById(`length-${field}-${shapeNumber}`);
        console.log(`Looking for input: length-${field}-${shapeNumber}`, input);
        if (input) {
            const value = input.value.trim();
            console.log(`Field ${field} value:`, value);
            if (!value || value === '' || isNaN(parseFloat(value)) || parseFloat(value) <= 0) {
                console.log(`Field ${field} is invalid:`, value);
                allValid = false;
            } else {
                values[field] = value;
            }
        } else {
            console.log(`Input not found for field ${field}`);
            allValid = false;
        }
    });

    console.log('Validation result:', allValid, values);

    if (!allValid) {
        alert('אנא הכנס ערכים תקינים לכל השדות');
        return;
    }

    // If we have a current row reference, update it
    if (window.currentShapeRow) {
        // Find the rib fields in the row
        const ribFields = window.currentShapeRow.querySelectorAll('.rib-field');

        // For shape 000, update first field
        if (shapeNumber === '000' && ribFields.length > 0) {
            ribFields[0].value = values.A;
            ribFields[0].dispatchEvent(new Event('change'));
        }

        // For shape 104, update first two fields
        if (shapeNumber === '104' && ribFields.length >= 2) {
            ribFields[0].value = values.A;
            ribFields[1].value = values.C;
            ribFields[0].dispatchEvent(new Event('change'));
            ribFields[1].dispatchEvent(new Event('change'));
        }

        // For shape 107, update first three fields with A, C, and E
        if (shapeNumber === '107' && ribFields.length >= 3) {
            ribFields[0].value = values.A;
            ribFields[1].value = values.C;
            ribFields[2].value = values.E;
            ribFields[0].dispatchEvent(new Event('change'));
            ribFields[1].dispatchEvent(new Event('change'));
            ribFields[2].dispatchEvent(new Event('change'));
        }
    }

    // Close the modal
    document.getElementById('catalogShapeModal').style.display = 'none';

    // Log success
    console.log(`Shape ${shapeNumber} saved with values:`, values);
}

// Initialize modal event handlers
document.addEventListener('DOMContentLoaded', function() {
    const modal = document.getElementById('catalogShapeModal');
    const closeBtn = document.querySelector('.close-modal');

    // Close modal when clicking X
    if (closeBtn) {
        closeBtn.onclick = function() {
            modal.style.display = 'none';
        }
    }

    // Close modal when clicking outside
    window.onclick = function(event) {
        if (event.target == modal) {
            modal.style.display = 'none';
        }
    }
});
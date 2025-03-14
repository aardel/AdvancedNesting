document.addEventListener('DOMContentLoaded', function() {
    // Tab switching
    const tabButtons = document.querySelectorAll('.tab-button');
    const tabContents = document.querySelectorAll('.tab-content');
    
    // Send settings to Fusion
    function sendSettingsToFusion(settings) {
        // In real implementation, this would communicate with Fusion 360
        adsk.fusionSendData("runNesting", JSON.stringify(settings)).then(result => {
            // Switch to preview tab
            tabButtons.forEach(btn => {
                if (btn.dataset.tab === 'preview') {
                    btn.click();
                }
            });
            
            // Process the result (would normally come from Fusion)
            const nestingResult = JSON.parse(result);
            
            // Update preview canvas with nesting results
            parts = nestingResult.placements;
            drawSheet();
            drawParts();
            
            // Update preview info
            updatePreviewInfo({
                sheetWidth: nestingResult.sheetWidth,
                sheetHeight: nestingResult.sheetHeight,
                partsPlaced: nestingResult.placements.length,
                materialUtilization: nestingResult.utilization
            });
            
            // Update results tab data
            updateResultsTab(nestingResult);
        });
    }
    
    // Update results tab
    function updateResultsTab(data) {
        // Update summary statistics
        document.getElementById('total-parts').textContent = data.placements.length;
        document.getElementById('sheets-required').textContent = 1; // For multi-sheet support, this would be dynamic
        document.getElementById('material-utilization').textContent = `${data.utilization.toFixed(1)}%`;
        document.getElementById('processing-time').textContent = `${data.processingTime}s`;
        
        // Update utilization bar
        const utilizationBar = document.getElementById('utilization-bar');
        utilizationBar.style.width = `${data.utilization}%`;
        utilizationBar.textContent = `${data.utilization.toFixed(1)}%`;
        
        // Update placement table
        const tableBody = document.getElementById('placement-table-body');
        tableBody.innerHTML = ''; // Clear existing entries
        
        data.placements.forEach((placement, index) => {
            const row = document.createElement('tr');
            
            // Sheet number
            const sheetCell = document.createElement('td');
            sheetCell.textContent = '1'; // For multi-sheet support, this would be dynamic
            row.appendChild(sheetCell);
            
            // Part ID
            const partCell = document.createElement('td');
            partCell.textContent = placement.part_id || `Part ${index + 1}`;
            row.appendChild(partCell);
            
            // Position
            const posCell = document.createElement('td');
            posCell.textContent = `(${placement.x.toFixed(1)}, ${placement.y.toFixed(1)})`;
            row.appendChild(posCell);
            
            // Rotation
            const rotCell = document.createElement('td');
            rotCell.textContent = placement.rotated ? '90°' : '0°';
            row.appendChild(rotCell);
            
            tableBody.appendChild(row);
        });
    }
    
    // Apply nesting button (switch to Fusion)
    const applyNestingBtn = document.getElementById('apply-nesting');
    applyNestingBtn.addEventListener('click', () => {
        adsk.fusionSendData("applyNesting", "").then(result => {
            // Handle completion
        });
    });
    
    // Export button
    const exportNestingBtn = document.getElementById('export-nesting');
    exportNestingBtn.addEventListener('click', () => {
        adsk.fusionSendData("exportNesting", "").then(result => {
            // Handle export completion
        });
    });
    
    // Save report button
    const saveReportBtn = document.getElementById('save-report');
    saveReportBtn.addEventListener('click', () => {
        adsk.fusionSendData("saveReport", "").then(result => {
            // Handle report saving completion
        });
    });
    
    // New nesting button
    const newNestingBtn = document.getElementById('new-nesting');
    newNestingBtn.addEventListener('click', () => {
        // Go back to settings tab
        tabButtons.forEach(btn => {
            if (btn.dataset.tab === 'settings') {
                btn.click();
            }
        });
    });
    
    // Initialize canvas when DOM is loaded
    initCanvas();
    
    // Handle incoming messages from Fusion
    window.fusionJavaScriptHandler = {
        handle: function(action, data) {
            try {
                if (action === "updatePreview") {
                    // Update the canvas with new nesting data
                    const nestingData = JSON.parse(data);
                    parts = nestingData.placements;
                    drawSheet();
                    drawParts();
                    updatePreviewInfo({
                        sheetWidth: nestingData.sheetWidth,
                        sheetHeight: nestingData.sheetHeight,
                        partsPlaced: nestingData.placements.length,
                        materialUtilization: nestingData.utilization
                    });
                    return "Preview updated";
                } 
                else if (action === "updateResults") {
                    // Update the results tab with complete data
                    const resultsData = JSON.parse(data);
                    updateResultsTab(resultsData);
                    return "Results updated";
                }
                else if (action === "debugger") {
                    debugger;
                }
                else {
                    return `Unexpected command type: ${action}`;
                }
            } catch (e) {
                console.log(e);
                console.log(`Exception caught with command: ${action}, data: ${data}`);
            }
            return "OK";
        }
    };
});

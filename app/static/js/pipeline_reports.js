/**
 * Sales Pipeline Reports JavaScript
 * Handles report generation and exports for pipeline data
 */
document.addEventListener('DOMContentLoaded', function() {
    // Initialize report generation buttons
    initializeReportButtons();
    
    // Initialize export buttons
    initializeExportButtons();
    
    /**
     * Initialize report generation buttons
     */
    function initializeReportButtons() {
        const reportButtons = document.querySelectorAll('.generate-report-btn');
        
        reportButtons.forEach(button => {
            button.addEventListener('click', function() {
                const reportType = this.getAttribute('data-report-type');
                generateReport(reportType);
            });
        });
    }
    
    /**
     * Initialize export buttons
     */
    function initializeExportButtons() {
        const exportButtons = document.querySelectorAll('.export-btn');
        
        exportButtons.forEach(button => {
            button.addEventListener('click', function() {
                const reportType = this.getAttribute('data-report-type');
                const format = this.getAttribute('data-format');
                exportReport(reportType, format);
            });
        });
    }
    
    /**
     * Generate a pipeline report
     */
    function generateReport(reportType) {
        // Show loading indicator
        showLoading();
        
        // Get filter values
        const filterForm = document.getElementById('reportFilterForm');
        const formData = filterForm ? new FormData(filterForm) : new FormData();
        formData.append('report_type', reportType);
        
        const params = new URLSearchParams(formData);
        
        // Fetch report data
        fetch('/pipeline/generate_report?' + params.toString(), {
            method: 'GET',
            headers: {
                'X-Requested-With': 'XMLHttpRequest'
            }
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                // Update the report container with the new report
                updateReportContainer(data);
            } else {
                alert('Error: ' + data.message);
            }
            
            // Hide loading indicator
            hideLoading();
        })
        .catch(error => {
            console.error('Error generating report:', error);
            alert('Error generating report. Please try again.');
            
            // Hide loading indicator
            hideLoading();
        });
    }
    
    /**
     * Export a pipeline report
     */
    function exportReport(reportType, format) {
        // Get filter values
        const filterForm = document.getElementById('reportFilterForm');
        const formData = filterForm ? new FormData(filterForm) : new FormData();
        formData.append('report_type', reportType);
        formData.append('format', format);
        
        const params = new URLSearchParams(formData);
        
        // Redirect to export URL
        window.location.href = '/pipeline/export_report?' + params.toString();
    }
    
    /**
     * Update the report container with new report data
     */
    function updateReportContainer(data) {
        const reportContainer = document.getElementById('reportContainer');
        if (!reportContainer) return;
        
        // Clear previous report
        reportContainer.innerHTML = '';
        
        // Create report title
        const reportTitle = document.createElement('h3');
        reportTitle.className = 'mb-4';
        reportTitle.textContent = data.report_title;
        reportContainer.appendChild(reportTitle);
        
        // Create report description
        if (data.report_description) {
            const reportDescription = document.createElement('p');
            reportDescription.className = 'text-muted mb-4';
            reportDescription.textContent = data.report_description;
            reportContainer.appendChild(reportDescription);
        }
        
        // Create report table if there's tabular data
        if (data.table_data && data.table_headers) {
            const tableContainer = document.createElement('div');
            tableContainer.className = 'table-responsive';
            
            const table = document.createElement('table');
            table.className = 'table table-striped table-hover';
            
            // Create table header
            const thead = document.createElement('thead');
            const headerRow = document.createElement('tr');
            
            data.table_headers.forEach(header => {
                const th = document.createElement('th');
                th.textContent = header;
                headerRow.appendChild(th);
            });
            
            thead.appendChild(headerRow);
            table.appendChild(thead);
            
            // Create table body
            const tbody = document.createElement('tbody');
            
            data.table_data.forEach(row => {
                const tr = document.createElement('tr');
                
                row.forEach(cell => {
                    const td = document.createElement('td');
                    td.textContent = cell;
                    tr.appendChild(td);
                });
                
                tbody.appendChild(tr);
            });
            
            table.appendChild(tbody);
            tableContainer.appendChild(table);
            reportContainer.appendChild(tableContainer);
        }
        
        // Create summary statistics if available
        if (data.summary_stats) {
            const summaryContainer = document.createElement('div');
            summaryContainer.className = 'row mt-4';
            
            Object.entries(data.summary_stats).forEach(([key, value]) => {
                const col = document.createElement('div');
                col.className = 'col-md-3 col-sm-6 mb-3';
                
                const card = document.createElement('div');
                card.className = 'card h-100';
                
                const cardBody = document.createElement('div');
                cardBody.className = 'card-body text-center';
                
                const statValue = document.createElement('div');
                statValue.className = 'h3 mb-2';
                statValue.textContent = value;
                
                const statLabel = document.createElement('div');
                statLabel.className = 'text-muted';
                statLabel.textContent = key.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase());
                
                cardBody.appendChild(statValue);
                cardBody.appendChild(statLabel);
                card.appendChild(cardBody);
                col.appendChild(card);
                summaryContainer.appendChild(col);
            });
            
            reportContainer.appendChild(summaryContainer);
        }
        
        // Create chart if chart data is available
        if (data.chart_data && data.chart_type) {
            const chartContainer = document.createElement('div');
            chartContainer.className = 'mt-4';
            
            const canvas = document.createElement('canvas');
            canvas.id = 'reportChart';
            chartContainer.appendChild(canvas);
            reportContainer.appendChild(chartContainer);
            
            // Create the chart
            createChart(canvas, data.chart_type, data.chart_data);
        }
        
        // Update export buttons to include the current filters
        updateExportButtons(data.report_type);
    }
    
    /**
     * Create a chart with the provided data
     */
    function createChart(canvas, chartType, chartData) {
        const ctx = canvas.getContext('2d');
        
        new Chart(ctx, {
            type: chartType,
            data: chartData,
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        position: 'top',
                    },
                    title: {
                        display: true,
                        text: chartData.title || 'Pipeline Report'
                    }
                }
            }
        });
    }
    
    /**
     * Update export buttons to include current filters
     */
    function updateExportButtons(reportType) {
        const exportButtons = document.querySelectorAll('.export-btn');
        
        exportButtons.forEach(button => {
            // Only update buttons for the current report type
            if (button.getAttribute('data-report-type') === reportType) {
                const format = button.getAttribute('data-format');
                const filterForm = document.getElementById('reportFilterForm');
                const formData = filterForm ? new FormData(filterForm) : new FormData();
                formData.append('report_type', reportType);
                formData.append('format', format);
                
                const params = new URLSearchParams(formData);
                button.setAttribute('href', '/pipeline/export_report?' + params.toString());
            }
        });
    }
    
    /**
     * Show loading indicator
     */
    function showLoading() {
        const loadingIndicator = document.getElementById('loadingIndicator');
        if (loadingIndicator) {
            loadingIndicator.classList.remove('d-none');
        }
    }
    
    /**
     * Hide loading indicator
     */
    function hideLoading() {
        const loadingIndicator = document.getElementById('loadingIndicator');
        if (loadingIndicator) {
            loadingIndicator.classList.add('d-none');
        }
    }
});

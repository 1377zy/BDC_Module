/**
 * Sales Pipeline Filters JavaScript
 * Handles filtering options for the pipeline visualization
 */
document.addEventListener('DOMContentLoaded', function() {
    // Initialize filter form
    const filterForm = document.getElementById('pipelineFilterForm');
    if (filterForm) {
        filterForm.addEventListener('submit', function(e) {
            e.preventDefault();
            applyFilters();
        });
    }
    
    // Initialize reset filters button
    const resetButton = document.getElementById('resetFiltersBtn');
    if (resetButton) {
        resetButton.addEventListener('click', function() {
            resetFilters();
        });
    }
    
    // Initialize saved filter dropdown
    const savedFilterSelect = document.getElementById('savedFilterSelect');
    if (savedFilterSelect) {
        savedFilterSelect.addEventListener('change', function() {
            if (this.value) {
                loadSavedFilter(this.value);
            }
        });
    }
    
    // Initialize save filter button
    const saveFilterBtn = document.getElementById('saveFilterBtn');
    if (saveFilterBtn) {
        saveFilterBtn.addEventListener('click', function() {
            saveCurrentFilter();
        });
    }
    
    // Initialize date range picker if available
    const dateRangePicker = document.getElementById('dateRangePicker');
    if (dateRangePicker && typeof daterangepicker !== 'undefined') {
        $(dateRangePicker).daterangepicker({
            opens: 'left',
            autoUpdateInput: false,
            locale: {
                cancelLabel: 'Clear',
                format: 'YYYY-MM-DD'
            }
        });
        
        $(dateRangePicker).on('apply.daterangepicker', function(ev, picker) {
            $(this).val(picker.startDate.format('YYYY-MM-DD') + ' to ' + picker.endDate.format('YYYY-MM-DD'));
        });
        
        $(dateRangePicker).on('cancel.daterangepicker', function() {
            $(this).val('');
        });
    }
    
    /**
     * Apply filters to the pipeline view
     */
    function applyFilters() {
        // Show loading indicator
        showLoading();
        
        // Get filter values
        const formData = new FormData(filterForm);
        const params = new URLSearchParams(formData);
        
        // Redirect to filtered view
        window.location.href = '/pipeline?' + params.toString();
    }
    
    /**
     * Reset all filters
     */
    function resetFilters() {
        // Clear all form inputs
        filterForm.reset();
        
        // Clear any custom styling on selects
        const selects = filterForm.querySelectorAll('select');
        selects.forEach(select => {
            if (select.classList.contains('selectpicker')) {
                $(select).selectpicker('refresh');
            }
        });
        
        // Apply the reset filters
        applyFilters();
    }
    
    /**
     * Load a saved filter
     */
    function loadSavedFilter(filterId) {
        // Show loading indicator
        showLoading();
        
        // Fetch saved filter data
        fetch('/pipeline/get_saved_filter/' + filterId, {
            method: 'GET',
            headers: {
                'X-Requested-With': 'XMLHttpRequest'
            }
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                // Reset form first
                filterForm.reset();
                
                // Apply filter values to the form
                Object.entries(data.filter_data).forEach(([key, value]) => {
                    const input = filterForm.querySelector(`[name="${key}"]`);
                    
                    if (input) {
                        if (input.type === 'checkbox') {
                            input.checked = value === true || value === 'true';
                        } else if (input.tagName === 'SELECT' && input.multiple) {
                            // Handle multi-select
                            if (Array.isArray(value)) {
                                Array.from(input.options).forEach(option => {
                                    option.selected = value.includes(option.value);
                                });
                                
                                // Update selectpicker if used
                                if (input.classList.contains('selectpicker')) {
                                    $(input).selectpicker('refresh');
                                }
                            }
                        } else {
                            input.value = value;
                        }
                    }
                });
                
                // Apply the filters
                applyFilters();
            } else {
                alert('Error: ' + data.message);
                hideLoading();
            }
        })
        .catch(error => {
            console.error('Error loading saved filter:', error);
            alert('Error loading saved filter. Please try again.');
            hideLoading();
        });
    }
    
    /**
     * Save the current filter configuration
     */
    function saveCurrentFilter() {
        // Prompt for filter name
        const filterName = prompt('Enter a name for this filter:');
        
        if (!filterName) return; // User cancelled
        
        // Show loading indicator
        showLoading();
        
        // Serialize form data
        const formData = new FormData(filterForm);
        formData.append('filter_name', filterName);
        
        // Send request to save filter
        fetch('/pipeline/save_filter', {
            method: 'POST',
            body: formData,
            headers: {
                'X-Requested-With': 'XMLHttpRequest'
            }
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                alert('Filter saved successfully!');
                
                // Add the new filter to the dropdown
                const option = document.createElement('option');
                option.value = data.filter_id;
                option.textContent = filterName;
                
                savedFilterSelect.appendChild(option);
                savedFilterSelect.value = data.filter_id;
            } else {
                alert('Error: ' + data.message);
            }
            
            hideLoading();
        })
        .catch(error => {
            console.error('Error saving filter:', error);
            alert('Error saving filter. Please try again.');
            hideLoading();
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

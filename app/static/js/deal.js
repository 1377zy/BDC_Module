/**
 * Deal Management JavaScript
 * Handles dynamic form behavior for deals
 */
document.addEventListener('DOMContentLoaded', function() {
    // Pipeline and stage selection handling
    const pipelineSelect = document.getElementById('pipeline_id');
    const stageSelect = document.getElementById('stage_id');
    
    if (pipelineSelect && stageSelect) {
        pipelineSelect.addEventListener('change', function() {
            fetchStagesForPipeline(this.value);
        });
    }
    
    // Activity modal type selection
    const activityModal = document.getElementById('activityModal');
    if (activityModal) {
        activityModal.addEventListener('show.bs.modal', function(event) {
            const button = event.relatedTarget;
            const activityType = button.getAttribute('data-type');
            
            if (activityType) {
                const activityTypeSelect = this.querySelector('#activity_type');
                if (activityTypeSelect) {
                    activityTypeSelect.value = activityType;
                }
                
                // Update modal title based on activity type
                const modalTitle = this.querySelector('.modal-title');
                if (modalTitle) {
                    const titles = {
                        'call': 'Log Call',
                        'email': 'Log Email',
                        'meeting': 'Schedule Meeting',
                        'note': 'Add Note',
                        'task': 'Add Task'
                    };
                    
                    modalTitle.textContent = titles[activityType] || 'Add Activity';
                }
            }
        });
    }
    
    // Mark completed checkbox behavior
    const markCompletedCheckbox = document.getElementById('mark_completed');
    if (markCompletedCheckbox) {
        markCompletedCheckbox.addEventListener('change', function() {
            const scheduledAtInput = document.getElementById('scheduled_at');
            
            if (this.checked && scheduledAtInput && !scheduledAtInput.value) {
                // If marking as completed and no scheduled date is set, use current date/time
                const now = new Date();
                const year = now.getFullYear();
                const month = String(now.getMonth() + 1).padStart(2, '0');
                const day = String(now.getDate()).padStart(2, '0');
                const hours = String(now.getHours()).padStart(2, '0');
                const minutes = String(now.getMinutes()).padStart(2, '0');
                
                scheduledAtInput.value = `${year}-${month}-${day}T${hours}:${minutes}`;
            }
        });
    }
    
    /**
     * Fetch stages for the selected pipeline
     */
    function fetchStagesForPipeline(pipelineId) {
        if (!pipelineId) return;
        
        // Show loading indicator
        stageSelect.innerHTML = '<option value="">Loading stages...</option>';
        stageSelect.disabled = true;
        
        fetch(`/get_pipeline_stages/${pipelineId}`, {
            method: 'GET',
            headers: {
                'X-Requested-With': 'XMLHttpRequest'
            }
        })
        .then(response => response.json())
        .then(data => {
            // Clear and re-enable the stage select
            stageSelect.innerHTML = '';
            stageSelect.disabled = false;
            
            if (data.success && data.stages.length > 0) {
                // Add each stage as an option
                data.stages.forEach(stage => {
                    const option = document.createElement('option');
                    option.value = stage.id;
                    option.textContent = stage.name;
                    stageSelect.appendChild(option);
                });
            } else {
                // Show error message if no stages were found
                stageSelect.innerHTML = '<option value="">No stages found</option>';
            }
        })
        .catch(error => {
            console.error('Error fetching stages:', error);
            stageSelect.innerHTML = '<option value="">Error loading stages</option>';
            stageSelect.disabled = false;
        });
    }
});

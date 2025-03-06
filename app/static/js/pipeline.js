/**
 * Sales Pipeline Visualization JavaScript
 * Handles drag-and-drop functionality and stage transitions
 */
document.addEventListener('DOMContentLoaded', function() {
    // Initialize all stage containers for drag and drop
    const stageContainers = document.querySelectorAll('.stage-body');
    const dealCards = document.querySelectorAll('.deal-card');
    
    // Track the deal being dragged and its original stage
    let draggedDeal = null;
    let originalStage = null;
    
    // Add drag event listeners to all deal cards
    dealCards.forEach(deal => {
        deal.addEventListener('dragstart', handleDragStart);
        deal.addEventListener('dragend', handleDragEnd);
    });
    
    // Add drop event listeners to all stage containers
    stageContainers.forEach(container => {
        container.addEventListener('dragover', handleDragOver);
        container.addEventListener('dragenter', handleDragEnter);
        container.addEventListener('dragleave', handleDragLeave);
        container.addEventListener('drop', handleDrop);
    });
    
    // Pipeline selector change event
    const pipelineSelector = document.getElementById('pipelineSelector');
    if (pipelineSelector) {
        pipelineSelector.addEventListener('change', function() {
            window.location.href = `/pipeline?pipeline_id=${this.value}`;
        });
    }
    
    /**
     * Handle the start of dragging a deal card
     */
    function handleDragStart(e) {
        draggedDeal = this;
        originalStage = this.parentNode;
        
        // Add a visual class to show it's being dragged
        setTimeout(() => {
            this.classList.add('dragging');
        }, 0);
        
        // Set the drag data
        e.dataTransfer.effectAllowed = 'move';
        e.dataTransfer.setData('text/plain', this.getAttribute('data-deal-id'));
    }
    
    /**
     * Handle the end of dragging a deal card
     */
    function handleDragEnd() {
        this.classList.remove('dragging');
        
        // Reset the dragged deal and original stage
        draggedDeal = null;
        originalStage = null;
        
        // Remove any highlighting from stage containers
        stageContainers.forEach(container => {
            container.classList.remove('drag-over');
        });
    }
    
    /**
     * Handle dragging over a stage container
     */
    function handleDragOver(e) {
        if (e.preventDefault) {
            e.preventDefault(); // Allows dropping
        }
        
        e.dataTransfer.dropEffect = 'move';
        return false;
    }
    
    /**
     * Handle entering a stage container while dragging
     */
    function handleDragEnter(e) {
        this.classList.add('drag-over');
    }
    
    /**
     * Handle leaving a stage container while dragging
     */
    function handleDragLeave() {
        this.classList.remove('drag-over');
    }
    
    /**
     * Handle dropping a deal card into a stage container
     */
    function handleDrop(e) {
        e.stopPropagation(); // Stops the browser from redirecting
        
        // Remove highlighting
        this.classList.remove('drag-over');
        
        // Only proceed if we have a valid dragged deal
        if (!draggedDeal) return false;
        
        // Get the target stage and deal ID
        const targetStage = this;
        const dealId = e.dataTransfer.getData('text/plain');
        const targetStageId = targetStage.id.replace('stage-', '');
        
        // Don't do anything if dropped in the same stage
        if (originalStage === targetStage) return false;
        
        // Move the deal visually
        targetStage.appendChild(draggedDeal);
        
        // Update the deal's stage on the server
        updateDealStage(dealId, targetStageId);
        
        return false;
    }
    
    /**
     * Send an AJAX request to update the deal's stage
     */
    function updateDealStage(dealId, stageId) {
        // Show a loading indicator
        const loadingToast = showToast('Moving deal...', 'info');
        
        fetch('/change_deal_stage_ajax', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-Requested-With': 'XMLHttpRequest'
            },
            body: JSON.stringify({
                deal_id: dealId,
                stage_id: stageId
            })
        })
        .then(response => response.json())
        .then(data => {
            // Hide the loading indicator
            hideToast(loadingToast);
            
            if (data.success) {
                showToast('Deal moved successfully!', 'success');
                
                // Update any stage counters
                updateStageCounts();
            } else {
                showToast('Error: ' + data.message, 'error');
                
                // Move the deal back to its original stage if there was an error
                if (originalStage && draggedDeal) {
                    originalStage.appendChild(draggedDeal);
                }
            }
        })
        .catch(error => {
            // Hide the loading indicator
            hideToast(loadingToast);
            
            showToast('Error: ' + error.message, 'error');
            
            // Move the deal back to its original stage if there was an error
            if (originalStage && draggedDeal) {
                originalStage.appendChild(draggedDeal);
            }
        });
    }
    
    /**
     * Update the deal count for each stage
     */
    function updateStageCounts() {
        stageContainers.forEach(container => {
            const stageId = container.id.replace('stage-', '');
            const dealCount = container.querySelectorAll('.deal-card').length;
            
            // Find the badge in the stage header and update it
            const stageHeader = container.previousElementSibling;
            const badge = stageHeader.querySelector('.badge');
            
            if (badge) {
                badge.textContent = dealCount;
            }
        });
    }
    
    /**
     * Show a toast notification
     */
    function showToast(message, type = 'info') {
        const toast = document.createElement('div');
        toast.className = `toast toast-${type}`;
        toast.innerHTML = message;
        
        document.body.appendChild(toast);
        
        // Trigger reflow to enable the transition
        toast.offsetHeight;
        
        // Show the toast
        toast.classList.add('show');
        
        // Auto-hide after 3 seconds for success/info messages
        if (type === 'success' || type === 'info') {
            setTimeout(() => {
                hideToast(toast);
            }, 3000);
        }
        
        return toast;
    }
    
    /**
     * Hide a toast notification
     */
    function hideToast(toast) {
        toast.classList.remove('show');
        
        // Remove from DOM after transition
        setTimeout(() => {
            if (toast.parentNode) {
                toast.parentNode.removeChild(toast);
            }
        }, 300);
    }
});

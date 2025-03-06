/**
 * Pipeline Form JavaScript
 * Handles stage management, reordering, and color picking
 */
document.addEventListener('DOMContentLoaded', function() {
    // Initialize sortable for stages
    const stagesContainer = document.getElementById('stagesContainer');
    if (stagesContainer) {
        new Sortable(stagesContainer, {
            animation: 150,
            handle: '.card-header',
            ghostClass: 'sortable-ghost',
            onEnd: function() {
                updateStageIndices();
            }
        });
    }
    
    // Initialize color pickers
    initializeColorPickers();
    
    // Add stage button
    const addStageBtn = document.getElementById('addStageBtn');
    if (addStageBtn) {
        addStageBtn.addEventListener('click', addNewStage);
    }
    
    // Remove stage buttons
    document.addEventListener('click', function(e) {
        if (e.target.closest('.remove-stage-btn')) {
            removeStage(e.target.closest('.stage-card'));
        }
    });
    
    // Form validation
    const pipelineForm = document.getElementById('pipelineForm');
    if (pipelineForm) {
        pipelineForm.addEventListener('submit', validateForm);
    }
    
    // Won/Lost stage checkboxes
    document.addEventListener('change', function(e) {
        if (e.target.matches('input[name="stage_is_won[]"]')) {
            handleWonStageChange(e.target);
        } else if (e.target.matches('input[name="stage_is_lost[]"]')) {
            handleLostStageChange(e.target);
        }
    });
    
    /**
     * Initialize color pickers for all stage color inputs
     */
    function initializeColorPickers() {
        const colorPickers = document.querySelectorAll('.color-picker');
        
        colorPickers.forEach(picker => {
            $(picker).spectrum({
                preferredFormat: "hex",
                showInput: true,
                showPalette: true,
                palette: [
                    ["#3498db", "#2ecc71", "#e74c3c", "#f39c12", "#9b59b6"],
                    ["#1abc9c", "#34495e", "#16a085", "#27ae60", "#2980b9"],
                    ["#8e44ad", "#f1c40f", "#e67e22", "#c0392b", "#d35400"]
                ],
                change: function(color) {
                    // Update the stage header color when the color is changed
                    const stageCard = this.closest('.stage-card');
                    const header = stageCard.querySelector('.card-header');
                    header.style.backgroundColor = color.toHexString();
                }
            });
        });
    }
    
    /**
     * Add a new stage to the pipeline
     */
    function addNewStage() {
        // Clone the stage template
        const template = document.getElementById('stageTemplate');
        const newStage = template.querySelector('.stage-card').cloneNode(true);
        
        // Remove the d-none class if it exists
        newStage.classList.remove('d-none');
        
        // Add it to the stages container
        const stagesContainer = document.getElementById('stagesContainer');
        stagesContainer.appendChild(newStage);
        
        // Update stage indices and numbering
        updateStageIndices();
        
        // Initialize color picker for the new stage
        initializeColorPickers();
        
        // Set focus on the stage name input
        const nameInput = newStage.querySelector('.stage-name');
        if (nameInput) {
            nameInput.focus();
        }
    }
    
    /**
     * Remove a stage from the pipeline
     */
    function removeStage(stageCard) {
        // Don't allow removing if there's only one stage
        const stageCount = document.querySelectorAll('.stage-card:not(.d-none)').length;
        if (stageCount <= 1) {
            alert('You must have at least one stage in the pipeline.');
            return;
        }
        
        // Confirm removal
        if (confirm('Are you sure you want to remove this stage?')) {
            stageCard.remove();
            updateStageIndices();
        }
    }
    
    /**
     * Update stage indices and numbering after reordering
     */
    function updateStageIndices() {
        const stages = document.querySelectorAll('.stage-card:not(.d-none)');
        
        stages.forEach((stage, index) => {
            // Update stage header title
            const header = stage.querySelector('.card-header h6');
            if (header) {
                header.textContent = `Stage ${index + 1}`;
            }
            
            // Update won/lost checkbox values
            const wonCheckbox = stage.querySelector('input[name="stage_is_won[]"]');
            if (wonCheckbox) {
                wonCheckbox.value = index;
            }
            
            const lostCheckbox = stage.querySelector('input[name="stage_is_lost[]"]');
            if (lostCheckbox) {
                lostCheckbox.value = index;
            }
        });
    }
    
    /**
     * Handle changes to the "Won Stage" checkbox
     */
    function handleWonStageChange(checkbox) {
        if (checkbox.checked) {
            // Uncheck all other "Won Stage" checkboxes
            const otherWonCheckboxes = document.querySelectorAll('input[name="stage_is_won[]"]:checked');
            otherWonCheckboxes.forEach(cb => {
                if (cb !== checkbox) {
                    cb.checked = false;
                }
            });
            
            // Uncheck the "Lost Stage" checkbox in the same stage
            const stageCard = checkbox.closest('.stage-card');
            const lostCheckbox = stageCard.querySelector('input[name="stage_is_lost[]"]');
            if (lostCheckbox) {
                lostCheckbox.checked = false;
            }
        }
    }
    
    /**
     * Handle changes to the "Lost Stage" checkbox
     */
    function handleLostStageChange(checkbox) {
        if (checkbox.checked) {
            // Uncheck all other "Lost Stage" checkboxes
            const otherLostCheckboxes = document.querySelectorAll('input[name="stage_is_lost[]"]:checked');
            otherLostCheckboxes.forEach(cb => {
                if (cb !== checkbox) {
                    cb.checked = false;
                }
            });
            
            // Uncheck the "Won Stage" checkbox in the same stage
            const stageCard = checkbox.closest('.stage-card');
            const wonCheckbox = stageCard.querySelector('input[name="stage_is_won[]"]');
            if (wonCheckbox) {
                wonCheckbox.checked = false;
            }
        }
    }
    
    /**
     * Validate the form before submission
     */
    function validateForm(e) {
        const stages = document.querySelectorAll('.stage-card:not(.d-none)');
        
        // Ensure there's at least one stage
        if (stages.length === 0) {
            e.preventDefault();
            alert('You must have at least one stage in the pipeline.');
            return false;
        }
        
        // Ensure all stage names are filled
        let allValid = true;
        stages.forEach(stage => {
            const nameInput = stage.querySelector('.stage-name');
            if (!nameInput.value.trim()) {
                nameInput.classList.add('is-invalid');
                allValid = false;
            } else {
                nameInput.classList.remove('is-invalid');
            }
        });
        
        if (!allValid) {
            e.preventDefault();
            alert('Please fill in all required fields.');
            return false;
        }
        
        return true;
    }
});

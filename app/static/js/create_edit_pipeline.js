/**
 * Create/Edit Pipeline JavaScript
 * Handles the pipeline and stage creation/editing functionality
 */
document.addEventListener('DOMContentLoaded', function() {
    // Initialize Sortable.js for stage reordering
    const stagesContainer = document.getElementById('stagesContainer');
    if (stagesContainer) {
        new Sortable(stagesContainer, {
            animation: 150,
            handle: '.stage-card-header',
            ghostClass: 'stage-card-ghost',
            onEnd: function() {
                updateStageOrder();
            }
        });
    }
    
    // Add stage button
    const addStageBtn = document.getElementById('addStageBtn');
    if (addStageBtn) {
        addStageBtn.addEventListener('click', function() {
            addNewStage();
        });
    }
    
    // Remove stage buttons (delegated event)
    document.addEventListener('click', function(e) {
        if (e.target.matches('.remove-stage-btn') || e.target.closest('.remove-stage-btn')) {
            const stageCard = e.target.closest('.stage-card');
            if (stageCard) {
                removeStage(stageCard);
            }
        }
    });
    
    // Color picker initialization
    initializeColorPickers();
    
    // Form validation
    const pipelineForm = document.getElementById('pipelineForm');
    if (pipelineForm) {
        pipelineForm.addEventListener('submit', function(e) {
            if (!validatePipelineForm()) {
                e.preventDefault();
            }
        });
    }
    
    // Stage type radio buttons
    document.addEventListener('change', function(e) {
        if (e.target.matches('input[name^="stage_type_"]')) {
            const stageCard = e.target.closest('.stage-card');
            updateStageTypeOptions(stageCard, e.target.value);
        }
    });
    
    /**
     * Initialize color pickers for all stage color inputs
     */
    function initializeColorPickers() {
        const colorPickers = document.querySelectorAll('.stage-color-picker');
        
        colorPickers.forEach(picker => {
            const defaultColor = picker.value || '#3498db';
            
            $(picker).spectrum({
                color: defaultColor,
                showInput: true,
                showInitial: true,
                showPalette: true,
                showSelectionPalette: true,
                maxSelectionSize: 10,
                preferredFormat: "hex",
                palette: [
                    ["#3498db", "#2ecc71", "#e74c3c", "#f39c12", "#9b59b6"],
                    ["#1abc9c", "#34495e", "#16a085", "#27ae60", "#2980b9"],
                    ["#8e44ad", "#f1c40f", "#e67e22", "#c0392b", "#d35400"]
                ],
                change: function(color) {
                    // Update the stage header color when the color is changed
                    const stageCard = this.closest('.stage-card');
                    const header = stageCard.querySelector('.stage-card-header');
                    
                    if (header) {
                        header.style.backgroundColor = color.toHexString();
                        header.style.borderColor = color.toHexString();
                        
                        // Determine if text should be white or black based on color brightness
                        const brightness = calculateBrightness(color.toHexString());
                        header.style.color = brightness > 128 ? '#000' : '#fff';
                    }
                }
            });
            
            // Set initial header color
            const stageCard = picker.closest('.stage-card');
            const header = stageCard.querySelector('.stage-card-header');
            
            if (header) {
                header.style.backgroundColor = defaultColor;
                header.style.borderColor = defaultColor;
                
                // Determine if text should be white or black based on color brightness
                const brightness = calculateBrightness(defaultColor);
                header.style.color = brightness > 128 ? '#000' : '#fff';
            }
        });
    }
    
    /**
     * Calculate the brightness of a color (0-255)
     */
    function calculateBrightness(hex) {
        // Remove the hash if it exists
        hex = hex.replace('#', '');
        
        // Parse the RGB values
        const r = parseInt(hex.substr(0, 2), 16);
        const g = parseInt(hex.substr(2, 2), 16);
        const b = parseInt(hex.substr(4, 2), 16);
        
        // Calculate brightness using the formula: (0.299*R + 0.587*G + 0.114*B)
        return (0.299 * r + 0.587 * g + 0.114 * b);
    }
    
    /**
     * Add a new stage to the pipeline
     */
    function addNewStage() {
        // Get the stage template
        const stageTemplate = document.getElementById('stageTemplate');
        if (!stageTemplate) return;
        
        // Clone the template
        const newStage = stageTemplate.cloneNode(true);
        newStage.id = '';
        newStage.classList.remove('d-none');
        
        // Get the current number of stages to set the new stage index
        const stageCount = document.querySelectorAll('.stage-card:not(.d-none):not(#stageTemplate)').length;
        const stageIndex = stageCount;
        
        // Update IDs and names with the new index
        updateStageIds(newStage, stageIndex);
        
        // Add the new stage to the container
        stagesContainer.appendChild(newStage);
        
        // Initialize color picker for the new stage
        const colorPicker = newStage.querySelector('.stage-color-picker');
        if (colorPicker) {
            $(colorPicker).spectrum({
                color: '#3498db',
                showInput: true,
                showInitial: true,
                showPalette: true,
                showSelectionPalette: true,
                maxSelectionSize: 10,
                preferredFormat: "hex",
                palette: [
                    ["#3498db", "#2ecc71", "#e74c3c", "#f39c12", "#9b59b6"],
                    ["#1abc9c", "#34495e", "#16a085", "#27ae60", "#2980b9"],
                    ["#8e44ad", "#f1c40f", "#e67e22", "#c0392b", "#d35400"]
                ],
                change: function(color) {
                    // Update the stage header color when the color is changed
                    const stageCard = this.closest('.stage-card');
                    const header = stageCard.querySelector('.stage-card-header');
                    
                    if (header) {
                        header.style.backgroundColor = color.toHexString();
                        header.style.borderColor = color.toHexString();
                        
                        // Determine if text should be white or black based on color brightness
                        const brightness = calculateBrightness(color.toHexString());
                        header.style.color = brightness > 128 ? '#000' : '#fff';
                    }
                }
            });
            
            // Set initial header color
            const header = newStage.querySelector('.stage-card-header');
            if (header) {
                header.style.backgroundColor = '#3498db';
                header.style.borderColor = '#3498db';
                header.style.color = '#fff';
            }
        }
        
        // Update stage numbers
        updateStageNumbers();
        
        // Set focus on the stage name input
        const nameInput = newStage.querySelector('input[name^="stage_name_"]');
        if (nameInput) {
            nameInput.focus();
        }
    }
    
    /**
     * Remove a stage from the pipeline
     */
    function removeStage(stageCard) {
        // Check if we have at least one stage (not counting the template)
        const stageCount = document.querySelectorAll('.stage-card:not(.d-none):not(#stageTemplate)').length;
        
        if (stageCount <= 1) {
            alert('You must have at least one stage in the pipeline.');
            return;
        }
        
        // Confirm removal
        if (confirm('Are you sure you want to remove this stage? This cannot be undone.')) {
            // Remove the stage
            stageCard.remove();
            
            // Update stage numbers and IDs
            updateStageNumbers();
            updateAllStageIds();
        }
    }
    
    /**
     * Update all stage IDs and names after reordering or removal
     */
    function updateAllStageIds() {
        const stages = document.querySelectorAll('.stage-card:not(.d-none):not(#stageTemplate)');
        
        stages.forEach((stage, index) => {
            updateStageIds(stage, index);
        });
    }
    
    /**
     * Update IDs and names for a specific stage
     */
    function updateStageIds(stageElement, index) {
        // Update input names and IDs
        const inputs = stageElement.querySelectorAll('input, select, textarea');
        inputs.forEach(input => {
            // Update name attribute
            if (input.name) {
                input.name = input.name.replace(/_(\\d+)$/, '_' + index);
            }
            
            // Update id attribute
            if (input.id) {
                input.id = input.id.replace(/_(\\d+)$/, '_' + index);
            }
        });
        
        // Update label for attributes
        const labels = stageElement.querySelectorAll('label');
        labels.forEach(label => {
            if (label.htmlFor) {
                label.htmlFor = label.htmlFor.replace(/_(\\d+)$/, '_' + index);
            }
        });
        
        // Set the stage index hidden input
        const indexInput = stageElement.querySelector('input[name^="stage_index_"]');
        if (indexInput) {
            indexInput.value = index;
        }
    }
    
    /**
     * Update stage numbers in headers after reordering or adding/removing stages
     */
    function updateStageNumbers() {
        const stages = document.querySelectorAll('.stage-card:not(.d-none):not(#stageTemplate)');
        
        stages.forEach((stage, index) => {
            const stageNumber = stage.querySelector('.stage-number');
            if (stageNumber) {
                stageNumber.textContent = 'Stage ' + (index + 1);
            }
        });
    }
    
    /**
     * Update stage order after drag and drop reordering
     */
    function updateStageOrder() {
        updateStageNumbers();
        updateAllStageIds();
    }
    
    /**
     * Update stage type options based on selected type
     */
    function updateStageTypeOptions(stageCard, stageType) {
        const winLostOptions = stageCard.querySelector('.win-lost-options');
        
        if (winLostOptions) {
            if (stageType === 'won') {
                winLostOptions.classList.remove('d-none');
                
                // Uncheck "Lost" if "Won" is selected
                const lostCheckbox = stageCard.querySelector('input[name^="stage_is_lost_"]');
                if (lostCheckbox && lostCheckbox.checked) {
                    lostCheckbox.checked = false;
                }
            } else if (stageType === 'lost') {
                winLostOptions.classList.remove('d-none');
                
                // Uncheck "Won" if "Lost" is selected
                const wonCheckbox = stageCard.querySelector('input[name^="stage_is_won_"]');
                if (wonCheckbox && wonCheckbox.checked) {
                    wonCheckbox.checked = false;
                }
            } else {
                winLostOptions.classList.add('d-none');
                
                // Uncheck both "Won" and "Lost" for normal stages
                const wonCheckbox = stageCard.querySelector('input[name^="stage_is_won_"]');
                const lostCheckbox = stageCard.querySelector('input[name^="stage_is_lost_"]');
                
                if (wonCheckbox) wonCheckbox.checked = false;
                if (lostCheckbox) lostCheckbox.checked = false;
            }
        }
    }
    
    /**
     * Validate the pipeline form before submission
     */
    function validatePipelineForm() {
        let isValid = true;
        
        // Validate pipeline name
        const pipelineName = document.getElementById('pipeline_name');
        if (!pipelineName.value.trim()) {
            isValid = false;
            pipelineName.classList.add('is-invalid');
        } else {
            pipelineName.classList.remove('is-invalid');
        }
        
        // Validate each stage
        const stages = document.querySelectorAll('.stage-card:not(.d-none):not(#stageTemplate)');
        
        stages.forEach(stage => {
            const stageName = stage.querySelector('input[name^="stage_name_"]');
            
            if (!stageName.value.trim()) {
                isValid = false;
                stageName.classList.add('is-invalid');
            } else {
                stageName.classList.remove('is-invalid');
            }
        });
        
        // Check if we have at least one stage
        if (stages.length === 0) {
            isValid = false;
            alert('You must add at least one stage to the pipeline.');
        }
        
        // Check if we have a "Won" stage
        const hasWonStage = Array.from(stages).some(stage => {
            const wonRadio = stage.querySelector('input[value="won"][name^="stage_type_"]');
            return wonRadio && wonRadio.checked;
        });
        
        if (!hasWonStage) {
            isValid = false;
            alert('You must designate at least one stage as a "Won" stage.');
        }
        
        return isValid;
    }
});

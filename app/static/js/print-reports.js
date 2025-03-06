/**
 * Print Reports Functionality
 * Auto Dealership BDC Module
 */

document.addEventListener('DOMContentLoaded', function() {
    // Find all print buttons
    const printButtons = document.querySelectorAll('.print-report-btn');
    
    // Add click event listener to each print button
    printButtons.forEach(button => {
        button.addEventListener('click', function(e) {
            e.preventDefault();
            
            // Get report title for the print header
            const reportTitle = document.querySelector('h1').innerText;
            
            // Add print-specific elements
            addPrintElements(reportTitle);
            
            // Print the document
            window.print();
            
            // Remove print-specific elements after printing
            setTimeout(removePrintElements, 100);
        });
    });
    
    /**
     * Add print-specific elements to the document
     * @param {string} reportTitle - The title of the report
     */
    function addPrintElements(reportTitle) {
        // Create report header
        const header = document.createElement('div');
        header.className = 'report-header print-only';
        header.innerHTML = `
            <div class="report-title">${reportTitle}</div>
            <div class="report-metadata">
                Generated on: ${new Date().toLocaleString()}
                <br>
                Auto Dealership BDC Module
            </div>
        `;
        
        // Add header to the beginning of the content
        const content = document.querySelector('.container');
        content.insertBefore(header, content.firstChild);
        
        // Add watermark for draft reports if needed
        if (document.querySelector('.draft-report')) {
            const watermark = document.createElement('div');
            watermark.className = 'draft-watermark print-only';
            watermark.innerText = 'DRAFT';
            document.body.appendChild(watermark);
        }
        
        // Add page breaks before major sections
        const sections = document.querySelectorAll('.row > .col-12 > .card, .row > .col-md-12 > .card');
        sections.forEach((section, index) => {
            if (index > 0) {
                section.classList.add('page-break');
            }
        });
        
        // Add class to body for print-specific styling
        document.body.classList.add('printing');
    }
    
    /**
     * Remove print-specific elements from the document
     */
    function removePrintElements() {
        // Remove report header
        const headers = document.querySelectorAll('.print-only');
        headers.forEach(header => header.remove());
        
        // Remove page break classes
        const pageBreaks = document.querySelectorAll('.page-break');
        pageBreaks.forEach(element => element.classList.remove('page-break'));
        
        // Remove printing class from body
        document.body.classList.remove('printing');
    }
});

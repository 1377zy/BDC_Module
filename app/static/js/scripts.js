// Auto Dealership BDC Application JavaScript

$(document).ready(function() {
    // Handle template selection for email form
    $('#template_id').change(function() {
        const templateId = $(this).val();
        if (templateId != 0) {
            $.get(`/communications/get_template/email/${templateId}`, function(data) {
                $('#subject').val(data.subject);
                $('#body').val(data.body);
            });
        }
    });

    // Handle template selection for SMS form
    $('#template_id').change(function() {
        const templateId = $(this).val();
        if (templateId != 0) {
            $.get(`/communications/get_template/sms/${templateId}`, function(data) {
                $('#body').val(data.body);
            });
        }
    });

    // Enable tooltips everywhere
    const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });

    // Enable popovers
    const popoverTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="popover"]'));
    popoverTriggerList.map(function (popoverTriggerEl) {
        return new bootstrap.Popover(popoverTriggerEl);
    });

    // Auto-dismiss alerts after 5 seconds
    window.setTimeout(function() {
        $(".alert").fadeTo(500, 0).slideUp(500, function(){
            $(this).remove(); 
        });
    }, 5000);

    // Dynamic placeholders for email/SMS templates
    $('.show-placeholders').click(function(e) {
        e.preventDefault();
        const placeholders = [
            '{first_name} - Lead\'s first name',
            '{last_name} - Lead\'s last name',
            '{email} - Lead\'s email address',
            '{phone} - Lead\'s phone number',
            '{agent_name} - Your name',
            '{dealership_name} - Dealership name',
            '{dealership_phone} - Dealership phone number',
            '{dealership_address} - Dealership address',
            '{appointment_date} - Scheduled appointment date',
            '{appointment_time} - Scheduled appointment time',
            '{vehicle} - Vehicle of interest'
        ];
        
        let placeholderList = '<ul>';
        placeholders.forEach(function(p) {
            placeholderList += `<li>${p}</li>`;
        });
        placeholderList += '</ul>';
        
        $('#placeholderModal .modal-body').html(placeholderList);
        new bootstrap.Modal(document.getElementById('placeholderModal')).show();
    });

    // Initialize date pickers
    if($('.datepicker').length > 0) {
        $('.datepicker').datepicker({
            format: 'yyyy-mm-dd',
            autoclose: true,
            todayHighlight: true
        });
    }

    // Add animation to dashboard cards
    $('.dashboard-card').addClass('fade-in');
    $('.stat-card').each(function(index) {
        $(this).css('animation-delay', (index * 0.1) + 's');
        $(this).addClass('fade-in');
    });

    // Character counter for SMS messages
    $('#sms-body').on('input', function() {
        const maxLength = 160;
        const currentLength = $(this).val().length;
        const remaining = maxLength - currentLength;
        
        $('#char-count').text(remaining);
        
        if (remaining < 20) {
            $('#char-count').addClass('text-danger').removeClass('text-muted');
        } else {
            $('#char-count').addClass('text-muted').removeClass('text-danger');
        }
    });

    // Confirm deletion of any item
    $('.confirm-delete').click(function(e) {
        if (!confirm('Are you sure you want to delete this item? This action cannot be undone.')) {
            e.preventDefault();
        }
    });

    // Handle appointment status changes
    $('#appointment-status').change(function() {
        const status = $(this).val();
        if (status === 'Cancelled' || status === 'Rescheduled') {
            $('#notes-section').removeClass('d-none');
            $('#appointment-notes').attr('required', true);
        } else {
            $('#notes-section').addClass('d-none');
            $('#appointment-notes').attr('required', false);
        }
    });

    // Real-time lead search
    $('#quick-search').on('input', function() {
        const searchTerm = $(this).val().toLowerCase();
        $('.lead-item').each(function() {
            const name = $(this).data('name').toLowerCase();
            const email = $(this).data('email').toLowerCase();
            const phone = $(this).data('phone').toLowerCase();
            
            if (name.includes(searchTerm) || email.includes(searchTerm) || phone.includes(searchTerm)) {
                $(this).show();
            } else {
                $(this).hide();
            }
        });
    });

    // Highlight today's date in appointment calendar
    const today = new Date();
    const todayString = today.toISOString().split('T')[0];
    $(`.calendar-day[data-date="${todayString}"]`).addClass('bg-light');
});

// Function to process template placeholders
function processTemplate(templateText, data) {
    return templateText
        .replace(/{first_name}/g, data.firstName || '')
        .replace(/{last_name}/g, data.lastName || '')
        .replace(/{email}/g, data.email || '')
        .replace(/{phone}/g, data.phone || '')
        .replace(/{agent_name}/g, data.agentName || '')
        .replace(/{dealership_name}/g, data.dealershipName || '')
        .replace(/{dealership_phone}/g, data.dealershipPhone || '')
        .replace(/{dealership_address}/g, data.dealershipAddress || '')
        .replace(/{appointment_date}/g, data.appointmentDate || '')
        .replace(/{appointment_time}/g, data.appointmentTime || '')
        .replace(/{vehicle}/g, data.vehicle || '');
}

// Function to fill template with lead data
function fillTemplateWithLeadData(leadId) {
    $.get(`/leads/${leadId}/data`, function(data) {
        const templateId = $('#template_id').val();
        if (templateId != 0) {
            const templateType = window.location.pathname.includes('email') ? 'email' : 'sms';
            $.get(`/communications/get_template/${templateType}/${templateId}`, function(template) {
                if (templateType === 'email') {
                    $('#subject').val(processTemplate(template.subject, data));
                    $('#body').val(processTemplate(template.body, data));
                } else {
                    $('#body').val(processTemplate(template.body, data));
                }
            });
        }
    });
}

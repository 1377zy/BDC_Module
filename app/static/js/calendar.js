document.addEventListener('DOMContentLoaded', function() {
    const calendarEl = document.getElementById('calendar');
    
    // Initialize FullCalendar
    const calendar = new FullCalendar.Calendar(calendarEl, {
        initialView: 'dayGridMonth',
        headerToolbar: false,
        height: '100%',
        firstDay: 1, // Monday
        businessHours: {
            daysOfWeek: [1, 2, 3, 4, 5, 6, 0], // Monday - Sunday
            startTime: '09:00',
            endTime: '20:00',
        },
        events: appointmentsData, // This will be defined in the template
        eventClick: function(info) {
            showAppointmentDetails(info.event.id);
        },
        eventClassNames: function(arg) {
            const status = arg.event.extendedProps.status.toLowerCase().replace(' ', '-');
            return ['appointment-' + status];
        },
        selectable: true,
        dateClick: function(info) {
            // Show the quick add appointment modal instead of redirecting
            showQuickAddModal(info.dateStr);
        }
    });
    
    calendar.render();
    
    // Navigation buttons
    document.getElementById('prev-button').addEventListener('click', function() {
        calendar.prev();
        updateMonthYearDisplay();
    });
    
    document.getElementById('next-button').addEventListener('click', function() {
        calendar.next();
        updateMonthYearDisplay();
    });
    
    document.getElementById('today-button').addEventListener('click', function() {
        calendar.today();
        updateMonthYearDisplay();
    });
    
    // View buttons
    document.getElementById('month-view').addEventListener('click', function() {
        calendar.changeView('dayGridMonth');
        updateActiveButton(this);
    });
    
    document.getElementById('week-view').addEventListener('click', function() {
        calendar.changeView('timeGridWeek');
        updateActiveButton(this);
    });
    
    document.getElementById('day-view').addEventListener('click', function() {
        calendar.changeView('timeGridDay');
        updateActiveButton(this);
    });
    
    // Update month/year display
    function updateMonthYearDisplay() {
        const calendarDate = calendar.getDate();
        const monthYear = calendarDate.toLocaleString('default', { month: 'long', year: 'numeric' });
        document.getElementById('current-month-year').textContent = monthYear;
    }
    
    // Initial month/year display
    updateMonthYearDisplay();
    
    // Update active button
    function updateActiveButton(button) {
        const buttons = document.querySelectorAll('.view-button');
        buttons.forEach(function(btn) {
            btn.classList.remove('active');
        });
        button.classList.add('active');
    }
    
    // Filter appointments by status
    const filterCheckboxes = document.querySelectorAll('.filter-status');
    filterCheckboxes.forEach(function(checkbox) {
        checkbox.addEventListener('change', function() {
            filterEvents();
        });
    });
    
    function filterEvents() {
        const selectedStatuses = Array.from(document.querySelectorAll('.filter-status:checked')).map(cb => cb.value);
        
        if (selectedStatuses.length === 0) {
            // If no filters selected, show all events
            calendar.getEvents().forEach(event => event.setProp('display', 'auto'));
        } else {
            // Otherwise, filter events
            calendar.getEvents().forEach(event => {
                const status = event.extendedProps.status;
                const display = selectedStatuses.includes(status) ? 'auto' : 'none';
                event.setProp('display', display);
            });
        }
    }
    
    // Print calendar
    document.getElementById('print-calendar').addEventListener('click', function() {
        window.print();
    });
    
    // Show appointment details in modal
    function showAppointmentDetails(appointmentId) {
        const modal = new bootstrap.Modal(document.getElementById('appointmentModal'));
        const loadingElement = document.getElementById('appointment-loading');
        const detailsElement = document.getElementById('appointment-details');
        
        // Show loading, hide details
        loadingElement.classList.remove('d-none');
        detailsElement.classList.add('d-none');
        
        // Show modal
        modal.show();
        
        // Fetch appointment details
        fetch(`/appointments/api/get/${appointmentId}`)
            .then(response => response.json())
            .then(data => {
                // Hide loading, show details
                loadingElement.classList.add('d-none');
                detailsElement.classList.remove('d-none');
                
                // Populate modal with appointment details
                document.getElementById('appointment-lead').textContent = `${data.lead.first_name} ${data.lead.last_name}`;
                document.getElementById('appointment-date').textContent = data.date;
                document.getElementById('appointment-time').textContent = data.time;
                document.getElementById('appointment-status').textContent = data.status;
                document.getElementById('appointment-vehicle').textContent = data.vehicle_interest || 'Not specified';
                
                if (data.notes) {
                    document.getElementById('appointment-notes').textContent = data.notes;
                    document.getElementById('appointment-notes-container').classList.remove('d-none');
                } else {
                    document.getElementById('appointment-notes-container').classList.add('d-none');
                }
                
                // Set links
                document.getElementById('appointment-view-link').href = `/appointments/view/${appointmentId}`;
                document.getElementById('appointment-edit-link').href = `/appointments/edit/${appointmentId}`;
                document.getElementById('appointment-lead-link').href = `/leads/${data.lead.id}`;
            })
            .catch(error => {
                console.error('Error fetching appointment details:', error);
                alert('Error loading appointment details. Please try again.');
            });
    }
    
    // Show quick add appointment modal
    function showQuickAddModal(date) {
        const modal = new bootstrap.Modal(document.getElementById('quickAddModal'));
        
        // Populate modal
        document.getElementById('quick-add-date').textContent = date;
        document.getElementById('quick-add-date-input').value = date;
        
        // Show modal
        modal.show();
    }
    
    // Handle quick add form submission
    document.getElementById('quick-add-submit').addEventListener('click', function() {
        document.getElementById('quickAddForm').submit();
    });
});

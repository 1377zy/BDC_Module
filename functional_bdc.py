from flask import Flask, render_template, redirect, url_for, flash, request
from datetime import datetime, timedelta
import os

app = Flask(__name__, template_folder='app/templates', static_folder='app/static')
app.config['SECRET_KEY'] = 'development-secret-key-123'

# Mock data
leads = [
    {'id': 1, 'name': 'John Smith', 'phone': '555-123-4567', 'email': 'john@example.com', 'status': 'New', 'vehicle': 'SUV'},
    {'id': 2, 'name': 'Jane Doe', 'phone': '555-987-6543', 'email': 'jane@example.com', 'status': 'Contacted', 'vehicle': 'Sedan'},
    {'id': 3, 'name': 'Bob Johnson', 'phone': '555-555-5555', 'email': 'bob@example.com', 'status': 'Qualified', 'vehicle': 'Truck'}
]

appointments = [
    {'id': 1, 'lead_id': 1, 'date': '2025-03-03', 'time': '10:00 AM', 'type': 'Test Drive'},
    {'id': 2, 'lead_id': 2, 'date': '2025-03-04', 'time': '2:30 PM', 'type': 'Sales Consultation'}
]

communications = [
    {'id': 1, 'lead_id': 1, 'type': 'Email', 'date': '2025-03-02', 'content': 'Follow-up on vehicle interest'},
    {'id': 2, 'lead_id': 1, 'type': 'SMS', 'date': '2025-03-03', 'content': 'Appointment reminder'},
    {'id': 3, 'lead_id': 2, 'type': 'Email', 'date': '2025-03-01', 'content': 'New vehicle listings'}
]

# Routes
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/leads')
def leads_page():
    # In a real app, we would fetch leads from a database
    return render_template('leads_page.html', leads=leads)

@app.route('/appointments')
def appointments_page():
    # In a real app, we would fetch appointments from a database
    return render_template('appointments_page.html', appointments=appointments, leads=leads)

@app.route('/communications')
def communications_page():
    # In a real app, we would fetch communications from a database
    return render_template('communications_page.html', communications=communications, leads=leads)

@app.route('/analytics')
def analytics_page():
    # In a real app, we would calculate analytics from actual data
    stats = {
        'total_leads': len(leads),
        'new_leads': sum(1 for lead in leads if lead['status'] == 'New'),
        'total_appointments': len(appointments),
        'total_communications': len(communications)
    }
    return render_template('analytics_page.html', stats=stats)

if __name__ == '__main__':
    app.run(debug=True, port=5001)

from flask import Flask, render_template, redirect, url_for, flash, request, jsonify
from datetime import datetime, timedelta
import os
import random

app = Flask(__name__, template_folder='app/templates', static_folder='app/static')
app.config['SECRET_KEY'] = 'development-secret-key-123'

# Mock data for demonstration
leads = [
    {'id': 1, 'first_name': 'John', 'last_name': 'Smith', 'email': 'john@example.com', 'phone': '555-123-4567', 'status': 'New', 'created_at': datetime.now() - timedelta(days=2), 'vehicle_interest': 'SUV'},
    {'id': 2, 'first_name': 'Jane', 'last_name': 'Doe', 'email': 'jane@example.com', 'phone': '555-987-6543', 'status': 'Contacted', 'created_at': datetime.now() - timedelta(days=1), 'vehicle_interest': 'Sedan'},
    {'id': 3, 'first_name': 'Bob', 'last_name': 'Johnson', 'email': 'bob@example.com', 'phone': '555-555-5555', 'status': 'Qualified', 'created_at': datetime.now() - timedelta(hours=12), 'vehicle_interest': 'Truck'},
]

appointments = [
    {'id': 1, 'lead_id': 1, 'date': datetime.now().date(), 'time': datetime.now().time(), 'purpose': 'Test Drive', 'status': 'Scheduled'},
    {'id': 2, 'lead_id': 2, 'date': (datetime.now() + timedelta(days=1)).date(), 'time': datetime.now().time(), 'purpose': 'Sales Consultation', 'status': 'Confirmed'},
]

communications = [
    {'id': 1, 'lead_id': 1, 'type': 'Email', 'content': 'Follow-up on vehicle interest', 'sent_at': datetime.now() - timedelta(hours=3)},
    {'id': 2, 'lead_id': 1, 'type': 'SMS', 'content': 'Appointment reminder', 'sent_at': datetime.now() - timedelta(hours=1)},
    {'id': 3, 'lead_id': 2, 'type': 'Email', 'content': 'New vehicle listings', 'sent_at': datetime.now() - timedelta(days=1)},
]

# Helper function to get lead by ID
def get_lead(lead_id):
    for lead in leads:
        if lead['id'] == lead_id:
            return lead
    return None

# Routes
@app.route('/')
def index():
    # Dashboard stats
    stats = {
        'total_leads': len(leads),
        'new_leads': sum(1 for lead in leads if lead['status'] == 'New'),
        'appointments_today': sum(1 for apt in appointments if apt['date'] == datetime.now().date()),
        'communications_today': sum(1 for comm in communications if comm['sent_at'].date() == datetime.now().date())
    }
    
    # Recent leads
    recent_leads = sorted(leads, key=lambda x: x['created_at'], reverse=True)[:5]
    
    # Today's appointments
    today_appointments = [apt for apt in appointments if apt['date'] == datetime.now().date()]
    today_appointments_with_leads = []
    for apt in today_appointments:
        lead = get_lead(apt['lead_id'])
        if lead:
            today_appointments_with_leads.append({
                'appointment': apt,
                'lead': lead
            })
    
    return render_template('index.html', 
                           stats=stats, 
                           recent_leads=recent_leads,
                           today_appointments=today_appointments_with_leads)

@app.route('/leads')
def leads_list():
    return render_template('leads.html', leads=leads)

@app.route('/lead/<int:lead_id>')
def lead_detail(lead_id):
    lead = get_lead(lead_id)
    if not lead:
        flash('Lead not found', 'danger')
        return redirect(url_for('leads_list'))
    
    lead_appointments = [apt for apt in appointments if apt['lead_id'] == lead_id]
    lead_communications = [comm for comm in communications if comm['lead_id'] == lead_id]
    
    return render_template('lead_detail.html', 
                           lead=lead, 
                           appointments=lead_appointments, 
                           communications=lead_communications)

@app.route('/lead/add', methods=['GET', 'POST'])
def add_lead():
    if request.method == 'POST':
        # In a real app, we would save to a database
        new_lead = {
            'id': len(leads) + 1,
            'first_name': request.form.get('first_name'),
            'last_name': request.form.get('last_name'),
            'email': request.form.get('email'),
            'phone': request.form.get('phone'),
            'status': 'New',
            'created_at': datetime.now(),
            'vehicle_interest': request.form.get('vehicle_interest')
        }
        leads.append(new_lead)
        flash('Lead added successfully', 'success')
        return redirect(url_for('leads_list'))
    
    return render_template('add_lead.html')

@app.route('/appointments')
def appointments_list():
    appointments_with_leads = []
    for apt in appointments:
        lead = get_lead(apt['lead_id'])
        if lead:
            appointments_with_leads.append({
                'appointment': apt,
                'lead': lead
            })
    
    return render_template('appointments.html', appointments=appointments_with_leads)

@app.route('/appointment/add', methods=['GET', 'POST'])
def add_appointment():
    if request.method == 'POST':
        # In a real app, we would save to a database
        new_appointment = {
            'id': len(appointments) + 1,
            'lead_id': int(request.form.get('lead_id')),
            'date': datetime.strptime(request.form.get('date'), '%Y-%m-%d').date(),
            'time': datetime.strptime(request.form.get('time'), '%H:%M').time(),
            'purpose': request.form.get('purpose'),
            'status': 'Scheduled'
        }
        appointments.append(new_appointment)
        flash('Appointment added successfully', 'success')
        return redirect(url_for('appointments_list'))
    
    return render_template('add_appointment.html', leads=leads)

@app.route('/communications')
def communications_list():
    communications_with_leads = []
    for comm in communications:
        lead = get_lead(comm['lead_id'])
        if lead:
            communications_with_leads.append({
                'communication': comm,
                'lead': lead
            })
    
    return render_template('communications.html', communications=communications_with_leads)

@app.route('/communication/add', methods=['GET', 'POST'])
def add_communication():
    if request.method == 'POST':
        # In a real app, we would save to a database
        new_communication = {
            'id': len(communications) + 1,
            'lead_id': int(request.form.get('lead_id')),
            'type': request.form.get('type'),
            'content': request.form.get('content'),
            'sent_at': datetime.now()
        }
        communications.append(new_communication)
        flash('Communication added successfully', 'success')
        return redirect(url_for('communications_list'))
    
    return render_template('add_communication.html', leads=leads)

@app.route('/analytics')
def analytics():
    # Mock analytics data
    lead_sources = ['Website', 'Referral', 'Walk-in', 'Phone', 'Email']
    lead_source_data = [random.randint(10, 50) for _ in range(len(lead_sources))]
    
    appointment_types = ['Test Drive', 'Sales Consultation', 'Service', 'Follow-up']
    appointment_type_data = [random.randint(5, 30) for _ in range(len(appointment_types))]
    
    monthly_leads = [random.randint(20, 100) for _ in range(12)]
    monthly_sales = [random.randint(5, 50) for _ in range(12)]
    
    return render_template('analytics.html', 
                           lead_sources=lead_sources,
                           lead_source_data=lead_source_data,
                           appointment_types=appointment_types,
                           appointment_type_data=appointment_type_data,
                           monthly_leads=monthly_leads,
                           monthly_sales=monthly_sales)

# API endpoints for AJAX calls
@app.route('/api/leads')
def api_leads():
    return jsonify(leads)

@app.route('/api/appointments')
def api_appointments():
    return jsonify(appointments)

@app.route('/api/communications')
def api_communications():
    return jsonify(communications)

if __name__ == '__main__':
    app.run(debug=True, port=5001)

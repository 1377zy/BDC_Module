from flask import Flask, render_template, redirect, url_for, flash, request
from datetime import datetime, timedelta
import random

app = Flask(__name__, template_folder='app/templates', static_folder='app/static')
app.config['SECRET_KEY'] = 'development-secret-key-123'

# Mock data for demonstration
leads = [
    {'id': 1, 'first_name': 'John', 'last_name': 'Smith', 'email': 'john@example.com', 'phone': '555-123-4567', 'status': 'New', 'created_at': datetime.now() - timedelta(days=2)},
    {'id': 2, 'first_name': 'Jane', 'last_name': 'Doe', 'email': 'jane@example.com', 'phone': '555-987-6543', 'status': 'Contacted', 'created_at': datetime.now() - timedelta(days=1)},
    {'id': 3, 'first_name': 'Bob', 'last_name': 'Johnson', 'email': 'bob@example.com', 'phone': '555-555-5555', 'status': 'Qualified', 'created_at': datetime.now() - timedelta(hours=12)},
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
    
    return render_template('index.html', stats=stats, leads=leads)

@app.route('/leads')
def leads_list():
    flash('Leads module accessed successfully', 'success')
    return redirect(url_for('index'))

@app.route('/appointments')
def appointments_list():
    flash('Appointments module accessed successfully', 'success')
    return redirect(url_for('index'))

@app.route('/communications')
def communications_list():
    flash('Communications module accessed successfully', 'success')
    return redirect(url_for('index'))

@app.route('/analytics')
def analytics():
    flash('Analytics module accessed successfully', 'success')
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(debug=True, port=5001)

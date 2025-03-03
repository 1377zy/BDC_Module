from flask import Flask, render_template, redirect, url_for, flash, request, send_from_directory, session, jsonify
from datetime import datetime, timedelta
import os
import random
from werkzeug.utils import secure_filename
# Try to import flask_mail, but provide a fallback if not available
try:
    from flask_mail import Mail, Message
except ImportError:
    # Create dummy classes for Mail and Message if flask_mail is not installed
    class Mail:
        def __init__(self, app=None):
            self.app = app
            
        def init_app(self, app):
            self.app = app
            
        def send(self, message):
            print(f"Would send email to {message.recipients} with subject: {message.subject}")
            
    class Message:
        def __init__(self, subject='', recipients=None, body='', html='', sender=None):
            self.subject = subject
            self.recipients = recipients or []
            self.body = body
            self.html = html
            self.sender = sender

from dotenv import load_dotenv
import csv
import io
import logging
from logging.handlers import RotatingFileHandler
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import Flow
from googleapiclient.discovery import build
from google.auth.transport.requests import Request
import base64
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import secrets
import phonenumbers
import json
import requests

# For development only - allows OAuth to work with HTTP instead of HTTPS
os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1'

# Constants for Google OAuth
CLIENT_SECRETS_FILE = 'client_secret.json'
API_SERVICE_NAME = 'gmail'
API_VERSION = 'v1'
SCOPES = ['https://www.googleapis.com/auth/gmail.send']

# Load environment variables from .env file
load_dotenv()

app = Flask(__name__, template_folder='app/templates', static_folder='app/static')
app.secret_key = os.environ.get('SECRET_KEY', 'development-secret-key-123')
app.config['UPLOAD_FOLDER'] = os.environ.get('CSV_IMPORT_DIRECTORY', 'temp')
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max upload size

# Ensure the upload directory exists
if not os.path.exists(app.config['UPLOAD_FOLDER']):
    os.makedirs(app.config['UPLOAD_FOLDER'])

# Configure logging
if not os.path.exists('logs'):
    os.makedirs('logs')
file_handler = RotatingFileHandler('logs/bdc_module.log', maxBytes=10240, backupCount=10)
file_handler.setFormatter(logging.Formatter(
    '[%(asctime)s] %(levelname)s in %(module)s: %(message)s'
))
app.logger.addHandler(file_handler)
app.logger.setLevel(logging.INFO)

# Configure email settings from environment variables
app.config['MAIL_SERVER'] = os.environ.get('MAIL_SERVER', 'smtp.gmail.com')
app.config['MAIL_PORT'] = int(os.environ.get('MAIL_PORT', 587))
app.config['MAIL_USE_TLS'] = os.environ.get('MAIL_USE_TLS', 'True').lower() in ('true', '1', 't')
app.config['MAIL_USE_SSL'] = os.environ.get('MAIL_USE_SSL', 'False').lower() in ('true', '1', 't')
app.config['MAIL_USERNAME'] = os.environ.get('MAIL_USERNAME', '')
app.config['MAIL_PASSWORD'] = os.environ.get('MAIL_PASSWORD', '')
app.config['MAIL_DEFAULT_SENDER'] = os.environ.get('MAIL_DEFAULT_SENDER', '')

# Initialize Flask-Mail
mail = Mail(app)

# Twilio configuration
TWILIO_ACCOUNT_SID = os.environ.get('TWILIO_ACCOUNT_SID', 'your-twilio-account-sid')
TWILIO_AUTH_TOKEN = os.environ.get('TWILIO_AUTH_TOKEN', 'your-twilio-auth-token')
TWILIO_PHONE_NUMBER = os.environ.get('TWILIO_PHONE_NUMBER', 'your-twilio-phone-number')

# Dealership information
DEALERSHIP_NAME = os.environ.get('DEALERSHIP_NAME', 'Your Dealership')
DEALERSHIP_ADDRESS = os.environ.get('DEALERSHIP_ADDRESS', '123 Main St, City, State 12345')
DEALERSHIP_PHONE = os.environ.get('DEALERSHIP_PHONE', '(555) 123-4567')
DEALERSHIP_WEBSITE = os.environ.get('DEALERSHIP_WEBSITE', 'www.yourdealership.com')

# Salesperson information
SALESPERSON_NAME = os.environ.get('SALESPERSON_NAME', 'John Doe')
SALESPERSON_EMAIL = os.environ.get('SALESPERSON_EMAIL', 'john.doe@example.com')
SALESPERSON_PHONE = os.environ.get('SALESPERSON_PHONE', '(555) 987-6543')

# Initialize Twilio client if credentials are available
twilio_available = False
twilio_client = None
try:
    if TWILIO_ACCOUNT_SID != 'your-twilio-account-sid' and TWILIO_AUTH_TOKEN != 'your-twilio-auth-token':
        from twilio.rest import Client
        twilio_client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)
        twilio_available = True
except Exception as e:
    app.logger.error(f"Failed to initialize Twilio: {str(e)}")

# Constants for template replacements
DEALERSHIP_NAME = os.environ.get('DEALERSHIP_NAME', 'Our Dealership')
DEALERSHIP_ADDRESS = os.environ.get('DEALERSHIP_ADDRESS', '123 Auto Lane')
DEALERSHIP_PHONE = os.environ.get('DEALERSHIP_PHONE', '555-123-4567')
DEALERSHIP_WEBSITE = os.environ.get('DEALERSHIP_WEBSITE', 'www.ourdealership.com')
SALESPERSON_NAME = os.environ.get('SALESPERSON_NAME', 'Your Salesperson')
SALESPERSON_EMAIL = os.environ.get('SALESPERSON_EMAIL', 'sales@ourdealership.com')
SALESPERSON_PHONE = os.environ.get('SALESPERSON_PHONE', '555-123-4567')

# Path for storing leads data
LEADS_DATA_FILE = 'data/leads.json'

# Ensure data directory exists
if not os.path.exists('data'):
    os.makedirs('data')

# Load leads from file if it exists
def load_leads_from_file():
    global leads_data
    if os.path.exists(LEADS_DATA_FILE):
        try:
            with open(LEADS_DATA_FILE, 'r') as f:
                loaded_data = json.load(f)
                # Convert string dates back to datetime objects
                for lead in loaded_data:
                    if 'created_at' in lead and lead['created_at']:
                        lead['created_at'] = datetime.fromisoformat(lead['created_at'])
                leads_data = loaded_data
                app.logger.info(f"Loaded {len(leads_data)} leads from file")
        except Exception as e:
            app.logger.error(f"Error loading leads data: {str(e)}")

# Save leads to file
def save_leads_to_file():
    try:
        # Convert datetime objects to ISO format strings for JSON serialization
        leads_to_save = []
        for lead in leads_data:
            lead_copy = lead.copy()
            if 'created_at' in lead_copy and isinstance(lead_copy['created_at'], datetime):
                lead_copy['created_at'] = lead_copy['created_at'].isoformat()
            leads_to_save.append(lead_copy)
            
        with open(LEADS_DATA_FILE, 'w') as f:
            json.dump(leads_to_save, f, indent=2)
        app.logger.info(f"Saved {len(leads_data)} leads to file")
        return True
    except Exception as e:
        app.logger.error(f"Error saving leads data: {str(e)}")
        return False

# Load leads at startup
leads_data = []
load_leads_from_file()

# Mock data for leads
if not leads_data:
    leads_data = [
        {
            'id': 1,
            'first_name': 'John',
            'last_name': 'Doe',
            'email': 'john.doe@example.com',
            'phone': '555-123-4567',
            'status': 'New',
            'vehicle_interest': '2023 Honda Accord',
            'notes': 'Interested in financing options',
            'created_at': datetime.now() - timedelta(days=2)
        },
        {
            'id': 2,
            'first_name': 'Jane',
            'last_name': 'Smith',
            'email': 'jane.smith@example.com',
            'phone': '555-987-6543',
            'status': 'Hot',
            'vehicle_interest': '2022 Toyota Camry',
            'notes': 'Prefers to be contacted by email',
            'created_at': datetime.now() - timedelta(days=1)
        },
        {
            'id': 3,
            'first_name': 'Bob',
            'last_name': 'Johnson',
            'email': 'bob.johnson@example.com',
            'phone': '555-555-5555',
            'status': 'Cold',
            'vehicle_interest': '2023 Ford F-150',
            'notes': 'Called about trade-in value',
            'created_at': datetime.now() - timedelta(hours=12)
        }
    ]

# Mock data for appointments
appointments_data = [
    {
        'id': 1,
        'lead_id': 1,
        'date': datetime.now().date() + timedelta(days=1),
        'time': datetime.now().replace(hour=14, minute=30, second=0, microsecond=0).time(),
        'purpose': '2023 Honda Accord Test Drive',
        'status': 'Scheduled',
        'notes': 'Customer is interested in financing options'
    },
    {
        'id': 2,
        'lead_id': 2,
        'date': datetime.now().date() + timedelta(days=2),
        'time': datetime.now().replace(hour=10, minute=0, second=0, microsecond=0).time(),
        'purpose': '2022 Toyota Camry Test Drive',
        'status': 'Confirmed',
        'notes': 'Customer requested a price quote before the appointment'
    }
]

# Mock data for communications
communications_data = [
    {
        'id': 1,
        'lead_id': 1,
        'type': 'Email',
        'content': 'Thank you for your interest in the 2023 Honda Accord. I would like to schedule a test drive with you.',
        'sent_at': datetime.now() - timedelta(days=1, hours=2)
    },
    {
        'id': 2,
        'lead_id': 1,
        'type': 'SMS',
        'content': 'Your appointment for tomorrow at 2:30 PM has been confirmed. Looking forward to meeting you!',
        'sent_at': datetime.now() - timedelta(hours=4)
    },
    {
        'id': 3,
        'lead_id': 2,
        'type': 'Email',
        'content': 'I have some great financing options for the 2022 Toyota Camry you were interested in. Would you like to discuss them?',
        'sent_at': datetime.now() - timedelta(hours=8)
    },
    {
        'id': 4,
        'lead_id': 1,
        'type': 'Call',
        'content': 'Discussed financing options for the Honda Accord. Customer is interested in a 60-month loan.',
        'duration': 8,  # minutes
        'call_outcome': 'Interested',
        'sent_at': datetime.now() - timedelta(days=2, hours=3)
    }
]

# Mock data for templates
templates_data = [
    {
        'id': 1,
        'name': 'Initial Contact',
        'type': 'Email',
        'subject': 'Welcome to {dealership_name}',
        'content': 'Dear {lead_first_name},\n\nThank you for your interest in {dealership_name}. We would love to help you find your perfect vehicle.\n\nPlease let me know if you have any questions or would like to schedule a test drive.\n\nBest regards,\n{salesperson_name}\n{salesperson_phone}'
    },
    {
        'id': 2,
        'name': 'Appointment Confirmation',
        'type': 'Email',
        'subject': 'Your appointment at {dealership_name}',
        'content': 'Dear {lead_first_name},\n\nThis is a confirmation of your appointment on {appointment_date} at {appointment_time}.\n\nWe look forward to seeing you!\n\nBest regards,\n{salesperson_name}\n{salesperson_phone}'
    },
    {
        'id': 3,
        'name': 'Welcome Text',
        'type': 'SMS',
        'content': 'Hi {lead_first_name}, this is {salesperson_name} from {dealership_name}. Thank you for your interest. How can I help you today?'
    },
    {
        'id': 4,
        'name': 'Appointment Reminder',
        'type': 'SMS',
        'content': 'Hi {lead_first_name}, just a reminder about your appointment tomorrow. Looking forward to seeing you! - {salesperson_name}, {dealership_name}'
    }
]

# Mock data for follow-ups
followups_data = [
    {
        'id': 1,
        'lead_id': 3,
        'lead_name': 'Bob Johnson',
        'scheduled_date': datetime.now().date() + timedelta(days=2),
        'scheduled_time': datetime.now().replace(hour=10, minute=0, second=0, microsecond=0).time(),
        'type': 'Call',
        'notes': 'Follow up on trade-in value discussion',
        'status': 'Pending',
        'priority': 'Medium'
    },
    {
        'id': 2,
        'lead_id': 2,
        'lead_name': 'Jane Smith',
        'scheduled_date': datetime.now().date() + timedelta(days=3),
        'scheduled_time': datetime.now().replace(hour=14, minute=0, second=0, microsecond=0).time(),
        'type': 'Email',
        'notes': 'Send updated financing options',
        'status': 'Pending',
        'priority': 'High'
    }
]

# Helper function to get lead by ID
def get_lead(lead_id):
    for lead in leads_data:
        if lead['id'] == lead_id:
            return lead
    return None

# Helper function to delete a lead by ID
def delete_lead_by_id(lead_id):
    """Delete a lead by ID and persist the change to file"""
    global leads_data
    lead = get_lead(lead_id)
    if lead:
        # Remove lead from in-memory data
        leads_data = [l for l in leads_data if l['id'] != lead_id]
        
        # Remove related appointments
        global appointments_data
        appointments_data = [a for a in appointments_data if a['lead_id'] != lead_id]
        
        # Remove related communications
        global communications_data
        communications_data = [c for c in communications_data if c['lead_id'] != lead_id]
        
        # Remove related followups
        global followups_data
        followups_data = [f for f in followups_data if f['lead_id'] != lead_id]
        
        # Persist changes to file
        success = save_leads_to_file()
        
        # Log the deletion
        app.logger.info(f"Lead {lead_id} deleted successfully. File save status: {success}")
        return True
    return False

# Helper function to get appointments for a lead
def get_lead_appointments(lead_id):
    return [a for a in appointments_data if a['lead_id'] == lead_id]

# Helper function to get communications for a lead
def get_lead_communications(lead_id):
    return [c for c in communications_data if c['lead_id'] == lead_id]

# Helper function to get follow-ups for a lead
def get_lead_followups(lead_id):
    return [f for f in followups_data if f['lead_id'] == lead_id]

# Helper function to get template by ID
def get_template(template_id):
    for template in templates_data:
        if template['id'] == template_id:
            return template
    return None

# Helper function to get templates by type
def get_templates_by_type(template_type):
    return [t for t in templates_data if t['type'] == template_type]

# Helper function to get followup by ID
def get_followup(followup_id):
    for followup in followups_data:
        if followup['id'] == followup_id:
            return followup
    return None

# Context processor for template functions
@app.context_processor
def inject_now():
    return {'now': datetime.now}

# Settings routes
@app.route('/settings')
def settings():
    # Get current settings from environment variables
    settings = {
        'mail_username': app.config['MAIL_USERNAME'],
        'mail_default_sender': app.config['MAIL_DEFAULT_SENDER'],
        'mail_server': app.config['MAIL_SERVER'],
        'mail_port': app.config['MAIL_PORT'],
        'mail_use_tls': app.config['MAIL_USE_TLS'],
        'twilio_account_sid': TWILIO_ACCOUNT_SID if TWILIO_ACCOUNT_SID != 'your-twilio-account-sid' else '',
        'twilio_phone_number': TWILIO_PHONE_NUMBER if TWILIO_PHONE_NUMBER != 'your-twilio-phone-number' else '',
        'dealership_name': DEALERSHIP_NAME,
        'dealership_address': DEALERSHIP_ADDRESS,
        'dealership_phone': DEALERSHIP_PHONE,
        'dealership_website': DEALERSHIP_WEBSITE,
        'salesperson_name': SALESPERSON_NAME,
        'salesperson_email': SALESPERSON_EMAIL,
        'salesperson_phone': SALESPERSON_PHONE,
        'google_auth_status': 'authorized' if 'google_credentials' in session else 'unauthorized'
    }
    
    return render_template('settings/index.html', 
                          settings=settings,
                          current_user={'is_authenticated': True})

@app.route('/settings/update-email', methods=['POST'])
def update_email_settings():
    mail_username = request.form.get('mail_username')
    mail_password = request.form.get('mail_password')
    mail_default_sender = request.form.get('mail_default_sender')
    mail_server = request.form.get('mail_server')
    mail_port = request.form.get('mail_port')
    mail_use_tls = 'mail_use_tls' in request.form
    
    # Update environment variables in memory
    os.environ['MAIL_USERNAME'] = mail_username
    os.environ['MAIL_DEFAULT_SENDER'] = mail_default_sender
    os.environ['MAIL_SERVER'] = mail_server
    os.environ['MAIL_PORT'] = mail_port
    os.environ['MAIL_USE_TLS'] = str(mail_use_tls)
    
    # Update app config
    app.config['MAIL_USERNAME'] = mail_username
    app.config['MAIL_DEFAULT_SENDER'] = mail_default_sender
    app.config['MAIL_SERVER'] = mail_server
    app.config['MAIL_PORT'] = int(mail_port)
    app.config['MAIL_USE_TLS'] = mail_use_tls
    
    # Only update password if provided
    if mail_password:
        os.environ['MAIL_PASSWORD'] = mail_password
        app.config['MAIL_PASSWORD'] = mail_password
        
        # Reinitialize mail with new settings
        global mail
        mail = Mail(app)
    
    # Update .env file
    update_env_file({
        'MAIL_USERNAME': mail_username,
        'MAIL_DEFAULT_SENDER': mail_default_sender,
        'MAIL_SERVER': mail_server,
        'MAIL_PORT': mail_port,
        'MAIL_USE_TLS': str(mail_use_tls)
    }, update_password=bool(mail_password), mail_password=mail_password)
    
    flash('Email settings updated successfully', 'success')
    app.logger.info('Email settings updated')
    return redirect('/settings')

@app.route('/authorize-google')
def authorize_google():
    # Create flow instance to manage the OAuth 2.0 Authorization Grant Flow steps.
    flow = Flow.from_client_secrets_file(
        CLIENT_SECRETS_FILE, scopes=SCOPES)

    # The URI created here must exactly match one of the authorized redirect URIs
    # for the OAuth 2.0 client, which you configured in the API Console. If this
    # value doesn't match an authorized URI, you will get a 'redirect_uri_mismatch'
    # error.
    flow.redirect_uri = "http://localhost:5001/oauth2callback"

    authorization_url, state = flow.authorization_url(
        # Enable offline access so that you can refresh an access token without
        # re-prompting the user for permission. Recommended for web server apps.
        access_type='offline',
        # Enable incremental authorization. Recommended as a best practice.
        include_granted_scopes='true')

    # Store the state so the callback can verify the auth server response.
    session['state'] = state

    return redirect(authorization_url)

@app.route('/oauth2callback')
def oauth2callback():
    # Specify the state when creating the flow in the callback so that it can
    # verified in the authorization server response.
    state = session.get('state', None)
    
    flow = Flow.from_client_secrets_file(
        CLIENT_SECRETS_FILE, scopes=SCOPES)
    flow.redirect_uri = "http://localhost:5001/oauth2callback"

    # Use the authorization server's response to fetch the OAuth 2.0 tokens.
    authorization_response = request.url

    try:
        flow.fetch_token(authorization_response=authorization_response)
    except Exception as e:
        app.logger.error(f"Error fetching token: {str(e)}")
        flash(f"Error authenticating with Google: {str(e)}", "danger")
        return redirect(url_for('settings'))

    # Store the credentials in the session.
    credentials = flow.credentials
    session['google_credentials'] = {
        'token': credentials.token,
        'refresh_token': credentials.refresh_token,
        'token_uri': credentials.token_uri,
        'client_id': credentials.client_id,
        'client_secret': credentials.client_secret,
        'scopes': credentials.scopes
    }

    flash('Successfully connected to Google!', 'success')
    return redirect(url_for('settings'))

@app.route('/revoke-google')
def revoke_google():
    if 'google_credentials' in session:
        credentials = Credentials(**session['google_credentials'])
        
        # Revoke the credentials
        try:
            revoke = requests.post('https://oauth2.googleapis.com/revoke',
                params={'token': credentials.token},
                headers = {'content-type': 'application/x-www-form-urlencoded'})
            
            status_code = getattr(revoke, 'status_code', 500)
            if status_code == 200:
                flash('Successfully disconnected from Google.', 'success')
            else:
                flash('An error occurred while trying to revoke token.', 'danger')
        except Exception as e:
            flash(f'Failed to revoke token: {str(e)}', 'danger')
        
        # Remove the credentials from the session
        del session['google_credentials']
    
    return redirect(url_for('settings'))

def send_email_with_gmail_api(to, subject, body_html):
    """Send an email using the Gmail API instead of SMTP"""
    if 'google_credentials' not in session:
        raise Exception("Not authorized with Google. Please authorize first.")
    
    # Build credentials from the stored session data
    credentials = Credentials(**session['google_credentials'])
    
    # If credentials are expired and we have a refresh token, refresh them
    if credentials.expired and credentials.refresh_token:
        credentials.refresh(Request())
        # Update the session with the new credentials
        session['google_credentials'] = {
            'token': credentials.token,
            'refresh_token': credentials.refresh_token,
            'token_uri': credentials.token_uri,
            'client_id': credentials.client_id,
            'client_secret': credentials.client_secret,
            'scopes': credentials.scopes
        }
    
    # Build the Gmail service
    service = build(API_SERVICE_NAME, API_VERSION, credentials=credentials)
    
    # Create a message
    message = MIMEMultipart('alternative')
    message['to'] = to
    message['subject'] = subject
    
    # Add the HTML part
    msg = MIMEText(body_html, 'html')
    message.attach(msg)
    
    # Encode the message
    raw_message = base64.urlsafe_b64encode(message.as_bytes()).decode()
    
    # Send the message
    try:
        message = service.users().messages().send(userId='me', body={'raw': raw_message}).execute()
        app.logger.info(f"Email sent to {to} with message ID: {message['id']}")
        return message
    except Exception as e:
        app.logger.error(f"Error sending email via Gmail API: {str(e)}")
        raise e

# Helper function to update the .env file
def update_env_file(updates, update_password=False, mail_password=None, update_twilio_token=False, twilio_auth_token=None):
    """Update the .env file with new values"""
    env_path = '.env'
    
    # Read the current .env file
    if os.path.exists(env_path):
        with open(env_path, 'r') as file:
            lines = file.readlines()
    else:
        lines = []
    
    # Process each line
    updated_lines = []
    for line in lines:
        line = line.strip()
        if not line or line.startswith('#'):
            updated_lines.append(line)
            continue
            
        key, value = line.split('=', 1) if '=' in line else (line, '')
        key = key.strip()
        
        # Check if this key should be updated
        if key in updates:
            updated_lines.append(f"{key}={updates[key]}")
            del updates[key]  # Remove from updates dict to track what's left
        elif key == 'MAIL_PASSWORD' and update_password:
            updated_lines.append(f"MAIL_PASSWORD={mail_password}")
        elif key == 'TWILIO_AUTH_TOKEN' and update_twilio_token:
            updated_lines.append(f"TWILIO_AUTH_TOKEN={twilio_auth_token}")
        else:
            updated_lines.append(line)
    
    # Add any new keys that weren't in the original file
    for key, value in updates.items():
        updated_lines.append(f"{key}={value}")
    
    # Write back to the .env file
    with open(env_path, 'w') as file:
        file.write('\n'.join(updated_lines))
        if not updated_lines[-1].endswith('\n'):
            file.write('\n')

# Routes
@app.route('/')
def index():
    # Dashboard stats
    stats = {
        'total_leads': len(leads_data),
        'new_leads': sum(1 for lead in leads_data if lead['status'] == 'New'),
        'appointments_today': sum(1 for apt in appointments_data if apt['date'] == datetime.now().date()),
        'communications_today': sum(1 for comm in communications_data if comm['sent_at'].date() == datetime.now().date()),
        'total_appointments': len(appointments_data),
        'todays_appointments': sum(1 for apt in appointments_data if apt['date'] == datetime.now().date())
    }
    
    # Recent leads
    recent_leads = sorted(leads_data, key=lambda x: x['created_at'], reverse=True)[:5]
    
    # Today's appointments
    today_appointments = [apt for apt in appointments_data if apt['date'] == datetime.now().date()]
    today_appointments_with_leads = []
    for apt in today_appointments:
        lead = get_lead(apt['lead_id'])
        if lead:
            today_appointments_with_leads.append({
                'appointment': apt,
                'lead': lead
            })
    
    return render_template('main/index.html', 
                           stats=stats, 
                           recent_leads=recent_leads,
                           today_appointments=today_appointments_with_leads,
                           current_user={'is_authenticated': True})

@app.route('/leads')
def leads():
    return render_template('leads/list.html', 
                           leads=leads_data, 
                           current_user={'is_authenticated': True},
                           search_form={},
                           pagination={'has_prev': False, 'has_next': False, 'page': 1, 'pages': 1})

@app.route('/leads/<int:lead_id>')
def view_lead(lead_id):
    lead = get_lead(lead_id)
    if not lead:
        flash('Lead not found', 'danger')
        return redirect('/leads')
    
    appointments = get_lead_appointments(lead_id)
    communications = get_lead_communications(lead_id)
    followups = get_lead_followups(lead_id)
    
    return render_template('leads/view.html', 
                           lead=lead, 
                           appointments=appointments, 
                           communications=communications,
                           followups=followups,
                           current_user={'is_authenticated': True})

@app.route('/appointments')
def appointments():
    appointments_with_leads = []
    for apt in appointments_data:
        lead = get_lead(apt['lead_id'])
        if lead:
            appointments_with_leads.append({
                'appointment': apt,
                'lead': lead
            })
    
    return render_template('appointments/list.html', 
                           appointments=appointments_with_leads, 
                           current_user={'is_authenticated': True},
                           search_form={},
                           pagination={'has_prev': False, 'has_next': False, 'page': 1, 'pages': 1},
                           title='All Appointments')

@app.route('/appointments/calendar')
def appointments_calendar():
    # Get all appointments
    appointments_with_leads = []
    for apt in appointments_data:
        lead = get_lead(apt['lead_id'])
        if lead:
            appointments_with_leads.append({
                'id': apt['id'],
                'title': f"{lead['first_name']} {lead['last_name']} - {apt['purpose']}",
                'start': f"{apt['date'].strftime('%Y-%m-%d')}T{apt['time'].strftime('%H:%M:%S')}",
                'end': f"{apt['date'].strftime('%Y-%m-%d')}T{(datetime.combine(apt['date'], apt['time']) + timedelta(hours=1)).time().strftime('%H:%M:%S')}",
                'status': apt['status'],
                'allDay': False
            })
    
    # Get today's appointments
    today_appointments = [apt for apt in appointments_data if apt['date'] == datetime.now().date()]
    today_appointments_with_leads = []
    for apt in today_appointments:
        lead = get_lead(apt['lead_id'])
        if lead:
            today_appointments_with_leads.append({
                'id': apt['id'],
                'time': apt['time'],
                'status': apt['status'],
                'lead': {
                    'first_name': lead['first_name'],
                    'last_name': lead['last_name']
                },
                'vehicle_interest': apt.get('vehicle_interest', '')
            })
    
    # Calculate appointment stats
    total_month = sum(1 for apt in appointments_data if apt['date'].month == datetime.now().month and apt['date'].year == datetime.now().year)
    total_week = sum(1 for apt in appointments_data if apt['date'] >= (datetime.now().date() - timedelta(days=datetime.now().weekday())) and apt['date'] <= (datetime.now().date() + timedelta(days=6-datetime.now().weekday())))
    no_show_count = sum(1 for apt in appointments_data if apt['status'] == 'No-Show')
    no_show_rate = round((no_show_count / len(appointments_data)) * 100) if appointments_data else 0
    conversion_rate = 65  # Mock data, would be calculated from actual sales
    
    # Generate available slots
    available_slots = []
    for i in range(1, 6):  # Next 5 days
        slot_date = datetime.now().date() + timedelta(days=i)
        day_of_week = slot_date.strftime('%A')
        for hour in [10, 14, 16]:  # 10 AM, 2 PM, 4 PM
            slot_time = datetime.strptime(f"{hour}:00", "%H:%M").time()
            # Check if this slot is already booked
            is_booked = any(apt['date'] == slot_date and apt['time'].hour == slot_time.hour for apt in appointments_data)
            if not is_booked:
                available_slots.append({
                    'date': slot_date.strftime('%Y-%m-%d'),
                    'time': slot_time.strftime('%I:%M %p'),
                    'day_of_week': day_of_week
                })
                if len(available_slots) >= 5:  # Limit to 5 available slots
                    break
        if len(available_slots) >= 5:
            break
    
    # Stats for the sidebar
    stats = {
        'total_month': total_month,
        'total_week': total_week,
        'no_show_rate': no_show_rate,
        'conversion_rate': conversion_rate
    }
    
    return render_template('appointments/calendar.html',
                          appointments_json=json.dumps(appointments_with_leads),
                          today_appointments=today_appointments_with_leads,
                          today=datetime.now(),
                          stats=stats,
                          available_slots=available_slots,
                          current_user={'is_authenticated': True})

@app.route('/appointments/api/get/<int:appointment_id>')
def get_appointment_api(appointment_id):
    """API endpoint to get appointment details for the calendar modal"""
    appointment = None
    for apt in appointments_data:
        if apt['id'] == appointment_id:
            appointment = apt
            break
    
    if not appointment:
        return jsonify({'error': 'Appointment not found'}), 404
    
    lead = get_lead(appointment['lead_id'])
    if not lead:
        return jsonify({'error': 'Lead not found'}), 404
    
    return jsonify({
        'id': appointment['id'],
        'date': appointment['date'].strftime('%Y-%m-%d'),
        'time': appointment['time'].strftime('%I:%M %p'),
        'purpose': appointment['purpose'],
        'status': appointment['status'],
        'notes': appointment.get('notes', ''),
        'vehicle_interest': appointment.get('vehicle_interest', ''),
        'lead': {
            'id': lead['id'],
            'first_name': lead['first_name'],
            'last_name': lead['last_name'],
            'email': lead.get('email', ''),
            'phone': lead.get('phone', '')
        }
    })

@app.route('/communications')
def communications():
    communications_with_leads = []
    for comm in communications_data:
        lead = get_lead(comm['lead_id'])
        if lead:
            communications_with_leads.append({
                'communication': comm,
                'lead': lead
            })
    
    return render_template('communications/list.html', 
                           communications=communications_with_leads, 
                           current_user={'is_authenticated': True},
                           search_form={},
                           pagination={'has_prev': False, 'has_next': False, 'page': 1, 'pages': 1},
                           type='all')

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
                           monthly_sales=monthly_sales,
                           current_user={'is_authenticated': True})

@app.route('/analytics/dashboard')
def analytics_dashboard():
    # Mock analytics dashboard data
    total_leads = len(leads_data)
    total_appointments = len(appointments_data)
    new_leads_today = sum(1 for lead in leads_data if datetime.strptime(lead['created_at'], '%Y-%m-%d %H:%M:%S').date() == datetime.now().date())
    communications_today = sum(1 for comm in communications_data if datetime.strptime(comm['sent_at'], '%Y-%m-%d %H:%M:%S').date() == datetime.now().date())
    
    # Lead status distribution
    lead_statuses = ['New', 'Contacted', 'Qualified', 'Proposal', 'Negotiation', 'Closed Won', 'Closed Lost']
    lead_status_counts = [sum(1 for lead in leads_data if lead['status'] == status) for status in lead_statuses]
    
    # Appointment status distribution
    appointment_statuses = ['Scheduled', 'Confirmed', 'Completed', 'No-show', 'Cancelled']
    appointment_status_counts = [sum(1 for appt in appointments_data if appt['status'] == status) for status in appointment_statuses]
    
    # Monthly lead trends
    months = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
    monthly_lead_counts = [random.randint(10, 50) for _ in range(12)]
    
    # Communication types
    communication_types = ['Email', 'Phone', 'SMS', 'In-person']
    communication_type_counts = [sum(1 for comm in communications_data if comm['type'] == type) for type in communication_types]
    
    # User performance
    users = ['John Smith', 'Jane Doe', 'Bob Johnson', 'Alice Williams']
    user_leads = [random.randint(5, 30) for _ in range(len(users))]
    user_appointments = [random.randint(3, 20) for _ in range(len(users))]
    user_communications = [random.randint(10, 50) for _ in range(len(users))]
    
    return render_template('analytics/dashboard.html',
                          total_leads=total_leads,
                          total_appointments=total_appointments,
                          new_leads_today=new_leads_today,
                          communications_today=communications_today,
                          lead_statuses=lead_statuses,
                          lead_status_counts=lead_status_counts,
                          appointment_statuses=appointment_statuses,
                          appointment_status_counts=appointment_status_counts,
                          months=months,
                          monthly_lead_counts=monthly_lead_counts,
                          communication_types=communication_types,
                          communication_type_counts=communication_type_counts,
                          users=users,
                          user_leads=user_leads,
                          user_appointments=user_appointments,
                          user_communications=user_communications,
                          current_user={'is_authenticated': True})

@app.route('/analytics/leads')
def lead_analytics():
    # Mock lead analytics data
    lead_sources = ['Website', 'Referral', 'Walk-in', 'Phone', 'Email']
    lead_source_counts = [sum(1 for lead in leads_data if lead['source'] == source) for source in lead_sources]
    
    # Lead conversion rates
    conversion_rates = [round(random.uniform(0.1, 0.8), 2) for _ in range(len(lead_sources))]
    
    # Lead age analysis
    age_ranges = ['0-7 days', '8-14 days', '15-30 days', '31-60 days', '60+ days']
    lead_age_counts = [random.randint(5, 30) for _ in range(len(age_ranges))]
    
    # Lead status by source
    lead_statuses = ['New', 'Contacted', 'Qualified', 'Proposal', 'Negotiation', 'Closed Won', 'Closed Lost']
    lead_status_by_source = []
    
    for source in lead_sources:
        source_data = {
            'source': source,
            'counts': [random.randint(1, 10) for _ in range(len(lead_statuses))]
        }
        lead_status_by_source.append(source_data)
    
    return render_template('analytics/leads.html',
                          lead_sources=lead_sources,
                          lead_source_counts=lead_source_counts,
                          conversion_rates=conversion_rates,
                          age_ranges=age_ranges,
                          lead_age_counts=lead_age_counts,
                          lead_statuses=lead_statuses,
                          lead_status_by_source=lead_status_by_source,
                          current_user={'is_authenticated': True})

@app.route('/analytics/appointments')
def appointment_analytics():
    # Mock appointment analytics data
    total_appointments = len(appointments_data)
    appointments_today = sum(1 for appt in appointments_data if datetime.strptime(appt['date'], '%Y-%m-%d').date() == datetime.now().date())
    
    # Appointment status distribution
    appointment_statuses = ['Scheduled', 'Confirmed', 'Completed', 'No-show', 'Cancelled']
    appointment_status_counts = [sum(1 for appt in appointments_data if appt['status'] == status) for status in appointment_statuses]
    
    # Appointment purpose distribution
    appointment_purposes = ['Test Drive', 'Sales Consultation', 'Service', 'Follow-up']
    appointment_purpose_counts = [sum(1 for appt in appointments_data if appt['purpose'] == purpose) for purpose in appointment_purposes]
    
    # Day of week distribution
    days_of_week = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
    day_distribution = [random.randint(5, 20) for _ in range(7)]
    
    # Time of day distribution
    time_ranges = ['9:00-11:00', '11:00-13:00', '13:00-15:00', '15:00-17:00', '17:00-19:00']
    time_distribution = [random.randint(5, 25) for _ in range(len(time_ranges))]
    
    # Monthly no-show rate
    months = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
    no_show_rates = [round(random.uniform(0.05, 0.25), 2) for _ in range(12)]
    
    return render_template('analytics/appointments.html',
                          total_appointments=total_appointments,
                          appointments_today=appointments_today,
                          appointment_statuses=appointment_statuses,
                          appointment_status_counts=appointment_status_counts,
                          appointment_purposes=appointment_purposes,
                          appointment_purpose_counts=appointment_purpose_counts,
                          days_of_week=days_of_week,
                          day_distribution=day_distribution,
                          time_ranges=time_ranges,
                          time_distribution=time_distribution,
                          months=months,
                          no_show_rates=no_show_rates,
                          current_user={'is_authenticated': True})

@app.route('/analytics/communications')
def communication_analytics():
    # Mock communication analytics data
    total_communications = len(communications_data)
    communications_today = sum(1 for comm in communications_data if datetime.strptime(comm['sent_at'], '%Y-%m-%d %H:%M:%S').date() == datetime.now().date())
    communications_week = random.randint(communications_today, communications_today + 50)
    communications_month = random.randint(communications_week, communications_week + 100)
    
    # Communication type distribution
    communication_types = [('Email', random.randint(10, 50)), 
                          ('SMS', random.randint(10, 50)), 
                          ('Call', random.randint(10, 50)), 
                          ('In-person', random.randint(5, 20))]
    
    # Communication status distribution
    communication_statuses = [('Sent', random.randint(20, 100)), 
                             ('Delivered', random.randint(15, 80)), 
                             ('Read', random.randint(10, 60)), 
                             ('Replied', random.randint(5, 40))]
    
    # Day of week distribution
    day_distribution = [
        {'day': 'Monday', 'count': random.randint(5, 30)},
        {'day': 'Tuesday', 'count': random.randint(5, 30)},
        {'day': 'Wednesday', 'count': random.randint(5, 30)},
        {'day': 'Thursday', 'count': random.randint(5, 30)},
        {'day': 'Friday', 'count': random.randint(5, 30)},
        {'day': 'Saturday', 'count': random.randint(2, 15)},
        {'day': 'Sunday', 'count': random.randint(1, 10)}
    ]
    
    # Hour distribution
    hour_distribution = [{'hour': hour, 'count': random.randint(1, 15)} for hour in range(9, 18)]
    
    # Monthly communication trends
    monthly_communications = [
        {'month': 'Jan', 'email': random.randint(10, 50), 'sms': random.randint(10, 50), 'call': random.randint(5, 30)},
        {'month': 'Feb', 'email': random.randint(10, 50), 'sms': random.randint(10, 50), 'call': random.randint(5, 30)},
        {'month': 'Mar', 'email': random.randint(10, 50), 'sms': random.randint(10, 50), 'call': random.randint(5, 30)},
        {'month': 'Apr', 'email': random.randint(10, 50), 'sms': random.randint(10, 50), 'call': random.randint(5, 30)},
        {'month': 'May', 'email': random.randint(10, 50), 'sms': random.randint(10, 50), 'call': random.randint(5, 30)},
        {'month': 'Jun', 'email': random.randint(10, 50), 'sms': random.randint(10, 50), 'call': random.randint(5, 30)},
        {'month': 'Jul', 'email': random.randint(10, 50), 'sms': random.randint(10, 50), 'call': random.randint(5, 30)},
        {'month': 'Aug', 'email': random.randint(10, 50), 'sms': random.randint(10, 50), 'call': random.randint(5, 30)},
        {'month': 'Sep', 'email': random.randint(10, 50), 'sms': random.randint(10, 50), 'call': random.randint(5, 30)},
        {'month': 'Oct', 'email': random.randint(10, 50), 'sms': random.randint(10, 50), 'call': random.randint(5, 30)},
        {'month': 'Nov', 'email': random.randint(10, 50), 'sms': random.randint(10, 50), 'call': random.randint(5, 30)},
        {'month': 'Dec', 'email': random.randint(10, 50), 'sms': random.randint(10, 50), 'call': random.randint(5, 30)}
    ]
    
    return render_template('analytics/communications.html',
                          total_communications=total_communications,
                          communications_today=communications_today,
                          communications_week=communications_week,
                          communications_month=communications_month,
                          communication_types=communication_types,
                          communication_statuses=communication_statuses,
                          day_distribution=day_distribution,
                          hour_distribution=hour_distribution,
                          monthly_communications=monthly_communications,
                          current_user={'is_authenticated': True})

@app.route('/analytics/export-report/<report_type>/<format>')
def export_report(report_type, format):
    """Export analytics data as CSV or Excel"""
    from io import BytesIO
    import csv
    
    if report_type == 'leads':
        filename = f"lead_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        headers = ['ID', 'Name', 'Email', 'Phone', 'Source', 'Status', 'Created At']
        data = [[lead['id'], f"{lead['first_name']} {lead['last_name']}", lead['email'], 
                lead['phone'], lead['source'], lead['status'], lead['created_at']] 
                for lead in leads_data]
    elif report_type == 'appointments':
        filename = f"appointment_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        headers = ['ID', 'Lead', 'Date', 'Time', 'Purpose', 'Status', 'Notes']
        data = [[appt['id'], appt['lead_name'], appt['date'], appt['time'], 
                appt['purpose'], appt['status'], appt.get('notes', '')] 
                for appt in appointments_data]
    elif report_type == 'communications':
        filename = f"communication_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        headers = ['ID', 'Lead', 'Type', 'Sent At', 'Content', 'Status']
        data = [[comm['id'], comm['lead_name'], comm['type'], comm['sent_at'], 
                comm['content'][:50] + '...' if len(comm['content']) > 50 else comm['content'], 
                comm.get('status', 'Sent')] 
                for comm in communications_data]
    else:
        return "Invalid report type", 400
    
    if format == 'csv':
        # Create CSV in memory
        output = BytesIO()
        writer = csv.writer(output)
        writer.writerow(headers)
        writer.writerows(data)
        
        # Prepare response
        output.seek(0)
        return send_from_directory(
            directory=os.path.dirname(os.path.abspath(__file__)),
            path=f"{filename}.csv",
            as_attachment=True,
            download_name=f"{filename}.csv",
            mimetype='text/csv'
        )
    elif format == 'excel':
        try:
            import xlsxwriter
            # Create Excel in memory
            output = BytesIO()
            workbook = xlsxwriter.Workbook(output)
            worksheet = workbook.add_worksheet()
            
            # Add headers
            for col, header in enumerate(headers):
                worksheet.write(0, col, header)
            
            # Add data
            for row_idx, row_data in enumerate(data, start=1):
                for col_idx, cell_data in enumerate(row_data):
                    worksheet.write(row_idx, col_idx, cell_data)
            
            workbook.close()
            
            # Prepare response
            output.seek(0)
            return send_from_directory(
                directory=os.path.dirname(os.path.abspath(__file__)),
                path=f"{filename}.xlsx",
                as_attachment=True,
                download_name=f"{filename}.xlsx",
                mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
            )
        except ImportError:
            flash('Excel export requires xlsxwriter package. Please install it or use CSV export.', 'warning')
            return redirect(url_for('analytics'))
    else:
        return "Invalid format", 400

# Helper functions for CSV import
@app.route('/leads/import', methods=['GET', 'POST'])
def import_leads():
    if request.method == 'POST':
        if 'file' not in request.files:
            flash('No file part', 'danger')
            return redirect(request.url)
        
        file = request.files['file']
        if file.filename == '':
            flash('No selected file', 'danger')
            return redirect(request.url)
        
        if file and file.filename.endswith('.csv'):
            try:
                # Read CSV file
                stream = io.StringIO(file.stream.read().decode("UTF8"), newline=None)
                csv_reader = csv.DictReader(stream)
                
                # Track import statistics
                imported_count = 0
                error_count = 0
                
                # Process each row
                for row in csv_reader:
                    try:
                        # Validate required fields
                        if not row.get('first_name') or not row.get('last_name'):
                            error_count += 1
                            continue
                        
                        # Create new lead
                        new_lead = {
                            'id': len(leads_data) + 1,
                            'first_name': row.get('first_name', '').strip(),
                            'last_name': row.get('last_name', '').strip(),
                            'email': row.get('email', '').strip(),
                            'phone': row.get('phone', '').strip(),
                            'status': row.get('status', 'New').strip(),
                            'vehicle_interest': row.get('vehicle_interest', '').strip(),
                            'notes': row.get('notes', '').strip(),
                            'created_at': datetime.now()
                        }
                        
                        # Add to leads data
                        leads_data.append(new_lead)
                        imported_count += 1
                        
                    except Exception as e:
                        app.logger.error(f"Error importing lead: {str(e)}")
                        error_count += 1
                
                if imported_count > 0:
                    flash(f'Successfully imported {imported_count} leads', 'success')
                if error_count > 0:
                    flash(f'Failed to import {error_count} leads due to errors', 'warning')
                
                save_leads_to_file()
                return redirect('/leads')
            
            except Exception as e:
                app.logger.error(f"Error processing CSV file: {str(e)}")
                flash(f'Error processing CSV file: {str(e)}', 'danger')
                return redirect(request.url)
        else:
            flash('File must be a CSV', 'danger')
            return redirect(request.url)
    
    return render_template('leads/import.html', 
                           current_user={'is_authenticated': True})

@app.route('/leads/download-template', methods=['GET'])
def download_lead_template():
    # Create a CSV in memory
    output = io.StringIO()
    writer = csv.writer(output)
    
    # Write header row with all required and optional fields
    writer.writerow(['first_name', 'last_name', 'email', 'phone', 'source', 'status', 'notes', 'make', 'model', 'year', 'new_or_used'])
    
    # Write sample rows to demonstrate proper formatting
    writer.writerow(['John', 'Doe', 'john.doe@example.com', '555-123-4567', 'Website', 'New', 'Interested in financing options', 'Toyota', 'Camry', '2023', 'New'])
    writer.writerow(['Jane', 'Smith', 'jane.smith@example.com', '555-987-6543', 'Referral', 'Contacted', 'Prefers email contact', 'Honda', 'Accord', '2022', 'New'])
    writer.writerow(['Robert', 'Johnson', 'robert@example.com', '555-555-5555', 'Walk-in', 'Qualified', 'Looking for family vehicle', 'Ford', 'Explorer', '2020', 'Used'])
    
    # Prepare the response
    output.seek(0)
    
    # Create a response with the CSV content
    response = app.response_class(
        response=output.getvalue(),
        status=200,
        mimetype='text/csv'
    )
    # Add timestamp to filename to prevent caching issues
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    response.headers["Content-Disposition"] = f"attachment; filename=lead_import_template_{timestamp}.csv"
    return response

@app.route('/communications/email', methods=['GET', 'POST'])
def send_email():
    if request.method == 'POST':
        lead_id = request.form.get('lead_id')
        subject = request.form.get('subject')
        content = request.form.get('content')
        template_id = request.form.get('template_id')
        
        # Get lead data for placeholder replacement
        lead = get_lead(int(lead_id)) if lead_id else None
        
        if not lead:
            flash('Lead not found', 'danger')
            return redirect('/communications')
            
        if template_id and lead:
            template = get_template(int(template_id))
            if template:
                subject = template['subject']
                content = template['content']
                
                # Replace placeholders
                subject = subject.replace('{dealership_name}', DEALERSHIP_NAME)
                content = content.replace('{first_name}', lead['first_name'])
                content = content.replace('{last_name}', lead['last_name'])
                content = content.replace('{dealership_name}', DEALERSHIP_NAME)
                content = content.replace('{salesperson_name}', SALESPERSON_NAME)
                content = content.replace('{salesperson_phone}', SALESPERSON_PHONE)
        
        # Add to our mock data
        new_communication = {
            'id': len(communications_data) + 1,
            'lead_id': int(lead_id),
            'type': 'Email',
            'content': content,
            'sent_at': datetime.now()
        }
        communications_data.append(new_communication)
        
        # Try to send the actual email
        email_sent = False
        if not lead.get('email'):
            flash('Email not sent: Lead has no email address', 'warning')
        elif app.config['MAIL_USERNAME'] == 'your-email@gmail.com' or app.config['MAIL_PASSWORD'] == 'your-app-password':
            flash('Email not sent: Email configuration incomplete. Please update your .env file with proper credentials.', 'warning')
            app.logger.warning(f"Email not sent to lead {lead_id}: Email configuration incomplete")
        else:
            try:
                msg = Message(
                    subject=subject,
                    recipients=[lead['email']],
                    body=content,
                    sender=app.config['MAIL_DEFAULT_SENDER']
                )
                mail.send(msg)
                email_sent = True
                flash(f'Email sent successfully to {lead["email"]}', 'success')
                app.logger.info(f"Email sent to lead {lead_id} at {lead['email']}")
            except Exception as e:
                error_message = str(e)
                flash(f'Email not sent: {error_message}', 'danger')
                app.logger.error(f"Failed to send email to lead {lead_id}: {error_message}")
        
        return redirect(f'/leads/{lead_id}')
    
    lead_id = request.args.get('lead_id')
    lead = get_lead(int(lead_id)) if lead_id else None
    email_templates = get_templates_by_type('Email')
    
    return render_template('communications/email.html', 
                           lead=lead,
                           templates=email_templates,
                           leads_data=leads_data,
                           communications_data=communications_data,
                           current_user={'is_authenticated': True})

@app.route('/communications/sms', methods=['GET', 'POST'])
def send_sms():
    if request.method == 'POST':
        lead_id = request.form.get('lead_id')
        content = request.form.get('content')
        template_id = request.form.get('template_id')
        
        # Get lead data for placeholder replacement
        lead = get_lead(int(lead_id)) if lead_id else None
        
        if not lead:
            flash('Lead not found', 'danger')
            return redirect('/communications')
            
        if template_id and lead:
            template = get_template(int(template_id))
            if template:
                content = template['content']
                
                # Replace placeholders
                content = content.replace('{first_name}', lead['first_name'])
                content = content.replace('{last_name}', lead['last_name'])
                content = content.replace('{dealership_name}', DEALERSHIP_NAME)
                content = content.replace('{salesperson_name}', SALESPERSON_NAME)
                content = content.replace('{salesperson_phone}', SALESPERSON_PHONE)
        
        # Add to our mock data
        new_communication = {
            'id': len(communications_data) + 1,
            'lead_id': int(lead_id),
            'type': 'SMS',
            'content': content,
            'sent_at': datetime.now()
        }
        communications_data.append(new_communication)
        
        # Try to send the actual SMS
        sms_sent = False
        if not lead.get('phone'):
            flash('SMS not sent: Lead has no phone number', 'warning')
            app.logger.warning(f"SMS not sent to lead {lead_id}: No phone number")
        elif not twilio_available:
            flash('SMS not sent: Twilio configuration incomplete. Please update your .env file with proper credentials.', 'warning')
            app.logger.warning(f"SMS not sent to lead {lead_id}: Twilio configuration incomplete")
        else:
            try:
                # Format the phone number (remove non-numeric characters)
                to_number = ''.join(filter(str.isdigit, lead['phone']))
                if not to_number.startswith('1') and len(to_number) == 10:
                    to_number = '1' + to_number
                
                # Add + if not present
                if not to_number.startswith('+'):
                    to_number = '+' + to_number
                
                message = twilio_client.messages.create(
                    body=content,
                    from_=TWILIO_PHONE_NUMBER,
                    to=to_number
                )
                sms_sent = True
                flash(f'SMS sent successfully to {lead["phone"]}', 'success')
                app.logger.info(f"SMS sent to lead {lead_id} at {lead['phone']}")
            except Exception as e:
                error_message = str(e)
                flash(f'SMS not sent: {error_message}', 'danger')
                app.logger.error(f"Failed to send SMS to lead {lead_id}: {error_message}")
        
        return redirect(f'/leads/{lead_id}')
    
    lead_id = request.args.get('lead_id')
    lead = get_lead(int(lead_id)) if lead_id else None
    sms_templates = get_templates_by_type('SMS')
    
    return render_template('communications/sms.html', 
                           lead=lead,
                           templates=sms_templates,
                           leads_data=leads_data,
                           communications_data=communications_data,
                           current_user={'is_authenticated': True})

@app.route('/communications/call', methods=['GET', 'POST'])
def log_call():
    if request.method == 'POST':
        lead_id = request.form.get('lead_id')
        content = request.form.get('content')
        duration = request.form.get('duration')
        call_outcome = request.form.get('call_outcome')
        followup_id = request.form.get('followup_id')
        
        # Add the call log to our mock data
        new_communication = {
            'id': len(communications_data) + 1,
            'lead_id': int(lead_id),
            'type': 'Call',
            'content': content,
            'duration': int(duration),
            'call_outcome': call_outcome,
            'sent_at': datetime.now()
        }
        communications_data.append(new_communication)
        
        # If this call is for a follow-up, mark the follow-up as completed
        if followup_id:
            followup = get_followup(int(followup_id))
            if followup:
                followup['status'] = 'Completed'
        
        flash('Call logged successfully', 'success')
        return redirect(f'/leads/{lead_id}')
    
    lead_id = request.args.get('lead_id')
    followup_id = request.args.get('followup_id')
    
    lead = None
    followup = None
    
    if followup_id:
        followup = get_followup(int(followup_id))
        if followup:
            lead_id = followup['lead_id']
            
    if lead_id:
        lead = get_lead(int(lead_id))
    
    return render_template('communications/call.html', 
                           lead=lead,
                           followup=followup,
                           leads_data=leads_data,
                           communications_data=communications_data,
                           current_user={'is_authenticated': True})

# Template management routes
@app.route('/templates')
def list_templates():
    template_type = request.args.get('type')
    if template_type:
        filtered_templates = [t for t in templates_data if t['type'] == template_type]
    else:
        filtered_templates = templates_data
        
    return render_template('templates/list.html', 
                           templates=filtered_templates,
                           current_user={'is_authenticated': True})

@app.route('/templates/add', methods=['GET', 'POST'])
def add_template():
    if request.method == 'POST':
        name = request.form.get('name')
        template_type = request.form.get('type')
        subject = request.form.get('subject', '')
        content = request.form.get('content')
        
        new_template = {
            'id': len(templates_data) + 1,
            'name': name,
            'type': template_type,
            'subject': subject if template_type == 'Email' else '',
            'content': content
        }
        templates_data.append(new_template)
        
        flash('Template added successfully', 'success')
        return redirect('/templates')
    
    return render_template('templates/add_edit.html', 
                           current_user={'is_authenticated': True})

@app.route('/templates/edit/<int:template_id>', methods=['GET', 'POST'])
def edit_template(template_id):
    template = get_template(template_id)
    if not template:
        flash('Template not found', 'danger')
        return redirect('/templates')
    
    if request.method == 'POST':
        template['name'] = request.form.get('name')
        template['type'] = request.form.get('type')
        if template['type'] == 'Email':
            template['subject'] = request.form.get('subject', '')
        template['content'] = request.form.get('content')
        
        flash('Template updated successfully', 'success')
        return redirect('/templates')
    
    return render_template('templates/add_edit.html', 
                           template=template,
                           current_user={'is_authenticated': True})

@app.route('/templates/delete/<int:template_id>', methods=['POST'])
def delete_template(template_id):
    global templates_data
    templates_data = [t for t in templates_data if t['id'] != template_id]
    flash('Template deleted successfully', 'success')
    return redirect('/templates')

# Follow-up management routes
@app.route('/followups')
def list_followups():
    status_filter = request.args.get('status')
    
    if status_filter:
        filtered_followups = [f for f in followups_data if f['status'] == status_filter]
    else:
        filtered_followups = followups_data
    
    # Sort by date and time
    filtered_followups.sort(key=lambda x: (x['scheduled_date'], x['scheduled_time']))
    
    return render_template('followups/list.html', 
                           followups=filtered_followups,
                           current_user={'is_authenticated': True})

@app.route('/followups/add', methods=['GET', 'POST'])
def add_followup():
    if request.method == 'POST':
        lead_id = int(request.form.get('lead_id'))
        scheduled_date_str = request.form.get('scheduled_date')
        scheduled_time_str = request.form.get('scheduled_time')
        followup_type = request.form.get('type')
        notes = request.form.get('notes')
        priority = request.form.get('priority', 'Medium')
        
        # Get lead name
        lead = get_lead(lead_id)
        lead_name = f"{lead['first_name']} {lead['last_name']}" if lead else f"Lead #{lead_id}"
        
        # Parse date and time
        scheduled_date = datetime.strptime(scheduled_date_str, '%Y-%m-%d').date()
        scheduled_time = datetime.strptime(scheduled_time_str, '%H:%M').time()
        
        new_followup = {
            'id': len(followups_data) + 1,
            'lead_id': lead_id,
            'lead_name': lead_name,
            'scheduled_date': scheduled_date,
            'scheduled_time': scheduled_time,
            'type': followup_type,
            'notes': notes,
            'status': 'Pending',
            'priority': priority
        }
        followups_data.append(new_followup)
        
        flash('Follow-up scheduled successfully', 'success')
        return redirect(f'/leads/{lead_id}' if lead_id else '/followups')
    
    lead_id = request.args.get('lead_id')
    lead = get_lead(int(lead_id)) if lead_id else None
    
    return render_template('followups/add_edit.html', 
                           lead=lead,
                           leads=leads_data,
                           current_user={'is_authenticated': True})

@app.route('/followups/edit/<int:followup_id>', methods=['GET', 'POST'])
def edit_followup(followup_id):
    followup = get_followup(followup_id)
    if not followup:
        flash('Follow-up not found', 'danger')
        return redirect('/followups')
    
    if request.method == 'POST':
        followup['scheduled_date'] = datetime.strptime(request.form.get('scheduled_date'), '%Y-%m-%d').date()
        followup['scheduled_time'] = datetime.strptime(request.form.get('scheduled_time'), '%H:%M').time()
        followup['type'] = request.form.get('type')
        followup['notes'] = request.form.get('notes')
        followup['priority'] = request.form.get('priority', 'Medium')
        
        flash('Follow-up updated successfully', 'success')
        return redirect('/followups')
    
    return render_template('followups/add_edit.html', 
                           followup=followup,
                           leads=leads_data,
                           current_user={'is_authenticated': True})

@app.route('/followups/complete/<int:followup_id>', methods=['GET', 'POST'])
def complete_followup(followup_id):
    followup = get_followup(followup_id)
    
    if followup:
        followup['status'] = 'Completed'
        flash('Follow-up marked as completed', 'success')
    else:
        flash('Follow-up not found', 'danger')
    
    return redirect('/followups')

@app.route('/followups/delete/<int:followup_id>', methods=['POST'])
def delete_followup(followup_id):
    global followups_data
    followups_data = [f for f in followups_data if f['id'] != followup_id]
    flash('Follow-up deleted successfully', 'success')
    return redirect('/followups')

# Add lead management routes
@app.route('/leads/add', methods=['GET', 'POST'])
def add_lead():
    if request.method == 'POST':
        # Get form data
        first_name = request.form.get('first_name')
        last_name = request.form.get('last_name')
        email = request.form.get('email')
        phone = request.form.get('phone')
        status = request.form.get('status', 'New')
        vehicle_interest = request.form.get('vehicle_interest')
        notes = request.form.get('notes')
        
        # Create new lead
        new_lead = {
            'id': len(leads_data) + 1,
            'first_name': first_name,
            'last_name': last_name,
            'email': email,
            'phone': phone,
            'status': status,
            'vehicle_interest': vehicle_interest,
            'notes': notes,
            'created_at': datetime.now()
        }
        
        # Add to leads data
        leads_data.append(new_lead)
        save_leads_to_file()
        
        flash('Lead added successfully', 'success')
        return redirect(f'/leads/{new_lead["id"]}')
    
    return render_template('leads/add.html', 
                           current_user={'is_authenticated': True})

@app.route('/leads/edit/<int:lead_id>', methods=['GET', 'POST'])
def edit_lead(lead_id):
    lead = get_lead(lead_id)
    if not lead:
        flash('Lead not found', 'danger')
        return redirect('/leads')
    
    if request.method == 'POST':
        # Get form data
        first_name = request.form.get('first_name')
        last_name = request.form.get('last_name')
        email = request.form.get('email')
        phone = request.form.get('phone')
        status = request.form.get('status')
        vehicle_interest = request.form.get('vehicle_interest')
        notes = request.form.get('notes')
        
        # Update lead data
        for idx, l in enumerate(leads_data):
            if l['id'] == lead_id:
                leads_data[idx]['first_name'] = first_name
                leads_data[idx]['last_name'] = last_name
                leads_data[idx]['email'] = email
                leads_data[idx]['phone'] = phone
                leads_data[idx]['status'] = status
                leads_data[idx]['vehicle_interest'] = vehicle_interest
                leads_data[idx]['notes'] = notes
                break
        
        save_leads_to_file()
        flash('Lead updated successfully', 'success')
        return redirect(f'/leads/{lead_id}')
    
    return render_template('leads/edit.html', 
                           lead=lead,
                           current_user={'is_authenticated': True})

@app.route('/leads/update-status/<int:lead_id>', methods=['GET', 'POST'])
def update_lead_status(lead_id):
    lead = get_lead(lead_id)
    if not lead:
        flash('Lead not found', 'danger')
        return redirect('/leads')
    
    if request.method == 'POST':
        status = request.form.get('status')
        
        # Update lead status
        for idx, l in enumerate(leads_data):
            if l['id'] == lead_id:
                leads_data[idx]['status'] = status
                break
        
        save_leads_to_file()
        flash('Lead status updated successfully', 'success')
        return redirect(f'/leads/{lead_id}')
    
    return render_template('leads/update_status.html', 
                           lead=lead,
                           current_user={'is_authenticated': True})

@app.route('/leads/delete/<int:lead_id>', methods=['POST'])
def delete_lead(lead_id):
    if delete_lead_by_id(lead_id):
        flash('Lead deleted successfully', 'success')
    else:
        flash('Lead not found', 'danger')
    return redirect('/leads')

# Settings routes
@app.route('/settings/update-sms', methods=['POST'])
def update_sms_settings():
    twilio_account_sid = request.form.get('twilio_account_sid')
    twilio_auth_token = request.form.get('twilio_auth_token')
    twilio_phone_number = request.form.get('twilio_phone_number')
    
    # Update environment variables in memory
    os.environ['TWILIO_ACCOUNT_SID'] = twilio_account_sid
    os.environ['TWILIO_PHONE_NUMBER'] = twilio_phone_number
    
    # Update global variables
    global TWILIO_ACCOUNT_SID, TWILIO_PHONE_NUMBER, twilio_available, twilio_client
    TWILIO_ACCOUNT_SID = twilio_account_sid
    TWILIO_PHONE_NUMBER = twilio_phone_number
    
    # Only update auth token if provided
    if twilio_auth_token:
        os.environ['TWILIO_AUTH_TOKEN'] = twilio_auth_token
        global TWILIO_AUTH_TOKEN
        TWILIO_AUTH_TOKEN = twilio_auth_token
    
    # Try to initialize Twilio client with new credentials
    if TWILIO_ACCOUNT_SID and TWILIO_AUTH_TOKEN and TWILIO_PHONE_NUMBER:
        try:
            from twilio.rest import Client
            twilio_client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)
            twilio_available = True
            app.logger.info("Twilio reinitialized successfully")
        except Exception as e:
            twilio_available = False
            app.logger.error(f"Failed to reinitialize Twilio: {str(e)}")
            flash(f'Failed to initialize Twilio: {str(e)}', 'danger')
            return redirect('/settings')
    
    # Update .env file
    update_env_file({
        'TWILIO_ACCOUNT_SID': twilio_account_sid,
        'TWILIO_PHONE_NUMBER': twilio_phone_number
    }, update_twilio_token=bool(twilio_auth_token), twilio_auth_token=twilio_auth_token)
    
    flash('SMS settings updated successfully', 'success')
    app.logger.info('SMS settings updated')
    return redirect('/settings')

@app.route('/settings/update-dealership', methods=['POST'])
def update_dealership_settings():
    dealership_name = request.form.get('dealership_name')
    dealership_address = request.form.get('dealership_address')
    dealership_phone = request.form.get('dealership_phone')
    dealership_website = request.form.get('dealership_website')
    
    # Update environment variables in memory
    os.environ['DEALERSHIP_NAME'] = dealership_name
    os.environ['DEALERSHIP_ADDRESS'] = dealership_address
    os.environ['DEALERSHIP_PHONE'] = dealership_phone
    os.environ['DEALERSHIP_WEBSITE'] = dealership_website
    
    # Update global variables
    global DEALERSHIP_NAME, DEALERSHIP_ADDRESS, DEALERSHIP_PHONE, DEALERSHIP_WEBSITE
    DEALERSHIP_NAME = dealership_name
    DEALERSHIP_ADDRESS = dealership_address
    DEALERSHIP_PHONE = dealership_phone
    DEALERSHIP_WEBSITE = dealership_website
    
    # Update .env file
    update_env_file({
        'DEALERSHIP_NAME': dealership_name,
        'DEALERSHIP_ADDRESS': dealership_address,
        'DEALERSHIP_PHONE': dealership_phone,
        'DEALERSHIP_WEBSITE': dealership_website
    })
    
    flash('Dealership information updated successfully', 'success')
    app.logger.info('Dealership settings updated')
    return redirect('/settings')

@app.route('/settings/update-salesperson', methods=['POST'])
def update_salesperson_settings():
    salesperson_name = request.form.get('salesperson_name')
    salesperson_email = request.form.get('salesperson_email')
    salesperson_phone = request.form.get('salesperson_phone')
    
    # Update environment variables in memory
    os.environ['SALESPERSON_NAME'] = salesperson_name
    os.environ['SALESPERSON_EMAIL'] = salesperson_email
    os.environ['SALESPERSON_PHONE'] = salesperson_phone
    
    # Update global variables
    global SALESPERSON_NAME, SALESPERSON_EMAIL, SALESPERSON_PHONE
    SALESPERSON_NAME = salesperson_name
    SALESPERSON_EMAIL = salesperson_email
    SALESPERSON_PHONE = salesperson_phone
    
    # Update .env file
    update_env_file({
        'SALESPERSON_NAME': salesperson_name,
        'SALESPERSON_EMAIL': salesperson_email,
        'SALESPERSON_PHONE': salesperson_phone
    })
    
    flash('Salesperson information updated successfully', 'success')
    app.logger.info('Salesperson settings updated')
    return redirect('/settings')

@app.route('/user/profile')
def user_profile():
    """User profile page"""
    # Mock user data - in a real app, this would come from a database
    user = {
        'username': 'demo_user',
        'email': 'demo@example.com',
        'first_name': 'Demo',
        'last_name': 'User',
        'role': 'BDC Manager',
        'phone': '(555) 123-4567',
        'created_at': datetime(2023, 1, 15),
        'last_login': datetime.now() - timedelta(days=1),
        'profile_image': '/static/img/default-profile.png'
    }
    
    # Activity stats
    activity = {
        'leads_added': 45,
        'appointments_scheduled': 28,
        'emails_sent': 120,
        'sms_sent': 75,
        'conversion_rate': 65  # percentage
    }
    
    # Recent activity
    recent_activity = [
        {
            'type': 'appointment',
            'description': 'Scheduled appointment with John Smith',
            'timestamp': datetime.now() - timedelta(hours=2)
        },
        {
            'type': 'email',
            'description': 'Sent follow-up email to Sarah Johnson',
            'timestamp': datetime.now() - timedelta(hours=4)
        },
        {
            'type': 'lead',
            'description': 'Added new lead: Michael Brown',
            'timestamp': datetime.now() - timedelta(hours=6)
        },
        {
            'type': 'sms',
            'description': 'Sent SMS reminder to David Wilson',
            'timestamp': datetime.now() - timedelta(hours=8)
        },
        {
            'type': 'note',
            'description': 'Added note to lead: Emily Davis',
            'timestamp': datetime.now() - timedelta(days=1)
        }
    ]
    
    return render_template('user/profile.html',
                          user=user,
                          activity=activity,
                          recent_activity=recent_activity,
                          current_user={'is_authenticated': True, 'username': 'demo_user'})

if __name__ == '__main__':
    # Ensure the upload folder exists
    os.makedirs(app.config.get('UPLOAD_FOLDER', 'temp'), exist_ok=True)
    app.run(debug=True, port=5001)

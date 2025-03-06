from flask import Flask, render_template, redirect, url_for, flash, request, send_from_directory, session, jsonify
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
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

# Import segmentation blueprint
from app.routes.segmentation_routes import segmentation_bp

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

# Register the segmentation blueprint
app.register_blueprint(segmentation_bp, url_prefix='/leads')

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

@app.route('/advanced_lead_search', methods=['GET'])
def advanced_lead_search():
    # Get saved search ID if provided
    saved_search_id = request.args.get('saved_search_id')
    search_params = {}
    search_results = []
    
    # If a saved search ID is provided, load those search parameters
    if saved_search_id:
        # In a real app, we would query the database
        # saved_search = SavedSearch.query.get(saved_search_id)
        # if saved_search:
        #     search_params = json.loads(saved_search.search_params)
        pass
    
    # Otherwise, get search parameters from the request
    else:
        # Basic information
        if request.args.get('name'):
            search_params['name'] = request.args.get('name')
        if request.args.get('email'):
            search_params['email'] = request.args.get('email')
        if request.args.get('phone'):
            search_params['phone'] = request.args.get('phone')
        
        # Status and source
        if request.args.getlist('status'):
            search_params['status'] = request.args.getlist('status')
        if request.args.getlist('source'):
            search_params['source'] = request.args.getlist('source')
        
        # Date range
        if request.args.get('created_from'):
            search_params['created_from'] = request.args.get('created_from')
        if request.args.get('created_to'):
            search_params['created_to'] = request.args.get('created_to')
        
        # Vehicle interest
        if request.args.get('vehicle_make'):
            search_params['vehicle_make'] = request.args.get('vehicle_make')
        if request.args.get('vehicle_model'):
            search_params['vehicle_model'] = request.args.get('vehicle_model')
        if request.args.get('vehicle_year'):
            search_params['vehicle_year'] = request.args.get('vehicle_year')
        if request.args.get('new_or_used'):
            search_params['new_or_used'] = request.args.get('new_or_used')
        
        # Communication history
        if request.args.get('last_contact'):
            search_params['last_contact'] = request.args.get('last_contact')
        if request.args.getlist('communication_type'):
            search_params['communication_type'] = request.args.getlist('communication_type')
        if request.args.get('has_appointment'):
            search_params['has_appointment'] = request.args.get('has_appointment')
        
        # Notes search
        if request.args.get('notes_search'):
            search_params['notes_search'] = request.args.get('notes_search')
            
        # Workflow status
        if request.args.getlist('workflow_status'):
            search_params['workflow_status'] = request.args.getlist('workflow_status')
            
        # Budget range
        if request.args.get('budget_min'):
            search_params['budget_min'] = request.args.get('budget_min')
        if request.args.get('budget_max'):
            search_params['budget_max'] = request.args.get('budget_max')
            
        # Timeline to purchase
        if request.args.get('purchase_timeline'):
            search_params['purchase_timeline'] = request.args.get('purchase_timeline')
            
        # Assigned to
        if request.args.getlist('assigned_to'):
            search_params['assigned_to'] = request.args.getlist('assigned_to')
    
    # If search parameters exist, perform the search
    if search_params:
        # In a real app, we would query the database with these parameters
        # For now, we'll filter our mock data
        filtered_leads = leads_data.copy()
        
        # Filter by name
        if 'name' in search_params:
            name_query = search_params['name'].lower()
            filtered_leads = [lead for lead in filtered_leads if 
                             name_query in (lead.get('first_name', '') + ' ' + lead.get('last_name', '')).lower()]
        
        # Filter by email
        if 'email' in search_params:
            email_query = search_params['email'].lower()
            filtered_leads = [lead for lead in filtered_leads if 
                             lead.get('email') and email_query in lead['email'].lower()]
        
        # Filter by phone
        if 'phone' in search_params:
            phone_query = search_params['phone'].replace('-', '').replace(' ', '')
            filtered_leads = [lead for lead in filtered_leads if 
                             lead.get('phone') and phone_query in lead['phone'].replace('-', '').replace(' ', '')]
        
        # Filter by status
        if 'status' in search_params:
            statuses = search_params['status']
            filtered_leads = [lead for lead in filtered_leads if lead.get('status') in statuses]
        
        # Filter by source
        if 'source' in search_params:
            sources = search_params['source']
            filtered_leads = [lead for lead in filtered_leads if lead.get('source') in sources]
        
        # Filter by date range
        if 'created_from' in search_params:
            try:
                created_from = datetime.strptime(search_params['created_from'], '%Y-%m-%d')
                filtered_leads = [lead for lead in filtered_leads if 
                                 lead.get('created_at') and lead['created_at'].date() >= created_from.date()]
            except (ValueError, TypeError):
                pass
        
        if 'created_to' in search_params:
            try:
                created_to = datetime.strptime(search_params['created_to'], '%Y-%m-%d')
                filtered_leads = [lead for lead in filtered_leads if 
                                 lead.get('created_at') and lead['created_at'].date() <= created_to.date()]
            except (ValueError, TypeError):
                pass
        
        # Filter by vehicle interest
        # In a real app, we would join with the VehicleInterest table
        # For now, we'll use the mock data's vehicle_interest field
        if 'vehicle_make' in search_params:
            make_query = search_params['vehicle_make'].lower()
            filtered_leads = [lead for lead in filtered_leads if 
                             lead.get('vehicle_interest') and make_query in lead['vehicle_interest'].lower()]
        
        if 'vehicle_model' in search_params:
            model_query = search_params['vehicle_model'].lower()
            filtered_leads = [lead for lead in filtered_leads if 
                             lead.get('vehicle_interest') and model_query in lead['vehicle_interest'].lower()]
        
        if 'vehicle_year' in search_params:
            year_query = search_params['vehicle_year']
            filtered_leads = [lead for lead in filtered_leads if 
                             lead.get('vehicle_interest') and year_query in lead['vehicle_interest']]
        
        if 'new_or_used' in search_params:
            new_or_used = search_params['new_or_used']
            filtered_leads = [lead for lead in filtered_leads if 
                             lead.get('vehicle_interest') and new_or_used in lead['vehicle_interest']]
        
        # Filter by last contact
        if 'last_contact' in search_params:
            last_contact = search_params['last_contact']
            now = datetime.now()
            
            if last_contact == '1':  # Today
                day_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
                filtered_leads = [lead for lead in filtered_leads if 
                                 any(comm.get('sent_at') >= day_start for comm in communications_data 
                                    if comm.get('lead_id') == lead.get('id'))]
            
            elif last_contact == '7':  # Last 7 days
                week_ago = now - timedelta(days=7)
                filtered_leads = [lead for lead in filtered_leads if 
                                 any(comm.get('sent_at') >= week_ago for comm in communications_data 
                                    if comm.get('lead_id') == lead.get('id'))]
            
            elif last_contact == '30':  # Last 30 days
                month_ago = now - timedelta(days=30)
                filtered_leads = [lead for lead in filtered_leads if 
                                 any(comm.get('sent_at') >= month_ago for comm in communications_data 
                                    if comm.get('lead_id') == lead.get('id'))]
            
            elif last_contact == '90':  # Last 90 days
                three_months_ago = now - timedelta(days=90)
                filtered_leads = [lead for lead in filtered_leads if 
                                 any(comm.get('sent_at') >= three_months_ago for comm in communications_data 
                                    if comm.get('lead_id') == lead.get('id'))]
            
            elif last_contact == 'never':  # Never contacted
                filtered_leads = [lead for lead in filtered_leads if 
                                 not any(comm.get('lead_id') == lead.get('id') for comm in communications_data)]
        
        # Filter by communication type
        if 'communication_type' in search_params:
            comm_types = search_params['communication_type']
            filtered_leads = [lead for lead in filtered_leads if 
                             any(comm.get('type') in comm_types and comm.get('lead_id') == lead.get('id') 
                                for comm in communications_data)]
        
        # Filter by appointment status
        if 'has_appointment' in search_params:
            appt_status = search_params['has_appointment']
            
            if appt_status == 'scheduled':
                filtered_leads = [lead for lead in filtered_leads if 
                                 any(appt.get('lead_id') == lead.get('id') and appt.get('status') in ['Scheduled', 'Confirmed'] 
                                    for appt in appointments_data)]
            
            elif appt_status == 'completed':
                filtered_leads = [lead for lead in filtered_leads if 
                                 any(appt.get('lead_id') == lead.get('id') and appt.get('status') == 'Completed' 
                                    for appt in appointments_data)]
            
            elif appt_status == 'none':
                filtered_leads = [lead for lead in filtered_leads if 
                                 not any(appt.get('lead_id') == lead.get('id') for appt in appointments_data)]
        
        # Filter by notes
        if 'notes_search' in search_params:
            notes_query = search_params['notes_search'].lower()
            filtered_leads = [lead for lead in filtered_leads if 
                             lead.get('notes') and notes_query in lead['notes'].lower()]
                             
        # Filter by workflow status
        if 'workflow_status' in search_params:
            workflow_statuses = search_params['workflow_status']
            # In a real app, we would join with the LeadWorkflow table
            # For now, we'll just simulate this filter
            if 'active' in workflow_statuses:
                # Simulate having some leads with active workflows
                active_workflow_lead_ids = [1, 3, 5]
                filtered_leads = [lead for lead in filtered_leads if lead.get('id') in active_workflow_lead_ids]
            elif 'completed' in workflow_statuses:
                # Simulate having some leads with completed workflows
                completed_workflow_lead_ids = [2, 4]
                filtered_leads = [lead for lead in filtered_leads if lead.get('id') in completed_workflow_lead_ids]
            elif 'none' in workflow_statuses:
                # Simulate having some leads with no workflows
                no_workflow_lead_ids = [6, 7, 8]
                filtered_leads = [lead for lead in filtered_leads if lead.get('id') in no_workflow_lead_ids]
        
        # Filter by budget range
        if 'budget_min' in search_params or 'budget_max' in search_params:
            # In a real app, we would have a budget field in the lead model
            # For now, we'll just simulate this filter
            # Assign random budgets to leads for demonstration
            for lead in filtered_leads:
                if not lead.get('budget'):
                    lead['budget'] = random.randint(10000, 100000)
            
            if 'budget_min' in search_params:
                budget_min = int(search_params['budget_min'])
                filtered_leads = [lead for lead in filtered_leads if lead.get('budget', 0) >= budget_min]
            
            if 'budget_max' in search_params:
                budget_max = int(search_params['budget_max'])
                filtered_leads = [lead for lead in filtered_leads if lead.get('budget', 0) <= budget_max]
        
        # Filter by timeline to purchase
        if 'purchase_timeline' in search_params:
            timeline = search_params['purchase_timeline']
            # In a real app, we would have a purchase_timeline field in the lead model
            # For now, we'll just simulate this filter
            # Assign random timelines to leads for demonstration
            timelines = ['immediate', '1-3_months', '3-6_months', '6-12_months', 'over_12_months']
            for lead in filtered_leads:
                if not lead.get('purchase_timeline'):
                    lead['purchase_timeline'] = random.choice(timelines)
            
            filtered_leads = [lead for lead in filtered_leads if lead.get('purchase_timeline') == timeline]
        
        # Filter by assigned to
        if 'assigned_to' in search_params:
            assigned_to_ids = [int(id) for id in search_params['assigned_to']]
            filtered_leads = [lead for lead in filtered_leads if lead.get('assigned_to') in assigned_to_ids]
        
        search_results = filtered_leads
        
        # Save search to history
        if search_results and 'current_user' in globals() and current_user.is_authenticated:
            try:
                search_history = SearchHistory(
                    user_id=current_user.id,
                    search_params=json.dumps(search_params),
                    results_count=len(search_results)
                )
                db.session.add(search_history)
                db.session.commit()
            except Exception as e:
                print(f"Error saving search history: {e}")
                db.session.rollback()
    
    # Get saved searches for the current user
    saved_searches = []
    if 'current_user' in globals() and current_user.is_authenticated:
        saved_searches = SavedSearch.query.filter_by(user_id=current_user.id).order_by(SavedSearch.created_at.desc()).all()
    else:
        # Mock saved searches data for demonstration
        saved_searches = [
            {
                'id': 1,
                'name': 'Hot Leads - This Week',
                'created_at': datetime.now() - timedelta(days=5)
            },
            {
                'id': 2,
                'name': 'Ford F-150 Interests',
                'created_at': datetime.now() - timedelta(days=10)
            },
            {
                'id': 3,
                'name': 'Uncontacted Leads',
                'created_at': datetime.now() - timedelta(days=2)
            }
        ]
    
    # Get recent search history for the current user
    search_history_list = []
    if 'current_user' in globals() and current_user.is_authenticated:
        search_history_list = SearchHistory.query.filter_by(user_id=current_user.id).order_by(SearchHistory.executed_at.desc()).limit(5).all()
    
    # Get all users for the assigned_to filter
    users = []
    if 'current_user' in globals() and current_user.is_authenticated:
        users = User.query.all()
    else:
        # Mock users data for demonstration
        users = [
            {'id': 1, 'first_name': 'John', 'last_name': 'Doe'},
            {'id': 2, 'first_name': 'Jane', 'last_name': 'Smith'},
            {'id': 3, 'first_name': 'Bob', 'last_name': 'Johnson'}
        ]
    
    return render_template('leads/advanced_search.html',
                          search_params=search_params,
                          search_results=search_results,
                          saved_searches=saved_searches,
                          search_history=search_history_list,
                          users=users,
                          current_user={'is_authenticated': True})

@app.route('/save_search', methods=['POST'])
def save_search():
    search_name = request.form.get('search_name')
    search_params = request.form.get('search_params')
    
    if not search_name or not search_params:
        flash('Search name and parameters are required.', 'danger')
        return redirect(url_for('advanced_lead_search'))
    
    # Save to the database
    if 'current_user' in globals() and current_user.is_authenticated:
        try:
            saved_search = SavedSearch(
                name=search_name,
                user_id=current_user.id,
                search_params=search_params
            )
            db.session.add(saved_search)
            db.session.commit()
            flash(f'Search "{search_name}" has been saved.', 'success')
        except Exception as e:
            print(f"Error saving search: {e}")
            db.session.rollback()
            flash('An error occurred while saving your search.', 'danger')
    else:
        # Mock save for demonstration
        flash(f'Search "{search_name}" has been saved.', 'success')
    
    return redirect(url_for('advanced_lead_search'))

@app.route('/delete_saved_search')
def delete_saved_search():
    search_id = request.args.get('id')
    
    if not search_id:
        flash('No search specified.', 'danger')
        return redirect(url_for('advanced_lead_search'))
    
    # In a real app, we would delete from the database
    # saved_search = SavedSearch.query.get(search_id)
    # if saved_search and saved_search.user_id == current_user.id:
    #     db.session.delete(saved_search)
    #     db.session.commit()
    #     flash('Saved search has been deleted.', 'success')
    # else:
    #     flash('Search not found or you do not have permission to delete it.', 'danger')
    
    flash('Saved search has been deleted.', 'success')
    return redirect(url_for('advanced_lead_search'))

@app.route('/export_search_results')
def export_search_results():
    # In a real app, we would retrieve the search results from the session or re-run the search
    # For now, we'll just return a sample CSV file
    
    # Create a CSV in memory
    output = io.StringIO()
    writer = csv.writer(output)
    
    # Write header row
    writer.writerow(['First Name', 'Last Name', 'Email', 'Phone', 'Status', 'Source', 'Vehicle Interest', 'Created Date'])
    
    # Write data rows (using mock data for now)
    for lead in leads_data:
        writer.writerow([
            lead.get('first_name', ''),
            lead.get('last_name', ''),
            lead.get('email', ''),
            lead.get('phone', ''),
            lead.get('status', ''),
            lead.get('source', ''),
            lead.get('vehicle_interest', ''),
            lead.get('created_at', datetime.now()).strftime('%Y-%m-%d')
        ])
    
    # Prepare the response
    output.seek(0)
    return send_from_directory(
        directory=os.path.join(app.root_path, 'static'),
        path='search_results.csv',
        as_attachment=True,
        download_name=f'lead_search_results_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv'
    )

@app.route('/view_lead/<int:lead_id>')
def view_lead(lead_id):
    # Get the lead
    lead = get_lead(lead_id)
    
    if not lead:
        flash('Lead not found.', 'danger')
        return redirect(url_for('leads'))
    
    # Get appointments for this lead
    lead_appointments = get_lead_appointments(lead_id)
    
    # Get communications for this lead
    communications = get_lead_communications(lead_id)
    
    # Get follow-ups for this lead
    followups = get_lead_followups(lead_id)
    
    return render_template('leads/view.html',
                          lead=lead,
                          appointments=lead_appointments,
                          communications=communications,
                          followups=followups,
                          current_user={'is_authenticated': True},
                          title='Lead Details')

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
                           pagination={'has_prev': False, 'has_next': False, 'page': 1, 'pages': 1})

@app.route('/appointments/calendar')
def appointments_calendar():
    # Get all appointments
    all_appointments = appointments_data
    
    # Format appointments for FullCalendar
    appointments_json = []
    for appointment in all_appointments:
        lead = next((lead for lead in leads_data if lead['id'] == appointment['lead_id']), None)
        if lead:
            lead_name = f"{lead['first_name']} {lead['last_name']}"
            
            # Check if date is already a string or a datetime object
            appointment_date = appointment['date']
            if not hasattr(appointment_date, 'strftime'):  # If it's a string, not a date object
                appointment_date = datetime.strptime(appointment_date, '%Y-%m-%d').date()
                
            appointments_json.append({
                'id': appointment['id'],
                'title': f"{lead_name} - {appointment['purpose']}",
                'start': f"{appointment_date.strftime('%Y-%m-%d')}T{appointment['time']}",
                'status': appointment['status'],
                'lead': {
                    'id': lead['id'],
                    'name': lead_name
                }
            })
    
    # Calculate stats
    today = datetime.now().date()
    start_of_week = today - timedelta(days=today.weekday())
    start_of_month = today.replace(day=1)
    
    # Count appointments for this month and week
    total_month = 0
    total_week = 0
    today_appointments = []
    
    for a in all_appointments:
        # Check if date is a string or datetime.date
        appointment_date = a['date']
        if not hasattr(appointment_date, 'strftime'):  # If it's a string, not a date object
            appointment_date = datetime.strptime(appointment_date, '%Y-%m-%d').date()
        
        # Now we can safely compare dates
        if appointment_date >= start_of_month:
            total_month += 1
        if appointment_date >= start_of_week:
            total_week += 1
        
        # Check if appointment is today
        if appointment_date == today:
            lead = next((lead for lead in leads_data if lead['id'] == a['lead_id']), None)
            if lead:
                today_appointments.append({
                    'id': a['id'],
                    'time': a['time'],
                    'status': a['status'],
                    'lead': {
                        'first_name': lead['first_name'],
                        'last_name': lead['last_name']
                    },
                    'vehicle_interest': a.get('vehicle_interest', '')
                })
    
    # Calculate no-show and conversion rates
    completed_appointments = [a for a in all_appointments if a['status'] in ['Completed', 'No Show']]
    no_shows = sum(1 for a in completed_appointments if a['status'] == 'No Show')
    conversions = sum(1 for a in completed_appointments if a['status'] == 'Completed' and a.get('converted', False))
    
    no_show_rate = round((no_shows / len(completed_appointments)) * 100) if completed_appointments else 0
    conversion_rate = round((conversions / len(completed_appointments)) * 100) if completed_appointments else 0
    
    # Generate available slots for the sidebar
    available_slots = []
    for i in range(7):
        slot_date = today + timedelta(days=i)
        if slot_date.weekday() < 5:  # Weekdays only
            for hour in [9, 11, 14, 16]:
                available_slots.append({
                    'date': slot_date.strftime('%Y-%m-%d'),
                    'time': f"{hour:02d}:00",
                    'day_of_week': slot_date.strftime('%A')
                })
                if len(available_slots) >= 5:
                    break
        if len(available_slots) >= 5:
            break
    
    # Get recent activity for the sidebar
    recent_activity = []
    for appointment in sorted(all_appointments, key=lambda x: x['id'], reverse=True)[:5]:
        lead = next((lead for lead in leads_data if lead['id'] == appointment['lead_id']), None)
        if lead:
            recent_activity.append({
                'type': 'appointment',
                'date': appointment['date'],
                'time': appointment['time'],
                'lead_name': f"{lead['first_name']} {lead['last_name']}",
                'lead_id': lead['id'],
                'status': appointment['status'],
                'purpose': appointment['purpose'],
                'id': appointment['id']
            })
    
    stats = {
        'total_month': total_month,
        'total_week': total_week,
        'no_show_rate': no_show_rate,
        'conversion_rate': conversion_rate
    }
    
    return render_template('appointments/calendar.html', 
                           appointments_json=json.dumps(appointments_json),
                           stats=stats,
                           available_slots=available_slots,
                           leads_data=leads_data,
                           recent_activity=recent_activity,
                           today=datetime.now().date(),
                           today_appointments=today_appointments,
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
    appointments_today = sum(1 for appt in appointments_data if appt['date'] == datetime.now().date())
    
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
        
        # Prepare the response
        output.seek(0)
        return send_from_directory(
            directory=os.path.join(app.root_path, 'static'),
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
                directory=os.path.join(app.root_path, 'static'),
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
        appointment_id = request.form.get('appointment_id')
        
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
        
        # Redirect based on context
        if appointment_id:
            return redirect(url_for('view_appointment', appointment_id=int(appointment_id)))
        else:
            return redirect(f'/leads/{lead_id}')
    
    # Handle GET request
    lead_id = request.args.get('lead_id')
    appointment_id = request.args.get('appointment_id')
    
    # If coming from an appointment view
    if appointment_id:
        # Find the appointment
        appointment = None
        for apt in appointments_data:
            if apt['id'] == int(appointment_id):
                appointment = apt
                break
        
        if not appointment:
            flash('Appointment not found.', 'danger')
            return redirect(url_for('appointments'))
        
        # Get the lead
        lead_id = appointment['lead_id']
    
    lead = get_lead(int(lead_id)) if lead_id else None
    email_templates = get_templates_by_type('Email')
    
    return render_template('communications/email.html', 
                           lead=lead,
                           templates=email_templates,
                           appointment_id=appointment_id,
                           current_user={'is_authenticated': True},
                           title='Send Email')

@app.route('/communications/sms', methods=['GET', 'POST'])
def send_sms():
    if request.method == 'POST':
        lead_id = request.form.get('lead_id')
        content = request.form.get('content')
        template_id = request.form.get('template_id')
        appointment_id = request.form.get('appointment_id')
        
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
        elif app.config['TWILIO_ACCOUNT_SID'] == 'your-account-sid' or app.config['TWILIO_AUTH_TOKEN'] == 'your-auth-token':
            flash('SMS not sent: Twilio configuration incomplete. Please update your .env file with proper credentials.', 'warning')
            app.logger.warning(f"SMS not sent to lead {lead_id}: Twilio configuration incomplete")
        else:
            try:
                # In a real app, we would use Twilio to send the SMS
                # client = Client(app.config['TWILIO_ACCOUNT_SID'], app.config['TWILIO_AUTH_TOKEN'])
                # message = client.messages.create(
                #     body=content,
                #     from_=app.config['TWILIO_PHONE_NUMBER'],
                #     to=lead['phone']
                # )
                # sms_sent = True
                
                # For demo purposes, we'll just pretend it was sent
                sms_sent = True
                flash(f'SMS sent successfully to {lead["phone"]}', 'success')
                app.logger.info(f"SMS sent to lead {lead_id} at {lead['phone']}")
            except Exception as e:
                error_message = str(e)
                flash(f'SMS not sent: {error_message}', 'danger')
                app.logger.error(f"Failed to send SMS to lead {lead_id}: {error_message}")
        
        # Redirect based on context
        if appointment_id:
            return redirect(url_for('view_appointment', appointment_id=int(appointment_id)))
        else:
            return redirect(f'/leads/{lead_id}')
    
    # Handle GET request
    lead_id = request.args.get('lead_id')
    appointment_id = request.args.get('appointment_id')
    
    # If coming from an appointment view
    if appointment_id:
        # Find the appointment
        appointment = None
        for apt in appointments_data:
            if apt['id'] == int(appointment_id):
                appointment = apt
                break
        
        if not appointment:
            flash('Appointment not found.', 'danger')
            return redirect(url_for('appointments'))
        
        # Get the lead
        lead_id = appointment['lead_id']
    
    lead = get_lead(int(lead_id)) if lead_id else None
    sms_templates = get_templates_by_type('SMS')
    
    return render_template('communications/sms.html', 
                           lead=lead,
                           templates=sms_templates,
                           appointment_id=appointment_id,
                           current_user={'is_authenticated': True},
                           title='Send SMS')

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
        'profile_image': '/static/img/default-profile.png',
        'preferences': {
            'email_notifications': True,
            'sms_notifications': False,
            'dark_mode': False
        }
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

@app.route('/add_appointment', methods=['GET', 'POST'])
def add_appointment():
    # Get all leads for the dropdown
    all_leads = leads_data
    
    if request.method == 'POST':
        # Get form data
        lead_id = int(request.form.get('lead_id'))
        date_str = request.form.get('date')
        time_str = request.form.get('time')
        purpose = request.form.get('purpose')
        notes = request.form.get('notes')
        
        # Parse date and time
        appointment_date = datetime.strptime(date_str, '%Y-%m-%d').date()
        appointment_time = datetime.strptime(time_str, '%H:%M').time()
        
        # Create new appointment
        new_appointment = {
            'id': len(appointments_data) + 1,
            'lead_id': lead_id,
            'date': appointment_date,
            'time': appointment_time,
            'purpose': purpose,
            'notes': notes,
            'status': 'Scheduled',
            'created_at': datetime.now()
        }
        
        # Add to appointments data
        appointments_data.append(new_appointment)
        
        flash('Appointment scheduled successfully!', 'success')
        return redirect(url_for('appointments'))
    
    # Get current date for the form or use the date from the query parameter
    selected_date = request.args.get('date', datetime.now().strftime('%Y-%m-%d'))
    
    return render_template('appointments/add.html', 
                          leads=all_leads,
                          current_user={'is_authenticated': True},
                          title='Schedule New Appointment',
                          current_date=selected_date)

@app.route('/view_appointment/<int:appointment_id>')
def view_appointment(appointment_id):
    # Find the appointment by ID
    appointment = None
    for apt in appointments_data:
        if apt['id'] == appointment_id:
            appointment = apt
            break
    
    if not appointment:
        flash('Appointment not found.', 'danger')
        return redirect(url_for('appointments'))
    
    # Get the lead associated with this appointment
    lead = get_lead(appointment['lead_id'])
    
    if not lead:
        flash('Lead associated with this appointment not found.', 'warning')
        return redirect(url_for('appointments'))
    
    # Add lead to appointment for template
    appointment['lead'] = lead
    
    # Get communications related to this lead
    communications = get_lead_communications(lead['id'])
    
    return render_template('appointments/view.html',
                          appointment=appointment,
                          lead=lead,
                          communications=communications,
                          current_user={'is_authenticated': True},
                          title='Appointment Details')

@app.route('/edit_appointment/<int:appointment_id>', methods=['GET', 'POST'])
def edit_appointment(appointment_id):
    # Find the appointment by ID
    appointment = None
    for apt in appointments_data:
        if apt['id'] == appointment_id:
            appointment = apt
            break
    
    if not appointment:
        flash('Appointment not found.', 'danger')
        return redirect(url_for('appointments'))
    
    # Get the lead associated with this appointment
    lead = get_lead(appointment['lead_id'])
    
    if not lead:
        flash('Lead associated with this appointment not found.', 'warning')
        return redirect(url_for('appointments'))
    
    if request.method == 'POST':
        # Get form data
        date_str = request.form.get('date')
        time_str = request.form.get('time')
        purpose = request.form.get('purpose')
        notes = request.form.get('notes')
        status = request.form.get('status')
        
        # Parse date and time
        appointment_date = datetime.strptime(date_str, '%Y-%m-%d').date()
        appointment_time = datetime.strptime(time_str, '%H:%M').time()
        
        # Update appointment
        appointment['date'] = appointment_date
        appointment['time'] = appointment_time
        appointment['purpose'] = purpose
        appointment['notes'] = notes
        appointment['status'] = status
        appointment['updated_at'] = datetime.now()
        
        flash('Appointment updated successfully!', 'success')
        return redirect(url_for('view_appointment', appointment_id=appointment_id))
    
    # Format date and time for the form
    date_str = appointment['date'].strftime('%Y-%m-%d')
    time_str = appointment['time'].strftime('%H:%M')
    
    # Get all leads for the dropdown
    all_leads = leads_data
    
    # Get current date for the form
    current_date = datetime.now().strftime('%Y-%m-%d')
    
    return render_template('appointments/create_edit.html', 
                          appointment=appointment,
                          lead=lead,
                          leads=all_leads,
                          date_str=date_str,
                          time_str=time_str,
                          current_date=current_date,
                          current_user={'is_authenticated': True},
                          title='Edit Appointment')

@app.route('/mark_confirmed/<int:appointment_id>')
def mark_confirmed(appointment_id):
    # Find the appointment by ID
    appointment = None
    for apt in appointments_data:
        if apt['id'] == appointment_id:
            appointment = apt
            break
    
    if not appointment:
        flash('Appointment not found.', 'danger')
        return redirect(url_for('appointments'))
    
    # Update appointment status
    appointment['status'] = 'Confirmed'
    appointment['updated_at'] = datetime.now()
    
    flash('Appointment marked as confirmed!', 'success')
    return redirect(url_for('view_appointment', appointment_id=appointment_id))

@app.route('/mark_completed/<int:appointment_id>')
def mark_completed(appointment_id):
    # Find the appointment by ID
    appointment = None
    for apt in appointments_data:
        if apt['id'] == appointment_id:
            appointment = apt
            break
    
    if not appointment:
        flash('Appointment not found.', 'danger')
        return redirect(url_for('appointments'))
    
    # Update appointment status
    appointment['status'] = 'Completed'
    appointment['updated_at'] = datetime.now()
    
    flash('Appointment marked as completed!', 'success')
    return redirect(url_for('view_appointment', appointment_id=appointment_id))

@app.route('/mark_cancelled/<int:appointment_id>')
def mark_cancelled(appointment_id):
    # Find the appointment by ID
    appointment = None
    for apt in appointments_data:
        if apt['id'] == appointment_id:
            appointment = apt
            break
    
    if not appointment:
        flash('Appointment not found.', 'danger')
        return redirect(url_for('appointments'))
    
    # Update appointment status
    appointment['status'] = 'Cancelled'
    appointment['updated_at'] = datetime.now()
    
    flash('Appointment marked as cancelled.', 'success')
    return redirect(url_for('view_appointment', appointment_id=appointment_id))

@app.route('/mark_no_show/<int:appointment_id>')
def mark_no_show(appointment_id):
    # Find the appointment by ID
    appointment = None
    for apt in appointments_data:
        if apt['id'] == appointment_id:
            appointment = apt
            break
    
    if not appointment:
        flash('Appointment not found.', 'danger')
        return redirect(url_for('appointments'))
    
    # Update appointment status
    appointment['status'] = 'No-Show'
    appointment['updated_at'] = datetime.now()
    
    flash('Appointment marked as no-show.', 'success')
    return redirect(url_for('view_appointment', appointment_id=appointment_id))

@app.route('/appointment_calendar')
def appointment_calendar():
    # Redirect to the appointments calendar view
    return redirect(url_for('appointments_calendar'))

@app.route('/user/save_preferences', methods=['POST'])
def save_preferences():
    """Save user preferences"""
    # In a real app, this would save to the database
    # For demo purposes, we'll just return success
    preferences = {
        'email_notifications': request.form.get('email_notifications') == 'true',
        'sms_notifications': request.form.get('sms_notifications') == 'true',
        'dark_mode': request.form.get('dark_mode') == 'true'
    }
    
    # Here you would save to the database
    # user.preferences = preferences
    # db.session.commit()
    
    return jsonify({'success': True, 'message': 'Preferences saved successfully'})

@app.route('/workflows')
def workflows():
    """Display all workflow templates."""
    workflows = WorkflowTemplate.query.all()
    
    # Calculate active leads count for each workflow
    for workflow in workflows:
        workflow.active_leads_count = LeadWorkflow.query.filter_by(
            workflow_template_id=workflow.id, 
            status='active'
        ).count()
    
    return render_template('workflows/list.html', workflows=workflows)

@app.route('/workflow/create', methods=['GET', 'POST'])
def create_workflow():
    """Create a new workflow template."""
    if request.method == 'POST':
        name = request.form.get('name')
        description = request.form.get('description')
        trigger_status = request.form.get('trigger_status')
        auto_apply = 'auto_apply' in request.form
        
        # Create new workflow
        workflow = WorkflowTemplate(
            name=name,
            description=description,
            trigger_status=trigger_status,
            auto_apply=auto_apply
        )
        db.session.add(workflow)
        db.session.flush()  # Get the workflow ID
        
        # Process steps
        step_types = request.form.getlist('step_type[]')
        delay_days = request.form.getlist('delay_days[]')
        template_ids = request.form.getlist('template_id[]')
        subjects = request.form.getlist('subject[]')
        contents = request.form.getlist('content[]')
        step_orders = request.form.getlist('step_order[]')
        
        for i in range(len(step_types)):
            step = WorkflowStep(
                workflow_id=workflow.id,
                step_type=step_types[i],
                delay_days=int(delay_days[i]),
                template_id=int(template_ids[i]) if template_ids[i] else None,
                subject=subjects[i],
                content=contents[i],
                step_order=int(step_orders[i])
            )
            db.session.add(step)
        
        db.session.commit()
        flash('Workflow created successfully!', 'success')
        return redirect(url_for('workflows'))
    
    # Mock data for templates until we implement them
    email_templates = [
        {'id': 1, 'name': 'Welcome Email'},
        {'id': 2, 'name': 'Follow-up Email'},
        {'id': 3, 'name': 'Appointment Reminder'}
    ]
    
    sms_templates = [
        {'id': 1, 'name': 'Welcome SMS'},
        {'id': 2, 'name': 'Follow-up SMS'},
        {'id': 3, 'name': 'Appointment Reminder SMS'}
    ]
    
    return render_template('workflows/create_edit.html', 
                           workflow=None, 
                           email_templates=email_templates,
                           sms_templates=sms_templates)

@app.route('/workflow/<int:workflow_id>')
def view_workflow(workflow_id):
    """View a workflow template and its active leads."""
    workflow = WorkflowTemplate.query.get_or_404(workflow_id)
    
    # Get active leads for this workflow
    active_leads = LeadWorkflow.query.filter_by(
        workflow_template_id=workflow_id,
        status='active'
    ).all()
    
    # Calculate active leads count
    active_leads_count = len(active_leads)
    
    # Add current step and next step date to each lead workflow
    for lead_workflow in active_leads:
        # Get the current step (last completed or first pending)
        current_step = LeadWorkflowStep.query.filter_by(
            lead_workflow_id=lead_workflow.id
        ).order_by(LeadWorkflowStep.scheduled_date).first()
        
        lead_workflow.current_step = current_step
        
        # Get the next step date
        next_step = LeadWorkflowStep.query.filter_by(
            lead_workflow_id=lead_workflow.id,
            status='pending'
        ).order_by(LeadWorkflowStep.scheduled_date).first()
        
        lead_workflow.next_step_date = next_step.scheduled_date if next_step else None
    
    # Mock data for templates until we implement them
    email_templates = [
        {'id': 1, 'name': 'Welcome Email'},
        {'id': 2, 'name': 'Follow-up Email'},
        {'id': 3, 'name': 'Appointment Reminder'}
    ]
    
    sms_templates = [
        {'id': 1, 'name': 'Welcome SMS'},
        {'id': 2, 'name': 'Follow-up SMS'},
        {'id': 3, 'name': 'Appointment Reminder SMS'}
    ]
    
    return render_template('workflows/view.html', 
                           workflow=workflow, 
                           active_leads=active_leads,
                           active_leads_count=active_leads_count,
                           email_templates=email_templates,
                           sms_templates=sms_templates)

@app.route('/workflow/edit/<int:workflow_id>', methods=['GET', 'POST'])
def edit_workflow(workflow_id):
    """Edit an existing workflow template."""
    workflow = WorkflowTemplate.query.get_or_404(workflow_id)
    
    if request.method == 'POST':
        workflow.name = request.form.get('name')
        workflow.description = request.form.get('description')
        workflow.trigger_status = request.form.get('trigger_status')
        workflow.auto_apply = 'auto_apply' in request.form
        
        # Clear existing steps
        WorkflowStep.query.filter_by(workflow_template_id=workflow_id).delete()
        
        # Process steps
        step_types = request.form.getlist('step_type[]')
        delay_days = request.form.getlist('delay_days[]')
        template_ids = request.form.getlist('template_id[]')
        subjects = request.form.getlist('subject[]')
        contents = request.form.getlist('content[]')
        step_orders = request.form.getlist('step_order[]')
        
        for i in range(len(step_types)):
            step = WorkflowStep(
                workflow_template_id=workflow_id,
                step_type=step_types[i],
                delay_days=int(delay_days[i]),
                template_id=int(template_ids[i]) if template_ids[i] else None,
                subject=subjects[i],
                content=contents[i],
                step_order=int(step_orders[i])
            )
            db.session.add(step)
        
        db.session.commit()
        flash('Workflow updated successfully!', 'success')
        return redirect(url_for('workflows'))
    
    # Mock data for templates until we implement them
    email_templates = [
        {'id': 1, 'name': 'Welcome Email'},
        {'id': 2, 'name': 'Follow-up Email'},
        {'id': 3, 'name': 'Appointment Reminder'}
    ]
    
    sms_templates = [
        {'id': 1, 'name': 'Welcome SMS'},
        {'id': 2, 'name': 'Follow-up SMS'},
        {'id': 3, 'name': 'Appointment Reminder SMS'}
    ]
    
    return render_template('workflows/create_edit.html', 
                           workflow=workflow, 
                           email_templates=email_templates,
                           sms_templates=sms_templates)

@app.route('/workflow/duplicate/<int:workflow_id>')
def duplicate_workflow(workflow_id):
    """Duplicate an existing workflow template."""
    original_workflow = WorkflowTemplate.query.get_or_404(workflow_id)
    
    # Create new workflow with copy of data
    new_workflow = WorkflowTemplate(
        name=f"{original_workflow.name} (Copy)",
        description=original_workflow.description,
        trigger_status=original_workflow.trigger_status,
        auto_apply=original_workflow.auto_apply
    )
    db.session.add(new_workflow)
    db.session.flush()  # Get the new workflow ID
    
    # Copy all steps
    for step in original_workflow.steps:
        new_step = WorkflowStep(
            workflow_id=new_workflow.id,
            step_type=step.step_type,
            delay_days=step.delay_days,
            template_id=step.template_id,
            subject=step.subject,
            content=step.content,
            step_order=step.step_order
        )
        db.session.add(new_step)
    
    db.session.commit()
    flash('Workflow duplicated successfully!', 'success')
    return redirect(url_for('edit_workflow', workflow_id=new_workflow.id))

@app.route('/workflow/delete')
def delete_workflow():
    """Delete a workflow template."""
    workflow_id = request.args.get('id', type=int)
    workflow = WorkflowTemplate.query.get_or_404(workflow_id)
    
    # Delete all active lead workflows
    lead_workflows = LeadWorkflow.query.filter_by(workflow_template_id=workflow_id).all()
    for lead_workflow in lead_workflows:
        # Delete all steps for this lead workflow
        LeadWorkflowStep.query.filter_by(lead_workflow_id=lead_workflow.id).delete()
        db.session.delete(lead_workflow)
    
    # Delete the workflow and its steps
    db.session.delete(workflow)
    db.session.commit()
    
    flash('Workflow deleted successfully!', 'success')
    return redirect(url_for('workflows'))

@app.route('/workflow/apply', methods=['GET', 'POST'])
def apply_workflow():
    """Apply a workflow to leads."""
    if request.method == 'POST':
        # Just return the filtered leads, actual application happens in apply_workflow_to_leads
        return redirect(url_for('workflows'))
    
    workflow_id = request.args.get('workflow_id', type=int)
    workflow = None
    if workflow_id:
        workflow = WorkflowTemplate.query.get_or_404(workflow_id)
    
    workflows = WorkflowTemplate.query.all()
    
    # Get all users for assignment filter
    users = User.query.all()
    
    return render_template('workflows/apply.html', 
                           workflow=workflow, 
                           workflows=workflows,
                           users=users)

@app.route('/workflow/filter_leads', methods=['POST'])
def filter_leads_for_workflow():
    """AJAX endpoint to filter leads based on criteria."""
    # Get filter parameters
    status = request.form.get('status')
    source = request.form.get('source')
    assigned_to = request.form.get('assigned_to')
    created_after = request.form.get('created_after')
    created_before = request.form.get('created_before')
    
    # Build query
    query = Lead.query
    
    if status:
        query = query.filter(Lead.status == status)
    
    if source:
        query = query.filter(Lead.source == source)
    
    if assigned_to:
        query = query.filter(Lead.assigned_to == int(assigned_to))
    
    if created_after:
        query = query.filter(Lead.created_at >= datetime.strptime(created_after, '%Y-%m-%d'))
    
    if created_before:
        query = query.filter(Lead.created_at <= datetime.strptime(created_before, '%Y-%m-%d') + timedelta(days=1))
    
    # Execute query
    leads = query.all()
    
    # Convert leads to JSON
    leads_json = []
    for lead in leads:
        leads_json.append({
            'id': lead.id,
            'first_name': lead.first_name,
            'last_name': lead.last_name,
            'email': lead.email,
            'phone': lead.phone,
            'status': lead.status,
            'source': lead.source,
            'created_at': lead.created_at.isoformat()
        })
    
    return jsonify({'leads': leads_json})

@app.route('/workflow/apply_to_leads', methods=['POST'])
def apply_workflow_to_leads():
    """Apply a workflow to selected leads."""
    workflow_id = request.form.get('workflow_id', type=int)
    lead_ids = request.form.getlist('lead_ids[]')
    
    if not workflow_id or not lead_ids:
        flash('Please select a workflow and at least one lead.', 'danger')
        return redirect(url_for('apply_workflow'))
    
    workflow = WorkflowTemplate.query.get_or_404(workflow_id)
    
    # Get all steps for this workflow
    steps = WorkflowStep.query.filter_by(workflow_template_id=workflow_id).order_by(WorkflowStep.step_order).all()
    
    # Process each lead
    for lead_id in lead_ids:
        # Check if lead already has this workflow active
        existing_workflow = LeadWorkflow.query.filter_by(
            lead_id=lead_id,
            workflow_template_id=workflow_id,
            status='active'
        ).first()
        
        if existing_workflow:
            continue  # Skip if already active
        
        # Create new lead workflow
        lead_workflow = LeadWorkflow(
            lead_id=lead_id,
            workflow_template_id=workflow_id,
            start_date=datetime.utcnow(),
            status='active'
        )
        db.session.add(lead_workflow)
        db.session.flush()  # Get the lead workflow ID
        
        # Create steps for this lead
        current_date = datetime.utcnow()
        for step in steps:
            scheduled_date = current_date + timedelta(days=step.delay_days)
            
            lead_workflow_step = LeadWorkflowStep(
                lead_workflow_id=lead_workflow.id,
                workflow_step_id=step.id,
                scheduled_date=scheduled_date,
                status='pending'
            )
            db.session.add(lead_workflow_step)
    
    db.session.commit()
    
    flash(f'Workflow applied to {len(lead_ids)} leads successfully!', 'success')
    return redirect(url_for('view_workflow', workflow_id=workflow_id))

@app.route('/workflow/execute_step', methods=['POST'])
def execute_workflow_step():
    """Execute a workflow step manually."""
    step_id = request.form.get('step_id', type=int)
    result = request.form.get('result', '')
    
    step = LeadWorkflowStep.query.get_or_404(step_id)
    lead_workflow = LeadWorkflow.query.get_or_404(step.lead_workflow_id)
    
    # Only allow executing pending steps in active workflows
    if step.status != 'pending' or lead_workflow.status != 'active':
        flash('This step cannot be executed.', 'danger')
        return redirect(url_for('view_lead_workflow', lead_workflow_id=lead_workflow.id))
    
    # Mark the step as completed
    step.status = 'completed'
    step.executed_date = datetime.utcnow()
    step.result = result
    
    # Create a communication record if applicable
    if step.workflow_step.step_type in ['Email', 'SMS', 'Call']:
        communication_type = {
            'Email': 'email',
            'SMS': 'sms',
            'Call': 'call'
        }.get(step.workflow_step.step_type)
        
        communication = Communication(
            lead_id=lead_workflow.lead_id,
            type=communication_type,
            direction='outbound',
            content=step.workflow_step.content,
            subject=step.workflow_step.subject if step.workflow_step.step_type == 'Email' else None,
            date=datetime.utcnow(),
            user_id=current_user.id if current_user.is_authenticated else None,
            notes=f"Automated from workflow: {lead_workflow.workflow_template.name}"
        )
        db.session.add(communication)
    
    # Check if this is the last step
    pending_steps = LeadWorkflowStep.query.filter_by(
        lead_workflow_id=lead_workflow.id,
        status='pending'
    ).count()
    
    if pending_steps == 0:
        lead_workflow.status = 'completed'
    
    db.session.commit()
    
    flash('Step executed successfully!', 'success')
    return redirect(url_for('view_lead_workflow', lead_workflow_id=lead_workflow.id))

@app.route('/workflow/skip_step', methods=['POST'])
def skip_workflow_step():
    """Skip a workflow step."""
    step_id = request.form.get('step_id', type=int)
    reason = request.form.get('reason', '')
    
    step = LeadWorkflowStep.query.get_or_404(step_id)
    lead_workflow = LeadWorkflow.query.get_or_404(step.lead_workflow_id)
    
    # Only allow skipping pending steps in active workflows
    if step.status != 'pending' or lead_workflow.status != 'active':
        flash('This step cannot be skipped.', 'danger')
        return redirect(url_for('view_lead_workflow', lead_workflow_id=lead_workflow.id))
    
    # Mark the step as skipped
    step.status = 'skipped'
    step.executed_date = datetime.utcnow()
    step.result = f"Skipped: {reason}"
    
    # Check if this is the last step
    pending_steps = LeadWorkflowStep.query.filter_by(
        lead_workflow_id=lead_workflow.id,
        status='pending'
    ).count()
    
    if pending_steps == 0:
        lead_workflow.status = 'completed'
    
    db.session.commit()
    
    flash('Step skipped successfully!', 'success')
    return redirect(url_for('view_lead_workflow', lead_workflow_id=lead_workflow.id))

@app.route('/workflow/process_due_steps')
def process_due_workflow_steps():
    """Process all due workflow steps (would be called by a scheduler in production)."""
    now = datetime.utcnow()
    
    # Find all pending steps that are due
    due_steps = LeadWorkflowStep.query.join(
        LeadWorkflow, LeadWorkflowStep.lead_workflow_id == LeadWorkflow.id
    ).filter(
        LeadWorkflowStep.status == 'pending',
        LeadWorkflow.status == 'active',
        LeadWorkflowStep.scheduled_date <= now
    ).all()
    
    processed_count = 0
    email_count = 0
    sms_count = 0
    
    for step in due_steps:
        # Get the workflow step details
        workflow_step = WorkflowStep.query.get(step.workflow_step_id)
        
        # Get the lead workflow
        lead_workflow = LeadWorkflow.query.get(step.lead_workflow_id)
        
        # Get the lead
        lead = Lead.query.get(lead_workflow.lead_id)
        
        # Get the workflow template
        workflow = WorkflowTemplate.query.get(lead_workflow.workflow_template_id)
        
        # Process based on step type
        if workflow_step.step_type == 'Email':
            # In a real app, this would send an actual email
            print(f"Would send email to {lead.email} with subject: {workflow_step.subject}")
            
            # For demo purposes, just log it
            email_count += 1
            
            # Mark step as completed
            step.status = 'completed'
            step.completed_date = now
            
        elif workflow_step.step_type == 'SMS':
            # In a real app, this would send an actual SMS
            print(f"Would send SMS to {lead.phone} with message: {workflow_step.content}")
            
            # For demo purposes, just log it
            sms_count += 1
            
            # Mark step as completed
            step.status = 'completed'
            step.completed_date = now
            
        elif workflow_step.step_type in ['Call', 'Task']:
            # These require manual action, so we'll create notifications
            # but not mark them as completed
            
            # Create a notification for this due step
            try:
                from app.routes.workflow_notifications import create_notification
                
                notification_title = f"{workflow_step.step_type} Due: {workflow.name}"
                notification_message = f"A {workflow_step.step_type.lower()} is due for lead {lead.first_name} {lead.last_name} as part of the '{workflow.name}' workflow."
                
                if workflow_step.step_type == 'Call':
                    notification_message += f" Phone: {lead.phone}"
                
                notification_link = url_for('upcoming_workflow_steps')
                
                create_notification(
                    title=notification_title,
                    message=notification_message,
                    notification_type='step_due',
                    link=notification_link,
                    lead_id=lead.id,
                    workflow_template_id=workflow.id,
                    lead_workflow_id=lead_workflow.id,
                    lead_workflow_step_id=step.id
                )
            except Exception as e:
                print(f"Error creating notification: {e}")
        
        processed_count += 1
    
    db.session.commit()
    
    # Find steps coming up in the next day and create notifications
    tomorrow = now + timedelta(days=1)
    
    upcoming_steps = LeadWorkflowStep.query.join(
        LeadWorkflow, LeadWorkflowStep.lead_workflow_id == LeadWorkflow.id
    ).filter(
        LeadWorkflowStep.status == 'pending',
        LeadWorkflow.status == 'active',
        LeadWorkflowStep.scheduled_date > now,
        LeadWorkflowStep.scheduled_date <= tomorrow
    ).all()
    
    upcoming_count = 0
    
    for step in upcoming_steps:
        # Get the workflow step details
        workflow_step = WorkflowStep.query.get(step.workflow_step_id)
        
        # Get the lead workflow
        lead_workflow = LeadWorkflow.query.get(step.lead_workflow_id)
        
        # Get the lead
        lead = Lead.query.get(lead_workflow.lead_id)
        
        # Get the workflow template
        workflow = WorkflowTemplate.query.get(lead_workflow.workflow_template_id)
        
        # Create a notification for this upcoming step
        try:
            from app.routes.workflow_notifications import create_notification
            
            notification_title = f"Upcoming {workflow_step.step_type}: {workflow.name}"
            notification_message = f"A {workflow_step.step_type.lower()} is scheduled for tomorrow for lead {lead.first_name} {lead.last_name} as part of the '{workflow.name}' workflow."
            notification_link = url_for('upcoming_workflow_steps')
            
            create_notification(
                title=notification_title,
                message=notification_message,
                notification_type='upcoming_step',
                link=notification_link,
                lead_id=lead.id,
                workflow_template_id=workflow.id,
                lead_workflow_id=lead_workflow.id,
                lead_workflow_step_id=step.id
            )
            
            upcoming_count += 1
        except Exception as e:
            print(f"Error creating notification: {e}")
    
    db.session.commit()
    
    # Check for completed workflows
    completed_workflows = LeadWorkflow.query.filter_by(status='active').all()
    completed_count = 0
    
    for workflow in completed_workflows:
        # Check if all steps are completed
        pending_steps = LeadWorkflowStep.query.filter_by(
            lead_workflow_id=workflow.id,
            status='pending'
        ).count()
        
        if pending_steps == 0:
            # All steps are completed, mark workflow as completed
            workflow.status = 'completed'
            workflow.end_date = now
            
            # Get the lead and workflow template
            lead = Lead.query.get(workflow.lead_id)
            template = WorkflowTemplate.query.get(workflow.workflow_template_id)
            
            # Create a notification for completed workflow
            try:
                from app.routes.workflow_notifications import create_notification
                
                notification_title = f"Workflow Completed: {template.name}"
                notification_message = f"The workflow '{template.name}' for lead {lead.first_name} {lead.last_name} has been completed successfully."
                notification_link = url_for('view_lead_workflow', lead_workflow_id=workflow.id)
                
                create_notification(
                    title=notification_title,
                    message=notification_message,
                    notification_type='workflow_complete',
                    link=notification_link,
                    lead_id=lead.id,
                    workflow_template_id=template.id,
                    lead_workflow_id=workflow.id
                )
                
                completed_count += 1
            except Exception as e:
                print(f"Error creating notification: {e}")
    
    db.session.commit()
    
    message = f"Processed {processed_count} due steps ({email_count} emails, {sms_count} SMS). "
    message += f"Created notifications for {upcoming_count} upcoming steps. "
    message += f"Completed {completed_count} workflows."
    
    flash(message, 'success')
    
    return redirect(url_for('workflows'))

@app.route('/workflow/pause')
def pause_lead_workflow():
    """Pause a lead workflow."""
    lead_workflow_id = request.args.get('id', type=int)
    lead_workflow = LeadWorkflow.query.get_or_404(lead_workflow_id)
    
    lead_workflow.status = 'paused'
    db.session.commit()
    
    flash('Workflow paused successfully!', 'success')
    return redirect(url_for('view_workflow', workflow_id=lead_workflow.workflow_template_id))

@app.route('/workflow/resume')
def resume_lead_workflow():
    """Resume a paused lead workflow."""
    lead_workflow_id = request.args.get('id', type=int)
    lead_workflow = LeadWorkflow.query.get_or_404(lead_workflow_id)
    
    lead_workflow.status = 'active'
    db.session.commit()
    
    flash('Workflow resumed successfully!', 'success')
    return redirect(url_for('view_workflow', workflow_id=lead_workflow.workflow_template_id))

@app.route('/workflow/cancel')
def cancel_lead_workflow():
    """Cancel a lead workflow."""
    lead_workflow_id = request.args.get('id', type=int)
    lead_workflow = LeadWorkflow.query.get_or_404(lead_workflow_id)
    
    lead_workflow.status = 'cancelled'
    
    # Mark all pending steps as cancelled
    pending_steps = LeadWorkflowStep.query.filter_by(
        lead_workflow_id=lead_workflow_id,
        status='pending'
    ).all()
    
    for step in pending_steps:
        step.status = 'cancelled'
    
    db.session.commit()
    
    flash('Workflow cancelled successfully!', 'success')
    return redirect(url_for('view_workflow', workflow_id=lead_workflow.workflow_template_id))

@app.route('/workflow/lead/<int:lead_workflow_id>')
def view_lead_workflow(lead_workflow_id):
    """View the progress of a specific lead workflow."""
    lead_workflow = LeadWorkflow.query.get_or_404(lead_workflow_id)
    
    # Get all steps for this lead workflow
    steps = LeadWorkflowStep.query.filter_by(
        lead_workflow_id=lead_workflow_id
    ).order_by(LeadWorkflowStep.scheduled_date).all()
    
    return render_template('workflows/lead_workflow.html',
                           lead_workflow=lead_workflow,
                           steps=steps)

@app.route('/workflow/analytics')
def workflow_analytics():
    """Display analytics and metrics for workflows."""
    time_range = request.args.get('time_range', 'month')
    
    # Calculate date range based on selected time range
    today = datetime.utcnow()
    if time_range == 'week':
        start_date = today - timedelta(days=7)
        date_format = '%a'  # Day of week abbreviation
    elif time_range == 'month':
        start_date = today - timedelta(days=30)
        date_format = '%d %b'  # Day and month abbreviation
    elif time_range == 'quarter':
        start_date = today - timedelta(days=90)
        date_format = '%b'  # Month abbreviation
    elif time_range == 'year':
        start_date = today - timedelta(days=365)
        date_format = '%b %Y'  # Month and year
    else:
        start_date = today - timedelta(days=30)
        date_format = '%d %b'
    
    # Get all lead workflows
    all_workflows = LeadWorkflow.query.all()
    total_workflows = len(all_workflows)
    
    # Count workflows by status
    active_count = LeadWorkflow.query.filter_by(status='active').count()
    completed_count = LeadWorkflow.query.filter_by(status='completed').count()
    
    # Calculate completion rate
    completion_rate = 0
    if total_workflows > 0:
        completion_rate = round((completed_count / total_workflows) * 100, 1)
    
    # Count steps by status
    completed_steps = LeadWorkflowStep.query.filter_by(status='completed').count()
    pending_steps = LeadWorkflowStep.query.filter_by(status='pending').count()
    skipped_steps = LeadWorkflowStep.query.filter_by(status='skipped').count()
    
    # Get step types distribution
    email_steps = LeadWorkflowStep.query.join(WorkflowStep).filter(WorkflowStep.step_type == 'Email').count()
    sms_steps = LeadWorkflowStep.query.join(WorkflowStep).filter(WorkflowStep.step_type == 'SMS').count()
    call_steps = LeadWorkflowStep.query.join(WorkflowStep).filter(WorkflowStep.step_type == 'Call').count()
    task_steps = LeadWorkflowStep.query.join(WorkflowStep).filter(WorkflowStep.step_type == 'Task').count()
    step_types_data = [email_steps, sms_steps, call_steps, task_steps]
    
    # Generate data for the workflow performance chart
    date_labels = []
    completed_data = []
    started_data = []
    
    # Generate date labels and initialize data arrays
    if time_range == 'week':
        # For a week, show each day
        for i in range(7):
            date = today - timedelta(days=6-i)
            date_labels.append(date.strftime(date_format))
            
            # Count workflows started on this day
            started = LeadWorkflow.query.filter(
                func.date(LeadWorkflow.start_date) == func.date(date)
            ).count()
            started_data.append(started)
            
            # Count workflows completed on this day
            completed = LeadWorkflow.query.filter(
                LeadWorkflow.status == 'completed',
                func.date(LeadWorkflow.end_date) == func.date(date)
            ).count()
            completed_data.append(completed)
    
    elif time_range == 'month':
        # For a month, group by every 3 days
        for i in range(0, 30, 3):
            date = today - timedelta(days=29-i)
            end_date = date + timedelta(days=2)
            date_labels.append(f"{date.strftime('%d')}-{end_date.strftime('%d')} {date.strftime('%b')}")
            
            # Count workflows started in this period
            started = LeadWorkflow.query.filter(
                LeadWorkflow.start_date >= date,
                LeadWorkflow.start_date <= end_date
            ).count()
            started_data.append(started)
            
            # Count workflows completed in this period
            completed = LeadWorkflow.query.filter(
                LeadWorkflow.status == 'completed',
                LeadWorkflow.end_date >= date,
                LeadWorkflow.end_date <= end_date
            ).count()
            completed_data.append(completed)
    
    elif time_range == 'quarter':
        # For a quarter, group by weeks
        for i in range(0, 90, 7):
            date = today - timedelta(days=89-i)
            end_date = date + timedelta(days=6)
            date_labels.append(f"{date.strftime('%d %b')}-{end_date.strftime('%d %b')}")
            
            # Count workflows started in this period
            started = LeadWorkflow.query.filter(
                LeadWorkflow.start_date >= date,
                LeadWorkflow.start_date <= end_date
            ).count()
            started_data.append(started)
            
            # Count workflows completed in this period
            completed = LeadWorkflow.query.filter(
                LeadWorkflow.status == 'completed',
                LeadWorkflow.end_date >= date,
                LeadWorkflow.end_date <= end_date
            ).count()
            completed_data.append(completed)
    
    elif time_range == 'year':
        # For a year, group by months
        for i in range(12):
            date = today.replace(day=1) - relativedelta(months=11-i)
            end_date = (date + relativedelta(months=1)) - timedelta(days=1)
            date_labels.append(date.strftime('%b %Y'))
            
            # Count workflows started in this period
            started = LeadWorkflow.query.filter(
                LeadWorkflow.start_date >= date,
                LeadWorkflow.start_date <= end_date
            ).count()
            started_data.append(started)
            
            # Count workflows completed in this period
            completed = LeadWorkflow.query.filter(
                LeadWorkflow.status == 'completed',
                LeadWorkflow.end_date >= date,
                LeadWorkflow.end_date <= end_date
            ).count()
            completed_data.append(completed)
    
    # Get top performing workflows
    top_workflows = []
    workflow_templates = WorkflowTemplate.query.all()
    
    for template in workflow_templates:
        # Get all lead workflows for this template
        lead_workflows = LeadWorkflow.query.filter_by(workflow_template_id=template.id).all()
        total = len(lead_workflows)
        
        if total > 0:
            # Calculate completion rate
            completed = len([lw for lw in lead_workflows if lw.status == 'completed'])
            completion_rate = round((completed / total) * 100, 1) if total > 0 else 0
            
            # Calculate average completion time for completed workflows
            completed_workflows = [lw for lw in lead_workflows if lw.status == 'completed' and lw.end_date is not None]
            total_days = 0
            for lw in completed_workflows:
                delta = lw.end_date - lw.start_date
                total_days += delta.days
            
            avg_completion_time = round(total_days / len(completed_workflows), 1) if completed_workflows else 0
            
            # Count active leads
            active_leads = LeadWorkflow.query.filter_by(
                workflow_template_id=template.id, 
                status='active'
            ).count()
            
            top_workflows.append({
                'id': template.id,
                'name': template.name,
                'completion_rate': completion_rate,
                'avg_completion_time': avg_completion_time,
                'active_leads': active_leads
            })
    
    # Sort workflows by completion rate (descending)
    top_workflows = sorted(top_workflows, key=lambda x: x['completion_rate'], reverse=True)[:5]
    
    # Get recent workflow activity
    recent_activities = []
    
    # Get recently completed steps
    recent_steps = LeadWorkflowStep.query.filter(
        LeadWorkflowStep.status.in_(['completed', 'skipped']),
        LeadWorkflowStep.executed_date is not None
    ).order_by(LeadWorkflowStep.executed_date.desc()).limit(10).all()
    
    for step in recent_steps:
        lead_workflow = LeadWorkflow.query.get(step.lead_workflow_id)
        lead = Lead.query.get(lead_workflow.lead_id)
        workflow = WorkflowTemplate.query.get(lead_workflow.workflow_template_id)
        workflow_step = WorkflowStep.query.get(step.workflow_step_id)
        
        action = f"{step.status.capitalize()} step: {workflow_step.step_type}"
        
        recent_activities.append({
            'date': step.executed_date,
            'lead_id': lead.id,
            'lead_name': f"{lead.first_name} {lead.last_name}",
            'workflow_id': workflow.id,
            'workflow_name': workflow.name,
            'action': action
        })
    
    # Get recently started/completed/cancelled workflows
    recent_workflows = LeadWorkflow.query.filter(
        LeadWorkflow.status.in_(['completed', 'cancelled']),
        LeadWorkflow.end_date is not None
    ).order_by(LeadWorkflow.end_date.desc()).limit(5).all()
    
    for lw in recent_workflows:
        lead = Lead.query.get(lw.lead_id)
        workflow = WorkflowTemplate.query.get(lw.workflow_template_id)
        
        action = f"Workflow {lw.status}"
        
        recent_activities.append({
            'date': lw.end_date,
            'lead_id': lead.id,
            'lead_name': f"{lead.first_name} {lead.last_name}",
            'workflow_id': workflow.id,
            'workflow_name': workflow.name,
            'action': action
        })
    
    # Sort recent activities by date (descending)
    recent_activities = sorted(recent_activities, key=lambda x: x['date'], reverse=True)[:10]
    
    return render_template('workflows/analytics.html',
                          completion_rate=completion_rate,
                          active_count=active_count,
                          completed_steps=completed_steps,
                          pending_steps=pending_steps,
                          date_labels=date_labels,
                          completed_data=completed_data,
                          started_data=started_data,
                          step_types_data=step_types_data,
                          top_workflows=top_workflows,
                          recent_activities=recent_activities,
                          time_range=time_range)

@app.route('/workflow/lead/update_status', methods=['POST'])
def update_lead_status_workflow():
    """Update a lead's status."""
    lead_id = request.form.get('lead_id', type=int)
    new_status = request.form.get('status')
    
    if not lead_id or not new_status:
        flash('Invalid request. Lead ID and status are required.', 'danger')
        return redirect(url_for('leads'))
    
    lead = Lead.query.get_or_404(lead_id)
    old_status = lead.status
    lead.status = new_status
    lead.status_updated_at = datetime.utcnow()
    db.session.commit()
    
    # Check for workflows that should be automatically applied
    applied_workflows = []
    if old_status != new_status:
        auto_workflows = WorkflowTemplate.query.filter_by(
            trigger_status=new_status,
            auto_apply=True,
            is_active=True
        ).all()
        
        for workflow in auto_workflows:
            # Check if this lead already has this workflow active
            existing_workflow = LeadWorkflow.query.filter_by(
                lead_id=lead_id,
                workflow_template_id=workflow.id,
                status='active'
            ).first()
            
            if not existing_workflow:
                # Create a new lead workflow
                lead_workflow = LeadWorkflow(
                    lead_id=lead_id,
                    workflow_template_id=workflow.id,
                    start_date=datetime.utcnow(),
                    status='active'
                )
                db.session.add(lead_workflow)
                db.session.flush()  # Get the lead workflow ID
                
                # Create steps for this lead workflow
                workflow_steps = WorkflowStep.query.filter_by(
                    workflow_template_id=workflow.id
                ).order_by(WorkflowStep.step_order).all()
                
                current_date = datetime.utcnow()
                
                for step in workflow_steps:
                    scheduled_date = current_date + timedelta(days=step.delay_days)
                    
                    lead_workflow_step = LeadWorkflowStep(
                        lead_workflow_id=lead_workflow.id,
                        workflow_step_id=step.id,
                        status='pending',
                        scheduled_date=scheduled_date
                    )
                    db.session.add(lead_workflow_step)
                    
                    current_date = scheduled_date
                
                db.session.commit()
                applied_workflows.append(workflow.name)
    
    flash(f'Lead status updated to {new_status}!', 'success')
    
    # Notify about auto-applied workflows
    if applied_workflows:
        workflow_names = ', '.join(applied_workflows)
        flash(f'The following workflows were automatically applied: {workflow_names}', 'info')
    
    return redirect(url_for('view_lead', lead_id=lead_id))

@app.route('/lead/update_status', methods=['POST'])
def update_lead_status_simple():
    """Update a lead's status."""
    lead_id = request.form.get('lead_id', type=int)
    new_status = request.form.get('status')
    
    if not lead_id or not new_status:
        flash('Invalid request. Lead ID and status are required.', 'danger')
        return redirect(url_for('leads'))
    
    lead = Lead.query.get_or_404(lead_id)
    old_status = lead.status
    lead.status = new_status
    lead.status_updated_at = datetime.utcnow()
    db.session.commit()
    
    # Check for workflows that should be automatically applied
    applied_workflows = []
    if old_status != new_status:
        auto_workflows = WorkflowTemplate.query.filter_by(
            trigger_status=new_status,
            auto_apply=True,
            is_active=True
        ).all()
        
        for workflow in auto_workflows:
            # Check if this lead already has this workflow active
            existing_workflow = LeadWorkflow.query.filter_by(
                lead_id=lead_id,
                workflow_template_id=workflow.id,
                status='active'
            ).first()
            
            if not existing_workflow:
                # Create a new lead workflow
                lead_workflow = LeadWorkflow(
                    lead_id=lead_id,
                    workflow_template_id=workflow.id,
                    start_date=datetime.utcnow(),
                    status='active'
                )
                db.session.add(lead_workflow)
                db.session.flush()  # Get the lead workflow ID
                
                # Create steps for this lead workflow
                workflow_steps = WorkflowStep.query.filter_by(
                    workflow_template_id=workflow.id
                ).order_by(WorkflowStep.step_order).all()
                
                current_date = datetime.utcnow()
                
                for step in workflow_steps:
                    scheduled_date = current_date + timedelta(days=step.delay_days)
                    
                    lead_workflow_step = LeadWorkflowStep(
                        lead_workflow_id=lead_workflow.id,
                        workflow_step_id=step.id,
                        status='pending',
                        scheduled_date=scheduled_date
                    )
                    db.session.add(lead_workflow_step)
                    
                    current_date = scheduled_date
                
                db.session.commit()
                applied_workflows.append(workflow.name)
    
    flash(f'Lead status updated to {new_status}!', 'success')
    
    # Notify about auto-applied workflows
    if applied_workflows:
        workflow_names = ', '.join(applied_workflows)
        flash(f'The following workflows were automatically applied: {workflow_names}', 'info')
    
    return redirect(url_for('view_lead', lead_id=lead_id))

@app.route('/workflow/upcoming', methods=['GET'])
def upcoming_workflow_steps():
    """Display upcoming workflow steps that need attention."""
    # Get time range for filtering
    time_range = request.args.get('time_range', 'today')
    
    # Calculate date ranges
    now = datetime.utcnow()
    today = now.date()
    tomorrow = today + timedelta(days=1)
    next_week = today + timedelta(days=7)
    
    if time_range == 'today':
        start_date = today
        end_date = tomorrow
        title = "Today's Tasks"
    elif time_range == 'tomorrow':
        start_date = tomorrow
        end_date = tomorrow + timedelta(days=1)
        title = "Tomorrow's Tasks"
    elif time_range == 'week':
        start_date = today
        end_date = next_week
        title = "This Week's Tasks"
    else:  # 'all' or any other value
        start_date = today
        end_date = None
        title = "All Upcoming Tasks"
    
    # Get all upcoming steps
    upcoming_steps = LeadWorkflowStep.query.join(LeadWorkflow).filter(
        LeadWorkflow.status == 'active',
        LeadWorkflowStep.status == 'pending',
        LeadWorkflowStep.scheduled_date >= start_date
    ).order_by(LeadWorkflowStep.scheduled_date).all()
    
    # Add lead and workflow data to each step
    for step in upcoming_steps:
        lead_workflow = LeadWorkflow.query.get(step.lead_workflow_id)
        lead = Lead.query.get(lead_workflow.lead_id)
        workflow = WorkflowTemplate.query.get(lead_workflow.workflow_template_id)
        
        step.lead = lead
        step.workflow = workflow
    
    return render_template('workflows/upcoming.html', 
                           upcoming_steps=upcoming_steps,
                           title=title,
                           current_user={'is_authenticated': True})

if __name__ == '__main__':
    # Ensure the upload folder exists
    os.makedirs(app.config.get('UPLOAD_FOLDER', 'temp'), exist_ok=True)
    app.run(debug=True, port=5001)

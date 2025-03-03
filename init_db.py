from app import create_app, db
from app.models import User, Lead, VehicleInterest, Communication, Appointment, EmailTemplate, SMSTemplate
from app.models.car import Car, CarImage, Match, UserPreference
from werkzeug.security import generate_password_hash

app = create_app()

with app.app_context():
    # Create all tables
    db.create_all()
    
    # Check if admin user exists
    admin = User.query.filter_by(username='admin').first()
    if not admin:
        # Create admin user
        admin = User(
            username='admin',
            email='admin@example.com',
            first_name='Admin',
            last_name='User',
            role='admin'
        )
        admin.set_password('admin123')  # Set a default password
        db.session.add(admin)
    
    # Create a BDC agent user if it doesn't exist
    agent = User.query.filter_by(username='bdcagent').first()
    if not agent:
        agent = User(
            username='bdcagent',
            email='bdc@example.com',
            first_name='BDC',
            last_name='Agent',
            role='bdc_agent'
        )
        agent.set_password('bdc123')  # Set a default password
        db.session.add(agent)
    
    # Create email templates if they don't exist
    if not EmailTemplate.query.first():
        welcome_template = EmailTemplate(
            name='Welcome Email',
            subject='Welcome to our Dealership!',
            body='Dear {first_name},\n\nThank you for your interest in our dealership. We look forward to helping you find your perfect vehicle.\n\nBest regards,\nThe Team at {dealership_name}',
            purpose='Initial Contact'
        )
        db.session.add(welcome_template)
        
        followup_template = EmailTemplate(
            name='Follow-up Email',
            subject='Following up on your recent inquiry',
            body='Dear {first_name},\n\nI wanted to follow up on your recent inquiry about {vehicle_interest}. Are you available for a test drive this week?\n\nBest regards,\n{agent_name}\n{dealership_name}',
            purpose='Follow-up'
        )
        db.session.add(followup_template)
        
        appointment_template = EmailTemplate(
            name='Appointment Confirmation',
            subject='Your appointment is confirmed',
            body='Dear {first_name},\n\nThis is to confirm your appointment on {appointment_date} at {appointment_time}. We look forward to seeing you!\n\nBest regards,\n{agent_name}\n{dealership_name}',
            purpose='Appointment Confirmation'
        )
        db.session.add(appointment_template)
    
    # Create SMS templates if they don't exist
    if not SMSTemplate.query.first():
        welcome_sms = SMSTemplate(
            name='Welcome SMS',
            body='Hi {first_name}, thanks for your interest in {dealership_name}! Let me know when you\'d like to schedule a visit.',
            purpose='Initial Contact'
        )
        db.session.add(welcome_sms)
        
        followup_sms = SMSTemplate(
            name='Follow-up SMS',
            body='Hi {first_name}, just following up on your interest in {vehicle_interest}. Available for a test drive this week?',
            purpose='Follow-up'
        )
        db.session.add(followup_sms)
        
        appointment_sms = SMSTemplate(
            name='Appointment Reminder',
            body='Reminder: Your appointment at {dealership_name} is tomorrow at {appointment_time}. See you then!',
            purpose='Appointment Reminder'
        )
        db.session.add(appointment_sms)
    
    # Commit all changes
    db.session.commit()
    
    print("Database initialized successfully with default data.")

if __name__ == '__main__':
    with app.app_context():
        # Create all tables
        db.create_all()

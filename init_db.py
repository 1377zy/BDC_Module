from app import create_app, db
from app.models import User, Lead, VehicleInterest, Communication, Appointment, EmailTemplate, SMSTemplate
from datetime import datetime, timedelta, time
from werkzeug.security import generate_password_hash
import random

def init_db():
    app = create_app()
    with app.app_context():
        # Create all tables
        db.create_all()
        
        # Create admin user if not exists
        if User.query.filter_by(username='admin').first() is None:
            user = User(username='admin', email='admin@example.com')
            user.set_password('admin123')
            db.session.add(user)
            db.session.commit()
            print("Admin user created")
        
        # Create email templates
        if EmailTemplate.query.count() == 0:
            templates = [
                {
                    'name': 'Initial Contact - New Lead',
                    'subject': 'Thank you for your interest in our dealership',
                    'body': '''Dear {first_name},

Thank you for your interest in our dealership. We're excited to help you find your perfect vehicle.

Would you prefer to schedule an appointment to discuss your needs in person? I'm available this week and would be happy to show you our inventory.

Please let me know what day and time would work best for you, or feel free to call me directly.

Looking forward to helping you!

Best regards,
{agent_name}
{dealership_name}
{dealership_phone}''',
                    'purpose': 'Initial Contact'
                },
                {
                    'name': 'Follow-up - No Response',
                    'subject': 'Following up on your vehicle inquiry',
                    'body': '''Dear {first_name},

I wanted to follow up on your recent inquiry about our vehicles. I haven't heard back from you and wanted to check if you're still interested or if you have any questions I can answer.

Our dealership currently has several special offers that might interest you. I'd be happy to provide more details or schedule a time for you to visit us.

Please let me know how I can help.

Best regards,
{agent_name}
{dealership_name}
{dealership_phone}''',
                    'purpose': 'Follow-up'
                },
                {
                    'name': 'Appointment Confirmation',
                    'subject': 'Your appointment is confirmed',
                    'body': '''Dear {first_name},

This email confirms your appointment at {dealership_name} on {appointment_date} at {appointment_time}.

During your visit, we'll discuss your vehicle preferences and requirements, and you'll have the opportunity to test drive vehicles that interest you.

Please bring your driver's license for test drives. If you're considering a trade-in, bringing your current vehicle's registration and any loan information would be helpful.

We're located at {dealership_address}. If you need directions or have any questions before your appointment, please don't hesitate to contact me.

I look forward to meeting you!

Best regards,
{agent_name}
{dealership_name}
{dealership_phone}''',
                    'purpose': 'Appointment Confirmation'
                },
                {
                    'name': 'Post-Visit Thank You',
                    'subject': 'Thank you for visiting our dealership',
                    'body': '''Dear {first_name},

Thank you for visiting {dealership_name} today. It was a pleasure meeting you and discussing your vehicle needs.

I hope you enjoyed your experience with us and found the {vehicle_of_interest} to your liking. If you have any additional questions about the vehicle or our financing options, please don't hesitate to reach out.

I'll be in touch soon to follow up, but feel free to contact me anytime if you'd like to schedule another test drive or discuss next steps.

Thank you again for your time!

Best regards,
{agent_name}
{dealership_name}
{dealership_phone}''',
                    'purpose': 'Thank You'
                }
            ]
            
            for template in templates:
                email_template = EmailTemplate(
                    name=template['name'],
                    subject=template['subject'],
                    body=template['body'],
                    purpose=template['purpose']
                )
                db.session.add(email_template)
            
            db.session.commit()
            print("Email templates created")
        
        # Create SMS templates
        if SMSTemplate.query.count() == 0:
            templates = [
                {
                    'name': 'Initial Contact',
                    'body': 'Hi {first_name}, this is {agent_name} from {dealership_name}. Thanks for your inquiry! When would be a good time to schedule a visit? Reply anytime!',
                    'purpose': 'Initial Contact'
                },
                {
                    'name': 'Follow-up',
                    'body': 'Hi {first_name}, following up on your recent inquiry. Still interested in the {vehicle}? I'm here to answer any questions!',
                    'purpose': 'Follow-up'
                },
                {
                    'name': 'Appointment Confirmation',
                    'body': 'Hi {first_name}, your appointment at {dealership_name} is confirmed for {date} at {time}. Reply Y to confirm or call to reschedule.',
                    'purpose': 'Appointment Confirmation'
                },
                {
                    'name': 'Appointment Reminder',
                    'body': 'Hi {first_name}, reminder: your appointment at {dealership_name} is tomorrow at {time}. We look forward to seeing you!',
                    'purpose': 'Appointment Reminder'
                },
                {
                    'name': 'Post-Visit',
                    'body': 'Hi {first_name}, thank you for visiting us today! How did you enjoy the {vehicle}? Let me know if you have any questions!',
                    'purpose': 'Thank You'
                }
            ]
            
            for template in templates:
                sms_template = SMSTemplate(
                    name=template['name'],
                    body=template['body'],
                    purpose=template['purpose']
                )
                db.session.add(sms_template)
            
            db.session.commit()
            print("SMS templates created")
            
        # Create sample leads if none exist
        if Lead.query.count() == 0:
            # Sample lead data
            sample_leads = [
                {'first_name': 'John', 'last_name': 'Smith', 'email': 'john.smith@example.com', 'phone': '5551234567', 'source': 'Website', 'status': 'New'},
                {'first_name': 'Emily', 'last_name': 'Johnson', 'email': 'emily.j@example.com', 'phone': '5552345678', 'source': 'Third Party', 'status': 'Contacted'},
                {'first_name': 'Michael', 'last_name': 'Williams', 'email': 'mwilliams@example.com', 'phone': '5553456789', 'source': 'Referral', 'status': 'Qualified'},
                {'first_name': 'Sarah', 'last_name': 'Brown', 'email': 'sarah.brown@example.com', 'phone': '5554567890', 'source': 'Walk-in', 'status': 'Appointment Set'},
                {'first_name': 'David', 'last_name': 'Miller', 'email': 'dmiller@example.com', 'phone': '5555678901', 'source': 'Website', 'status': 'Contacted'}
            ]
            
            # Vehicle interests
            vehicle_interests = [
                {'make': 'Toyota', 'model': 'Camry', 'year': 2023, 'new_or_used': 'New'},
                {'make': 'Honda', 'model': 'Accord', 'year': 2022, 'new_or_used': 'New'},
                {'make': 'Ford', 'model': 'F-150', 'year': 2021, 'new_or_used': 'Used'},
                {'make': 'Chevrolet', 'model': 'Silverado', 'year': 2023, 'new_or_used': 'New'},
                {'make': 'Tesla', 'model': 'Model 3', 'year': 2023, 'new_or_used': 'New'},
                {'make': 'BMW', 'model': 'X5', 'year': 2020, 'new_or_used': 'Used'},
                {'make': 'Nissan', 'model': 'Altima', 'year': 2022, 'new_or_used': 'New'}
            ]
            
            # Create leads and associated data
            for lead_data in sample_leads:
                lead = Lead(**lead_data)
                db.session.add(lead)
                db.session.flush()  # Get ID before commit
                
                # Add 1-2 vehicle interests
                for i in range(random.randint(1, 2)):
                    vi = random.choice(vehicle_interests)
                    vehicle_interest = VehicleInterest(
                        lead_id=lead.id,
                        make=vi['make'],
                        model=vi['model'],
                        year=vi['year'],
                        new_or_used=vi['new_or_used']
                    )
                    db.session.add(vehicle_interest)
                
                # Add some communications
                if lead.status in ['Contacted', 'Qualified', 'Appointment Set']:
                    # Add email communication
                    comm1 = Communication(
                        lead_id=lead.id,
                        type='Email',
                        direction='Outbound',
                        content=f"Hello {lead.first_name}, thank you for your interest in our dealership. We'd love to schedule a time for you to visit us.",
                        status='Sent',
                        sent_at=datetime.now() - timedelta(days=random.randint(1, 5))
                    )
                    db.session.add(comm1)
                    
                    # Add SMS communication
                    comm2 = Communication(
                        lead_id=lead.id,
                        type='SMS',
                        direction='Outbound',
                        content=f"Hi {lead.first_name}, this is Auto Dealership. When would be a good time to schedule a visit? Reply anytime!",
                        status='Sent',
                        sent_at=datetime.now() - timedelta(days=random.randint(1, 3))
                    )
                    db.session.add(comm2)
                
                # Add appointment if status is Appointment Set
                if lead.status == 'Appointment Set':
                    appointment_date = datetime.now().date() + timedelta(days=random.randint(1, 7))
                    appointment_time = time(hour=random.randint(9, 16), minute=0)
                    
                    appointment = Appointment(
                        lead_id=lead.id,
                        date=appointment_date,
                        time=appointment_time,
                        purpose='Test Drive',
                        status='Scheduled',
                        notes='Customer is interested in financing options.'
                    )
                    db.session.add(appointment)
            
            db.session.commit()
            print("Sample leads, vehicle interests, communications, and appointments created")
            
        print("Database initialization complete")

if __name__ == '__main__':
    init_db()

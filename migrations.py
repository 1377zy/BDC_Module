import os
import json
from datetime import datetime
from models import db, Lead, Appointment, Communication, Template, Followup, User, Setting
from werkzeug.security import generate_password_hash

def str_to_datetime(date_str):
    """Convert ISO format date string to datetime object"""
    if date_str and isinstance(date_str, str):
        return datetime.fromisoformat(date_str)
    return date_str

def migrate_json_to_db():
    """Migrate data from JSON files to SQLite database"""
    print("Starting migration from JSON files to database...")
    
    # Create a demo user if none exists
    if User.query.count() == 0:
        demo_user = User(
            username='demo_user',
            email='demo@example.com',
            first_name='Demo',
            last_name='User',
            role='admin',
            phone='(555) 123-4567',
            created_at=datetime.now(),
            last_login=datetime.now()
        )
        demo_user.set_password('password')
        db.session.add(demo_user)
        db.session.commit()
        print("Created demo user")
    
    # Migrate leads
    leads_file = 'data/leads.json'
    if os.path.exists(leads_file):
        try:
            with open(leads_file, 'r') as f:
                leads_data = json.load(f)
                
            for lead_data in leads_data:
                # Check if lead already exists
                existing_lead = Lead.query.filter_by(
                    first_name=lead_data.get('first_name', ''),
                    last_name=lead_data.get('last_name', ''),
                    email=lead_data.get('email', '')
                ).first()
                
                if not existing_lead:
                    lead = Lead(
                        id=lead_data.get('id'),
                        first_name=lead_data.get('first_name', ''),
                        last_name=lead_data.get('last_name', ''),
                        email=lead_data.get('email', ''),
                        phone=lead_data.get('phone', ''),
                        status=lead_data.get('status', 'New'),
                        vehicle_interest=lead_data.get('vehicle_interest', ''),
                        notes=lead_data.get('notes', ''),
                        created_at=str_to_datetime(lead_data.get('created_at')),
                        source=lead_data.get('source', 'Manual Entry'),
                        user_id=1  # Assign to demo user
                    )
                    db.session.add(lead)
            
            db.session.commit()
            print(f"Migrated {len(leads_data)} leads")
        except Exception as e:
            db.session.rollback()
            print(f"Error migrating leads: {str(e)}")
    
    # Migrate appointments
    # This would be similar to leads migration, but we'll need to ensure
    # the lead_id references exist in the database
    
    # Migrate settings from .env file
    env_file = '.env'
    if os.path.exists(env_file):
        try:
            with open(env_file, 'r') as f:
                lines = f.readlines()
            
            for line in lines:
                line = line.strip()
                if not line or line.startswith('#'):
                    continue
                
                if '=' in line:
                    key, value = line.split('=', 1)
                    key = key.strip()
                    value = value.strip()
                    
                    # Check if setting already exists
                    existing_setting = Setting.query.filter_by(key=key).first()
                    
                    # Determine if this is a sensitive setting
                    is_sensitive = 'PASSWORD' in key or 'TOKEN' in key or 'SECRET' in key
                    
                    # Determine category
                    category = 'general'
                    if 'MAIL' in key:
                        category = 'email'
                    elif 'TWILIO' in key:
                        category = 'sms'
                    elif 'DEALERSHIP' in key:
                        category = 'dealership'
                    elif 'SALESPERSON' in key:
                        category = 'salesperson'
                    
                    if not existing_setting:
                        setting = Setting(
                            key=key,
                            value=value,
                            category=category,
                            is_sensitive=is_sensitive
                        )
                        db.session.add(setting)
                    else:
                        existing_setting.value = value
                        existing_setting.category = category
                        existing_setting.is_sensitive = is_sensitive
            
            db.session.commit()
            print("Migrated settings from .env file")
        except Exception as e:
            db.session.rollback()
            print(f"Error migrating settings: {str(e)}")
    
    print("Migration completed")

if __name__ == '__main__':
    # This allows running this script directly for testing
    from app import app
    with app.app_context():
        migrate_json_to_db()

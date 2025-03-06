from datetime import datetime
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from app import db, login

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), index=True, unique=True)
    email = db.Column(db.String(120), index=True, unique=True)
    password_hash = db.Column(db.String(128))
    first_name = db.Column(db.String(64))
    last_name = db.Column(db.String(64))
    phone = db.Column(db.String(20))
    role = db.Column(db.String(20), default='bdc_agent')  # bdc_agent, manager, admin
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    leads = db.relationship('Lead', backref='assigned_to', lazy='dynamic')
    appointments = db.relationship('Appointment', backref='scheduled_by', lazy='dynamic')
    communications = db.relationship('Communication', backref='sent_by', lazy='dynamic')
    
    # Car preferences (for the car matching functionality)
    preferences = db.relationship('UserPreference', backref='user', uselist=False)
    car_matches = db.relationship('Match', backref='user', lazy='dynamic')
    
    def __repr__(self):
        return f'<User {self.username}>'
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
    
    def get_full_name(self):
        if self.first_name and self.last_name:
            return f"{self.first_name} {self.last_name}"
        return self.username

@login.user_loader
def load_user(id):
    return User.query.get(int(id))

class Lead(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    first_name = db.Column(db.String(64))
    last_name = db.Column(db.String(64))
    email = db.Column(db.String(120), index=True)
    phone = db.Column(db.String(20))
    source = db.Column(db.String(64))  # Website, Referral, Walk-in, etc.
    status = db.Column(db.String(64))  # New, Contacted, Qualified, Appointment Set, etc.
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    
    # Relationships
    communications = db.relationship('Communication', backref='lead', lazy='dynamic')
    appointments = db.relationship('Appointment', backref='lead', lazy='dynamic')
    vehicle_interests = db.relationship('VehicleInterest', backref='lead', lazy='dynamic')
    
    def __repr__(self):
        return f'<Lead {self.first_name} {self.last_name}>'

class VehicleInterest(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    lead_id = db.Column(db.Integer, db.ForeignKey('lead.id'))
    make = db.Column(db.String(64))
    model = db.Column(db.String(64))
    year = db.Column(db.Integer)
    new_or_used = db.Column(db.String(10))  # 'New' or 'Used'
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<VehicleInterest {self.make} {self.model} ({self.year})>'

class Communication(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    lead_id = db.Column(db.Integer, db.ForeignKey('lead.id'))
    type = db.Column(db.String(20))  # Email or SMS
    direction = db.Column(db.String(10))  # Inbound or Outbound
    content = db.Column(db.Text)
    status = db.Column(db.String(20))  # Sent, Delivered, Read, Failed
    sent_at = db.Column(db.DateTime, default=datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    
    def __repr__(self):
        return f'<Communication {self.type} to Lead {self.lead_id}>'

class Appointment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    lead_id = db.Column(db.Integer, db.ForeignKey('lead.id'))
    date = db.Column(db.Date)
    time = db.Column(db.Time)
    purpose = db.Column(db.String(64))  # Test Drive, Sales Consultation, Service, etc.
    status = db.Column(db.String(20))  # Scheduled, Confirmed, Completed, No-Show, Rescheduled, Cancelled
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    
    def __repr__(self):
        return f'<Appointment with Lead {self.lead_id} on {self.date} at {self.time}>'

class EmailTemplate(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), unique=True)
    subject = db.Column(db.String(128))
    body = db.Column(db.Text)
    purpose = db.Column(db.String(64))  # Initial Contact, Follow-up, Appointment Confirmation, etc.
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f'<EmailTemplate {self.name}>'

class SMSTemplate(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), unique=True)
    body = db.Column(db.String(160))  # Standard SMS length
    purpose = db.Column(db.String(64))  # Initial Contact, Follow-up, Appointment Confirmation, etc.
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f'<SMSTemplate {self.name}>'

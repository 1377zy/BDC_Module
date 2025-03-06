from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash

db = SQLAlchemy()

class User(db.Model):
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    first_name = db.Column(db.String(64))
    last_name = db.Column(db.String(64))
    role = db.Column(db.String(20), default='user')  # admin, manager, user
    phone = db.Column(db.String(20))
    created_at = db.Column(db.DateTime, default=datetime.now)
    last_login = db.Column(db.DateTime)
    profile_image = db.Column(db.String(256), default='/static/img/default-profile.png')
    is_active = db.Column(db.Boolean, default=True)
    
    # Relationships
    leads = db.relationship('Lead', backref='assigned_to', lazy='dynamic')
    appointments = db.relationship('Appointment', backref='created_by', lazy='dynamic')
    communications = db.relationship('Communication', backref='sent_by', lazy='dynamic')
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
        
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
    
    def __repr__(self):
        return f'<User {self.username}>'

class Lead(db.Model):
    __tablename__ = 'leads'
    
    id = db.Column(db.Integer, primary_key=True)
    first_name = db.Column(db.String(64), nullable=False)
    last_name = db.Column(db.String(64), nullable=False)
    email = db.Column(db.String(120))
    phone = db.Column(db.String(20))
    status = db.Column(db.String(20), default='New')  # New, Hot, Warm, Cold, Sold, Dead
    vehicle_interest = db.Column(db.String(120))
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.now)
    updated_at = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now)
    source = db.Column(db.String(64))  # Website, Referral, Walk-in, etc.
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    
    # Relationships
    appointments = db.relationship('Appointment', backref='lead', lazy='dynamic', cascade='all, delete-orphan')
    communications = db.relationship('Communication', backref='lead', lazy='dynamic', cascade='all, delete-orphan')
    followups = db.relationship('Followup', backref='lead', lazy='dynamic', cascade='all, delete-orphan')
    
    def __repr__(self):
        return f'<Lead {self.first_name} {self.last_name}>'

class Appointment(db.Model):
    __tablename__ = 'appointments'
    
    id = db.Column(db.Integer, primary_key=True)
    lead_id = db.Column(db.Integer, db.ForeignKey('leads.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    date = db.Column(db.Date, nullable=False)
    time = db.Column(db.Time, nullable=False)
    purpose = db.Column(db.String(120))  # Test Drive, Sales Consultation, etc.
    status = db.Column(db.String(20), default='Scheduled')  # Scheduled, Completed, No-Show, Cancelled
    notes = db.Column(db.Text)
    vehicle_interest = db.Column(db.String(120))
    created_at = db.Column(db.DateTime, default=datetime.now)
    updated_at = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now)
    
    def __repr__(self):
        return f'<Appointment {self.date} {self.time} for Lead {self.lead_id}>'

class Communication(db.Model):
    __tablename__ = 'communications'
    
    id = db.Column(db.Integer, primary_key=True)
    lead_id = db.Column(db.Integer, db.ForeignKey('leads.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    type = db.Column(db.String(20), nullable=False)  # Email, SMS, Call
    content = db.Column(db.Text)
    subject = db.Column(db.String(120))  # For emails
    duration = db.Column(db.Integer)  # For calls, in seconds
    call_outcome = db.Column(db.String(64))  # For calls
    sent_at = db.Column(db.DateTime, default=datetime.now)
    status = db.Column(db.String(20), default='Sent')  # Sent, Delivered, Failed
    
    def __repr__(self):
        return f'<Communication {self.type} to Lead {self.lead_id}>'

class Template(db.Model):
    __tablename__ = 'templates'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), nullable=False)
    type = db.Column(db.String(20), nullable=False)  # Email, SMS
    subject = db.Column(db.String(120))  # For email templates
    content = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.now)
    updated_at = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))  # Creator of the template
    
    def __repr__(self):
        return f'<Template {self.name} ({self.type})>'

class Followup(db.Model):
    __tablename__ = 'followups'
    
    id = db.Column(db.Integer, primary_key=True)
    lead_id = db.Column(db.Integer, db.ForeignKey('leads.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    scheduled_date = db.Column(db.Date, nullable=False)
    scheduled_time = db.Column(db.Time, nullable=False)
    type = db.Column(db.String(20), nullable=False)  # Call, Email, SMS
    notes = db.Column(db.Text)
    status = db.Column(db.String(20), default='Pending')  # Pending, Completed, Missed
    priority = db.Column(db.String(20), default='Medium')  # High, Medium, Low
    created_at = db.Column(db.DateTime, default=datetime.now)
    
    def __repr__(self):
        return f'<Followup {self.type} for Lead {self.lead_id}>'

class Setting(db.Model):
    __tablename__ = 'settings'
    
    id = db.Column(db.Integer, primary_key=True)
    key = db.Column(db.String(64), unique=True, nullable=False)
    value = db.Column(db.Text)
    category = db.Column(db.String(64))  # email, sms, dealership, etc.
    is_sensitive = db.Column(db.Boolean, default=False)  # For passwords, tokens, etc.
    updated_at = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now)
    
    def __repr__(self):
        return f'<Setting {self.key}>'

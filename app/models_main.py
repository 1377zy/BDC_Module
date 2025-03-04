from datetime import datetime, timedelta
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from app import db, login
import jwt
from flask import current_app
from app.models.car import UserPreference

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
    is_active = db.Column(db.Boolean, default=True)
    last_login = db.Column(db.DateTime)
    
    # Relationships
    leads = db.relationship('Lead', backref='assigned_to', lazy='dynamic', foreign_keys='Lead.assigned_to_id')
    appointments = db.relationship('Appointment', backref='scheduled_by', lazy='dynamic', foreign_keys='Appointment.scheduled_by_id')
    communications = db.relationship('Communication', backref='sent_by', lazy='dynamic', foreign_keys='Communication.sent_by_id')
    
    # Car preferences (for the car matching functionality)
    preferences = db.relationship('UserPreference', backref='user', uselist=False)
    car_matches = db.relationship('Match', backref='user', lazy='dynamic', foreign_keys='Match.user_id')
    
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
    
    def get_reset_password_token(self, expires_in=600):
        return jwt.encode(
            {'reset_password': self.id, 'exp': datetime.utcnow() + timedelta(seconds=expires_in)},
            current_app.config['SECRET_KEY'], algorithm='HS256')
    
    @staticmethod
    def verify_reset_password_token(token):
        try:
            id = jwt.decode(token, current_app.config['SECRET_KEY'], algorithms=['HS256'])['reset_password']
        except:
            return None
        return User.query.get(id)

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
    assigned_to_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    
    # Relationships
    communications = db.relationship('Communication', backref='lead', lazy='dynamic')
    appointments = db.relationship('Appointment', backref='lead', lazy='dynamic')
    vehicle_interests = db.relationship('VehicleInterest', backref='lead', lazy='dynamic')
    matches = db.relationship('Match', backref='lead', lazy='dynamic')
    
    def __repr__(self):
        return f'<Lead {self.first_name} {self.last_name}>'

class VehicleInterest(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    lead_id = db.Column(db.Integer, db.ForeignKey('lead.id'))
    make = db.Column(db.String(64))
    model = db.Column(db.String(64))
    year = db.Column(db.Integer)
    trim = db.Column(db.String(64))
    body_style = db.Column(db.String(64))  # SUV, Sedan, Truck, etc.
    color_exterior = db.Column(db.String(64))
    color_interior = db.Column(db.String(64))
    engine = db.Column(db.String(64))  # e.g. "2.0L Turbo", "V6 3.5L"
    transmission = db.Column(db.String(64))  # e.g. "Automatic", "Manual", "CVT"
    drivetrain = db.Column(db.String(64))  # e.g. "FWD", "AWD", "4WD", "RWD"
    fuel_type = db.Column(db.String(64))  # e.g. "Gasoline", "Diesel", "Hybrid", "Electric"
    new_or_used = db.Column(db.String(10))  # 'New' or 'Used'
    mileage = db.Column(db.Integer)  # For used vehicles
    features = db.Column(db.Text)  # Comma-separated list of features
    price_min = db.Column(db.Float)  # Minimum price range
    price_max = db.Column(db.Float)  # Maximum price range
    priority = db.Column(db.Integer, default=1)  # 1 = primary interest, 2 = secondary, etc.
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<VehicleInterest {self.make} {self.model} ({self.year})>'

class Communication(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    lead_id = db.Column(db.Integer, db.ForeignKey('lead.id'))
    sent_by_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    type = db.Column(db.String(20))  # Email or SMS
    direction = db.Column(db.String(10))  # Inbound or Outbound
    content = db.Column(db.Text)
    status = db.Column(db.String(20))  # Sent, Delivered, Read, Failed
    sent_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<Communication {self.type} to Lead {self.lead_id}>'

class Appointment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    lead_id = db.Column(db.Integer, db.ForeignKey('lead.id'))
    scheduled_by_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    date = db.Column(db.Date)
    time = db.Column(db.Time)
    purpose = db.Column(db.String(64))  # Test Drive, Sales Consultation, Service, etc.
    status = db.Column(db.String(20))  # Scheduled, Confirmed, Completed, No-Show, Rescheduled, Cancelled
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
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

class Inventory(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    stock_number = db.Column(db.String(64), unique=True)  # Replaces VIN
    make = db.Column(db.String(64))
    model = db.Column(db.String(64))
    year = db.Column(db.Integer)
    trim = db.Column(db.String(64))
    body_style = db.Column(db.String(64))
    color_exterior = db.Column(db.String(64))
    color_interior = db.Column(db.String(64))
    engine = db.Column(db.String(64))
    transmission = db.Column(db.String(64))
    drivetrain = db.Column(db.String(64))
    fuel_type = db.Column(db.String(64))
    new_or_used = db.Column(db.String(10))
    mileage = db.Column(db.Integer)
    features = db.Column(db.Text)
    invoice_price = db.Column(db.Float)  # Dealer's cost
    msrp = db.Column(db.Float)  # Manufacturer's suggested retail price
    sale_price = db.Column(db.Float)  # Actual selling price
    status = db.Column(db.String(20))  # Available, Sold, On Hold, In Transit, etc.
    location = db.Column(db.String(64))  # Lot location or storage area
    days_in_inventory = db.Column(db.Integer, default=0)
    description = db.Column(db.Text)
    image_urls = db.Column(db.Text)  # Comma-separated list of image URLs
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    matches = db.relationship('Match', backref='vehicle', lazy='dynamic')
    
    def __repr__(self):
        return f'<Inventory {self.stock_number} - {self.year} {self.make} {self.model}>'

class Match(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    lead_id = db.Column(db.Integer, db.ForeignKey('lead.id'))
    inventory_id = db.Column(db.Integer, db.ForeignKey('inventory.id'))
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))  # Who created the match
    match_score = db.Column(db.Float)  # 0-100 score of how well it matches
    status = db.Column(db.String(20))  # Suggested, Presented, Rejected, Interested
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f'<Match Lead:{self.lead_id} Vehicle:{self.inventory_id} Score:{self.match_score}>'

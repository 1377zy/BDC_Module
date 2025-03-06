# This file is maintained for backward compatibility
# All model definitions have been moved to models_main.py to avoid circular imports
# Any changes to models should be made in models_main.py

from datetime import datetime
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from app import db, login
import jinja2
import random

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
    saved_searches = db.relationship('SavedSearch', backref='user', lazy='dynamic')
    notification_settings = db.relationship('WorkflowNotificationSettings', backref='user', uselist=False)
    search_history = db.relationship('SearchHistory', backref='user', lazy='dynamic')
    created_pipelines = db.relationship('SalesPipeline', backref='creator', lazy=True)
    assigned_deals = db.relationship('Deal', foreign_keys='Deal.assigned_to_id', backref='assigned_to', lazy=True)
    created_deals = db.relationship('Deal', foreign_keys='Deal.created_by', backref='creator', lazy=True)
    deal_activities = db.relationship('DealActivity', backref='creator', lazy=True)
    stage_transitions = db.relationship('StageTransition', backref='creator', lazy=True)
    pipeline_filters = db.relationship('PipelineFilter', backref='user', lazy=True)
    created_campaigns = db.relationship('MarketingCampaign', backref='creator', lazy=True)
    
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

# Import all models from models_main.py
from app.models_main import *

# New models for inventory management
class Car(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    make = db.Column(db.String(64))
    model = db.Column(db.String(64))
    year = db.Column(db.Integer)
    trim = db.Column(db.String(64), nullable=True)
    color = db.Column(db.String(32), nullable=True)
    price = db.Column(db.Float)
    mileage = db.Column(db.Integer)
    vin = db.Column(db.String(17), unique=True)
    status = db.Column(db.String(20), default='Available')  # Available, Sold, On Hold, etc.
    description = db.Column(db.Text, nullable=True)
    features = db.Column(db.Text, nullable=True)
    new_or_used = db.Column(db.String(10), default='Used')  # New or Used
    body_style = db.Column(db.String(20), nullable=True)  # Sedan, SUV, Truck, etc.
    transmission = db.Column(db.String(20), nullable=True)  # Automatic, Manual, etc.
    fuel_type = db.Column(db.String(20), nullable=True)  # Gasoline, Diesel, Electric, etc.
    engine = db.Column(db.String(64), nullable=True)
    exterior_color = db.Column(db.String(32), nullable=True)
    interior_color = db.Column(db.String(32), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    images = db.relationship('CarImage', backref='car', lazy='dynamic', cascade='all, delete-orphan')
    interested_leads = db.relationship('VehicleInterest', backref='car', lazy='dynamic')
    appointments = db.relationship('Appointment', backref='car', lazy='dynamic')
    
    def __repr__(self):
        return f'<Car {self.year} {self.make} {self.model}>'
    
    def primary_image_url(self):
        primary = self.images.filter_by(is_primary=True).first()
        if primary:
            return primary.url
        # Return first image or default image
        first_image = self.images.first()
        if first_image:
            return first_image.url
        return '/static/img/no-car-image.jpg'
    
    def format_price(self):
        return "${:,.2f}".format(self.price)

class CarImage(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    car_id = db.Column(db.Integer, db.ForeignKey('car.id'))
    url = db.Column(db.String(255))
    is_primary = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<CarImage {self.id} for Car {self.car_id}>'

class Match(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    car_id = db.Column(db.Integer, db.ForeignKey('car.id'))
    lead_id = db.Column(db.Integer, db.ForeignKey('lead.id'), nullable=True)
    score = db.Column(db.Integer)  # Match score from 0-100
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    car = db.relationship('Car', backref='matches')
    lead = db.relationship('Lead', backref='matches')
    
    def __repr__(self):
        return f'<Match {self.id} Score: {self.score}>'

class UserPreference(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    preferred_makes = db.Column(db.String(255), nullable=True)  # Comma-separated list
    preferred_models = db.Column(db.String(255), nullable=True)  # Comma-separated list
    min_year = db.Column(db.Integer, nullable=True)
    max_year = db.Column(db.Integer, nullable=True)
    min_price = db.Column(db.Float, nullable=True)
    max_price = db.Column(db.Float, nullable=True)
    preferred_body_styles = db.Column(db.String(255), nullable=True)  # Comma-separated list
    preferred_colors = db.Column(db.String(255), nullable=True)  # Comma-separated list
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f'<UserPreference for User {self.user_id}>'

# Task management models
class Task(db.Model):
    """Task model for user assignments and follow-ups"""
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(128))
    description = db.Column(db.Text, nullable=True)
    status = db.Column(db.String(20), default='open')  # open, in_progress, completed, cancelled
    priority = db.Column(db.String(20), default='medium')  # low, medium, high, urgent
    due_date = db.Column(db.DateTime, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    completed_at = db.Column(db.DateTime, nullable=True)
    
    # Task assignment
    assigned_to_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    assigned_to = db.relationship('User', backref=db.backref('tasks', lazy='dynamic'))
    
    # Task can be related to various entities (lead, appointment, etc.)
    related_entity_type = db.Column(db.String(30), nullable=True)
    related_entity_id = db.Column(db.Integer, nullable=True)
    
    def __repr__(self):
        return f'<Task {self.title}>'
    
    def mark_completed(self):
        """Mark the task as completed"""
        self.status = 'completed'
        self.completed_at = datetime.utcnow()
        
        # If this is a lead-related task, update the lead's last activity
        if self.related_entity_type == 'lead':
            lead = Lead.query.get(self.related_entity_id)
            if lead:
                lead.last_activity_date = datetime.utcnow()
                
                # Add activity record
                activity = LeadActivity(
                    lead=lead,
                    activity_type='task_completed',
                    description=f'Task completed: {self.title}',
                    performed_by_id=self.assigned_to_id,
                    related_entity_type='task',
                    related_entity_id=self.id
                )
                db.session.add(activity)
                
                # Recalculate lead score
                lead.calculate_score()
                
                # Update lifecycle stage
                lead.update_lifecycle_stage()

class Lead(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    first_name = db.Column(db.String(64))
    last_name = db.Column(db.String(64))
    email = db.Column(db.String(120), index=True)
    phone = db.Column(db.String(20))
    source = db.Column(db.String(64))  # Website, Referral, Walk-in, etc.
    status = db.Column(db.String(64))  # New, Contacted, Qualified, Appointment Set, etc.
    notes = db.Column(db.Text)
    assigned_to_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    vehicle_interests = db.relationship('VehicleInterest', backref='lead', lazy='dynamic')
    communications = db.relationship('Communication', backref='lead', lazy='dynamic')
    appointments = db.relationship('Appointment', backref='lead', lazy='dynamic')
    score = db.Column(db.Integer, default=0)  # Lead score from 0-100
    last_activity_date = db.Column(db.DateTime, nullable=True)
    follow_up_date = db.Column(db.DateTime, nullable=True)
    follow_up_type = db.Column(db.String(20), nullable=True)  # email, call, text
    lifecycle_stage = db.Column(db.String(30), default='new')  # new, engaged, qualified, opportunity, customer, closed
    
    def __repr__(self):
        return f'<Lead {self.first_name} {self.last_name}>'
        
    def get_full_name(self):
        return f"{self.first_name} {self.last_name}"
        
    def calculate_score(self):
        """Calculate lead score based on various factors"""
        score = 0
        
        # Base score based on lead source
        source_scores = {
            'Website': 10,
            'Referral': 30,
            'Walk-in': 40,
            'Phone': 20,
            'Email': 15,
            'Social Media': 10,
            'Third Party': 5
        }
        score += source_scores.get(self.source, 0)
        
        # Add points for completeness of contact info
        if self.email:
            score += 10
        if self.phone:
            score += 10
            
        # Add points for vehicle interests
        interests_count = self.vehicle_interests.count()
        score += min(interests_count * 5, 15)  # Up to 15 points for interests
        
        # Add points for communication history
        comms_count = self.communications.count()
        score += min(comms_count * 2, 20)  # Up to 20 points for communications
        
        # Add points for appointments
        appointments_count = self.appointments.count()
        score += min(appointments_count * 10, 30)  # Up to 30 points for appointments
        
        # Recency factor - more recent leads get higher scores
        if self.last_activity_date:
            days_since_activity = (datetime.utcnow() - self.last_activity_date).days
            if days_since_activity < 1:
                score += 15
            elif days_since_activity < 3:
                score += 10
            elif days_since_activity < 7:
                score += 5
                
        # Cap the score at 100
        self.score = min(score, 100)
        return self.score
        
    def update_lifecycle_stage(self):
        """Update the lifecycle stage based on lead activity and status"""
        if self.status == 'Closed Won':
            self.lifecycle_stage = 'customer'
        elif self.status == 'Closed Lost':
            self.lifecycle_stage = 'closed'
        elif self.status == 'Appointment Set' or self.status == 'Appointment Confirmed':
            self.lifecycle_stage = 'opportunity'
        elif self.status == 'Qualified':
            self.lifecycle_stage = 'qualified'
        elif self.communications.count() > 0:
            self.lifecycle_stage = 'engaged'
        else:
            self.lifecycle_stage = 'new'
        
        return self.lifecycle_stage

class VehicleInterest(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    lead_id = db.Column(db.Integer, db.ForeignKey('lead.id'))
    make = db.Column(db.String(64))
    model = db.Column(db.String(64))
    year = db.Column(db.Integer)
    new_or_used = db.Column(db.String(10))  # 'New' or 'Used'
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Link to actual car if available
    car_id = db.Column(db.Integer, db.ForeignKey('car.id'), nullable=True)
    car = db.relationship('Car', backref=db.backref('interested_leads', lazy='dynamic'))
    
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
    
    # Link to car if appointment is for a specific car
    car_id = db.Column(db.Integer, db.ForeignKey('car.id'), nullable=True)
    car = db.relationship('Car', backref=db.backref('appointments', lazy='dynamic'))
    
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

class ScheduledReport(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64))
    report_type = db.Column(db.String(64))  # inventory, leads, sales, performance
    frequency = db.Column(db.String(20))  # daily, weekly, monthly
    day_of_week = db.Column(db.Integer, nullable=True)  # 0-6 (Monday-Sunday) for weekly reports
    day_of_month = db.Column(db.Integer, nullable=True)  # 1-31 for monthly reports
    time_of_day = db.Column(db.Time)  # Time to send the report
    recipients = db.Column(db.Text)  # Comma-separated list of email addresses
    active = db.Column(db.Boolean, default=True)
    format = db.Column(db.String(10), default='pdf')  # pdf, csv, excel
    include_charts = db.Column(db.Boolean, default=True)
    date_range = db.Column(db.String(20), default='last_30_days')  # last_7_days, last_30_days, last_90_days, custom
    custom_start_date = db.Column(db.Date, nullable=True)
    custom_end_date = db.Column(db.Date, nullable=True)
    created_by_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    created_by = db.relationship('User', backref='scheduled_reports')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_sent_at = db.Column(db.DateTime, nullable=True)
    archived = db.Column(db.Boolean, default=False)
    archive_path = db.Column(db.String(255), nullable=True)
    template_id = db.Column(db.Integer, db.ForeignKey('report_template.id'), nullable=True)
    template = db.relationship('ReportTemplate', backref='scheduled_reports')
    
    def __repr__(self):
        return f'<ScheduledReport {self.name} ({self.report_type})>'
    
    def get_recipients_list(self):
        """Return a list of email addresses from the recipients string."""
        if not self.recipients:
            return []
        return [email.strip() for email in self.recipients.split(',') if email.strip()]
    
    def is_due(self):
        """Check if the report is due to be sent based on frequency and last sent time."""
        if not self.active:
            return False
            
        now = datetime.utcnow()
        
        # If never sent before, it's due
        if not self.last_sent_at:
            return True
            
        if self.frequency == 'daily':
            # Check if it's been at least 23 hours since last sent
            return (now - self.last_sent_at).total_seconds() >= 23 * 3600
            
        elif self.frequency == 'weekly':
            # Check if it's the right day of the week and at least 6 days since last sent
            return now.weekday() == self.day_of_week and (now - self.last_sent_at).days >= 6
            
        elif self.frequency == 'monthly':
            # Check if it's the right day of the month and at least 28 days since last sent
            return now.day == self.day_of_month and (now - self.last_sent_at).days >= 28
            
        return False

class ReportTemplate(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64))
    description = db.Column(db.Text, nullable=True)
    report_type = db.Column(db.String(64))  # inventory, leads, sales, performance
    header_html = db.Column(db.Text, nullable=True)
    footer_html = db.Column(db.Text, nullable=True)
    css_styles = db.Column(db.Text, nullable=True)
    include_logo = db.Column(db.Boolean, default=True)
    include_timestamp = db.Column(db.Boolean, default=True)
    include_page_numbers = db.Column(db.Boolean, default=True)
    created_by_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    created_by = db.relationship('User', backref='report_templates')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    is_default = db.Column(db.Boolean, default=False)
    usage_count = db.Column(db.Integer, default=0)  # Track how many times this template has been used
    
    def __repr__(self):
        return f'<ReportTemplate {self.name} ({self.report_type})>'

class LeadActivity(db.Model):
    """Model to track all lead activities for a complete timeline view"""
    id = db.Column(db.Integer, primary_key=True)
    lead_id = db.Column(db.Integer, db.ForeignKey('lead.id'))
    lead = db.relationship('Lead', backref=db.backref('activities', lazy='dynamic'))
    activity_type = db.Column(db.String(30))  # email, call, text, note, status_change, appointment, etc.
    description = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    performed_by_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    performed_by = db.relationship('User', backref=db.backref('lead_activities', lazy='dynamic'))
    related_entity_type = db.Column(db.String(30), nullable=True)  # communication, appointment, etc.
    related_entity_id = db.Column(db.Integer, nullable=True)
    
    def __repr__(self):
        return f'<LeadActivity {self.activity_type} for Lead {self.lead_id}>'

class LeadFollowUpSequence(db.Model):
    """Model for automated follow-up sequences"""
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64))
    description = db.Column(db.Text, nullable=True)
    is_active = db.Column(db.Boolean, default=True)
    created_by_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    created_by = db.relationship('User', backref=db.backref('created_sequences', lazy='dynamic'))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    trigger_type = db.Column(db.String(30))  # new_lead, status_change, no_response, etc.
    lead_source = db.Column(db.String(64), nullable=True)  # Only apply to leads from this source
    steps = db.relationship('FollowUpStep', backref='sequence', lazy='dynamic', cascade='all, delete-orphan')
    
    def __repr__(self):
        return f'<LeadFollowUpSequence {self.name}>'

class FollowUpStep(db.Model):
    """Individual steps in a follow-up sequence"""
    id = db.Column(db.Integer, primary_key=True)
    sequence_id = db.Column(db.Integer, db.ForeignKey('lead_follow_up_sequence.id'))
    step_number = db.Column(db.Integer)
    delay_days = db.Column(db.Integer, default=0)  # Days to wait after previous step
    delay_hours = db.Column(db.Integer, default=0)  # Hours to wait after previous step
    action_type = db.Column(db.String(20))  # email, sms, task, etc.
    template_id = db.Column(db.Integer, nullable=True)  # ID of email or SMS template
    task_description = db.Column(db.Text, nullable=True)
    task_assignee_role = db.Column(db.String(20), nullable=True)  # Role to assign task to
    is_active = db.Column(db.Boolean, default=True)
    
    def __repr__(self):
        return f'<FollowUpStep {self.step_number} of Sequence {self.sequence_id}>'

class LeadSequenceAssignment(db.Model):
    """Tracks which leads are assigned to which sequences and their progress"""
    id = db.Column(db.Integer, primary_key=True)
    lead_id = db.Column(db.Integer, db.ForeignKey('lead.id'))
    lead = db.relationship('Lead', backref=db.backref('sequence_assignments', lazy='dynamic'))
    sequence_id = db.Column(db.Integer, db.ForeignKey('lead_follow_up_sequence.id'))
    sequence = db.relationship('LeadFollowUpSequence', backref=db.backref('lead_assignments', lazy='dynamic'))
    current_step = db.Column(db.Integer, default=0)
    is_active = db.Column(db.Boolean, default=True)
    started_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_step_completed_at = db.Column(db.DateTime, nullable=True)
    next_step_due_at = db.Column(db.DateTime, nullable=True)
    completed_at = db.Column(db.DateTime, nullable=True)
    
    def __repr__(self):
        return f'<LeadSequenceAssignment Lead {self.lead_id} on Sequence {self.sequence_id}>'

class Task(db.Model):
    """Task model for user assignments and follow-ups"""
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(128))
    description = db.Column(db.Text, nullable=True)
    status = db.Column(db.String(20), default='open')  # open, in_progress, completed, cancelled
    priority = db.Column(db.String(20), default='medium')  # low, medium, high, urgent
    due_date = db.Column(db.DateTime, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    completed_at = db.Column(db.DateTime, nullable=True)
    
    # Task assignment
    assigned_to_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    assigned_to = db.relationship('User', backref=db.backref('tasks', lazy='dynamic'))
    
    # Task can be related to various entities (lead, appointment, etc.)
    related_entity_type = db.Column(db.String(30), nullable=True)
    related_entity_id = db.Column(db.Integer, nullable=True)
    
    def __repr__(self):
        return f'<Task {self.title}>'
    
    def mark_completed(self):
        """Mark the task as completed"""
        self.status = 'completed'
        self.completed_at = datetime.utcnow()
        
        # If this is a lead-related task, update the lead's last activity
        if self.related_entity_type == 'lead':
            lead = Lead.query.get(self.related_entity_id)
            if lead:
                lead.last_activity_date = datetime.utcnow()
                
                # Add activity record
                activity = LeadActivity(
                    lead=lead,
                    activity_type='task_completed',
                    description=f'Task completed: {self.title}',
                    performed_by_id=self.assigned_to_id,
                    related_entity_type='task',
                    related_entity_id=self.id
                )
                db.session.add(activity)
                
                # Recalculate lead score
                lead.calculate_score()
                
                # Update lifecycle stage
                lead.update_lifecycle_stage()

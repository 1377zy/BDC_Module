from datetime import datetime, timedelta
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from app import db, login
import jwt
from flask import current_app
from app.models.car import UserPreference

class User(UserMixin, db.Model):
    __tablename__ = 'user'
    __table_args__ = {'extend_existing': True}
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), index=True, unique=True)
    email = db.Column(db.String(120), index=True, unique=True)
    password_hash = db.Column(db.String(128))
    first_name = db.Column(db.String(64))
    last_name = db.Column(db.String(64))
    role = db.Column(db.String(20))  # admin, manager, agent
    phone = db.Column(db.String(20))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_login = db.Column(db.DateTime)
    
    # Relationships
    leads = db.relationship('Lead', backref='agent', lazy='dynamic')
    appointments = db.relationship('Appointment', backref='agent', lazy='dynamic')
    communications = db.relationship('Communication', backref='agent', lazy='dynamic')
    car_matches = db.relationship('app.models_main.LeadVehicleMatch', backref='user', lazy='dynamic', foreign_keys='app.models_main.LeadVehicleMatch.user_id')
    
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

class Workflow(db.Model):
    """Model for workflow templates."""
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), nullable=False)
    description = db.Column(db.Text)
    active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    steps = db.relationship('WorkflowStep', backref='workflow', lazy='dynamic', cascade='all, delete-orphan')
    workflow_leads = db.relationship('WorkflowLead', backref='workflow', lazy='dynamic', cascade='all, delete-orphan')
    
    def __repr__(self):
        return f'<Workflow {self.name}>'

class WorkflowStep(db.Model):
    """Model for steps within a workflow."""
    id = db.Column(db.Integer, primary_key=True)
    workflow_id = db.Column(db.Integer, db.ForeignKey('workflow.id'))
    name = db.Column(db.String(64), nullable=False)
    description = db.Column(db.Text)
    step_type = db.Column(db.String(20))  # Email, Call, Task, etc.
    action_data = db.Column(db.Text)  # JSON data for the action
    delay_days = db.Column(db.Integer, default=0)  # Days to wait before executing
    step_order = db.Column(db.Integer)  # Order in the workflow
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<WorkflowStep {self.name} for Workflow {self.workflow_id}>'

class WorkflowLead(db.Model):
    """Model for tracking leads in workflows."""
    id = db.Column(db.Integer, primary_key=True)
    workflow_id = db.Column(db.Integer, db.ForeignKey('workflow.id'))
    lead_id = db.Column(db.Integer, db.ForeignKey('lead.id'))
    current_step = db.Column(db.Integer)  # Current step in the workflow
    status = db.Column(db.String(20))  # Active, Completed, Paused
    start_date = db.Column(db.DateTime, default=datetime.utcnow)
    completed_date = db.Column(db.DateTime)
    notes = db.Column(db.Text)
    
    def __repr__(self):
        return f'<WorkflowLead Workflow:{self.workflow_id} Lead:{self.lead_id}>'

class Lead(db.Model):
    __tablename__ = 'lead'
    __table_args__ = {'extend_existing': True}
    
    id = db.Column(db.Integer, primary_key=True)
    first_name = db.Column(db.String(64))
    last_name = db.Column(db.String(64))
    email = db.Column(db.String(120))
    phone = db.Column(db.String(20))
    address = db.Column(db.String(120))
    city = db.Column(db.String(64))
    state = db.Column(db.String(2))
    zip_code = db.Column(db.String(10))
    status = db.Column(db.String(20))  # New, Contacted, Qualified, Appointment, Sold, Lost
    source = db.Column(db.String(64))  # Website, Phone, Walk-in, Referral, etc.
    notes = db.Column(db.Text)
    budget_min = db.Column(db.Float)
    budget_max = db.Column(db.Float)
    timeline = db.Column(db.String(20))  # Immediate, 1-3 months, 3-6 months, 6+ months
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    agent_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    
    # Relationships
    appointments = db.relationship('Appointment', backref='lead', lazy='dynamic')
    communications = db.relationship('Communication', backref='lead', lazy='dynamic')
    vehicle_interests = db.relationship('VehicleInterest', backref='lead', lazy='dynamic')
    workflow_leads = db.relationship('WorkflowLead', backref='lead', lazy='dynamic')
    matches = db.relationship('app.models_main.LeadVehicleMatch', backref='lead', lazy='dynamic')
    
    def __repr__(self):
        return f'<Lead {self.first_name} {self.last_name}>'

class VehicleInterest(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    lead_id = db.Column(db.Integer, db.ForeignKey('lead.id'))
    vehicle_id = db.Column(db.Integer, db.ForeignKey('inventory.id'))
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
    __tablename__ = 'inventory'
    __table_args__ = {'extend_existing': True}
    
    id = db.Column(db.Integer, primary_key=True)
    vin = db.Column(db.String(17), unique=True)
    make = db.Column(db.String(64))
    model = db.Column(db.String(64))
    year = db.Column(db.Integer)
    trim = db.Column(db.String(64))
    color = db.Column(db.String(64))
    mileage = db.Column(db.Integer)
    price = db.Column(db.Float)
    condition = db.Column(db.String(20))  # New, Used, Certified Pre-Owned
    body_style = db.Column(db.String(64))
    transmission = db.Column(db.String(20))
    fuel_type = db.Column(db.String(20))
    drivetrain = db.Column(db.String(20))
    engine = db.Column(db.String(64))
    interior_color = db.Column(db.String(64))
    status = db.Column(db.String(20))  # Available, Sold, On Hold, In Service
    features = db.Column(db.Text)
    description = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    matches = db.relationship('app.models_main.LeadVehicleMatch', backref='vehicle', lazy='dynamic')
    
    def __repr__(self):
        return f'<Inventory {self.vin} - {self.year} {self.make} {self.model}>'

class LeadVehicleMatch(db.Model):
    __tablename__ = 'match'
    __table_args__ = {'extend_existing': True}
    
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
        return f'<LeadVehicleMatch Lead:{self.lead_id} Vehicle:{self.inventory_id} Score:{self.match_score}>'

# Lead Segmentation Models
class Segment(db.Model):
    """Model for lead segments."""
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=True)
    created_by = db.Column(db.Integer, db.ForeignKey('user.id'))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    is_dynamic = db.Column(db.Boolean, default=True)
    criteria = db.relationship('SegmentCriteria', backref='segment', lazy=True, cascade="all, delete-orphan")
    leads = db.relationship('Lead', secondary='segment_lead', backref=db.backref('segments', lazy='dynamic'))
    creator = db.relationship('User', backref='created_segments')
    
    def __repr__(self):
        return f'<Segment {self.name}>'

# Association table for many-to-many relationship between segments and leads
segment_lead = db.Table('segment_lead',
    db.Column('segment_id', db.Integer, db.ForeignKey('segment.id'), primary_key=True),
    db.Column('lead_id', db.Integer, db.ForeignKey('lead.id'), primary_key=True),
    db.Column('added_at', db.DateTime, default=datetime.utcnow)
)

class SegmentCriteria(db.Model):
    """Model for segment criteria."""
    id = db.Column(db.Integer, primary_key=True)
    segment_id = db.Column(db.Integer, db.ForeignKey('segment.id'))
    field = db.Column(db.String(50), nullable=False)
    operator = db.Column(db.String(20), nullable=False)
    value = db.Column(db.String(255), nullable=False)
    
    def __repr__(self):
        return f'<SegmentCriteria {self.field} {self.operator} {self.value}>'

class LeadInterest(db.Model):
    """Model for tracking lead interests."""
    id = db.Column(db.Integer, primary_key=True)
    lead_id = db.Column(db.Integer, db.ForeignKey('lead.id'))
    interest_type = db.Column(db.String(50), nullable=False)
    interest_value = db.Column(db.String(100), nullable=False)
    interest_level = db.Column(db.Integer, default=5)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    lead = db.relationship('Lead', backref='interests')
    
    def __repr__(self):
        return f'<LeadInterest {self.interest_type}: {self.interest_value}>'

class LeadBudget(db.Model):
    """Model for tracking lead budget information."""
    id = db.Column(db.Integer, primary_key=True)
    lead_id = db.Column(db.Integer, db.ForeignKey('lead.id'))
    min_amount = db.Column(db.Float, nullable=True)
    max_amount = db.Column(db.Float, nullable=True)
    preferred_payment_type = db.Column(db.String(50), nullable=True)
    down_payment = db.Column(db.Float, nullable=True)
    monthly_payment = db.Column(db.Float, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    lead = db.relationship('Lead', backref='budget_info', uselist=False)
    
    def __repr__(self):
        return f'<LeadBudget ${self.min_amount}-${self.max_amount}>'

class LeadTimeline(db.Model):
    """Model for tracking lead purchase timeline."""
    id = db.Column(db.Integer, primary_key=True)
    lead_id = db.Column(db.Integer, db.ForeignKey('lead.id'))
    timeline_type = db.Column(db.String(50), nullable=False)
    specific_date = db.Column(db.Date, nullable=True)
    urgency_level = db.Column(db.Integer, default=5)
    reason = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    lead = db.relationship('Lead', backref='purchase_timeline', uselist=False)
    
    def __repr__(self):
        return f'<LeadTimeline {self.timeline_type}>'

class CustomSegmentField(db.Model):
    """Model for custom segment fields defined by users."""
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False, unique=True)
    display_name = db.Column(db.String(100), nullable=False)
    field_type = db.Column(db.String(20), nullable=False)
    options = db.Column(db.Text, nullable=True)
    created_by = db.Column(db.Integer, db.ForeignKey('user.id'))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    creator = db.relationship('User', backref='custom_fields')
    values = db.relationship('CustomSegmentValue', backref='field', lazy=True, cascade="all, delete-orphan")
    
    def __repr__(self):
        return f'<CustomSegmentField {self.name}>'

class CustomSegmentValue(db.Model):
    """Model for values of custom segment fields for leads."""
    id = db.Column(db.Integer, primary_key=True)
    field_id = db.Column(db.Integer, db.ForeignKey('custom_segment_field.id'))
    lead_id = db.Column(db.Integer, db.ForeignKey('lead.id'))
    value = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    lead = db.relationship('Lead', backref='custom_values')
    
    def __repr__(self):
        return f'<CustomSegmentValue {self.field_id}: {self.value}>'

# Sales Pipeline Models
class SalesPipeline(db.Model):
    """Model for sales pipeline configuration."""
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=True)
    is_active = db.Column(db.Boolean, default=True)
    created_by = db.Column(db.Integer, db.ForeignKey('user.id'))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    stages = db.relationship('PipelineStage', backref='pipeline', lazy=True, cascade="all, delete-orphan", order_by="PipelineStage.order")
    deals = db.relationship('Deal', backref='pipeline', lazy=True)
    creator = db.relationship('User', backref='created_pipelines')
    
    def __repr__(self):
        return f'<SalesPipeline {self.name}>'

class PipelineStage(db.Model):
    """Model for stages within a sales pipeline."""
    id = db.Column(db.Integer, primary_key=True)
    pipeline_id = db.Column(db.Integer, db.ForeignKey('sales_pipeline.id'))
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=True)
    order = db.Column(db.Integer, nullable=False)
    color = db.Column(db.String(20), default="#3498db")  # Default color for the stage
    probability = db.Column(db.Integer, default=0)  # Probability of closing (0-100%)
    is_won = db.Column(db.Boolean, default=False)  # Whether this stage represents a won deal
    is_lost = db.Column(db.Boolean, default=False)  # Whether this stage represents a lost deal
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    deals = db.relationship('Deal', backref='stage', lazy=True)
    stage_transitions = db.relationship('StageTransition', backref='to_stage', lazy=True, foreign_keys='StageTransition.to_stage_id')
    
    def __repr__(self):
        return f'<PipelineStage {self.name} (Order: {self.order})>'

class Deal(db.Model):
    """Model for deals in the sales pipeline."""
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    lead_id = db.Column(db.Integer, db.ForeignKey('lead.id'))
    pipeline_id = db.Column(db.Integer, db.ForeignKey('sales_pipeline.id'))
    stage_id = db.Column(db.Integer, db.ForeignKey('pipeline_stage.id'))
    value = db.Column(db.Float, default=0.0)  # Monetary value of the deal
    expected_close_date = db.Column(db.Date, nullable=True)
    priority = db.Column(db.Integer, default=2)  # 1=Low, 2=Medium, 3=High
    status = db.Column(db.String(20), default="active")  # active, won, lost
    assigned_to_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    created_by = db.Column(db.Integer, db.ForeignKey('user.id'))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    lead = db.relationship('Lead', backref='deals')
    assigned_to = db.relationship('User', foreign_keys=[assigned_to_id], backref='assigned_deals')
    creator = db.relationship('User', foreign_keys=[created_by], backref='created_deals')
    activities = db.relationship('DealActivity', backref='deal', lazy=True, cascade="all, delete-orphan")
    transitions = db.relationship('StageTransition', backref='deal', lazy=True, cascade="all, delete-orphan")
    
    def __repr__(self):
        return f'<Deal {self.title} (${self.value})>'

class DealActivity(db.Model):
    """Model for activities related to a deal."""
    id = db.Column(db.Integer, primary_key=True)
    deal_id = db.Column(db.Integer, db.ForeignKey('deal.id'))
    activity_type = db.Column(db.String(50), nullable=False)  # call, email, meeting, note, etc.
    description = db.Column(db.Text, nullable=True)
    scheduled_at = db.Column(db.DateTime, nullable=True)
    completed_at = db.Column(db.DateTime, nullable=True)
    created_by = db.Column(db.Integer, db.ForeignKey('user.id'))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    creator = db.relationship('User', backref='deal_activities')
    
    def __repr__(self):
        return f'<DealActivity {self.activity_type} for Deal {self.deal_id}>'

class StageTransition(db.Model):
    """Model for tracking stage transitions of deals."""
    id = db.Column(db.Integer, primary_key=True)
    deal_id = db.Column(db.Integer, db.ForeignKey('deal.id'))
    from_stage_id = db.Column(db.Integer, db.ForeignKey('pipeline_stage.id'), nullable=True)
    to_stage_id = db.Column(db.Integer, db.ForeignKey('pipeline_stage.id'))
    transition_date = db.Column(db.DateTime, default=datetime.utcnow)
    days_in_previous_stage = db.Column(db.Integer, nullable=True)  # Days spent in the previous stage
    notes = db.Column(db.Text, nullable=True)
    created_by = db.Column(db.Integer, db.ForeignKey('user.id'))
    
    # Relationships
    from_stage = db.relationship('PipelineStage', foreign_keys=[from_stage_id])
    creator = db.relationship('User', backref='stage_transitions')
    
    def __repr__(self):
        return f'<StageTransition for Deal {self.deal_id} from {self.from_stage_id} to {self.to_stage_id}>'

# Search Models
class SavedSearch(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64))
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    search_params = db.Column(db.Text)  # JSON string of search parameters
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationship
    user = db.relationship('User', backref='saved_searches')
    
    def __repr__(self):
        return f'<SavedSearch {self.name}>'

class SearchHistory(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    search_params = db.Column(db.Text)  # JSON string of search parameters
    results_count = db.Column(db.Integer)
    executed_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationship
    user = db.relationship('User', backref='search_history')

# Marketing Campaign Models
class MarketingCampaign(db.Model):
    """Model for marketing campaigns."""
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=True)
    campaign_type = db.Column(db.String(50), nullable=False)  # Email, Social, Print, Radio, TV, etc.
    budget = db.Column(db.Float, nullable=True)
    start_date = db.Column(db.Date, nullable=False)
    end_date = db.Column(db.Date, nullable=True)
    status = db.Column(db.String(20), default='planned')  # planned, active, completed, cancelled
    created_by = db.Column(db.Integer, db.ForeignKey('user.id'))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    creator = db.relationship('User', backref='created_campaigns')
    channels = db.relationship('CampaignChannel', backref='campaign', lazy=True, cascade="all, delete-orphan")
    metrics = db.relationship('CampaignMetric', backref='campaign', lazy=True, cascade="all, delete-orphan")
    leads = db.relationship('Lead', secondary='campaign_lead', backref=db.backref('campaigns', lazy='dynamic'))
    
    def __repr__(self):
        return f'<MarketingCampaign {self.name}>'
    
    def total_leads(self):
        """Get the total number of leads generated by this campaign."""
        return len(self.leads)
    
    def conversion_rate(self):
        """Calculate the conversion rate of leads to appointments."""
        total_leads = self.total_leads()
        if total_leads == 0:
            return 0
            
        # Count leads with appointments
        leads_with_appointments = 0
        for lead in self.leads:
            if lead.appointments.count() > 0:
                leads_with_appointments += 1
                
        return (leads_with_appointments / total_leads) * 100
    
    def cost_per_lead(self):
        """Calculate the cost per lead for this campaign."""
        total_leads = self.total_leads()
        if total_leads == 0 or self.budget is None:
            return 0
            
        return self.budget / total_leads
    
    def roi(self):
        """Calculate the ROI of the campaign based on estimated value of leads."""
        if self.budget is None or self.budget == 0:
            return 0
            
        # Sum the estimated value of all leads
        total_value = 0
        for lead in self.leads:
            # If lead has a budget, use the max amount as estimated value
            if lead.budget_info and lead.budget_info.max_amount:
                total_value += lead.budget_info.max_amount
            else:
                # Use a default average value
                total_value += 25000  # Example average car value
                
        if total_value == 0:
            return 0
            
        return ((total_value - self.budget) / self.budget) * 100

class CampaignChannel(db.Model):
    """Model for tracking different channels within a campaign."""
    id = db.Column(db.Integer, primary_key=True)
    campaign_id = db.Column(db.Integer, db.ForeignKey('marketing_campaign.id'))
    channel_name = db.Column(db.String(50), nullable=False)  # Facebook, Instagram, Google Ads, etc.
    description = db.Column(db.Text, nullable=True)
    cost = db.Column(db.Float, nullable=True)
    start_date = db.Column(db.Date, nullable=True)
    end_date = db.Column(db.Date, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Metrics specific to this channel
    impressions = db.Column(db.Integer, default=0)
    clicks = db.Column(db.Integer, default=0)
    conversions = db.Column(db.Integer, default=0)
    
    def __repr__(self):
        return f'<CampaignChannel {self.channel_name} for Campaign {self.campaign_id}>'
    
    def click_through_rate(self):
        """Calculate the click-through rate (CTR) for this channel."""
        if self.impressions == 0:
            return 0
        return (self.clicks / self.impressions) * 100
    
    def conversion_rate(self):
        """Calculate the conversion rate for this channel."""
        if self.clicks == 0:
            return 0
        return (self.conversions / self.clicks) * 100
    
    def cost_per_click(self):
        """Calculate the cost per click (CPC) for this channel."""
        if self.clicks == 0 or self.cost is None:
            return 0
        return self.cost / self.clicks
    
    def cost_per_conversion(self):
        """Calculate the cost per conversion for this channel."""
        if self.conversions == 0 or self.cost is None:
            return 0
        return self.cost / self.conversions

class CampaignMetric(db.Model):
    """Model for tracking campaign metrics over time."""
    id = db.Column(db.Integer, primary_key=True)
    campaign_id = db.Column(db.Integer, db.ForeignKey('marketing_campaign.id'))
    metric_name = db.Column(db.String(50), nullable=False)  # impressions, clicks, leads, etc.
    metric_value = db.Column(db.Float, nullable=False)
    date = db.Column(db.Date, default=datetime.utcnow().date)
    notes = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<CampaignMetric {self.metric_name}: {self.metric_value} for Campaign {self.campaign_id}>'

# Association table for many-to-many relationship between campaigns and leads
campaign_lead = db.Table('campaign_lead',
    db.Column('campaign_id', db.Integer, db.ForeignKey('marketing_campaign.id'), primary_key=True),
    db.Column('lead_id', db.Integer, db.ForeignKey('lead.id'), primary_key=True),
    db.Column('source_channel', db.String(50), nullable=True),  # Which specific channel the lead came from
    db.Column('first_touch_date', db.DateTime, default=datetime.utcnow),
    db.Column('conversion_date', db.DateTime, nullable=True)  # When they converted to a lead
)

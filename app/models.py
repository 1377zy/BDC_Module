# This file is maintained for backward compatibility
# All model definitions have been moved to models_main.py to avoid circular imports
# Any changes to models should be made in models_main.py

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
    
    # Relationships
    communications = db.relationship('Communication', backref='lead', lazy='dynamic')
    appointments = db.relationship('Appointment', backref='lead', lazy='dynamic')
    vehicle_interests = db.relationship('VehicleInterest', backref='lead', lazy='dynamic')
    workflows = db.relationship('LeadWorkflow', backref='lead', lazy='dynamic')
    notifications = db.relationship('WorkflowNotification', backref='lead', lazy='dynamic')
    interests = db.relationship('LeadInterest', backref='lead', lazy='dynamic')
    budget_info = db.relationship('LeadBudget', backref='lead', uselist=False)
    purchase_timeline = db.relationship('LeadTimeline', backref='lead', uselist=False)
    custom_values = db.relationship('CustomSegmentValue', backref='lead', lazy='dynamic')
    segments = db.relationship('Segment', secondary='segment_lead', backref=db.backref('leads', lazy='dynamic'))
    deals = db.relationship('Deal', backref='lead', lazy=True)
    campaigns = db.relationship('MarketingCampaign', secondary='campaign_lead', 
                                backref=db.backref('leads', lazy='dynamic'))
    
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
    
    def __repr__(self):
        return f'<SearchHistory {self.id} - {self.executed_at}>'

class WorkflowTemplate(db.Model):
    """Model for workflow templates."""
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    trigger_status = db.Column(db.String(50), nullable=True)
    auto_apply = db.Column(db.Boolean, default=False)
    
    # Relationships
    steps = db.relationship('WorkflowStep', backref='workflow_template', lazy=True, cascade="all, delete-orphan")
    lead_workflows = db.relationship('LeadWorkflow', backref='workflow_template', lazy=True)
    notifications = db.relationship('WorkflowNotification', backref='workflow_template', lazy='dynamic')
    
    def __repr__(self):
        return f'<WorkflowTemplate {self.name}>'

class WorkflowStep(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    workflow_id = db.Column(db.Integer, db.ForeignKey('workflow_template.id'))
    step_type = db.Column(db.String(20))  # Email, SMS, Call, Task
    delay_days = db.Column(db.Integer, default=0)  # Days to wait before executing this step
    template_id = db.Column(db.Integer)  # ID of email or SMS template if applicable
    subject = db.Column(db.String(128))  # For emails or tasks
    content = db.Column(db.Text)  # Content of the step
    step_order = db.Column(db.Integer)  # Order in the workflow sequence
    
    def __repr__(self):
        return f'<WorkflowStep {self.step_type} - {self.step_order}>'

class LeadWorkflow(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    lead_id = db.Column(db.Integer, db.ForeignKey('lead.id'))
    workflow_template_id = db.Column(db.Integer, db.ForeignKey('workflow_template.id'))
    start_date = db.Column(db.DateTime, default=datetime.utcnow)
    status = db.Column(db.String(20), default='active')  # active, completed, paused, cancelled
    
    # Relationships
    lead = db.relationship('Lead', backref='workflows')
    workflow_template = db.relationship('WorkflowTemplate')
    steps = db.relationship('LeadWorkflowStep', backref='lead_workflow', lazy='dynamic', cascade='all, delete-orphan')
    notifications = db.relationship('WorkflowNotification', backref='lead_workflow', lazy='dynamic')
    
    def __repr__(self):
        return f'<LeadWorkflow {self.id} for Lead {self.lead_id}>'

class LeadWorkflowStep(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    lead_workflow_id = db.Column(db.Integer, db.ForeignKey('lead_workflow.id'))
    workflow_step_id = db.Column(db.Integer, db.ForeignKey('workflow_step.id'))
    scheduled_date = db.Column(db.DateTime)
    executed_date = db.Column(db.DateTime, nullable=True)
    status = db.Column(db.String(20), default='pending')  # pending, completed, failed, skipped
    result = db.Column(db.Text, nullable=True)  # Any result or note from the step execution
    
    # Relationships
    workflow_step = db.relationship('WorkflowStep')
    notifications = db.relationship('WorkflowNotification', backref='lead_workflow_step', lazy='dynamic')
    
    def __repr__(self):
        return f'<LeadWorkflowStep {self.id} - {self.status}>'

class WorkflowNotification(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    message = db.Column(db.Text, nullable=False)
    notification_type = db.Column(db.String(50), nullable=False)  # 'auto_apply', 'step_due', 'workflow_complete'
    is_read = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    link = db.Column(db.String(255), nullable=True)
    
    # Optional relationships
    lead_id = db.Column(db.Integer, db.ForeignKey('lead.id'), nullable=True)
    lead = db.relationship('Lead', backref='notifications', lazy=True)
    
    workflow_template_id = db.Column(db.Integer, db.ForeignKey('workflow_template.id'), nullable=True)
    workflow_template = db.relationship('WorkflowTemplate', backref='notifications', lazy=True)
    
    lead_workflow_id = db.Column(db.Integer, db.ForeignKey('lead_workflow.id'), nullable=True)
    lead_workflow = db.relationship('LeadWorkflow', backref='notifications', lazy=True)
    
    lead_workflow_step_id = db.Column(db.Integer, db.ForeignKey('lead_workflow_step.id'), nullable=True)
    lead_workflow_step = db.relationship('LeadWorkflowStep', backref='notifications', lazy=True)

class WorkflowNotificationSettings(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email_notifications = db.Column(db.Boolean, default=True)
    browser_notifications = db.Column(db.Boolean, default=True)
    notification_time = db.Column(db.String(5), default='08:00')  # Format: HH:MM
    advance_notice = db.Column(db.Integer, default=0)  # Days in advance to notify
    
    # User relationship if you have a user model
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    user = db.relationship('User', backref='notification_settings', lazy=True)

# Lead Segmentation Models
class Segment(db.Model):
    """Model for lead segments."""
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=True)
    created_by = db.Column(db.Integer, db.ForeignKey('user.id'))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    is_dynamic = db.Column(db.Boolean, default=True)  # Dynamic segments auto-update based on criteria
    
    # Relationships
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
    field = db.Column(db.String(50), nullable=False)  # The field to filter on (e.g., 'interest', 'budget', 'timeline')
    operator = db.Column(db.String(20), nullable=False)  # equals, contains, greater_than, less_than, etc.
    value = db.Column(db.String(255), nullable=False)  # The value to compare against
    
    def __repr__(self):
        return f'<SegmentCriteria {self.field} {self.operator} {self.value}>'

class LeadInterest(db.Model):
    """Model for tracking lead interests."""
    id = db.Column(db.Integer, primary_key=True)
    lead_id = db.Column(db.Integer, db.ForeignKey('lead.id'))
    interest_type = db.Column(db.String(50), nullable=False)  # Category of interest (e.g., 'vehicle_type', 'feature', 'service')
    interest_value = db.Column(db.String(100), nullable=False)  # Specific interest (e.g., 'SUV', 'leather seats', 'financing')
    interest_level = db.Column(db.Integer, default=5)  # Scale of 1-10, 10 being highest interest
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationship
    lead = db.relationship('Lead', backref='interests')
    
    def __repr__(self):
        return f'<LeadInterest {self.interest_type}: {self.interest_value} (Level: {self.interest_level})>'

class LeadBudget(db.Model):
    """Model for tracking lead budget information."""
    id = db.Column(db.Integer, primary_key=True)
    lead_id = db.Column(db.Integer, db.ForeignKey('lead.id'))
    min_amount = db.Column(db.Float, nullable=True)
    max_amount = db.Column(db.Float, nullable=True)
    preferred_payment_type = db.Column(db.String(50), nullable=True)  # cash, finance, lease
    down_payment = db.Column(db.Float, nullable=True)
    monthly_payment = db.Column(db.Float, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationship
    lead = db.relationship('Lead', backref='budget_info', uselist=False)
    
    def __repr__(self):
        return f'<LeadBudget ${self.min_amount}-${self.max_amount}>'

class LeadTimeline(db.Model):
    """Model for tracking lead purchase timeline."""
    id = db.Column(db.Integer, primary_key=True)
    lead_id = db.Column(db.Integer, db.ForeignKey('lead.id'))
    timeline_type = db.Column(db.String(50), nullable=False)  # immediate, within_month, within_three_months, within_six_months, future
    specific_date = db.Column(db.Date, nullable=True)  # If the lead has a specific purchase date in mind
    urgency_level = db.Column(db.Integer, default=5)  # Scale of 1-10, 10 being most urgent
    reason = db.Column(db.Text, nullable=True)  # Reason for timeline (e.g., "Current lease ending")
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationship
    lead = db.relationship('Lead', backref='purchase_timeline', uselist=False)
    
    def __repr__(self):
        return f'<LeadTimeline {self.timeline_type} (Urgency: {self.urgency_level})>'

class CustomSegmentField(db.Model):
    """Model for custom segment fields defined by users."""
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False, unique=True)
    display_name = db.Column(db.String(100), nullable=False)
    field_type = db.Column(db.String(20), nullable=False)  # text, number, date, boolean, select
    options = db.Column(db.Text, nullable=True)  # JSON string of options for select fields
    created_by = db.Column(db.Integer, db.ForeignKey('user.id'))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationship
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
    
    # Relationship
    lead = db.relationship('Lead', backref='custom_values')
    
    def __repr__(self):
        return f'<CustomSegmentValue {self.field.name}: {self.value}>'

# Sales Pipeline Models
class SalesPipeline(db.Model):
    """Model for sales pipelines."""
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=True)
    created_by = db.Column(db.Integer, db.ForeignKey('user.id'))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    is_active = db.Column(db.Boolean, default=True)
    
    # Relationships
    stages = db.relationship('PipelineStage', backref='pipeline', lazy=True, 
                            order_by='PipelineStage.order', cascade="all, delete-orphan")
    deals = db.relationship('Deal', backref='pipeline', lazy=True)
    creator = db.relationship('User', backref='created_pipelines')
    
    def __repr__(self):
        return f'<Pipeline {self.name}>'
    
    @property
    def total_value(self):
        """Calculate the total value of all deals in the pipeline."""
        return sum(deal.value for deal in self.deals if deal.value)
    
    @property
    def total_deals(self):
        """Get the total number of deals in the pipeline."""
        return len(self.deals)
    
    @property
    def won_deals(self):
        """Get all deals that are in a 'won' stage."""
        won_stage_ids = [stage.id for stage in self.stages if stage.is_won]
        return [deal for deal in self.deals if deal.stage_id in won_stage_ids]
    
    @property
    def lost_deals(self):
        """Get all deals that are in a 'lost' stage."""
        lost_stage_ids = [stage.id for stage in self.stages if stage.is_lost]
        return [deal for deal in self.deals if deal.stage_id in lost_stage_ids]
    
    @property
    def win_rate(self):
        """Calculate the win rate as a percentage."""
        closed_deals = len(self.won_deals) + len(self.lost_deals)
        if closed_deals == 0:
            return 0
        return (len(self.won_deals) / closed_deals) * 100


class PipelineStage(db.Model):
    """Model for stages within a sales pipeline."""
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=True)
    pipeline_id = db.Column(db.Integer, db.ForeignKey('sales_pipeline.id'))
    order = db.Column(db.Integer, nullable=False)
    color = db.Column(db.String(7), default='#3498db')  # Hex color code
    is_won = db.Column(db.Boolean, default=False)
    is_lost = db.Column(db.Boolean, default=False)
    probability = db.Column(db.Integer, default=0)  # Probability percentage (0-100)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    deals = db.relationship('Deal', backref='stage', lazy=True)
    transitions_from = db.relationship('StageTransition', 
                                      foreign_keys='StageTransition.from_stage_id',
                                      backref='from_stage', lazy=True)
    transitions_to = db.relationship('StageTransition', 
                                    foreign_keys='StageTransition.to_stage_id',
                                    backref='to_stage', lazy=True)
    
    def __repr__(self):
        return f'<Stage {self.name} (Pipeline: {self.pipeline_id})>'
    
    @property
    def total_value(self):
        """Calculate the total value of all deals in this stage."""
        return sum(deal.value for deal in self.deals if deal.value)
    
    @property
    def avg_time_in_stage(self):
        """Calculate the average time deals spend in this stage (in days)."""
        transitions = StageTransition.query.filter_by(to_stage_id=self.id).all()
        if not transitions:
            return 0
            
        total_days = 0
        count = 0
        
        for transition in transitions:
            # Find the next transition for this deal
            next_transition = StageTransition.query.filter(
                StageTransition.deal_id == transition.deal_id,
                StageTransition.from_stage_id == self.id,
                StageTransition.created_at > transition.created_at
            ).order_by(StageTransition.created_at).first()
            
            if next_transition:
                # Calculate days between transitions
                days = (next_transition.created_at - transition.created_at).days
                total_days += days
                count += 1
                
        return total_days / count if count > 0 else 0


class Deal(db.Model):
    """Model for deals in the sales pipeline."""
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=True)
    value = db.Column(db.Float, nullable=True)
    currency = db.Column(db.String(3), default='USD')
    pipeline_id = db.Column(db.Integer, db.ForeignKey('sales_pipeline.id'))
    stage_id = db.Column(db.Integer, db.ForeignKey('pipeline_stage.id'))
    lead_id = db.Column(db.Integer, db.ForeignKey('lead.id'), nullable=True)
    assigned_to_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    probability = db.Column(db.Integer, nullable=True)  # Can override stage probability
    expected_close_date = db.Column(db.Date, nullable=True)
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
    
    @property
    def days_in_pipeline(self):
        """Calculate the number of days this deal has been in the pipeline."""
        return (datetime.utcnow() - self.created_at).days
    
    @property
    def days_in_current_stage(self):
        """Calculate the number of days this deal has been in the current stage."""
        last_transition = StageTransition.query.filter_by(
            deal_id=self.id, 
            to_stage_id=self.stage_id
        ).order_by(StageTransition.created_at.desc()).first()
        
        if last_transition:
            return (datetime.utcnow() - last_transition.created_at).days
        else:
            # If no transition record, use deal creation date
            return self.days_in_pipeline
    
    @property
    def is_won(self):
        """Check if the deal is in a 'won' stage."""
        stage = PipelineStage.query.get(self.stage_id)
        return stage.is_won if stage else False
    
    @property
    def is_lost(self):
        """Check if the deal is in a 'lost' stage."""
        stage = PipelineStage.query.get(self.stage_id)
        return stage.is_lost if stage else False
    
    @property
    def is_active(self):
        """Check if the deal is still active (not won or lost)."""
        return not (self.is_won or self.is_lost)
    
    @property
    def last_activity(self):
        """Get the most recent activity for this deal."""
        return DealActivity.query.filter_by(deal_id=self.id).order_by(DealActivity.created_at.desc()).first()


class DealActivity(db.Model):
    """Model for tracking activities related to deals."""
    id = db.Column(db.Integer, primary_key=True)
    deal_id = db.Column(db.Integer, db.ForeignKey('deal.id'))
    activity_type = db.Column(db.String(50), nullable=False)  # call, email, meeting, note, task, etc.
    title = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=True)
    created_by = db.Column(db.Integer, db.ForeignKey('user.id'))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    scheduled_date = db.Column(db.DateTime, nullable=True)  # For future activities
    completed_date = db.Column(db.DateTime, nullable=True)  # For completed activities
    is_completed = db.Column(db.Boolean, default=False)
    
    # Relationships
    creator = db.relationship('User', backref='deal_activities')
    
    def __repr__(self):
        return f'<DealActivity {self.activity_type}: {self.title}>'


class StageTransition(db.Model):
    """Model for tracking deal movements between stages."""
    id = db.Column(db.Integer, primary_key=True)
    deal_id = db.Column(db.Integer, db.ForeignKey('deal.id'))
    from_stage_id = db.Column(db.Integer, db.ForeignKey('pipeline_stage.id'))
    to_stage_id = db.Column(db.Integer, db.ForeignKey('pipeline_stage.id'))
    created_by = db.Column(db.Integer, db.ForeignKey('user.id'))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    notes = db.Column(db.Text, nullable=True)
    
    # Relationships
    creator = db.relationship('User', backref='stage_transitions')
    
    def __repr__(self):
        return f'<StageTransition Deal {self.deal_id}: {self.from_stage_id} -> {self.to_stage_id}>'


class PipelineFilter(db.Model):
    """Model for saved pipeline filters."""
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    pipeline_id = db.Column(db.Integer, db.ForeignKey('sales_pipeline.id'))
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    filter_data = db.Column(db.Text, nullable=False)  # JSON string of filter parameters
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    pipeline = db.relationship('SalesPipeline', backref='saved_filters')
    user = db.relationship('User', backref='pipeline_filters')
    
    def __repr__(self):
        return f'<PipelineFilter {self.name} (Pipeline: {self.pipeline_id})>'


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

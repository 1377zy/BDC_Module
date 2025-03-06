from flask_wtf import FlaskForm
from wtforms import StringField, SelectField, DateField, BooleanField, IntegerField, SelectMultipleField, SubmitField
from wtforms.validators import Optional, Length, NumberRange
from datetime import datetime

class AdvancedSearchForm(FlaskForm):
    """Form for advanced lead search functionality"""
    # Basic information
    first_name = StringField('First Name', validators=[Optional(), Length(max=64)])
    last_name = StringField('Last Name', validators=[Optional(), Length(max=64)])
    email = StringField('Email', validators=[Optional(), Length(max=120)])
    phone = StringField('Phone', validators=[Optional(), Length(max=20)])
    
    # Lead status and source
    status = SelectField('Status', choices=[
        ('', 'Any Status'),
        ('new', 'New'),
        ('contacted', 'Contacted'),
        ('qualified', 'Qualified'),
        ('unqualified', 'Unqualified'),
        ('nurturing', 'Nurturing'),
        ('converted', 'Converted')
    ], validators=[Optional()])
    
    source = SelectField('Source', choices=[
        ('', 'Any Source'),
        ('website', 'Website'),
        ('phone', 'Phone'),
        ('email', 'Email'),
        ('referral', 'Referral'),
        ('social_media', 'Social Media'),
        ('walk_in', 'Walk-in'),
        ('event', 'Event'),
        ('other', 'Other')
    ], validators=[Optional()])
    
    # Date ranges
    created_from = DateField('Created From', format='%Y-%m-%d', validators=[Optional()])
    created_to = DateField('Created To', format='%Y-%m-%d', validators=[Optional()])
    updated_from = DateField('Updated From', format='%Y-%m-%d', validators=[Optional()])
    updated_to = DateField('Updated To', format='%Y-%m-%d', validators=[Optional()])
    
    # Vehicle interests
    vehicle_make = StringField('Vehicle Make', validators=[Optional(), Length(max=64)])
    vehicle_model = StringField('Vehicle Model', validators=[Optional(), Length(max=64)])
    vehicle_year_min = IntegerField('Min Year', validators=[Optional(), NumberRange(min=1900, max=datetime.now().year + 1)])
    vehicle_year_max = IntegerField('Max Year', validators=[Optional(), NumberRange(min=1900, max=datetime.now().year + 1)])
    new_or_used = SelectField('New or Used', choices=[
        ('', 'Any'),
        ('new', 'New'),
        ('used', 'Used')
    ], validators=[Optional()])
    
    # Budget information
    budget_min = IntegerField('Min Budget', validators=[Optional(), NumberRange(min=0)])
    budget_max = IntegerField('Max Budget', validators=[Optional(), NumberRange(min=0)])
    preferred_payment = SelectField('Preferred Payment', choices=[
        ('', 'Any'),
        ('cash', 'Cash'),
        ('finance', 'Finance'),
        ('lease', 'Lease')
    ], validators=[Optional()])
    
    # Timeline information
    timeline = SelectField('Purchase Timeline', choices=[
        ('', 'Any'),
        ('immediate', 'Immediate (0-7 days)'),
        ('short', 'Short (1-4 weeks)'),
        ('medium', 'Medium (1-3 months)'),
        ('long', 'Long (3+ months)')
    ], validators=[Optional()])
    
    # Workflow and engagement
    in_workflow = BooleanField('In Active Workflow', default=False)
    has_appointment = BooleanField('Has Appointment', default=False)
    has_communication = BooleanField('Has Communication', default=False)
    
    # Segments
    segments = SelectMultipleField('Segments', coerce=int, validators=[Optional()])
    
    # Sorting
    sort_by = SelectField('Sort By', choices=[
        ('created_at', 'Date Created'),
        ('updated_at', 'Last Updated'),
        ('last_name', 'Last Name'),
        ('first_name', 'First Name'),
        ('status', 'Status')
    ], default='created_at')
    
    sort_order = SelectField('Sort Order', choices=[
        ('desc', 'Descending'),
        ('asc', 'Ascending')
    ], default='desc')
    
    # Actions
    submit = SubmitField('Search')
    save = SubmitField('Save Search')
    export = SubmitField('Export Results')

class SavedSearchForm(FlaskForm):
    """Form for saving searches"""
    name = StringField('Search Name', validators=[Length(min=3, max=64)])
    description = StringField('Description', validators=[Optional(), Length(max=200)])
    is_default = BooleanField('Set as Default', default=False)
    submit = SubmitField('Save')

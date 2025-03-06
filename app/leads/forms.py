from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, SelectField, SubmitField
from wtforms.validators import DataRequired, Email, Length, Optional

class LeadForm(FlaskForm):
    first_name = StringField('First Name', validators=[DataRequired()])
    last_name = StringField('Last Name', validators=[DataRequired()])
    email = StringField('Email', validators=[Optional(), Email()])
    phone = StringField('Phone', validators=[DataRequired()])
    source = SelectField('Lead Source', choices=[
        ('Website', 'Website'),
        ('Phone', 'Phone Inquiry'),
        ('Walk-in', 'Walk-in'),
        ('Referral', 'Referral'),
        ('Third Party', 'Third Party Site'),
        ('Social Media', 'Social Media'),
        ('Other', 'Other')
    ])
    status = SelectField('Status', choices=[
        ('New', 'New'),
        ('Contacted', 'Contacted'),
        ('Qualified', 'Qualified'),
        ('Appointment Set', 'Appointment Set'),
        ('Sold', 'Sold'),
        ('Lost', 'Lost'),
        ('Inactive', 'Inactive')
    ])
    notes = TextAreaField('Notes', validators=[Optional(), Length(max=500)])
    submit = SubmitField('Save Lead')

class VehicleInterestForm(FlaskForm):
    make = StringField('Make', validators=[DataRequired()])
    model = StringField('Model', validators=[DataRequired()])
    year = StringField('Year', validators=[Optional()])
    new_or_used = SelectField('New or Used', choices=[
        ('New', 'New'),
        ('Used', 'Used')
    ])
    notes = TextAreaField('Notes', validators=[Optional(), Length(max=200)])
    submit = SubmitField('Save Vehicle Interest')

class SearchLeadForm(FlaskForm):
    search_term = StringField('Search by name, email or phone')
    status = SelectField('Status', choices=[
        ('', 'All Statuses'),
        ('New', 'New'),
        ('Contacted', 'Contacted'),
        ('Qualified', 'Qualified'),
        ('Appointment Set', 'Appointment Set'),
        ('Sold', 'Sold'),
        ('Lost', 'Lost'),
        ('Inactive', 'Inactive')
    ])
    source = SelectField('Source', choices=[
        ('', 'All Sources'),
        ('Website', 'Website'),
        ('Phone', 'Phone Inquiry'),
        ('Walk-in', 'Walk-in'),
        ('Referral', 'Referral'),
        ('Third Party', 'Third Party Site'),
        ('Social Media', 'Social Media'),
        ('Other', 'Other')
    ])
    submit = SubmitField('Search')

class MatchForm(FlaskForm):
    """Form for creating and editing lead-vehicle matches."""
    lead_id = SelectField('Lead', coerce=int, validators=[DataRequired()])
    inventory_id = SelectField('Vehicle', coerce=int, validators=[DataRequired()])
    user_id = SelectField('Created By', coerce=int, validators=[DataRequired()])
    match_score = StringField('Match Score (0-100)', validators=[DataRequired()])
    status = SelectField('Status', choices=[
        ('Suggested', 'Suggested'),
        ('Presented', 'Presented'),
        ('Rejected', 'Rejected'),
        ('Interested', 'Interested')
    ], validators=[DataRequired()])
    notes = TextAreaField('Notes', validators=[Optional()])
    submit = SubmitField('Save Match')

class InventoryForm(FlaskForm):
    """Form for creating and editing inventory items."""
    vin = StringField('VIN', validators=[DataRequired(), Length(max=17)])
    make = StringField('Make', validators=[DataRequired(), Length(max=64)])
    model = StringField('Model', validators=[DataRequired(), Length(max=64)])
    year = StringField('Year', validators=[DataRequired()])
    trim = StringField('Trim', validators=[Optional(), Length(max=64)])
    color = StringField('Exterior Color', validators=[Optional(), Length(max=64)])
    interior_color = StringField('Interior Color', validators=[Optional(), Length(max=64)])
    mileage = StringField('Mileage', validators=[Optional()])
    price = StringField('Price', validators=[Optional()])
    condition = SelectField('Condition', choices=[
        ('New', 'New'),
        ('Used', 'Used'),
        ('Certified Pre-Owned', 'Certified Pre-Owned')
    ])
    body_style = StringField('Body Style', validators=[Optional(), Length(max=64)])
    transmission = SelectField('Transmission', choices=[
        ('Automatic', 'Automatic'),
        ('Manual', 'Manual'),
        ('CVT', 'CVT'),
        ('Other', 'Other')
    ])
    fuel_type = SelectField('Fuel Type', choices=[
        ('Gasoline', 'Gasoline'),
        ('Diesel', 'Diesel'),
        ('Hybrid', 'Hybrid'),
        ('Electric', 'Electric'),
        ('Other', 'Other')
    ])
    drivetrain = SelectField('Drivetrain', choices=[
        ('FWD', 'FWD'),
        ('RWD', 'RWD'),
        ('AWD', 'AWD'),
        ('4WD', '4WD'),
        ('Other', 'Other')
    ])
    engine = StringField('Engine', validators=[Optional(), Length(max=64)])
    features = TextAreaField('Features', validators=[Optional()])
    description = TextAreaField('Description', validators=[Optional()])
    status = SelectField('Status', choices=[
        ('Available', 'Available'),
        ('Sold', 'Sold'),
        ('On Hold', 'On Hold'),
        ('In Service', 'In Service')
    ])
    submit = SubmitField('Save Vehicle')

class SearchInventoryForm(FlaskForm):
    """Form for searching inventory."""
    make = StringField('Make')
    model = StringField('Model')
    year_min = StringField('Min Year')
    year_max = StringField('Max Year')
    price_min = StringField('Min Price')
    price_max = StringField('Max Price')
    status = SelectField('Status', choices=[
        ('', 'Any Status'),
        ('Available', 'Available'),
        ('Sold', 'Sold'),
        ('On Hold', 'On Hold'),
        ('In Service', 'In Service')
    ])
    submit = SubmitField('Search')

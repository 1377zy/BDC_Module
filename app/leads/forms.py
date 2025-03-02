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

from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, SelectField, SubmitField, DateField, TimeField
from wtforms.validators import DataRequired, Length, Optional
from datetime import datetime, time

class AppointmentForm(FlaskForm):
    date = DateField('Date', validators=[DataRequired()], format='%Y-%m-%d')
    time = TimeField('Time', validators=[DataRequired()], format='%H:%M')
    purpose = SelectField('Purpose', choices=[
        ('Test Drive', 'Test Drive'),
        ('Sales Consultation', 'Sales Consultation'),
        ('Vehicle Appraisal', 'Vehicle Appraisal'),
        ('Financing Discussion', 'Financing Discussion'),
        ('Final Purchase', 'Final Purchase'),
        ('Other', 'Other')
    ])
    status = SelectField('Status', choices=[
        ('Scheduled', 'Scheduled'),
        ('Confirmed', 'Confirmed'),
        ('Completed', 'Completed'),
        ('No-Show', 'No-Show'),
        ('Rescheduled', 'Rescheduled'),
        ('Cancelled', 'Cancelled')
    ])
    notes = TextAreaField('Notes', validators=[Optional(), Length(max=500)])
    submit = SubmitField('Save Appointment')
    
    def validate_date(self, date):
        # Ensure date is not in the past
        if date.data < datetime.now().date():
            raise ValidationError('Appointment date cannot be in the past')
    
class AppointmentSearchForm(FlaskForm):
    start_date = DateField('Start Date', validators=[Optional()], format='%Y-%m-%d')
    end_date = DateField('End Date', validators=[Optional()], format='%Y-%m-%d')
    status = SelectField('Status', choices=[
        ('', 'All Statuses'),
        ('Scheduled', 'Scheduled'),
        ('Confirmed', 'Confirmed'),
        ('Completed', 'Completed'),
        ('No-Show', 'No-Show'),
        ('Rescheduled', 'Rescheduled'),
        ('Cancelled', 'Cancelled')
    ], validators=[Optional()])
    lead_name = StringField('Lead Name', validators=[Optional()])
    submit = SubmitField('Search')

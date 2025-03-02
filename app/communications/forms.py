from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, SelectField, SubmitField, HiddenField
from wtforms.validators import DataRequired, Email, Length, Optional

class EmailForm(FlaskForm):
    template_id = SelectField('Email Template', coerce=int)
    subject = StringField('Subject', validators=[DataRequired()])
    body = TextAreaField('Message', validators=[DataRequired(), Length(max=10000)])
    submit = SubmitField('Send Email')

class SMSForm(FlaskForm):
    template_id = SelectField('SMS Template', coerce=int)
    body = TextAreaField('Message', validators=[DataRequired(), Length(max=160)])
    submit = SubmitField('Send SMS')

class EmailTemplateForm(FlaskForm):
    name = StringField('Template Name', validators=[DataRequired()])
    subject = StringField('Subject', validators=[DataRequired()])
    body = TextAreaField('Body', validators=[DataRequired()])
    purpose = SelectField('Purpose', choices=[
        ('Initial Contact', 'Initial Contact'),
        ('Follow-up', 'Follow-up'),
        ('Appointment Confirmation', 'Appointment Confirmation'),
        ('Appointment Reminder', 'Appointment Reminder'),
        ('Thank You', 'Thank You'),
        ('Other', 'Other')
    ])
    submit = SubmitField('Save Template')

class SMSTemplateForm(FlaskForm):
    name = StringField('Template Name', validators=[DataRequired()])
    body = TextAreaField('Body', validators=[DataRequired(), Length(max=160)])
    purpose = SelectField('Purpose', choices=[
        ('Initial Contact', 'Initial Contact'),
        ('Follow-up', 'Follow-up'),
        ('Appointment Confirmation', 'Appointment Confirmation'),
        ('Appointment Reminder', 'Appointment Reminder'),
        ('Thank You', 'Thank You'),
        ('Other', 'Other')
    ])
    submit = SubmitField('Save Template')

class CommunicationSearchForm(FlaskForm):
    lead_name = StringField('Lead Name', validators=[Optional()])
    comm_type = SelectField('Type', choices=[
        ('', 'All Types'),
        ('Email', 'Email'),
        ('SMS', 'SMS')
    ], validators=[Optional()])
    direction = SelectField('Direction', choices=[
        ('', 'All Directions'),
        ('Inbound', 'Inbound'),
        ('Outbound', 'Outbound')
    ], validators=[Optional()])
    submit = SubmitField('Search')

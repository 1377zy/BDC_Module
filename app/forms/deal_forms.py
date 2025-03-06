from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, SelectField, DecimalField, IntegerField, DateField, HiddenField
from wtforms.validators import DataRequired, Optional, NumberRange, Length, ValidationError
from datetime import date

class DealForm(FlaskForm):
    """Form for creating and editing deals"""
    title = StringField('Deal Title', validators=[DataRequired(), Length(min=3, max=100)])
    pipeline_id = SelectField('Pipeline', validators=[DataRequired()], coerce=int)
    stage_id = SelectField('Stage', validators=[DataRequired()], coerce=int)
    lead_id = SelectField('Associated Lead', validators=[Optional()], coerce=int)
    value = DecimalField('Deal Value', validators=[Optional(), NumberRange(min=0)], places=2)
    probability = IntegerField('Probability (%)', validators=[Optional(), NumberRange(min=0, max=100)], default=50)
    expected_close_date = DateField('Expected Close Date', validators=[Optional()], format='%Y-%m-%d')
    description = TextAreaField('Description', validators=[Optional(), Length(max=1000)])
    tags = StringField('Tags', validators=[Optional(), Length(max=200)])
    
    def validate_expected_close_date(self, field):
        if field.data and field.data < date.today():
            raise ValidationError('Expected close date cannot be in the past')

class DealFilterForm(FlaskForm):
    """Form for filtering deals in pipeline view"""
    pipeline_id = SelectField('Pipeline', validators=[Optional()], coerce=int)
    stage_id = SelectField('Stage', validators=[Optional()], coerce=int)
    lead_id = SelectField('Lead', validators=[Optional()], coerce=int)
    min_value = DecimalField('Min Value', validators=[Optional(), NumberRange(min=0)], places=2)
    max_value = DecimalField('Max Value', validators=[Optional(), NumberRange(min=0)], places=2)
    min_probability = IntegerField('Min Probability', validators=[Optional(), NumberRange(min=0, max=100)])
    max_probability = IntegerField('Max Probability', validators=[Optional(), NumberRange(min=0, max=100)])
    min_close_date = DateField('Min Close Date', validators=[Optional()], format='%Y-%m-%d')
    max_close_date = DateField('Max Close Date', validators=[Optional()], format='%Y-%m-%d')
    search = StringField('Search', validators=[Optional()])
    tags = StringField('Tags', validators=[Optional()])
    sort_by = SelectField('Sort By', choices=[
        ('created_at', 'Date Created'),
        ('updated_at', 'Date Updated'),
        ('title', 'Title'),
        ('value', 'Value'),
        ('probability', 'Probability'),
        ('expected_close_date', 'Expected Close Date')
    ], validators=[Optional()])
    sort_order = SelectField('Sort Order', choices=[
        ('asc', 'Ascending'),
        ('desc', 'Descending')
    ], validators=[Optional()])

class SaveFilterForm(FlaskForm):
    """Form for saving deal filters"""
    name = StringField('Filter Name', validators=[DataRequired(), Length(min=3, max=50)])
    filter_data = HiddenField('Filter Data', validators=[DataRequired()])
    is_default = IntegerField('Set as Default', validators=[Optional()])

class DealActivityForm(FlaskForm):
    """Form for creating deal activities"""
    activity_type = SelectField('Activity Type', choices=[
        ('call', 'Call'),
        ('email', 'Email'),
        ('meeting', 'Meeting'),
        ('note', 'Note'),
        ('task', 'Task')
    ], validators=[DataRequired()])
    title = StringField('Title', validators=[DataRequired(), Length(min=3, max=100)])
    description = TextAreaField('Description', validators=[Optional(), Length(max=1000)])
    scheduled_at = DateField('Date', validators=[Optional()], format='%Y-%m-%d')
    mark_completed = IntegerField('Mark as Completed', validators=[Optional()])
    completed_at = DateField('Completion Date', validators=[Optional()], format='%Y-%m-%d')
    
    def validate_completed_at(self, field):
        if field.data and self.scheduled_at.data and field.data < self.scheduled_at.data:
            raise ValidationError('Completion date cannot be before scheduled date')

class StageTransitionForm(FlaskForm):
    """Form for moving deals between stages"""
    from_stage_id = HiddenField('From Stage', validators=[DataRequired()])
    to_stage_id = SelectField('To Stage', validators=[DataRequired()], coerce=int)
    notes = TextAreaField('Notes', validators=[Optional(), Length(max=500)])

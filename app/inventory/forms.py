from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileAllowed, FileRequired
from wtforms import StringField, TextAreaField, SelectField, SubmitField, IntegerField, FloatField, MultipleFileField
from wtforms.validators import DataRequired, Length, Optional, NumberRange

class CarForm(FlaskForm):
    make = StringField('Make', validators=[DataRequired(), Length(max=64)])
    model = StringField('Model', validators=[DataRequired(), Length(max=64)])
    year = IntegerField('Year', validators=[DataRequired(), NumberRange(min=1900, max=2100)])
    trim = StringField('Trim', validators=[Optional(), Length(max=64)])
    color = StringField('Color', validators=[Optional(), Length(max=32)])
    price = FloatField('Price', validators=[DataRequired(), NumberRange(min=0)])
    mileage = IntegerField('Mileage', validators=[DataRequired(), NumberRange(min=0)])
    vin = StringField('VIN', validators=[DataRequired(), Length(min=17, max=17)])
    status = SelectField('Status', choices=[
        ('Available', 'Available'),
        ('Sold', 'Sold'),
        ('On Hold', 'On Hold'),
        ('In Service', 'In Service'),
        ('Pending Delivery', 'Pending Delivery')
    ])
    description = TextAreaField('Description', validators=[Optional(), Length(max=1000)])
    features = TextAreaField('Features', validators=[Optional(), Length(max=500)])
    new_or_used = SelectField('New or Used', choices=[
        ('New', 'New'),
        ('Used', 'Used')
    ])
    body_style = SelectField('Body Style', choices=[
        ('Sedan', 'Sedan'),
        ('SUV', 'SUV'),
        ('Truck', 'Truck'),
        ('Coupe', 'Coupe'),
        ('Convertible', 'Convertible'),
        ('Hatchback', 'Hatchback'),
        ('Wagon', 'Wagon'),
        ('Van', 'Van'),
        ('Other', 'Other')
    ])
    transmission = SelectField('Transmission', choices=[
        ('Automatic', 'Automatic'),
        ('Manual', 'Manual'),
        ('CVT', 'CVT'),
        ('Dual-Clutch', 'Dual-Clutch'),
        ('Electric', 'Electric')
    ])
    fuel_type = SelectField('Fuel Type', choices=[
        ('Gasoline', 'Gasoline'),
        ('Diesel', 'Diesel'),
        ('Electric', 'Electric'),
        ('Hybrid', 'Hybrid'),
        ('Plug-in Hybrid', 'Plug-in Hybrid'),
        ('Hydrogen', 'Hydrogen'),
        ('Other', 'Other')
    ])
    images = MultipleFileField('Images', validators=[Optional()])
    submit = SubmitField('Save Vehicle')

class CarSearchForm(FlaskForm):
    make = StringField('Make')
    model = StringField('Model')
    min_year = IntegerField('Min Year', validators=[Optional(), NumberRange(min=1900, max=2100)])
    max_year = IntegerField('Max Year', validators=[Optional(), NumberRange(min=1900, max=2100)])
    min_price = FloatField('Min Price', validators=[Optional(), NumberRange(min=0)])
    max_price = FloatField('Max Price', validators=[Optional(), NumberRange(min=0)])
    max_mileage = IntegerField('Max Mileage', validators=[Optional(), NumberRange(min=0)])
    status = SelectField('Status', choices=[
        ('', 'All Statuses'),
        ('Available', 'Available'),
        ('Sold', 'Sold'),
        ('On Hold', 'On Hold'),
        ('In Service', 'In Service'),
        ('Pending Delivery', 'Pending Delivery')
    ])
    new_or_used = SelectField('New or Used', choices=[
        ('', 'Both'),
        ('New', 'New'),
        ('Used', 'Used')
    ])
    body_style = SelectField('Body Style', choices=[
        ('', 'All Body Styles'),
        ('Sedan', 'Sedan'),
        ('SUV', 'SUV'),
        ('Truck', 'Truck'),
        ('Coupe', 'Coupe'),
        ('Convertible', 'Convertible'),
        ('Hatchback', 'Hatchback'),
        ('Wagon', 'Wagon'),
        ('Van', 'Van'),
        ('Other', 'Other')
    ])
    submit = SubmitField('Search')

class CarImageForm(FlaskForm):
    image = FileField('Image', validators=[
        FileRequired(),
        FileAllowed(['jpg', 'jpeg', 'png'], 'Images only!')
    ])
    is_primary = SelectField('Primary Image?', choices=[
        ('0', 'No'),
        ('1', 'Yes')
    ])
    submit = SubmitField('Upload Image')

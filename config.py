import os
from dotenv import load_dotenv

basedir = os.path.abspath(os.path.dirname(__file__))
load_dotenv(os.path.join(basedir, '.env'))

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'you-will-never-guess'
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or \
        'sqlite:///' + os.path.join(basedir, 'app.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Email configuration
    MAIL_SERVER = os.environ.get('MAIL_SERVER')
    MAIL_PORT = int(os.environ.get('MAIL_PORT') or 25)
    MAIL_USE_TLS = os.environ.get('MAIL_USE_TLS') is not None
    MAIL_USERNAME = os.environ.get('MAIL_USERNAME')
    MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD')
    MAIL_DEFAULT_SENDER = os.environ.get('MAIL_DEFAULT_SENDER')
    
    # Twilio configuration for SMS
    TWILIO_ACCOUNT_SID = os.environ.get('TWILIO_ACCOUNT_SID')
    TWILIO_AUTH_TOKEN = os.environ.get('TWILIO_AUTH_TOKEN')
    TWILIO_PHONE_NUMBER = os.environ.get('TWILIO_PHONE_NUMBER')
    
    # Dealership configuration
    DEALERSHIP_NAME = os.environ.get('DEALERSHIP_NAME') or 'Auto Dealership'
    DEALERSHIP_ADDRESS = os.environ.get('DEALERSHIP_ADDRESS') or '123 Car Street, Autoville, AU 12345'
    DEALERSHIP_PHONE = os.environ.get('DEALERSHIP_PHONE') or '(555) 123-4567'
    DEALERSHIP_WEBSITE = os.environ.get('DEALERSHIP_WEBSITE') or 'www.autodealership.com'
    DEALERSHIP_HOURS = os.environ.get('DEALERSHIP_HOURS') or 'Mon-Fri: 9am-8pm, Sat: 9am-6pm, Sun: Closed'

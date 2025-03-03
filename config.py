import os
from dotenv import load_dotenv

basedir = os.path.abspath(os.path.dirname(__file__))
load_dotenv(os.path.join(basedir, '.env'))

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'you-will-never-guess'
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or \
        'sqlite:///' + os.path.join(basedir, 'app.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Backup configuration
    BACKUP_ENABLED = os.environ.get('BACKUP_ENABLED', 'True').lower() in ('true', 'yes', '1')
    BACKUP_DIRECTORY = os.environ.get('BACKUP_DIRECTORY') or os.path.join(basedir, 'backups')
    BACKUP_INTERVAL_HOURS = int(os.environ.get('BACKUP_INTERVAL_HOURS') or 24)
    
    # User authentication settings
    SESSION_TYPE = 'filesystem'
    PERMANENT_SESSION_LIFETIME = 86400  # 24 hours in seconds
    REMEMBER_COOKIE_DURATION = 2592000  # 30 days in seconds
    PASSWORD_RESET_EXPIRY = 3600  # 1 hour in seconds
    
    # Email configuration
    MAIL_SERVER = os.environ.get('MAIL_SERVER')
    MAIL_PORT = int(os.environ.get('MAIL_PORT') or 25)
    MAIL_USE_TLS = os.environ.get('MAIL_USE_TLS', 'False').lower() in ('true', 'yes', '1')
    MAIL_USERNAME = os.environ.get('MAIL_USERNAME')
    MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD')
    MAIL_DEFAULT_SENDER = os.environ.get('MAIL_DEFAULT_SENDER')
    MAIL_SUBJECT_PREFIX = '[BDC Module] '
    
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
    
    # File upload settings
    UPLOAD_FOLDER = os.path.join(basedir, 'uploads')
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16 MB max upload size
    ALLOWED_EXTENSIONS = {'csv', 'xlsx', 'pdf', 'jpg', 'jpeg', 'png'}
    
    # Logging configuration
    LOG_TO_STDOUT = os.environ.get('LOG_TO_STDOUT')
    LOG_LEVEL = os.environ.get('LOG_LEVEL') or 'INFO'
    
    # API rate limiting
    RATELIMIT_DEFAULT = "200 per day, 50 per hour"
    RATELIMIT_STORAGE_URL = "memory://"
    
    @staticmethod
    def init_app(app):
        """Initialize application with this configuration"""
        # Create necessary directories
        os.makedirs(Config.BACKUP_DIRECTORY, exist_ok=True)
        os.makedirs(Config.UPLOAD_FOLDER, exist_ok=True)
        
        # Set up logging
        if Config.LOG_TO_STDOUT:
            import logging
            stream_handler = logging.StreamHandler()
            stream_handler.setLevel(getattr(logging, Config.LOG_LEVEL))
            app.logger.addHandler(stream_handler)
            
class DevelopmentConfig(Config):
    DEBUG = True
    SQLALCHEMY_DATABASE_URI = os.environ.get('DEV_DATABASE_URL') or \
        'sqlite:///' + os.path.join(basedir, 'dev-app.db')
    
class TestingConfig(Config):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = os.environ.get('TEST_DATABASE_URL') or \
        'sqlite:///' + os.path.join(basedir, 'test-app.db')
    WTF_CSRF_ENABLED = False
    
class ProductionConfig(Config):
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or \
        'sqlite:///' + os.path.join(basedir, 'app.db')
    
    @classmethod
    def init_app(cls, app):
        Config.init_app(app)
        
        # Production-specific logging
        import logging
        from logging.handlers import RotatingFileHandler
        file_handler = RotatingFileHandler('logs/bdc_module.log',
                                          maxBytes=10240, backupCount=10)
        file_handler.setFormatter(logging.Formatter(
            '%(asctime)s %(levelname)s: %(message)s '
            '[in %(pathname)s:%(lineno)d]'))
        file_handler.setLevel(logging.INFO)
        app.logger.addHandler(file_handler)
        
config = {
    'development': DevelopmentConfig,
    'testing': TestingConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
}

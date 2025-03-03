from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_migrate import Migrate
from flask_session import Session
from flask_wtf.csrf import CSRFProtect
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
import os
import logging
from logging.handlers import RotatingFileHandler

# Create extensions instances
db = SQLAlchemy()
migrate = Migrate()
login_manager = LoginManager()
csrf = CSRFProtect()
limiter = Limiter(key_func=get_remote_address)

# Try to import flask_mail, but provide a fallback if not available
try:
    from flask_mail import Mail
    mail = Mail()
except ImportError:
    # Create dummy Mail class if flask_mail is not installed
    class Mail:
        def __init__(self, app=None):
            self.app = app
            
        def init_app(self, app):
            self.app = app
            
        def send(self, message):
            app = self.app
            if app:
                app.logger.info(f"Would send email to {message.recipients} with subject: {message.subject}")
            else:
                print(f"Would send email to {message.recipients} with subject: {message.subject}")
    
    mail = Mail()

def create_app(config_name='default'):
    """Application factory function to create and configure the Flask app"""
    app = Flask(__name__)
    
    # Load configuration
    from config import config
    app.config.from_object(config[config_name])
    config[config_name].init_app(app)
    
    # Initialize extensions
    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)
    login_manager.login_view = 'auth.login'
    login_manager.login_message_category = 'info'
    csrf.init_app(app)
    mail.init_app(app)
    
    # Configure session
    if app.config.get('SESSION_TYPE'):
        Session(app)
    
    # Configure rate limiting
    limiter.init_app(app)
    
    # Set up logging
    if not app.debug and not app.testing:
        if not os.path.exists('logs'):
            os.mkdir('logs')
        file_handler = RotatingFileHandler('logs/bdc_module.log', 
                                          maxBytes=10240, backupCount=10)
        file_handler.setFormatter(logging.Formatter(
            '%(asctime)s %(levelname)s: %(message)s '
            '[in %(pathname)s:%(lineno)d]'))
        file_handler.setLevel(logging.INFO)
        app.logger.addHandler(file_handler)
        
        app.logger.setLevel(logging.INFO)
        app.logger.info('BDC Module startup')
    
    # Register blueprints
    from app.auth import bp as auth_bp
    app.register_blueprint(auth_bp, url_prefix='/auth')
    
    from app.leads import bp as leads_bp
    app.register_blueprint(leads_bp, url_prefix='/leads')
    
    from app.appointments import bp as appointments_bp
    app.register_blueprint(appointments_bp, url_prefix='/appointments')
    
    from app.communications import bp as communications_bp
    app.register_blueprint(communications_bp, url_prefix='/communications')
    
    from app.settings import bp as settings_bp
    app.register_blueprint(settings_bp, url_prefix='/settings')
    
    from app.main import bp as main_bp
    app.register_blueprint(main_bp)
    
    from app.api import bp as api_bp
    app.register_blueprint(api_bp, url_prefix='/api')
    
    from app.analytics import bp as analytics_bp
    app.register_blueprint(analytics_bp, url_prefix='/analytics')
    
    # Initialize database backup scheduler
    if app.config.get('BACKUP_ENABLED', False):
        from app.utils.backup import init_backup_scheduler
        init_backup_scheduler(app)
    
    return app

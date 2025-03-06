from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_bootstrap import Bootstrap5
from config import Config
import jinja2
import random

db = SQLAlchemy()
login = LoginManager()
login.login_view = 'auth.login'
bootstrap = Bootstrap5()

def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)
    
    db.init_app(app)
    login.init_app(app)
    bootstrap.init_app(app)
    
    # Register custom Jinja2 filters
    app.jinja_env.filters['nl2br'] = lambda value: jinja2.utils.markupsafe.Markup(value.replace('\n', '<br>')) if value else ''
    app.jinja_env.filters['random_bg'] = lambda value: f"random{random.randint(1, 8)}"
    
    from app.auth import bp as auth_bp
    app.register_blueprint(auth_bp, url_prefix='/auth')
    
    from app.main import bp as main_bp
    app.register_blueprint(main_bp)
    
    from app.leads import bp as leads_bp
    app.register_blueprint(leads_bp, url_prefix='/leads')
    
    from app.appointments import bp as appointments_bp
    app.register_blueprint(appointments_bp, url_prefix='/appointments')
    
    from app.communications import bp as communications_bp
    app.register_blueprint(communications_bp, url_prefix='/communications')
    
    from app.inventory import bp as inventory_bp
    app.register_blueprint(inventory_bp, url_prefix='/inventory')
    
    from app.reports import bp as reports_bp
    app.register_blueprint(reports_bp, url_prefix='/reports')
    
    # Initialize reports commands
    from app.reports import init_app as init_reports
    init_reports(app)
    
    return app

from app import models

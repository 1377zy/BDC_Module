from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_bootstrap import Bootstrap
from flask_mail import Mail
from config import Config
from datetime import datetime

db = SQLAlchemy()
login = LoginManager()
login.login_view = 'auth.login'
bootstrap = Bootstrap()
mail = Mail()

def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)
    
    db.init_app(app)
    login.init_app(app)
    bootstrap.init_app(app)
    mail.init_app(app)
    
    # Add context processor for templates
    @app.context_processor
    def inject_now():
        return {'now': datetime.now}
    
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
    
    from app.search import bp as search_bp
    app.register_blueprint(search_bp, url_prefix='/search')
    
    from app.analytics import bp as analytics_bp
    app.register_blueprint(analytics_bp, url_prefix='/analytics')
    
    return app

from app import models_main

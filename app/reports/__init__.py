from flask import Blueprint

bp = Blueprint('reports', __name__)

from app.reports import routes, templates

def init_app(app):
    """Initialize the reports blueprint with the app."""
    from app.reports import commands
    commands.init_app(app)

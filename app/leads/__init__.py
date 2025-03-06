from flask import Blueprint

bp = Blueprint('leads', __name__)

from app.leads import routes

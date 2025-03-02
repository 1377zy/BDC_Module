from flask import Blueprint

bp = Blueprint('communications', __name__)

from app.communications import routes

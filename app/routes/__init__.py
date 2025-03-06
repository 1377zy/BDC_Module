# Import and register all route blueprints here
from app.routes.segmentation_routes import segmentation_bp

def register_all_routes(app):
    """Register all route blueprints with the Flask app."""
    app.register_blueprint(segmentation_bp, url_prefix='/leads')

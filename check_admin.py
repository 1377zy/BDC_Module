from app import create_app, db
from app.models_main import User

app = create_app()
with app.app_context():
    user = User.query.filter_by(role='admin').first()
    print('Admin user:', user.username if user else None)

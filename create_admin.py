from app import create_app, db
from app.models_main import User
from werkzeug.security import generate_password_hash

app = create_app()
with app.app_context():
    # Check if admin user already exists
    admin = User.query.filter_by(username='admin').first()
    if admin:
        print('Admin user already exists')
    else:
        # Create admin user
        admin = User(
            username='admin',
            email='admin@example.com',
            first_name='Admin',
            last_name='User',
            role='admin',
            is_active=True,
            password_hash=generate_password_hash('adminpassword')
        )
        db.session.add(admin)
        db.session.commit()
        print('Admin user created successfully')

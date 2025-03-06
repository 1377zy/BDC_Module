from app import create_app, db
from app.models_main import User

app = create_app()
with app.app_context():
    # Get the admin user
    admin = User.query.filter_by(username='admin').first()
    if admin:
        # Reset the password
        admin.set_password('admin123')
        db.session.commit()
        print(f'Password reset for user {admin.username}')
    else:
        print('Admin user not found')

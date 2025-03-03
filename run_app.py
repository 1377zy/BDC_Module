from flask import Flask, render_template, redirect, url_for, flash, request
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
from flask_bootstrap import Bootstrap
import os

# Create Flask app
app = Flask(__name__, template_folder='app/templates', static_folder='app/static')
app.config['SECRET_KEY'] = 'development-secret-key-123'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///app.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Initialize extensions
db = SQLAlchemy(app)
login = LoginManager(app)
login.login_view = 'login'
bootstrap = Bootstrap(app)

# Add template functions
@app.context_processor
def inject_now():
    return {'now': datetime.now}

# Define models
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), index=True, unique=True)
    email = db.Column(db.String(120), index=True, unique=True)
    password_hash = db.Column(db.String(128))
    first_name = db.Column(db.String(64))
    last_name = db.Column(db.String(64))
    role = db.Column(db.String(20), default='bdc_agent')
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

@login.user_loader
def load_user(id):
    return User.query.get(int(id))

class Lead(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    first_name = db.Column(db.String(64))
    last_name = db.Column(db.String(64))
    email = db.Column(db.String(120), index=True)
    phone = db.Column(db.String(20))
    source = db.Column(db.String(64))
    status = db.Column(db.String(64))
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class Appointment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    lead_id = db.Column(db.Integer, db.ForeignKey('lead.id'))
    date = db.Column(db.Date)
    time = db.Column(db.Time)
    purpose = db.Column(db.String(64))
    status = db.Column(db.String(20))
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    lead = db.relationship('Lead', backref='appointments')

class Communication(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    lead_id = db.Column(db.Integer, db.ForeignKey('lead.id'))
    type = db.Column(db.String(20))
    content = db.Column(db.Text)
    sent_at = db.Column(db.DateTime, default=datetime.utcnow)
    lead = db.relationship('Lead', backref='communications')

# Routes
@app.route('/')
def index():
    if not current_user.is_authenticated:
        return redirect(url_for('login'))
    
    # Dashboard stats
    stats = {
        'total_leads': Lead.query.count(),
        'new_leads': Lead.query.filter_by(status='New').count(),
        'appointments_today': Appointment.query.filter_by(date=datetime.utcnow().date()).count(),
        'communications_today': Communication.query.filter(
            Communication.sent_at >= datetime.utcnow().replace(hour=0, minute=0, second=0)
        ).count()
    }
    
    # Recent leads
    recent_leads = Lead.query.order_by(Lead.created_at.desc()).limit(5).all()
    
    # Today's appointments
    today_appointments = Appointment.query.filter_by(date=datetime.utcnow().date()).all()
    
    return render_template('main/index.html', 
                           stats=stats, 
                           recent_leads=recent_leads,
                           today_appointments=today_appointments)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        user = User.query.filter_by(username=username).first()
        
        if user is None or not user.check_password(password):
            flash('Invalid username or password', 'danger')
            return redirect(url_for('login'))
        
        login_user(user, remember=True)
        return redirect(url_for('index'))
    
    return render_template('auth/login.html')

@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('login'))

@app.route('/leads')
@login_required
def leads():
    all_leads = Lead.query.all()
    return render_template('leads/index.html', leads=all_leads)

@app.route('/appointments')
@login_required
def appointments():
    all_appointments = Appointment.query.all()
    return render_template('appointments/index.html', appointments=all_appointments)

@app.route('/communications')
@login_required
def communications():
    all_communications = Communication.query.all()
    return render_template('communications/index.html', communications=all_communications)

# Initialize the database
@app.before_first_request
def create_tables():
    db.create_all()
    
    # Create admin user if it doesn't exist
    if User.query.filter_by(username='admin').first() is None:
        admin = User(
            username='admin',
            email='admin@example.com',
            first_name='Admin',
            last_name='User',
            role='admin'
        )
        admin.set_password('admin123')
        db.session.add(admin)
        db.session.commit()

if __name__ == '__main__':
    app.run(debug=True, port=5001)

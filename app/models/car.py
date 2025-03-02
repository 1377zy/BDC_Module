from app import db
from datetime import datetime

class Car(db.Model):
    """Model for car inventory in the dealership."""
    id = db.Column(db.Integer, primary_key=True)
    make = db.Column(db.String(64), index=True)
    model = db.Column(db.String(64), index=True)
    year = db.Column(db.Integer, index=True)
    trim = db.Column(db.String(64))
    color = db.Column(db.String(32))
    price = db.Column(db.Float)
    mileage = db.Column(db.Integer)
    vin = db.Column(db.String(17), unique=True)
    status = db.Column(db.String(20))  # Available, Sold, On Hold, etc.
    description = db.Column(db.Text)
    features = db.Column(db.Text)
    new_or_used = db.Column(db.String(10))  # New or Used
    body_style = db.Column(db.String(32))  # Sedan, SUV, Truck, etc.
    transmission = db.Column(db.String(20))  # Automatic, Manual, etc.
    fuel_type = db.Column(db.String(20))  # Gasoline, Diesel, Electric, Hybrid
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    images = db.relationship('CarImage', backref='car', lazy='dynamic', cascade="all, delete-orphan")
    
    def __repr__(self):
        return f'<Car {self.year} {self.make} {self.model}>'
    
    @staticmethod
    def get_next_unseen(user_id):
        """Get the next car that hasn't been seen by the user.
        This would be used for the swiping functionality."""
        from app.models import Match
        
        # Get IDs of cars the user has already seen
        seen_car_ids = db.session.query(Match.car_id).filter(Match.user_id == user_id).all()
        seen_car_ids = [car_id for (car_id,) in seen_car_ids]
        
        # Get the next unseen car
        next_car = Car.query.filter(
            Car.id.notin_(seen_car_ids),
            Car.status == 'Available'
        ).first()
        
        return next_car

class CarImage(db.Model):
    """Model for car images."""
    id = db.Column(db.Integer, primary_key=True)
    car_id = db.Column(db.Integer, db.ForeignKey('car.id'))
    url = db.Column(db.String(256))
    is_primary = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<CarImage {self.id} for Car {self.car_id}>'

class Match(db.Model):
    """Model for tracking user-car matches (likes/dislikes)."""
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    car_id = db.Column(db.Integer, db.ForeignKey('car.id'))
    liked = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Define a unique constraint to prevent duplicate matches
    __table_args__ = (db.UniqueConstraint('user_id', 'car_id', name='_user_car_uc'),)
    
    def __repr__(self):
        return f'<Match User {self.user_id} {"likes" if self.liked else "dislikes"} Car {self.car_id}>'
    
    @staticmethod
    def create(user_id, car_id, liked):
        """Create a new match or update an existing one."""
        match = Match.query.filter_by(user_id=user_id, car_id=car_id).first()
        
        if match:
            match.liked = liked
        else:
            match = Match(user_id=user_id, car_id=car_id, liked=liked)
            db.session.add(match)
        
        db.session.commit()
        return match
    
    @staticmethod
    def get_user_matches(user_id):
        """Get all cars that a user has liked."""
        return Match.query.filter_by(user_id=user_id, liked=True).all()

class UserPreference(db.Model):
    """Model for storing user preferences for car matching."""
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), unique=True)
    max_price = db.Column(db.Float)
    min_year = db.Column(db.Integer)
    preferred_makes = db.Column(db.String(256))  # Comma-separated list
    preferred_body_styles = db.Column(db.String(256))  # Comma-separated list
    max_mileage = db.Column(db.Integer)
    new_or_used = db.Column(db.String(10))  # New, Used, or Both
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f'<UserPreference for User {self.user_id}>'
    
    @staticmethod
    def get_preferences(user_id):
        """Get preferences for a user, creating default ones if none exist."""
        prefs = UserPreference.query.filter_by(user_id=user_id).first()
        
        if not prefs:
            prefs = UserPreference(
                user_id=user_id,
                max_price=50000.0,
                min_year=datetime.now().year - 5,
                preferred_makes="",
                preferred_body_styles="",
                max_mileage=100000,
                new_or_used="Both"
            )
            db.session.add(prefs)
            db.session.commit()
        
        return prefs
    
    @staticmethod
    def update_preferences(user_id, data):
        """Update preferences for a user."""
        prefs = UserPreference.get_preferences(user_id)
        
        # Update fields from data
        for key, value in data.items():
            if hasattr(prefs, key):
                setattr(prefs, key, value)
        
        db.session.commit()
        return prefs

from flask import Blueprint

bp = Blueprint('leads', __name__)

from app.leads import routes, advanced, task_routes

from flask_login import login_required, current_user
from ..models import Car, Match, UserPreference

@bp.route('/cars')
@login_required
def car_listings():
    """List all available cars."""
    cars = Car.query.filter_by(is_active=True).all()
    return render_template('leads/cars.html', cars=cars)

@bp.route('/car/<int:car_id>')
@login_required
def car_detail(car_id):
    """Show detailed information about a car."""
    car = Car.query.get_or_404(car_id)
    return render_template('leads/car_detail.html', car=car)

@bp.route('/car/add', methods=['GET', 'POST'])
@login_required
def add_car():
    """Add a new car listing."""
    if request.method == 'POST':
        car = Car(
            make=request.form['make'],
            model=request.form['model'],
            year=request.form['year'],
            price=request.form['price'],
            mileage=request.form['mileage'],
            description=request.form['description'],
            images=request.files.getlist('images')
        )
        car.save()
        return jsonify({'status': 'success', 'car_id': car.id})
    
    return render_template('leads/add_car.html')

@bp.route('/matches/dealer')
@login_required
def dealer_matches():
    """Show matches for dealer's cars."""
    matches = Match.query.filter(
        Match.car_id.in_(Car.query.with_entities(Car.id))
    ).all()
    return render_template('leads/dealer_matches.html', matches=matches)

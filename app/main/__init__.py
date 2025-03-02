from flask import Blueprint, render_template, jsonify, request
from flask_login import login_required, current_user
from ..models import Car, UserPreference, Match

main = Blueprint('main', __name__)

@main.route('/')
@login_required
def index():
    return render_template('main/index.html')

@main.route('/swipe')
@login_required
def swipe():
    """Show the next car for swiping."""
    # Get next unseen car based on user preferences
    next_car = Car.get_next_unseen(current_user.id)
    return render_template('main/swipe.html', car=next_car)

@main.route('/like/<int:car_id>', methods=['POST'])
@login_required
def like_car(car_id):
    """Handle liking a car."""
    match = Match.create(user_id=current_user.id, car_id=car_id, liked=True)
    if match:
        return jsonify({'status': 'success', 'match': True})
    return jsonify({'status': 'success', 'match': False})

@main.route('/dislike/<int:car_id>', methods=['POST'])
@login_required
def dislike_car(car_id):
    """Handle disliking a car."""
    Match.create(user_id=current_user.id, car_id=car_id, liked=False)
    return jsonify({'status': 'success'})

@main.route('/matches')
@login_required
def matches():
    """Show user's matched cars."""
    user_matches = Match.get_user_matches(current_user.id)
    return render_template('main/matches.html', matches=user_matches)

@main.route('/preferences', methods=['GET', 'POST'])
@login_required
def preferences():
    """Handle user preferences."""
    if request.method == 'POST':
        UserPreference.update_preferences(
            user_id=current_user.id,
            data=request.form
        )
        return jsonify({'status': 'success'})
    
    user_preferences = UserPreference.get_preferences(current_user.id)
    return render_template('main/preferences.html', preferences=user_preferences)

from app import create_app, db
from app.models import User, Lead, VehicleInterest, Communication, Appointment, EmailTemplate, SMSTemplate
from app.models.car import Car, CarImage, Match, UserPreference

app = create_app()

@app.shell_context_processor
def make_shell_context():
    return {
        'db': db, 
        'User': User, 
        'Lead': Lead, 
        'VehicleInterest': VehicleInterest,
        'Communication': Communication,
        'Appointment': Appointment,
        'EmailTemplate': EmailTemplate,
        'SMSTemplate': SMSTemplate,
        'Car': Car,
        'CarImage': CarImage,
        'Match': Match,
        'UserPreference': UserPreference
    }

if __name__ == '__main__':
    app.run(debug=True)

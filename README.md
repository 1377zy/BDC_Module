# Auto Dealership BDC Module

## Project Structure
- `app/`: Main application directory
  - `templates/`: HTML templates for the UI
  - `communications/`: Handle communication (e.g., emails, SMS)
  - `appointments/`: Manage appointments for test drives and sales consultations
  - `leads/`: Manage leads and customer interactions
  - `main/`: Main application logic and dashboard
  - `auth/`: User authentication and management

## Key Features
- Lead management and tracking
- Appointment scheduling and management
- Communication tools (email and SMS)
- Performance analytics and reporting
- User authentication and role management

## Technologies
- Backend: Python (Flask)
- Frontend: HTML, CSS, JavaScript, Bootstrap 5
- Database: SQLite (can be configured for PostgreSQL)
- Email: SMTP integration
- SMS: Twilio integration

## Initial Setup
1. Clone the repository
2. Create a virtual environment: `python -m venv venv`
3. Activate the virtual environment:
   - Windows: `venv\Scripts\activate`
   - Unix/MacOS: `source venv/bin/activate`
4. Install dependencies: `pip install -r requirements.txt`
5. Copy `.env.example` to `.env` and configure your environment variables
6. Initialize the database: `python init_db.py`
7. Run the application: `python app.py`

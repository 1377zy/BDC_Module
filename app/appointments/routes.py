from flask import render_template, flash, redirect, url_for, request, jsonify
from flask_login import login_required
from app import db
from app.appointments import bp
from app.appointments.forms import AppointmentForm, AppointmentSearchForm
from app.models import Appointment, Lead
from app.email.email_handler import send_appointment_confirmation_email, send_appointment_update_email
from app.sms.sms_handler import send_appointment_confirmation_sms, send_appointment_update_sms
from datetime import datetime, timedelta, time

@bp.route('/list')
@login_required
def list_appointments():
    form = AppointmentSearchForm()
    page = request.args.get('page', 1, type=int)
    
    # Create base query
    query = Appointment.query
    
    # Apply filters if provided in URL
    status = request.args.get('status')
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    lead_name = request.args.get('lead_name')
    
    if status:
        query = query.filter(Appointment.status == status)
        form.status.data = status
    
    if start_date:
        try:
            start_date_obj = datetime.strptime(start_date, '%Y-%m-%d').date()
            query = query.filter(Appointment.date >= start_date_obj)
            form.start_date.data = start_date_obj
        except ValueError:
            pass
        
    if end_date:
        try:
            end_date_obj = datetime.strptime(end_date, '%Y-%m-%d').date()
            query = query.filter(Appointment.date <= end_date_obj)
            form.end_date.data = end_date_obj
        except ValueError:
            pass
        
    if lead_name:
        form.lead_name.data = lead_name
        query = query.join(Lead).filter(
            (Lead.first_name.ilike(f'%{lead_name}%')) |
            (Lead.last_name.ilike(f'%{lead_name}%'))
        )
    
    # Order by date and time
    appointments = query.order_by(Appointment.date, Appointment.time).paginate(
        page=page, per_page=10, error_out=False)
    
    return render_template('appointments/list.html', title='All Appointments', 
                           appointments=appointments, form=form)

@bp.route('/create/<int:lead_id>', methods=['GET', 'POST'])
@login_required
def create_appointment(lead_id):
    lead = Lead.query.get_or_404(lead_id)
    form = AppointmentForm()
    
    if form.validate_on_submit():
        appointment = Appointment(
            lead_id=lead.id,
            date=form.date.data,
            time=form.time.data,
            purpose=form.purpose.data,
            status=form.status.data,
            notes=form.notes.data
        )
        db.session.add(appointment)
        
        # Update lead status if currently before "Appointment Set"
        if lead.status in ['New', 'Contacted', 'Qualified']:
            lead.status = 'Appointment Set'
        
        db.session.commit()
        
        # Send confirmation email and SMS
        try:
            if lead.email:
                send_appointment_confirmation_email(lead, appointment)
            if lead.phone:
                send_appointment_confirmation_sms(lead, appointment)
        except Exception as e:
            flash(f'Appointment created but there was an error sending confirmation: {str(e)}', 'warning')
        else:
            flash('Appointment created and confirmation sent successfully!', 'success')
            
        return redirect(url_for('leads.view_lead', lead_id=lead.id))
    
    return render_template('appointments/create.html', title='Schedule Appointment', 
                           form=form, lead=lead)

@bp.route('/edit/<int:appointment_id>', methods=['GET', 'POST'])
@login_required
def edit_appointment(appointment_id):
    appointment = Appointment.query.get_or_404(appointment_id)
    lead = Lead.query.get(appointment.lead_id)
    form = AppointmentForm()
    
    if form.validate_on_submit():
        # Save the previous status to check if it changed
        previous_status = appointment.status
        
        appointment.date = form.date.data
        appointment.time = form.time.data
        appointment.purpose = form.purpose.data
        appointment.status = form.status.data
        appointment.notes = form.notes.data
        
        db.session.commit()
        
        # Send update notification if the status changed
        if previous_status != form.status.data:
            try:
                if lead.email:
                    send_appointment_update_email(lead, appointment)
                if lead.phone:
                    send_appointment_update_sms(lead, appointment)
            except Exception as e:
                flash(f'Appointment updated but there was an error sending notification: {str(e)}', 'warning')
            else:
                flash('Appointment updated and notification sent successfully!', 'success')
        else:
            flash('Appointment updated successfully!', 'success')
            
        return redirect(url_for('appointments.view_appointment', appointment_id=appointment.id))
    
    elif request.method == 'GET':
        form.date.data = appointment.date
        form.time.data = appointment.time
        form.purpose.data = appointment.purpose
        form.status.data = appointment.status
        form.notes.data = appointment.notes
        
    return render_template('appointments/edit.html', title='Edit Appointment', 
                           form=form, appointment=appointment, lead=lead)

@bp.route('/<int:appointment_id>')
@login_required
def view_appointment(appointment_id):
    appointment = Appointment.query.get_or_404(appointment_id)
    lead = Lead.query.get(appointment.lead_id)
    
    return render_template('appointments/view.html', title='View Appointment',
                           appointment=appointment, lead=lead)

@bp.route('/today')
@login_required
def today_appointments():
    today = datetime.now().date()
    appointments = Appointment.query.filter(
        Appointment.date == today,
        Appointment.status.in_(['Scheduled', 'Confirmed'])
    ).order_by(Appointment.time).all()
    
    return render_template('appointments/today.html', title="Today's Appointments",
                           appointments=appointments, date=today)

@bp.route('/week')
@login_required
def week_appointments():
    today = datetime.now().date()
    end_of_week = today + timedelta(days=6)
    
    appointments = Appointment.query.filter(
        Appointment.date >= today,
        Appointment.date <= end_of_week,
        Appointment.status.in_(['Scheduled', 'Confirmed'])
    ).order_by(Appointment.date, Appointment.time).all()
    
    # Group appointments by date
    appointments_by_date = {}
    for app in appointments:
        date_str = app.date.strftime('%Y-%m-%d')
        if date_str not in appointments_by_date:
            appointments_by_date[date_str] = []
        appointments_by_date[date_str].append(app)
    
    return render_template('appointments/week.html', title="This Week's Appointments",
                           appointments_by_date=appointments_by_date, 
                           start_date=today, end_date=end_of_week)

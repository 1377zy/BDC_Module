from flask import render_template, flash, redirect, url_for, request, current_app
from flask_login import current_user, login_required
from app.main import bp
from app.models import Lead, Appointment, Communication
from datetime import datetime, timedelta

@bp.route('/')
@bp.route('/index')
@login_required
def index():
    # Get dashboard data
    today = datetime.now().date()
    tomorrow = today + timedelta(days=1)
    
    # Today's appointments
    todays_appointments = Appointment.query.filter(
        Appointment.date == today,
        Appointment.status.in_(['Scheduled', 'Confirmed'])
    ).order_by(Appointment.time).all()
    
    # Tomorrow's appointments
    tomorrows_appointments = Appointment.query.filter(
        Appointment.date == tomorrow,
        Appointment.status.in_(['Scheduled', 'Confirmed'])
    ).order_by(Appointment.time).all()
    
    # Recent leads (last 7 days)
    week_ago = today - timedelta(days=7)
    recent_leads = Lead.query.filter(
        Lead.created_at >= week_ago
    ).order_by(Lead.created_at.desc()).limit(10).all()
    
    # Recent communications
    recent_communications = Communication.query.order_by(
        Communication.sent_at.desc()
    ).limit(10).all()
    
    # Calculate KPIs
    total_leads = Lead.query.count()
    appointments_set = Appointment.query.filter(
        Appointment.created_at >= week_ago
    ).count()
    appointment_rate = 0
    if total_leads > 0:
        appointment_rate = (appointments_set / total_leads) * 100
        
    # Leads by status
    new_leads = Lead.query.filter_by(status='New').count()
    contacted_leads = Lead.query.filter_by(status='Contacted').count()
    appointment_set_leads = Lead.query.filter_by(status='Appointment Set').count()
    
    return render_template('main/index.html', title='Dashboard',
                          todays_appointments=todays_appointments,
                          tomorrows_appointments=tomorrows_appointments,
                          recent_leads=recent_leads,
                          recent_communications=recent_communications,
                          total_leads=total_leads,
                          appointments_set=appointments_set,
                          appointment_rate=appointment_rate,
                          new_leads=new_leads,
                          contacted_leads=contacted_leads,
                          appointment_set_leads=appointment_set_leads)

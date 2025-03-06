from flask import render_template, flash, redirect, url_for, request, jsonify, current_app
from flask_login import current_user, login_required
from app.main import bp
from app.models_main import Lead, Appointment, Communication, User
from datetime import datetime, timedelta
import json

@bp.route('/')
@bp.route('/index')
@login_required
def index():
    # Get dashboard data
    today = datetime.now().date()
    tomorrow = today + timedelta(days=1)
    week_ago = today - timedelta(days=7)
    
    # Today's appointments
    today_appointments = Appointment.query.filter(
        Appointment.date == today,
        Appointment.status.in_(['Scheduled', 'Confirmed'])
    ).order_by(Appointment.time).all()
    
    # Tomorrow's appointments
    tomorrow_appointments = Appointment.query.filter(
        Appointment.date == tomorrow,
        Appointment.status.in_(['Scheduled', 'Confirmed'])
    ).order_by(Appointment.time).all()
    
    # Recent leads (last 7 days)
    recent_leads = Lead.query.filter(
        Lead.created_at >= week_ago
    ).order_by(Lead.created_at.desc()).limit(10).all()
    
    # Recent communications
    recent_communications = Communication.query.order_by(
        Communication.sent_at.desc()
    ).limit(10).all()
    
    # Calculate statistics
    total_leads = Lead.query.count()
    total_appointments = Appointment.query.count()
    todays_appointment_count = len(today_appointments)
    total_communications = Communication.query.count()
    
    # Calculate conversion rate (leads to appointments)
    conversion_rate = 0
    if total_leads > 0:
        leads_with_appointments = Lead.query.join(Appointment).distinct().count()
        conversion_rate = round((leads_with_appointments / total_leads) * 100, 1)
    
    # Calculate average response time
    avg_response_time = "N/A"
    communications = Communication.query.filter(
        Communication.direction == "Outbound",
        Communication.sent_at >= week_ago
    ).all()
    
    if communications:
        response_times = []
        for comm in communications:
            lead = Lead.query.get(comm.lead_id)
            if lead:
                # Calculate time between lead creation and first communication
                if lead.created_at and comm.sent_at:
                    response_time = (comm.sent_at - lead.created_at).total_seconds() / 3600  # hours
                    response_times.append(response_time)
        
        if response_times:
            avg_response_time = round(sum(response_times) / len(response_times), 1)
    
    # Lead status breakdown
    statuses = ['New', 'Contacted', 'Qualified', 'Appointment Set', 'Sold', 'Lost']
    lead_status_counts = {}
    for status in statuses:
        count = Lead.query.filter_by(status=status).count()
        if count > 0:
            lead_status_counts[status] = count
    
    # Calculate percentages
    lead_status_breakdown = {}
    for status, count in lead_status_counts.items():
        percentage = round((count / total_leads) * 100) if total_leads > 0 else 0
        lead_status_breakdown[status] = percentage
    
    # Get follow-ups due today
    follow_ups = []  # This would be populated from a FollowUp model if it exists
    
    # Compile stats
    stats = {
        'total_leads': total_leads,
        'total_appointments': total_appointments,
        'todays_appointments': todays_appointment_count,
        'total_communications': total_communications,
        'conversion_rate': conversion_rate,
        'avg_response_time': avg_response_time,
        'lead_status_breakdown': lead_status_breakdown
    }
    
    return render_template('main/index.html', 
                          title='Dashboard',
                          stats=stats,
                          today_appointments=today_appointments,
                          tomorrow_appointments=tomorrow_appointments,
                          recent_leads=recent_leads,
                          recent_communications=recent_communications,
                          follow_ups=follow_ups)

@bp.route('/matches')
@login_required
def matches():
    """Show leads with high match potential."""
    # This would typically use a matching algorithm based on lead preferences
    # For now, we'll simulate it with a simple query
    
    # Get leads with vehicle interests
    leads_with_interests = Lead.query.join(Lead.vehicle_interests).all()
    
    # Create a list of "matches" with simulated scores
    matches = []
    for lead in leads_with_interests:
        # Calculate a match score (this would be more sophisticated in a real app)
        # Here we're just using a random score between 70-95 for demonstration
        import random
        score = random.randint(70, 95)
        
        matches.append({
            'lead': lead,
            'score': score,
            'matched_on': datetime.now().date() - timedelta(days=random.randint(0, 5))
        })
    
    # Sort by score (highest first)
    matches.sort(key=lambda x: x['score'], reverse=True)
    
    return render_template('main/matches.html', matches=matches)

@bp.route('/preferences', methods=['GET', 'POST'])
@login_required
def preferences():
    """Handle system preferences."""
    if request.method == 'POST':
        # Process the form data
        data = request.get_json()
        
        # In a real app, you would save these preferences to a database
        # For now, we'll just return success
        return jsonify({'status': 'success'})
    
    # Get current preferences (this would come from a database in a real app)
    preferences = {
        'email_notifications': True,
        'sms_notifications': True,
        'appointment_reminders': True,
        'appointment_buffer': 30,
        'reminder_time': 24,
        'lead_follow_up_days': 3,
        'auto_assign_leads': False,
        'dashboard_timeframe': 'week'
    }
    
    return render_template('main/preferences.html', preferences=preferences)

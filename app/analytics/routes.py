from flask import render_template, request, jsonify, current_app, send_file
from flask_login import login_required, current_user
from sqlalchemy import func, extract, case, and_, or_
from datetime import datetime, timedelta
import calendar
import json
import io
import csv
import xlsxwriter
from app.analytics import bp
from app.models import Lead, Appointment, Communication, User
from app.decorators import manager_required
from app import db

@bp.route('/dashboard')
@login_required
def dashboard():
    """Main analytics dashboard with key performance indicators"""
    # Date ranges
    today = datetime.now().date()
    start_of_week = today - timedelta(days=today.weekday())
    start_of_month = today.replace(day=1)
    
    # Lead statistics
    total_leads = Lead.query.count()
    new_leads_today = Lead.query.filter(func.date(Lead.created_at) == today).count()
    new_leads_week = Lead.query.filter(Lead.created_at >= start_of_week).count()
    new_leads_month = Lead.query.filter(Lead.created_at >= start_of_month).count()
    
    # Lead statuses
    lead_statuses = db.session.query(
        Lead.status, func.count(Lead.id)
    ).group_by(Lead.status).all()
    
    # Appointment statistics
    total_appointments = Appointment.query.count()
    appointments_today = Appointment.query.filter(
        func.date(Appointment.date) == today
    ).count()
    appointments_week = Appointment.query.filter(
        Appointment.date >= start_of_week
    ).count()
    appointments_month = Appointment.query.filter(
        Appointment.date >= start_of_month
    ).count()
    
    # Appointment statuses
    appointment_statuses = db.session.query(
        Appointment.status, func.count(Appointment.id)
    ).group_by(Appointment.status).all()
    
    # Communication statistics
    total_communications = Communication.query.count()
    communications_today = Communication.query.filter(
        func.date(Communication.sent_at) == today
    ).count()
    communications_week = Communication.query.filter(
        Communication.sent_at >= start_of_week
    ).count()
    communications_month = Communication.query.filter(
        Communication.sent_at >= start_of_month
    ).count()
    
    # Communication types
    communication_types = db.session.query(
        Communication.type, func.count(Communication.id)
    ).group_by(Communication.type).all()
    
    # User performance (for managers/admins)
    user_performance = None
    if current_user.role in ['admin', 'manager']:
        user_performance = db.session.query(
            User.username,
            func.count(Lead.id).label('leads'),
            func.count(Appointment.id).label('appointments'),
            func.count(Communication.id).label('communications')
        ).outerjoin(Lead, User.id == Lead.user_id
        ).outerjoin(Appointment, User.id == Appointment.user_id
        ).outerjoin(Communication, User.id == Communication.user_id
        ).group_by(User.username).all()
    
    return render_template('analytics/dashboard.html',
                          title='Analytics Dashboard',
                          total_leads=total_leads,
                          new_leads_today=new_leads_today,
                          new_leads_week=new_leads_week,
                          new_leads_month=new_leads_month,
                          lead_statuses=lead_statuses,
                          total_appointments=total_appointments,
                          appointments_today=appointments_today,
                          appointments_week=appointments_week,
                          appointments_month=appointments_month,
                          appointment_statuses=appointment_statuses,
                          total_communications=total_communications,
                          communications_today=communications_today,
                          communications_week=communications_week,
                          communications_month=communications_month,
                          communication_types=communication_types,
                          user_performance=user_performance)

@bp.route('/leads')
@login_required
def lead_analytics():
    """Detailed lead analytics"""
    # Lead source analysis
    lead_sources = db.session.query(
        Lead.source, func.count(Lead.id)
    ).group_by(Lead.source).all()
    
    # Lead status by source
    lead_status_by_source = db.session.query(
        Lead.source, Lead.status, func.count(Lead.id)
    ).group_by(Lead.source, Lead.status).all()
    
    # Lead conversion rates (leads with appointments)
    lead_with_appointments = db.session.query(
        Lead.id
    ).join(Appointment).distinct().count()
    
    conversion_rate = 0
    if total_leads := Lead.query.count():
        conversion_rate = (lead_with_appointments / total_leads) * 100
    
    # Lead age analysis
    current_time = datetime.now()
    lead_age_buckets = {
        'Less than 1 day': 0,
        '1-3 days': 0,
        '4-7 days': 0,
        '1-2 weeks': 0,
        '2-4 weeks': 0,
        'Over 1 month': 0
    }
    
    for lead in Lead.query.all():
        age = (current_time - lead.created_at).days
        if age < 1:
            lead_age_buckets['Less than 1 day'] += 1
        elif 1 <= age <= 3:
            lead_age_buckets['1-3 days'] += 1
        elif 4 <= age <= 7:
            lead_age_buckets['4-7 days'] += 1
        elif 8 <= age <= 14:
            lead_age_buckets['1-2 weeks'] += 1
        elif 15 <= age <= 30:
            lead_age_buckets['2-4 weeks'] += 1
        else:
            lead_age_buckets['Over 1 month'] += 1
    
    # Monthly lead trends
    year = datetime.now().year
    monthly_leads = []
    
    for month in range(1, 13):
        count = Lead.query.filter(
            extract('year', Lead.created_at) == year,
            extract('month', Lead.created_at) == month
        ).count()
        monthly_leads.append({
            'month': calendar.month_name[month],
            'count': count
        })
    
    return render_template('analytics/leads.html',
                          title='Lead Analytics',
                          lead_sources=lead_sources,
                          lead_status_by_source=lead_status_by_source,
                          lead_with_appointments=lead_with_appointments,
                          conversion_rate=conversion_rate,
                          lead_age_buckets=lead_age_buckets,
                          monthly_leads=monthly_leads)

@bp.route('/appointments')
@login_required
def appointment_analytics():
    """Detailed appointment analytics"""
    # Appointment outcome analysis
    appointment_outcomes = db.session.query(
        Appointment.status, func.count(Appointment.id)
    ).group_by(Appointment.status).all()
    
    # Appointment purpose analysis
    appointment_purposes = db.session.query(
        Appointment.purpose, func.count(Appointment.id)
    ).group_by(Appointment.purpose).all()
    
    # Appointment day of week distribution
    days = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
    day_counts = [0] * 7
    
    for appointment in Appointment.query.all():
        day_of_week = appointment.date.weekday()
        day_counts[day_of_week] += 1
    
    day_distribution = [{'day': days[i], 'count': day_counts[i]} for i in range(7)]
    
    # Appointment time of day distribution
    hour_counts = [0] * 24
    
    for appointment in Appointment.query.all():
        hour = appointment.time.hour
        hour_counts[hour] += 1
    
    time_distribution = [{'hour': hour, 'count': hour_counts[hour]} for hour in range(24)]
    
    # No-show rate over time
    year = datetime.now().year
    monthly_no_shows = []
    
    for month in range(1, 13):
        total = Appointment.query.filter(
            extract('year', Appointment.date) == year,
            extract('month', Appointment.date) == month
        ).count()
        
        no_shows = Appointment.query.filter(
            extract('year', Appointment.date) == year,
            extract('month', Appointment.date) == month,
            Appointment.status == 'No-Show'
        ).count()
        
        rate = 0 if total == 0 else (no_shows / total) * 100
        
        monthly_no_shows.append({
            'month': calendar.month_name[month],
            'rate': rate
        })
    
    return render_template('analytics/appointments.html',
                          title='Appointment Analytics',
                          appointment_outcomes=appointment_outcomes,
                          appointment_purposes=appointment_purposes,
                          day_distribution=day_distribution,
                          time_distribution=time_distribution,
                          monthly_no_shows=monthly_no_shows)

@bp.route('/communications')
@login_required
def communication_analytics():
    """Detailed communication analytics"""
    # Communication type distribution
    communication_types = db.session.query(
        Communication.type, func.count(Communication.id)
    ).group_by(Communication.type).all()
    
    # Communication status distribution
    communication_statuses = db.session.query(
        Communication.status, func.count(Communication.id)
    ).group_by(Communication.status).all()
    
    # Communications by hour of day
    hour_counts = [0] * 24
    
    for comm in Communication.query.all():
        hour = comm.sent_at.hour
        hour_counts[hour] += 1
    
    hour_distribution = [{'hour': hour, 'count': hour_counts[hour]} for hour in range(24)]
    
    # Communications by day of week
    days = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
    day_counts = [0] * 7
    
    for comm in Communication.query.all():
        day_of_week = comm.sent_at.weekday()
        day_counts[day_of_week] += 1
    
    day_distribution = [{'day': days[i], 'count': day_counts[i]} for i in range(7)]
    
    # Monthly communication trends
    year = datetime.now().year
    monthly_communications = []
    
    for month in range(1, 13):
        email_count = Communication.query.filter(
            extract('year', Communication.sent_at) == year,
            extract('month', Communication.sent_at) == month,
            Communication.type == 'Email'
        ).count()
        
        sms_count = Communication.query.filter(
            extract('year', Communication.sent_at) == year,
            extract('month', Communication.sent_at) == month,
            Communication.type == 'SMS'
        ).count()
        
        call_count = Communication.query.filter(
            extract('year', Communication.sent_at) == year,
            extract('month', Communication.sent_at) == month,
            Communication.type == 'Call'
        ).count()
        
        monthly_communications.append({
            'month': calendar.month_name[month],
            'email': email_count,
            'sms': sms_count,
            'call': call_count
        })
    
    return render_template('analytics/communications.html',
                          title='Communication Analytics',
                          communication_types=communication_types,
                          communication_statuses=communication_statuses,
                          hour_distribution=hour_distribution,
                          day_distribution=day_distribution,
                          monthly_communications=monthly_communications)

@bp.route('/export/<report_type>')
@login_required
@manager_required
def export_report(report_type):
    """Export analytics data in CSV or Excel format"""
    format_type = request.args.get('format', 'csv')
    
    if report_type == 'leads':
        data = Lead.query.all()
        headers = ['ID', 'First Name', 'Last Name', 'Email', 'Phone', 'Status', 
                  'Vehicle Interest', 'Source', 'Created At', 'Updated At']
        
        rows = [[
            lead.id, lead.first_name, lead.last_name, lead.email, lead.phone,
            lead.status, lead.vehicle_interest, lead.source, 
            lead.created_at.strftime('%Y-%m-%d %H:%M:%S'),
            lead.updated_at.strftime('%Y-%m-%d %H:%M:%S')
        ] for lead in data]
        
    elif report_type == 'appointments':
        data = Appointment.query.all()
        headers = ['ID', 'Lead ID', 'Date', 'Time', 'Purpose', 'Status', 'Notes', 'Created At']
        
        rows = [[
            appt.id, appt.lead_id, appt.date.strftime('%Y-%m-%d'), 
            appt.time.strftime('%H:%M:%S'), appt.purpose, appt.status, appt.notes,
            appt.created_at.strftime('%Y-%m-%d %H:%M:%S')
        ] for appt in data]
        
    elif report_type == 'communications':
        data = Communication.query.all()
        headers = ['ID', 'Lead ID', 'Type', 'Subject', 'Content', 'Status', 'Sent At']
        
        rows = [[
            comm.id, comm.lead_id, comm.type, comm.subject, comm.content,
            comm.status, comm.sent_at.strftime('%Y-%m-%d %H:%M:%S')
        ] for comm in data]
        
    elif report_type == 'users':
        if current_user.role != 'admin':
            return jsonify({'error': 'Unauthorized access'}), 403
            
        data = User.query.all()
        headers = ['ID', 'Username', 'Email', 'First Name', 'Last Name', 'Role', 'Active']
        
        rows = [[
            user.id, user.username, user.email, user.first_name, user.last_name,
            user.role, 'Yes' if user.is_active else 'No'
        ] for user in data]
        
    else:
        return jsonify({'error': 'Invalid report type'}), 400
    
    # Generate file in memory
    if format_type == 'csv':
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(headers)
        writer.writerows(rows)
        
        mem_file = io.BytesIO()
        mem_file.write(output.getvalue().encode('utf-8'))
        mem_file.seek(0)
        
        return send_file(
            mem_file,
            mimetype='text/csv',
            as_attachment=True,
            download_name=f'{report_type}_report_{datetime.now().strftime("%Y%m%d")}.csv'
        )
        
    elif format_type == 'excel':
        output = io.BytesIO()
        workbook = xlsxwriter.Workbook(output)
        worksheet = workbook.add_worksheet()
        
        # Add headers
        for col, header in enumerate(headers):
            worksheet.write(0, col, header)
        
        # Add data
        for row_idx, row_data in enumerate(rows, 1):
            for col_idx, cell_data in enumerate(row_data):
                worksheet.write(row_idx, col_idx, cell_data)
        
        workbook.close()
        output.seek(0)
        
        return send_file(
            output,
            mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            as_attachment=True,
            download_name=f'{report_type}_report_{datetime.now().strftime("%Y%m%d")}.xlsx'
        )
    
    else:
        return jsonify({'error': 'Invalid format type'}), 400

@bp.route('/api/chart_data/<chart_type>')
@login_required
def chart_data(chart_type):
    """API endpoint to get chart data for the analytics dashboards"""
    if chart_type == 'lead_sources':
        data = db.session.query(
            Lead.source, func.count(Lead.id).label('count')
        ).group_by(Lead.source).all()
        
        return jsonify({
            'labels': [item[0] or 'Unknown' for item in data],
            'data': [item[1] for item in data]
        })
        
    elif chart_type == 'lead_statuses':
        data = db.session.query(
            Lead.status, func.count(Lead.id).label('count')
        ).group_by(Lead.status).all()
        
        return jsonify({
            'labels': [item[0] for item in data],
            'data': [item[1] for item in data]
        })
        
    elif chart_type == 'monthly_leads':
        year = datetime.now().year
        data = []
        
        for month in range(1, 13):
            count = Lead.query.filter(
                extract('year', Lead.created_at) == year,
                extract('month', Lead.created_at) == month
            ).count()
            data.append(count)
        
        return jsonify({
            'labels': [calendar.month_name[month] for month in range(1, 13)],
            'data': data
        })
        
    elif chart_type == 'appointment_statuses':
        data = db.session.query(
            Appointment.status, func.count(Appointment.id).label('count')
        ).group_by(Appointment.status).all()
        
        return jsonify({
            'labels': [item[0] for item in data],
            'data': [item[1] for item in data]
        })
        
    elif chart_type == 'communication_types':
        data = db.session.query(
            Communication.type, func.count(Communication.id).label('count')
        ).group_by(Communication.type).all()
        
        return jsonify({
            'labels': [item[0] for item in data],
            'data': [item[1] for item in data]
        })
        
    elif chart_type == 'user_performance':
        if current_user.role not in ['admin', 'manager']:
            return jsonify({'error': 'Unauthorized access'}), 403
            
        data = db.session.query(
            User.username,
            func.count(Lead.id).label('leads')
        ).outerjoin(Lead, User.id == Lead.user_id
        ).group_by(User.username).all()
        
        return jsonify({
            'labels': [item[0] for item in data],
            'data': [item[1] for item in data]
        })
        
    else:
        return jsonify({'error': 'Invalid chart type'}), 400
